#!/usr/bin/env python3
"""
Clarification Orchestrator

Manages the complete flow:
1. Generate clarification questions from MAYBE evaluation
2. Create approval request for employer
3. Wait for employer approval
4. Send email to candidate (via Zo email)
5. Track response
6. Re-evaluate with clarification
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

from workers.clarification.email_composer import compose_email, save_email_draft
from workers.clarification.approval_workflow import create_approval_request, save_approval_request
from workers.clarification.employer_email_templates import format_approval_request_email as format_approval_email
from workers.clarification.employer_email_templates import format_approval_request_email

# Import Zo tools

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def initiate_clarification_flow(
    job_id: str,
    candidate_id: str,
    job_dir: Path,
    dry_run: bool = False
) -> Dict:
    """
    Initiate clarification flow for MAYBE candidate.
    
    Steps:
    1. Load gestalt evaluation
    2. Check if MAYBE decision
    3. Create approval request
    4. Generate email draft
    5. Return status
    
    Args:
        job_id: Job identifier
        candidate_id: Candidate identifier
        job_dir: Path to job directory
        dry_run: If True, don't write files
    
    Returns:
        Status dict with next actions
    """
    logger.info(f"Initiating clarification flow: {job_id}/{candidate_id}")
    
    # Load gestalt evaluation
    candidate_dir = job_dir / "candidates" / candidate_id
    eval_path = candidate_dir / "outputs" / "gestalt_evaluation.json"
    
    if not eval_path.exists():
        raise FileNotFoundError(f"Gestalt evaluation not found: {eval_path}")
    
    eval_data = json.loads(eval_path.read_text())
    
    # Check decision
    if eval_data.get("decision") != "MAYBE":
        logger.info(f"Candidate is {eval_data.get('decision')}, not MAYBE. No clarification needed.")
        return {
            "status": "not_needed",
            "decision": eval_data.get("decision"),
            "message": "Candidate does not require clarification"
        }
    
    # Extract data
    questions = eval_data.get("clarification_questions", [])
    if not questions:
        raise ValueError("MAYBE decision but no clarification questions found")
    
    concerns = eval_data.get("concerns", [])
    rationale = "; ".join([c.get("issue", "") for c in concerns[:3]])
    
    candidate_summary = eval_data.get("overall_narrative", "")
    
    # Get candidate email from parsed fields
    fields_path = candidate_dir / "parsed" / "fields.json"
    candidate_email = "unknown@example.com"
    if fields_path.exists():
        fields = json.loads(fields_path.read_text())
        candidate_email = fields.get("email", candidate_email)
    
    # Get job title from rubric
    rubric_path = job_dir / "rubric.json"
    job_title = job_id
    if rubric_path.exists():
        rubric = json.loads(rubric_path.read_text())
        job_title = rubric.get("job_title", job_id)
    
    # Create approval request
    approval_request = create_approval_request(
        candidate_id=candidate_id,
        job_id=job_id,
        questions=questions,
        rationale=f"MAYBE decision. Concerns: {rationale}",
        candidate_summary=candidate_summary
    )
    
    # Generate email draft
    email_draft = compose_email(
        candidate_id=candidate_id,
        job_id=job_id,
        job_title=job_title,
        candidate_email=candidate_email,
        questions=questions,
        company_name="The hiring team"
    )
    
    if not dry_run:
        # Save approval request
        approval_path = save_approval_request(approval_request, job_dir)
        logger.info(f"✓ Saved approval request: {approval_path}")
        
        # Send approval email to employer (V)
        try:
            from workers.clarification.employer_email_templates import format_approval_request_email
            
            email_content = format_approval_request_email(
                candidate_id=candidate_id,
                job_title=job_title,
                candidate_summary=candidate_summary,
                rationale=f"MAYBE decision. Concerns: {rationale}",
                questions=questions,
                request_id=approval_request.request_id
            )
            
            # Import and use send_email_to_user
            import __main__
            if hasattr(__main__, 'send_email_to_user'):
                __main__.send_email_to_user(
                    subject=email_content.subject,
                    markdown_body=email_content.body_markdown
                )
                logger.info("✓ Sent approval request email to employer")
            else:
                logger.warning("[SIMULATION] send_email_to_user not available")
                logger.info(f"Would send: {email_content.subject}")
        except Exception as e:
            logger.error(f"Failed to send employer email: {e}")
            logger.info("Approval request saved but employer must be notified manually")
        
        # Save email draft
        email_path = save_email_draft(email_draft, job_dir)
        logger.info(f"✓ Saved email draft: {email_path}")
    else:
        logger.info("[DRY RUN] Would save approval request and email draft")
    
    # Format employer notification
    #     employer_email = format_approval_request_email(approval_request, job_title)
    
    return {
        "status": "pending_approval",
        "approval_request_id": approval_request.request_id,
        "candidate_email": candidate_email,
        "questions_count": len(questions),
        #         "employer_notification": employer_email,
        "message": f"Clarification flow initiated. Awaiting employer approval for {len(questions)} questions."
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Initiate clarification flow for MAYBE candidates")
    parser.add_argument("--job", required=True, help="Job ID")
    parser.add_argument("--candidate", required=True, help="Candidate ID")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    
    args = parser.parse_args()
    
    try:
        job_dir = Path(f"jobs/{args.job}")
        
        if not job_dir.exists():
            raise FileNotFoundError(f"Job directory not found: {job_dir}")
        
        result = initiate_clarification_flow(
            job_id=args.job,
            candidate_id=args.candidate,
            job_dir=job_dir,
            dry_run=args.dry_run
        )
        
        logger.info(f"Status: {result['status']}")
        logger.info(f"Message: {result['message']}")
        
        if result['status'] == 'pending_approval':
            logger.info("\n=== NEXT STEPS ===")
            logger.info("1. Review approval request in jobs/{job}/approvals/")
            logger.info("2. Send employer notification email")
            logger.info("3. Wait for employer approval")
            logger.info("4. Run: python send_clarification_email.py --request-id {id}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
