#!/usr/bin/env python3
"""Intake Trigger — moves inbox_drop submissions into job candidate folders
and optionally kicks off the pipeline.

Usage:
    python3 scripts/intake_trigger.py --once            # process queue and exit
    python3 scripts/intake_trigger.py --poll 30         # poll every 30s
    python3 scripts/intake_trigger.py --once --dry-run  # preview without moving
"""

import argparse
import json
import logging
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lib.paths import ZOATS_HOME

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INBOX_DIR = ZOATS_HOME / "inbox_drop"
JOBS_DIR = ZOATS_HOME / "jobs"
PROCESSED_DIR = INBOX_DIR / ".processed"
ERRORS_DIR = INBOX_DIR / ".errors"


def load_settings() -> Dict[str, Any]:
    settings_path = ZOATS_HOME / "config" / "settings.json"
    if settings_path.exists():
        return json.loads(settings_path.read_text())
    return {}


def discover_submissions() -> List[Path]:
    """Find unprocessed submission folders in inbox_drop/."""
    if not INBOX_DIR.exists():
        return []
    submissions = []
    for entry in sorted(INBOX_DIR.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue
        submission_json = entry / "submission.json"
        if submission_json.exists():
            submissions.append(entry)
    return submissions


def generate_candidate_id(name: str) -> str:
    """Generate a candidate ID from submission timestamp and name."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe = name.strip().lower().replace(" ", "-")[:20]
    return f"{ts}--{safe}"


def process_submission(submission_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Process a single inbox_drop submission into a job candidate folder."""
    result: Dict[str, Any] = {"submission": submission_dir.name, "steps": []}

    # Read submission metadata
    sub_json = submission_dir / "submission.json"
    try:
        sub_data = json.loads(sub_json.read_text())
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Cannot read submission.json: {e}"
        return result

    job_id = sub_data.get("job_id", "unknown")
    name = sub_data.get("name", "unknown")
    result["job_id"] = job_id
    result["applicant"] = name

    # Validate job exists
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists():
        logger.error(f"[intake] Job not found: {job_id} — moving to .errors/")
        result["status"] = "error_no_job"
        result["error"] = f"Job directory not found: {job_dir}"
        if not dry_run:
            ERRORS_DIR.mkdir(parents=True, exist_ok=True)
            error_dest = ERRORS_DIR / submission_dir.name
            shutil.move(str(submission_dir), str(error_dest))
            # Write error log
            error_log = error_dest / "intake_error.json"
            error_log.write_text(json.dumps({
                "error": f"Job not found: {job_id}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, indent=2))
            result["steps"].append(f"Moved to {error_dest}")
        return result

    # Generate candidate ID and create folder
    candidate_id = generate_candidate_id(name)
    candidate_dir = job_dir / "candidates" / candidate_id
    raw_dir = candidate_dir / "raw"

    logger.info(f"[intake] {name} → {job_id}/candidates/{candidate_id}")
    result["candidate_id"] = candidate_id

    if dry_run:
        result["steps"].append(f"Would create: {candidate_dir}")
        result["steps"].append(f"Would copy resume to: {raw_dir}")
        result["steps"].append(f"Would copy submission.json to: {candidate_dir}")
        result["steps"].append(f"Would move {submission_dir.name} to .processed/")
        result["status"] = "dry_run"
        return result

    # Create candidate directory
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Copy resume files from inbox raw/ to candidate raw/
    inbox_raw = submission_dir / "raw"
    if inbox_raw.exists():
        for f in inbox_raw.iterdir():
            shutil.copy2(str(f), str(raw_dir / f.name))
            result["steps"].append(f"Copied {f.name} → {raw_dir / f.name}")
    else:
        logger.warning(f"[intake] No raw/ directory in {submission_dir.name}")

    # Copy submission.json
    shutil.copy2(str(sub_json), str(candidate_dir / "submission.json"))
    result["steps"].append("Copied submission.json")

    # Move to .processed/
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    processed_dest = PROCESSED_DIR / submission_dir.name
    shutil.move(str(submission_dir), str(processed_dest))
    result["steps"].append(f"Moved to {processed_dest}")

    result["status"] = "intake_complete"
    return result


def trigger_pipeline(job_id: str, candidate_id: str, dry_run: bool = False) -> Dict[str, Any]:
    """Optionally trigger the pipeline for a newly-ingested candidate."""
    pipeline_script = ZOATS_HOME / "pipeline" / "run.py"
    if not pipeline_script.exists():
        return {"triggered": False, "reason": "pipeline/run.py not found"}

    cmd = [sys.executable, str(pipeline_script), "--job", job_id]
    if dry_run:
        cmd.append("--dry-run")

    logger.info(f"[intake] Triggering pipeline: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return {
        "triggered": True,
        "returncode": res.returncode,
        "success": res.returncode == 0,
        "stdout_tail": res.stdout[-500:] if res.stdout else "",
        "stderr_tail": res.stderr[-500:] if res.stderr else "",
    }


def run_once(dry_run: bool = False) -> List[Dict[str, Any]]:
    """Process all pending submissions and exit."""
    settings = load_settings()
    auto_pipeline = settings.get("auto_pipeline", False)

    submissions = discover_submissions()
    if not submissions:
        logger.info("[intake] No pending submissions in inbox_drop/")
        return []

    logger.info(f"[intake] Found {len(submissions)} pending submission(s)")
    results = []

    for sub_dir in submissions:
        result = process_submission(sub_dir, dry_run=dry_run)
        results.append(result)

        # Trigger pipeline if configured and intake succeeded
        if auto_pipeline and result.get("status") == "intake_complete":
            job_id = result.get("job_id", "")
            candidate_id = result.get("candidate_id", "")
            if job_id and candidate_id:
                pipeline_result = trigger_pipeline(job_id, candidate_id, dry_run=dry_run)
                result["pipeline"] = pipeline_result
                if pipeline_result.get("success"):
                    logger.info(f"[intake] Pipeline completed for {candidate_id}")
                elif pipeline_result.get("triggered"):
                    logger.warning(f"[intake] Pipeline failed for {candidate_id}")

    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="ZoATS Intake Trigger")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true", help="Process queue and exit")
    mode.add_argument("--poll", type=int, metavar="SECONDS", help="Poll interval in seconds")
    ap.add_argument("--dry-run", action="store_true", help="Preview without moving files")

    args = ap.parse_args()

    logger.info(f"[intake] ZOATS_HOME={ZOATS_HOME}")
    logger.info(f"[intake] inbox_drop={INBOX_DIR}")

    if args.once:
        results = run_once(dry_run=args.dry_run)
        print(json.dumps(results, indent=2, default=str))
        return 0

    # Polling mode
    logger.info(f"[intake] Polling every {args.poll}s (Ctrl+C to stop)")
    try:
        while True:
            results = run_once(dry_run=args.dry_run)
            if results:
                for r in results:
                    status = r.get("status", "unknown")
                    logger.info(f"[intake] {r.get('applicant', '?')} → {status}")
            time.sleep(args.poll)
    except KeyboardInterrupt:
        logger.info("[intake] Stopped")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
