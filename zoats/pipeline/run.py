#!/usr/bin/env python3
"""Pipeline Orchestrator CLI - End-to-end candidate processing."""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Roots
ROOT = Path(__file__).resolve().parents[1]  # ZoATS/
JOBS_DIR = ROOT / "jobs"
WORKERS = ROOT / "workers"


def run_worker(worker_script: Path, args: List[str], dry_run: bool = False) -> Dict[str, Any]:
    cmd = [sys.executable, str(worker_script)] + args
    if dry_run and "--dry-run" not in args:
        cmd.append("--dry-run")
    logger.info(f"[run] {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "cmd": " ".join(cmd),
        "returncode": res.returncode,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "success": res.returncode == 0,
    }


def discover_candidates(job_path: Path) -> List[str]:
    cdir = job_path / "candidates"
    if not cdir.exists():
        return []
    return [p.name for p in cdir.iterdir() if p.is_dir()]


def process_candidate(job: str, candidate_id: str, dry_run: bool = False) -> Dict[str, Any]:
    results: Dict[str, Any] = {"candidate_id": candidate_id, "steps": {}}

    # Parser
    parser_res = run_worker(WORKERS / "parser" / "main.py", ["--job", job, "--candidate", candidate_id], dry_run)
    results["steps"]["parser"] = parser_res
    if not parser_res["success"]:
        logger.warning(f"[{candidate_id}] parser failed; skipping downstream")
        results["status"] = "parser_failed"
        return results

    # Quick Test (deal-breaker gate)
    quick_test_script = WORKERS / "quick_test" / "main.py"
    if quick_test_script.exists():
        quick_test_res = run_worker(quick_test_script, ["--job", job, "--candidate", candidate_id], dry_run)
        results["steps"]["quick_test"] = quick_test_res
        if not quick_test_res["success"]:
            logger.warning(f"[{candidate_id}] quick_test failed; skipping downstream")
            results["status"] = "quick_test_failed"
            return results
        
        # Check if quick test passed
        quick_test_path = JOBS_DIR / job / "candidates" / candidate_id / "outputs" / "quick_test.json"
        if quick_test_path.exists():
            quick_test_data = json.loads(quick_test_path.read_text())
            quick_test_status = quick_test_data.get("status", "unknown")
            results["quick_test_status"] = quick_test_status
            
            if quick_test_status == "fail":
                logger.info(f"[{candidate_id}] quick_test status=fail → skipping downstream")
                results["status"] = "rejected_quick_test"
                results["decision"] = "PASS"
                return results
        else:
            logger.warning(f"[{candidate_id}] quick_test.json not found, continuing anyway")
            results["quick_test_status"] = "unknown"
    else:
        logger.warning(f"[{candidate_id}] quick_test script not found, skipping")
        results["steps"]["quick_test"] = {"success": False, "reason": "not_found"}

    # Gestalt Scoring
    scorer_script = WORKERS / "scoring" / "main_gestalt.py"
    if scorer_script.exists():
        scorer_res = run_worker(scorer_script, ["--job", job, "--candidate", candidate_id], dry_run)
        results["steps"]["scorer"] = scorer_res
        if not scorer_res["success"]:
            results["status"] = "scorer_failed"
            return results
        
        # Check decision from gestalt evaluation
        eval_path = JOBS_DIR / job / "candidates" / candidate_id / "outputs" / "gestalt_evaluation.json"
        if eval_path.exists():
            eval_data = json.loads(eval_path.read_text())
            decision = eval_data.get("decision", "UNKNOWN")
            results["decision"] = decision
            
            # If MAYBE, trigger clarification flow
            if decision == "MAYBE":
                logger.info(f"[{candidate_id}] MAYBE decision → triggering clarification")
                clarif_script = WORKERS / "clarification" / "orchestrator.py"
                clarif_res = run_worker(clarif_script, ["--job", job, "--candidate", candidate_id], dry_run)
                results["steps"]["clarification"] = clarif_res
                results["status"] = "clarification_pending"
                return results
            
            # If BACKUP_LIST, add to backup instead of clarification
            elif decision == "BACKUP_LIST":
                logger.info(f"[{candidate_id}] BACKUP_LIST → adding to backup candidates")
                backup_script = WORKERS / "backup_list" / "manager.py"
                if backup_script.exists():
                    # Add to backup list (reads eval file internally)
                    import sys
                    from manager import add_to_backup_list
                    add_to_backup_list(job, candidate_id, eval_data)
                results["status"] = "backup_list"
                return results
        else:
            results["decision"] = "UNKNOWN"
    else:
        results["steps"]["scorer"] = {"success": False, "reason": "not_implemented"}

    # Dossier
    dossier_script = WORKERS / "dossier" / "main.py"
    if dossier_script.exists():
        dossier_res = run_worker(dossier_script, ["--job", job, "--candidate", candidate_id], dry_run)
        results["steps"]["dossier"] = dossier_res
        if not dossier_res["success"]:
            results["status"] = "dossier_failed"
            return results
    else:
        results["steps"]["dossier"] = {"success": False, "reason": "not_implemented"}
        results["status"] = "partial_complete"
        return results

    results["status"] = "complete"
    return results


