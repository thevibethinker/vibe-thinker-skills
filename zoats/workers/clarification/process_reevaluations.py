#!/usr/bin/env python3
"""
Process Re-evaluation Queue

Processes candidates who submitted clarification responses.
Runs reevaluate.py for each queued candidate.
"""
import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import List

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def find_pending_reevaluations(job_id: str) -> List[Path]:
    """Find all pending re-evaluation tasks"""
    queue_dir = Path(f"jobs/{job_id}/reevaluation_queue")
    if not queue_dir.exists():
        return []
    
    pending = []
    for task_file in queue_dir.glob("*_reeval.json"):
        task = json.loads(task_file.read_text())
        if task.get("status") == "pending":
            pending.append(task_file)
    
    return pending


def process_reevaluation(job_id: str, task_file: Path, dry_run: bool = False) -> bool:
    """Process a single re-evaluation task"""
    task = json.loads(task_file.read_text())
    candidate_id = task["candidate_id"]
    
    logger.info(f"Re-evaluating {candidate_id}...")
    
    if dry_run:
        logger.info(f"[DRY RUN] Would re-evaluate {candidate_id}")
        return True
    
    # Run reevaluate.py
    reevaluate_script = Path(__file__).parent / "reevaluate.py"
    
    try:
        result = subprocess.run(
            ["python3", str(reevaluate_script), "--job", job_id, "--candidate", candidate_id, "--force"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info(f"✓ Re-evaluated {candidate_id}")
            
            # Mark task as complete
            task["status"] = "complete"
            task["completed_at"] = json.loads('{"timestamp":""}')["timestamp"]  # UTC timestamp
            task_file.write_text(json.dumps(task, indent=2))
            
            return True
        else:
            logger.error(f"Re-evaluation failed for {candidate_id}: {result.stderr}")
            
            # Mark as failed
            task["status"] = "failed"
            task["error"] = result.stderr[:500]
            task_file.write_text(json.dumps(task, indent=2))
            
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Re-evaluation timed out for {candidate_id}")
        task["status"] = "failed"
        task["error"] = "Timeout"
        task_file.write_text(json.dumps(task, indent=2))
        return False
    except Exception as e:
        logger.error(f"Error processing {candidate_id}: {e}")
        task["status"] = "failed"
        task["error"] = str(e)
        task_file.write_text(json.dumps(task, indent=2))
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Process re-evaluation queue")
    parser.add_argument("--job", required=True, help="Job ID")
    parser.add_argument("--dry-run", action="store_true", help="Check without processing")
    
    args = parser.parse_args()
    
    try:
        # Find pending tasks
        pending = find_pending_reevaluations(args.job)
        
        if not pending:
            logger.info("No pending re-evaluations")
            return 0
        
        logger.info(f"Processing {len(pending)} re-evaluation(s)")
        
        # Process each task
        success_count = 0
        for task_file in pending:
            if process_reevaluation(args.job, task_file, dry_run=args.dry_run):
                success_count += 1
        
        logger.info(f"✓ Processed {success_count}/{len(pending)} re-evaluations")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
