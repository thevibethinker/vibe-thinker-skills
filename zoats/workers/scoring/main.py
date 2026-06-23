#!/usr/bin/env python3
"""
Main Gestalt Scoring Entry Point

Usage:
  python workers/scoring/main_gestalt.py --job <job-id> --candidate <candidate-id> [--dry-run]
"""
import sys as _sys
from pathlib import Path as _Path
_REPO_ROOT = _Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))
import argparse
import json
import logging
import sys
from pathlib import Path

from workers.scoring.gestalt_scorer import evaluate_gestalt

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_rubric(job_dir: Path):
    rubric_path = job_dir / "rubric.json"
    if rubric_path.exists():
        return json.loads(rubric_path.read_text())
    return {}


def load_resume(candidate_dir: Path):
    text_path = candidate_dir / "parsed" / "text.md"
    if not text_path.exists():
        raise FileNotFoundError(f"Resume not found: {text_path}")
    return text_path.read_text()


def main():
    parser = argparse.ArgumentParser(description="Gestalt evaluation")
    parser.add_argument("--job", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    try:
        # Load data
        job_dir = Path(f"jobs/{args.job}")
        candidate_dir = job_dir / "candidates" / args.candidate
        
        rubric = load_rubric(job_dir)
        resume_text = load_resume(candidate_dir)
        
        # Evaluate
        logger.info(f"Evaluating {args.candidate} for {args.job}...")
        result = evaluate_gestalt(resume_text, rubric, args.job, args.candidate)
        
        # Write output
        output_dir = candidate_dir / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "gestalt_evaluation.json"
        
        if args.dry_run:
            logger.info(f"[DRY RUN] Would write: {output_path}")
            print(json.dumps(result.to_dict(), indent=2))
        else:
            output_path.write_text(json.dumps(result.to_dict(), indent=2))
            logger.info(f"✓ Wrote evaluation → {output_path}")
        
        logger.info(f"  Decision: {result.decision} (confidence: {result.confidence})")
        logger.info(f"  {result.overall_narrative}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