def validate_job_readiness(job: str) -> None:
    job_dir = JOBS_DIR / job
    if not job_dir.exists():
        raise FileNotFoundError(f"Job not found: {job_dir}")

    jd = job_dir / "job-description.md"
    legacy_jd = job_dir / "job_description.md"
    if not jd.exists() and legacy_jd.exists():
        logger.warning(
            "[migrate] job_description.md detected. Canonical is job-description.md. "
            "Please rename for future runs."
        )
        jd = legacy_jd

    required = [
        (jd, "job description (job-description.md)"),
        (job_dir / "rubric.json", "rubric.json"),
        (job_dir / "deal_breakers.json", "deal_breakers.json"),
    ]
    missing = [name for p, name in required if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Job is not ready to run pipeline. Missing required file(s): "
            + ", ".join(missing)
            + f". Job dir: {job_dir}"
        )


def main() -> int:
    ap = argparse.ArgumentParser(description="ZoATS Pipeline Orchestrator")
    ap.add_argument("--job", required=True)
    ap.add_argument("--from-inbox", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="Reprocess already-processed candidates")
    args = ap.parse_args()

    job_path = JOBS_DIR / args.job
    if not job_path.exists():
        logger.error(f"Job not found: {job_path}")
        return 1

    try:
        validate_job_readiness(args.job)
    except Exception as e:
        logger.error(str(e))
        return 1

    logger.info(f"[pipeline] starting for job: {args.job}")
    results: Dict[str, Any] = {"job": args.job, "stages": {}}

    # Optional intake
    if args.from_inbox:
        intake_script = WORKERS / "intake" / "main.py"
        intake_res = run_worker(intake_script, ["--job", args.job], dry_run=args.dry_run)
        results["stages"]["intake"] = intake_res
        if not intake_res["success"]:
            logger.error("[stage] intake failed; continuing with existing candidates")

    candidates = discover_candidates(job_path)

    # Idempotency: skip already-processed candidates unless --force
    if not args.dry_run and not args.force:
        unprocessed = []
        for cid in candidates:
            marker = job_path / "candidates" / cid / ".processed"
            if marker.exists():
                logger.info(f"Skipping already-processed candidate: {cid}")
            else:
                unprocessed.append(cid)
        candidates = unprocessed

    if not candidates:
        logger.warning(f"[pipeline] no candidates found in {job_path / 'candidates'}")
        results["candidates_processed"] = 0
        results["summary"] = {"total": 0, "complete": 0, "partial": 0, "failed": 0}
        print(json.dumps(results, indent=2))
        return 0

    logger.info(f"[pipeline] discovered {len(candidates)} candidate(s)")

    cand_results: List[Dict[str, Any]] = []
    for cid in candidates:
        try:
            result = process_candidate(args.job, cid, dry_run=args.dry_run)
            cand_results.append(result)
            # Write .processed marker on successful completion
            if not args.dry_run and result.get("status") in ("complete", "partial_complete"):
                from datetime import datetime, timezone
                marker = job_path / "candidates" / cid / ".processed"
                marker.write_text(datetime.now(timezone.utc).isoformat())
        except Exception as e:
            logger.exception(f"[pipeline] error processing {cid}: {e}")
            cand_results.append({"candidate_id": cid, "status": "error", "error": str(e)})

    complete = sum(1 for r in cand_results if r.get("status") == "complete")
    partial = sum(1 for r in cand_results if r.get("status") == "partial_complete")
    clarification_pending = sum(1 for r in cand_results if r.get("status") == "clarification_pending")
    failed = len(cand_results) - complete - partial - clarification_pending

    # Decision breakdown
    decision_breakdown = {
        "STRONG_INTERVIEW": sum(1 for r in cand_results if r.get("decision") == "STRONG_INTERVIEW"),
        "INTERVIEW": sum(1 for r in cand_results if r.get("decision") == "INTERVIEW"),
        "MAYBE": sum(1 for r in cand_results if r.get("decision") == "MAYBE"),
        "PASS_quick_test": sum(1 for r in cand_results if r.get("status") == "rejected_quick_test"),
        "PASS_scoring": sum(1 for r in cand_results if r.get("decision") == "PASS" and r.get("status") != "rejected_quick_test"),
        "BACKUP_LIST": sum(1 for r in cand_results if r.get("decision") == "BACKUP_LIST"),
        "UNKNOWN": sum(1 for r in cand_results if r.get("decision") == "UNKNOWN" or "decision" not in r),
    }

    results["candidates_processed"] = len(cand_results)
    results["candidate_results"] = cand_results
    results["summary"] = {
        "total": len(cand_results), 
        "complete": complete, 
        "partial": partial, 
        "clarification_pending": clarification_pending,
        "failed": failed,
        "decision_breakdown": decision_breakdown
    }

    log_file = job_path / "pipeline_run.json"
    if not args.dry_run:
        log_file.write_text(json.dumps(results, indent=2))
        logger.info(f"[pipeline] wrote log to {log_file}")
    else:
        logger.info(f"[dry-run] would write log to {log_file}")

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
