#!/usr/bin/env python3
"""
Re-evaluate with Clarification

Re-runs gestalt evaluation with candidate's clarification responses.
Updates decision: MAYBE → INTERVIEW or PASS
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
from typing import Dict

# Import gestalt scorer
from workers.scoring.gestalt_scorer import evaluate_gestalt

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_original_evaluation(job_id: str, candidate_id: str) -> Dict:
    """Load original MAYBE evaluation"""
    eval_path = Path(f"jobs/{job_id}/candidates/{candidate_id}/outputs/gestalt_evaluation.json")
    if not eval_path.exists():
        raise FileNotFoundError(f"Original evaluation not found: {eval_path}")
    return json.loads(eval_path.read_text())


def load_clarification_response(job_id: str, candidate_id: str) -> Dict:
    """Load candidate's response"""
    response_path = Path(f"jobs/{job_id}/candidates/{candidate_id}/outputs/clarification_response.json")
    if not response_path.exists():
        raise FileNotFoundError(f"Clarification response not found: {response_path}")
    return json.loads(response_path.read_text())


def augment_resume_with_responses(resume_text: str, response_data: Dict) -> str:
    """Append clarification responses to resume"""
    augmented = resume_text + "\n\n---\n\n"
    augmented += "## CLARIFICATION RESPONSES\n\n"
    
    for key, answer in response_data["answers"].items():
        if key != "full_response":
            augmented += f"**{key.upper()}:** {answer}\n\n"
    
    return augmented


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-evaluate with clarification")
    parser.add_argument("--job", required=True, help="Job ID")
    parser.add_argument("--candidate", required=True, help="Candidate ID")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    parser.add_argument("--force", action="store_true", help="Force re-evaluation even if not MAYBE")
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Re-evaluating {args.candidate} for {args.job}")
        
        # Load original evaluation
        original_eval = load_original_evaluation(args.job, args.candidate)
        
        # Check original decision
        if original_eval["decision"] != "MAYBE" and not args.force:
            logger.warning(f"Original decision was {original_eval['decision']}, not MAYBE")
            logger.info("Re-evaluation is for MAYBE candidates who provided clarification")
            logger.info("Use --force to override")
            return 1
        
        # Load clarification response
        response_data = load_clarification_response(args.job, args.candidate)
        
        # Load resume
        resume_path = Path(f"jobs/{args.job}/candidates/{args.candidate}/parsed/text.md")
        resume_text = resume_path.read_text()
        
        # Augment resume with responses
        augmented_resume = augment_resume_with_responses(resume_text, response_data)
        
        # Load rubric
        rubric_path = Path(f"jobs/{args.job}/rubric.json")
        rubric = json.loads(rubric_path.read_text()) if rubric_path.exists() else {}
        
        # Re-evaluate
        logger.info("Running re-evaluation with clarification...")
        new_eval = evaluate_gestalt(
            resume_text=augmented_resume,
            rubric=rubric,
            job_id=args.job,
            candidate_id=args.candidate
        )
        
        logger.info(f"Original decision: {original_eval['decision']}")
        logger.info(f"New decision: {new_eval.decision}")
        logger.info(f"Confidence: {new_eval.confidence}")
        logger.info(f"Narrative: {new_eval.overall_narrative}")
        
        if args.dry_run:
            logger.info("[DRY RUN] Would save new evaluation")
            logger.info(json.dumps(new_eval.to_dict(), indent=2))
            return 0
        
        # Save new evaluation
        eval_path = Path(f"jobs/{args.job}/candidates/{args.candidate}/outputs/gestalt_evaluation.json")
        eval_path.write_text(json.dumps(new_eval.to_dict(), indent=2))
        
        # Save comparison
        comparison = {
            "candidate_id": args.candidate,
            "job_id": args.job,
            "original_decision": original_eval["decision"],
            "new_decision": new_eval.decision,
            "original_concerns": [c["issue"] for c in original_eval["concerns"]],
            "new_concerns": [c.issue for c in new_eval.concerns],
            "clarification_effective": new_eval.decision != "PASS",
            "reevaluated_at": new_eval.timestamp
        }
        
        comparison_path = Path(f"jobs/{args.job}/candidates/{args.candidate}/outputs/reevaluation_comparison.json")
        comparison_path.write_text(json.dumps(comparison, indent=2))
        
        logger.info(f"✓ Saved new evaluation: {eval_path}")
        logger.info(f"✓ Saved comparison: {comparison_path}")
        
        if new_eval.decision == "INTERVIEW":
            logger.info("🎉 Candidate moved to INTERVIEW after clarification")
        elif new_eval.decision == "STRONG_INTERVIEW":
            logger.info("🎉🎉 Candidate moved to STRONG_INTERVIEW after clarification")
        else:
            logger.info(f"Candidate remains: {new_eval.decision}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
