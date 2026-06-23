#!/usr/bin/env python3
"""
Batch runner for MAYBE clarification emails.
- Scans one job (or all jobs) for candidates with decision == "MAYBE"
- Generates individualized clarification_email.md drafts (approval gated)
- Updates a job-level approvals manifest at jobs/{job_id}/approvals/maybe_pending.json

Usage:
  python workers/maybe_email/batch.py --job <job-id> [--dry-run]
  python workers/maybe_email/batch.py --all-jobs [--dry-run]
"""
import argparse, json, logging, subprocess
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
JOBS_DIR = ROOT / "jobs"
MAIN = ROOT / "workers" / "maybe_email" / "main.py"


def list_jobs() -> list[Path]:
    return [p for p in JOBS_DIR.iterdir() if p.is_dir()]


def read_json(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def append_manifest(job_dir: Path, candidate_id: str, email_path: Path, dry_run: bool) -> None:
    approvals_dir = job_dir / "approvals"
    manifest_path = approvals_dir / "maybe_pending.json"
    approvals_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = []
    # de-dupe
    if any(item.get("candidate_id") == candidate_id for item in manifest):
        logger.info(f"Already in manifest: {candidate_id}")
        return
    manifest.append({
        "candidate_id": candidate_id,
        "email_path": str(email_path),
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    if dry_run:
        logger.info(f"[DRY RUN] Would update manifest: {manifest_path}")
    else:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"✓ Manifest updated: {manifest_path}")


def process_job(job_dir: Path, dry_run: bool) -> int:
    candidates_dir = job_dir / "candidates"
    if not candidates_dir.exists():
        return 0
    count = 0
    for cand_dir in sorted(candidates_dir.iterdir()):
        ge = cand_dir / "outputs" / "gestalt_evaluation.json"
        if not ge.exists():
            continue
        data = read_json(ge)
        if not data or data.get("decision") != "MAYBE":
            continue
        candidate_id = cand_dir.name
        cmd = ["python", str(MAIN), "--job", job_dir.name, "--candidate", candidate_id]
        if dry_run:
            cmd.append("--dry-run")
        logger.info(f"Running: {' '.join(cmd)}")
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if res.returncode != 0:
            logger.error(f"Composer failed for {candidate_id}: {res.stderr or res.stdout}")
            continue
        # determine output path
        email_path = cand_dir / "outputs" / "clarification_email.md"
        if email_path.exists() or dry_run:
            append_manifest(job_dir, candidate_id, email_path, dry_run=dry_run)
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="Batch-generate MAYBE clarification emails with approval gating")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--job", help="Job ID to scan (e.g., test-fixture)")
    g.add_argument("--all-jobs", action="store_true", help="Scan all jobs")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing manifests")
    args = parser.parse_args()

    if args.all_jobs:
        total = 0
        for job in list_jobs():
            c = process_job(job, dry_run=args.dry_run)
            if c:
                logger.info(f"Job {job.name}: {c} MAYBE drafts queued")
            total += c
        logger.info(f"✓ Complete. Total MAYBE drafts queued: {total}")
    else:
        job_dir = JOBS_DIR / args.job
        if not job_dir.exists():
            logger.error(f"Job not found: {job_dir}")
            return 1
        c = process_job(job_dir, dry_run=args.dry_run)
        logger.info(f"✓ Complete. {c} MAYBE drafts queued for {args.job}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
