#!/usr/bin/env python3
"""
Backup List Manager

Manages candidates with too many unknowns to justify immediate clarification.
These candidates are revisited only if the shortlist is insufficient.
"""
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def add_to_backup_list(job_id: str, candidate_id: str, evaluation: Dict) -> None:
    """Add candidate to backup list"""
    job_dir = Path(f"jobs/{job_id}")
    backup_file = job_dir / "backup_list.json"
    
    # Load existing
    if backup_file.exists():
        backup_data = json.loads(backup_file.read_text())
    else:
        backup_data = {
            "job_id": job_id,
            "candidates": [],
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
    
    # Add candidate
    backup_data["candidates"].append({
        "candidate_id": candidate_id,
        "added_at": datetime.utcnow().isoformat() + "Z",
        "reason": "Too many unknowns to justify clarification effort",
        "concerns": [c["issue"] for c in evaluation.get("concerns", [])],
        "strengths": [s["category"] for s in evaluation.get("key_strengths", [])],
        "narrative": evaluation.get("overall_narrative", ""),
        "status": "backup"
    })
    
    backup_data["last_updated"] = datetime.utcnow().isoformat() + "Z"
    backup_data["count"] = len(backup_data["candidates"])
    
    # Write
    backup_file.write_text(json.dumps(backup_data, indent=2))
    logger.info(f"✓ Added {candidate_id} to backup list ({backup_data['count']} total)")


def get_backup_list(job_id: str) -> List[Dict]:
    """Get all backup candidates for a job"""
    backup_file = Path(f"jobs/{job_id}/backup_list.json")
    if not backup_file.exists():
        return []
    
    data = json.loads(backup_file.read_text())
    return data.get("candidates", [])


def promote_from_backup(job_id: str, candidate_id: str) -> bool:
    """Promote a candidate from backup to active consideration"""
    backup_file = Path(f"jobs/{job_id}/backup_list.json")
    if not backup_file.exists():
        logger.error(f"No backup list found for {job_id}")
        return False
    
    data = json.loads(backup_file.read_text())
    candidates = data.get("candidates", [])
    
    # Find and update
    found = False
    for cand in candidates:
        if cand["candidate_id"] == candidate_id:
            cand["status"] = "promoted"
            cand["promoted_at"] = datetime.utcnow().isoformat() + "Z"
            found = True
            break
    
    if found:
        data["last_updated"] = datetime.utcnow().isoformat() + "Z"
        backup_file.write_text(json.dumps(data, indent=2))
        logger.info(f"✓ Promoted {candidate_id} from backup to active")
        return True
    else:
        logger.error(f"Candidate {candidate_id} not found in backup list")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup List Manager")
    parser.add_argument("--job", required=True)
    parser.add_argument("--action", choices=["list", "promote"], required=True)
    parser.add_argument("--candidate", help="Candidate ID for promote action")
    args = parser.parse_args()
    
    if args.action == "list":
        candidates = get_backup_list(args.job)
        print(json.dumps({"job_id": args.job, "backup_candidates": candidates, "count": len(candidates)}, indent=2))
    
    elif args.action == "promote":
        if not args.candidate:
            logger.error("--candidate required for promote action")
            return 1
        success = promote_from_backup(args.job, args.candidate)
        return 0 if success else 1
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
