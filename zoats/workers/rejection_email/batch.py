#!/usr/bin/env python3
"""
Batch runner for REJECTION/PASS email drafts (for human approval).
- Scans one job (or all jobs) for candidates with decision in {"REJECT", "PASS"}
- Generates individualized decline email drafts per candidate
- Queues each draft in approvals manifest jobs/{job_id}/approvals/reject_pending.json
- Never sends email; drafts only

Usage:
  python workers/rejection_email/batch.py --job <job-id> [--dry-run] [--limit N]
  python workers/rejection_email/batch.py --all-jobs [--dry-run] [--limit N]
"""

import argparse, json, logging, subprocess
from datetime import datetime, UTC
from pathlib import Path
from lib.paths import ZOATS_HOME

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

WS = ZOATS_HOME


def run_decline(job_id: str, candidate_id: str, dry_run: bool) -> int:
    cmd = [
        "python",
        str(WS / "workers" / "rejection_email" / "main.py"),
        "--job", job_id,
        "--candidate", candidate_id,
    ]
    if dry_run:
        cmd.append("--dry-run")
    logger.info("Running: %s", " ".join(cmd))
    return subprocess.call(cmd)


def queue_manifest(job_dir: Path, candidate_id: str, email_path: Path, dry_run: bool) -> None:
    approvals_dir = job_dir / "approvals"
    approvals_dir.mkdir(parents=True, exist_ok=True)
    manifest = approvals_dir / "reject_pending.json"
    record = {
        "candidate_id": candidate_id,
        "email_path": str(email_path),
        "status": "pending",
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    if dry_run:
        logger.info("[DRY RUN] Would update manifest: %s with %s", manifest, record)
        return
    data = []
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text())
        except Exception:
            logger.warning("Manifest unreadable; recreating: %s", manifest)
    # de-dupe by candidate_id
    data = [r for r in data if r.get("candidate_id") != candidate_id]
    data.append(record)
    manifest.write_text(json.dumps(data, indent=2))
    logger.info("Queued approval: %s", record)


def scan_job(job_dir: Path, dry_run: bool, limit: int) -> int:
    candidates_dir = job_dir / "candidates"
    if not candidates_dir.exists():
        return 0
    count = 0
    for cand_dir in candidates_dir.iterdir():
        ge = cand_dir / "outputs" / "gestalt_evaluation.json"
        if not ge.exists():
            continue
        # skip if draft already exists
        email_path = cand_dir / "outputs" / "rejection_email.md"
        if email_path.exists():
            continue
        try:
            decision = json.loads(ge.read_text()).get("decision")
        except Exception:
            continue
        if decision not in {"REJECT", "PASS"}:
            continue
        # run decline draft
        rc = run_decline(job_dir.name, cand_dir.name, dry_run)
        queue_manifest(job_dir, cand_dir.name, email_path, dry_run)
        count += 1
        if limit and count >= limit:
            break
    return count


def main() -> int:
    p = argparse.ArgumentParser(description="Queue rejection email drafts for approval")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--job")
    g.add_argument("--all-jobs", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0, help="Max candidates to process (0 = no limit)")
    args = p.parse_args()

    if args.all_jobs:
        total = 0
        jobs_dir = WS / "jobs"
        for job_dir in jobs_dir.iterdir():
            if not job_dir.is_dir():
                continue
            c = scan_job(job_dir, dry_run=args.dry_run, limit=args.limit)
            logger.info("Job %s: %d drafts queued", job_dir.name, c)
            total += c
            if args.limit and total >= args.limit:
                break
        logger.info("✓ Complete. %d rejection drafts queued across all jobs", total)
        return 0
    else:
        job_dir = WS / "jobs" / args.job
        c = scan_job(job_dir, dry_run=args.dry_run, limit=args.limit)
        logger.info("✓ Complete. %d rejection drafts queued for %s", c, args.job)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
