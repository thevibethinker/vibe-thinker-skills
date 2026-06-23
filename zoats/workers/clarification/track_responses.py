import sys as _sys
from pathlib import Path as _Path
_REPO_ROOT = _Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))
import sys
from pathlib import Path
from workers.clarification.llm_email_parser import parse_email_response_llm
#!/usr/bin/env python3
"""
Track Clarification Responses

Monitors inbox for candidate responses to clarification emails.
Matches responses to approval requests and triggers re-evaluation.
"""
import argparse
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def find_pending_clarifications(job_id: str) -> List[Dict]:
    """Find all sent clarification requests awaiting response"""
    approvals_dir = Path(f"jobs/{job_id}/approvals")
    if not approvals_dir.exists():
        return []
    
    pending = []
    for approval_file in approvals_dir.glob("*.json"):
        approval = json.loads(approval_file.read_text())
        if approval["status"] == "sent":
            pending.append(approval)
    
    return pending


def check_inbox_for_responses(pending_requests: List[Dict]) -> List[Dict]:
    """
    Check Zo inbox for responses to clarification emails
    """
    logger.info(f"Checking inbox for {len(pending_requests)} pending responses")
    
    try:
        import __main__
        
        if not hasattr(__main__, 'use_app_gmail'):
            logger.warning("[SIMULATION] use_app_gmail not available")
            return []
        
        use_app_gmail = __main__.use_app_gmail
        
        # Search for unread emails
        recent_emails = use_app_gmail(
            tool_name="gmail-search-emails",
            configured_props={
                "query": "is:unread",
                "max_results": 50
            }
        )
        
        responses = []
        
        # Match emails to pending requests
        for request in pending_requests:
            candidate_email = request.get("candidate_email", "")
            request_id = request["request_id"]
            candidate_id = request["candidate_id"]
            
            for email in recent_emails.get("messages", []):
                email_from = email.get("from", "").lower()
                email_body = email.get("body", "") + " " + email.get("snippet", "")
                
                # Match by sender email or request_id in body
                if candidate_email.lower() in email_from or request_id in email_body:
                    # Parse answers
                    questions = request.get("questions", [])
                    answers = parse_candidate_response(email_body, questions)
                    
                    responses.append({
                        "candidate_id": candidate_id,
                        "request_id": request_id,
                        "answers": answers,
                        "raw_email": email_body,
                        "email_id": email.get("id", ""),
                        "received_at": email.get("date", "")
                    })
                    
                    # Mark as read
                    try:
                        use_app_gmail(
                            tool_name="gmail-mark-as-read",
                            configured_props={"message_id": email["id"]}
                        )
                    except:
                        pass  # Best effort
                    
                    break
        
        return responses
        
    except Exception as e:
        logger.error(f"Gmail check failed: {e}", exc_info=True)
        return []


def parse_candidate_response(email_body: str, questions: List[str]) -> Dict:
    """
    Parse candidate's email response to extract answers
    
    Attempts to match answers to questions using simple heuristics.
    """
    answers = {}
    
    # Try to extract numbered responses
    for i, question in enumerate(questions, 1):
        # Look for patterns like "1.", "Q1:", "Question 1:"
        pattern = rf"(?:^|\n)\s*(?:{i}\.?|Q{i}:?|Question\s*{i}:?)\s*(.+?)(?=(?:\n\s*(?:{i+1}\.?|Q{i+1}:?|Question\s*{i+1}:?)|\Z))"
        match = re.search(pattern, email_body, re.DOTALL | re.IGNORECASE)
        
        if match:
            answer = match.group(1).strip()
            answers[f"q{i}"] = answer
        else:
            # Fallback: just include full body
            answers[f"q{i}"] = "[See full response below]"
    
    answers["full_response"] = email_body
    
    return answers


def save_response(job_id: str, candidate_id: str, request_id: str, response_data: Dict):
    """Save candidate response"""
    response_path = Path(f"jobs/{job_id}/candidates/{candidate_id}/outputs/clarification_response.json")
    response_path.parent.mkdir(parents=True, exist_ok=True)
    
    response_record = {
        "request_id": request_id,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "received_at": datetime.utcnow().isoformat() + "Z",
        "answers": response_data["answers"],
        "raw_email": response_data.get("raw_email", ""),
        "status": "received"
    }
    
    response_path.write_text(json.dumps(response_record, indent=2))
    
    # Update approval request
    approval_path = Path(f"jobs/{job_id}/approvals/{request_id}.json")
    if approval_path.exists():
        approval = json.loads(approval_path.read_text())
        approval["status"] = "responded"
        approval["response_received_at"] = response_record["received_at"]
        approval_path.write_text(json.dumps(approval, indent=2))
    
    logger.info(f"✓ Saved response: {response_path}")


def trigger_reevaluation(job_id: str, candidate_id: str):
    """Trigger re-evaluation with clarification"""
    logger.info(f"Triggering re-evaluation for {candidate_id}")
    
    # Create reevaluation task
    reevaluation_queue = Path(f"jobs/{job_id}/reevaluation_queue")
    reevaluation_queue.mkdir(parents=True, exist_ok=True)
    
    task = {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "trigger": "clarification_response",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "pending"
    }
    
    task_path = reevaluation_queue / f"{candidate_id}_reeval.json"
    task_path.write_text(json.dumps(task, indent=2))
    
    logger.info(f"✓ Queued re-evaluation: {task_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Track clarification responses")
    parser.add_argument("--job", required=True, help="Job ID")
    parser.add_argument("--dry-run", action="store_true", help="Check without processing")
    
    args = parser.parse_args()
    
    try:
        # Find pending clarifications
        pending = find_pending_clarifications(args.job)
        
        if not pending:
            logger.info("No pending clarification requests")
            return 0
        
        logger.info(f"Monitoring {len(pending)} pending clarification(s)")
        
        # Check inbox for responses
        responses = check_inbox_for_responses(pending)
        
        if not responses:
            logger.info("No new responses found")
            return 0
        
        # Process responses
        for response in responses:
            candidate_id = response["candidate_id"]
            request_id = response["request_id"]
            
            logger.info(f"Processing response from {candidate_id}")
            
            if args.dry_run:
                logger.info(f"[DRY RUN] Would process response from {candidate_id}")
                continue
            
            # Save response
            save_response(args.job, candidate_id, request_id, response)
            
            # Trigger re-evaluation
            trigger_reevaluation(args.job, candidate_id)
        
        logger.info(f"✓ Processed {len(responses)} response(s)")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
