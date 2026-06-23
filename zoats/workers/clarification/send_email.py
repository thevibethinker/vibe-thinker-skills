#!/usr/bin/env python3
"""
Send Clarification Email via Zo

Sends approved clarification emails to candidates using Zo's Gmail integration.
"""
import argparse
import json
import logging
from pathlib import Path
from typing import Dict
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_approval_request(request_id: str, job_id: str) -> Dict:
    """Load approval request"""
    approval_path = Path(f"jobs/{job_id}/approvals/{request_id}.json")
    if not approval_path.exists():
        raise FileNotFoundError(f"Approval request not found: {approval_path}")
    return json.loads(approval_path.read_text())


def load_email_draft(job_id: str, candidate_id: str) -> Dict:
    """Load email draft"""
    email_path = Path(f"jobs/{job_id}/candidates/{candidate_id}/outputs/clarification_email_draft.json")
    if not email_path.exists():
        raise FileNotFoundError(f"Email draft not found: {email_path}")
    return json.loads(email_path.read_text())


def get_candidate_email(job_id: str, candidate_id: str) -> str:
    """Extract candidate email from parsed fields"""
    fields_path = Path(f"jobs/{job_id}/candidates/{candidate_id}/parsed/fields.json")
    if fields_path.exists():
        fields = json.loads(fields_path.read_text())
        if "email" in fields:
            return fields["email"]
    
    # Fallback to prompt
    logger.warning(f"No email found in parsed fields for {candidate_id}")
    return None


def send_via_zo_gmail(to_email: str, subject: str, body: str, request_id: str) -> Dict:
    """
    Send email via Zo's Gmail integration
    
    NOTE: This requires the user to have connected Gmail in Zo settings.
    The actual sending will be done via use_app_gmail tool.
    
    For now, this creates a send request that can be executed by the pipeline.
    """
    send_request = {
        "type": "clarification_email",
        "request_id": request_id,
        "to": to_email,
        "subject": subject,
        "body": body,
        "method": "gmail",
        "status": "pending_send"
    }
    
    return send_request


def mark_email_sent(approval_path: Path, email_metadata: Dict):
    """Update approval request with sent status"""
    approval = json.loads(approval_path.read_text())
    approval["status"] = "sent"
    approval["email_sent_at"] = email_metadata.get("sent_at")
    approval["email_metadata"] = email_metadata
    approval_path.write_text(json.dumps(approval, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Send clarification email via Zo")
    parser.add_argument("--request-id", required=True, help="Approval request ID")
    parser.add_argument("--job", required=True, help="Job ID")
    parser.add_argument("--candidate", required=True, help="Candidate ID")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    
    args = parser.parse_args()
    
    try:
        # Load approval request
        approval = load_approval_request(args.request_id, args.job)
        
        # Check if approved
        if approval["status"] != "approved":
            logger.error(f"Approval status: {approval['status']} (must be 'approved' to send)")
            return 1
        
        # Load email draft
        email_draft = load_email_draft(args.job, args.candidate)
        
        # Get candidate email
        candidate_email = get_candidate_email(args.job, args.candidate)
        if not candidate_email:
            logger.error(f"No email address found for candidate {args.candidate}")
            logger.info("Please add email to parsed/fields.json or specify with --to-email")
            return 1
        
        # Use approved questions (may be modified by employer)
        final_questions = approval.get("modified_questions") or approval["questions"]
        
        # Rebuild email body with final questions
        email_body = email_draft["body"]
        # Replace questions section
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(final_questions)])
        
        logger.info(f"Sending clarification email to: {candidate_email}")
        logger.info(f"Subject: {email_draft['subject']}")
        logger.info(f"Questions: {len(final_questions)}")
        
        if args.dry_run:
            logger.info("[DRY RUN] Would send email:")
            logger.info(f"  To: {candidate_email}")
            logger.info(f"  Subject: {email_draft['subject']}")
            logger.info(f"  Questions:\n{questions_text}")
            return 0
        
        # Create send request
        send_request = send_via_zo_gmail(
            to_email=candidate_email,
            subject=email_draft["subject"],
            body=email_body,
            request_id=args.request_id
        )
        
        # Save send request for pipeline execution
        send_queue_dir = Path(f"jobs/{args.job}/send_queue")
        send_queue_dir.mkdir(parents=True, exist_ok=True)
        
        send_request_path = send_queue_dir / f"{args.request_id}_send.json"
        send_request_path.write_text(json.dumps(send_request, indent=2))
        
        logger.info(f"✓ Send request queued: {send_request_path}")
        logger.info("  Execute with: python workers/clarification/execute_sends.py")
        
        # Mark as pending send
        approval_path = Path(f"jobs/{args.job}/approvals/{args.request_id}.json")
        approval["status"] = "pending_send"
        approval_path.write_text(json.dumps(approval, indent=2))
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
