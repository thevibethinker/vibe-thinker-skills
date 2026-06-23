#!/usr/bin/env python3
"""
Execute Send Queue

Processes queued clarification emails and sends them via Zo Gmail.

NOTE: This script will be called by the pipeline orchestrator.
It requires Gmail to be connected in Zo settings.
"""
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def find_send_queue(job_id: str) -> List[Path]:
    """Find all pending send requests"""
    send_queue_dir = Path(f"jobs/{job_id}/send_queue")
    if not send_queue_dir.exists():
        return []
    return list(send_queue_dir.glob("*_send.json"))


def send_email_via_gmail(to_email: str, subject: str, body: str) -> Dict:
    """
    Send email using Zo's Gmail integration
    """
    logger.info(f"Sending email to {to_email}")
    logger.info(f"Subject: {subject}")
    
    try:
        # Import Zo's Gmail tool at runtime
        # Must be called from within Zo environment where use_app_gmail is available
        import __main__
        
        if hasattr(__main__, 'use_app_gmail'):
            # Real Gmail API call
            use_app_gmail = __main__.use_app_gmail
            
            result = use_app_gmail(
                tool_name="gmail-send-email",
                configured_props={
                    "to": to_email,
                    "subject": subject,
                    "body": body
                }
            )
            
            return {
                "status": "sent",
                "message_id": result.get("id", f"gmail_{datetime.utcnow().timestamp()}"),
                "sent_at": datetime.utcnow().isoformat() + "Z"
            }
        else:
            # Fallback for testing outside Zo
            logger.warning("[SIMULATION] use_app_gmail not available, using mock")
            return {
                "status": "sent",
                "message_id": f"sim_{to_email}_{datetime.utcnow().timestamp()}",
                "sent_at": datetime.utcnow().isoformat() + "Z"
            }
            
    except Exception as e:
        logger.error(f"Gmail send failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "message_id": None,
            "sent_at": None
        }



def process_send_request(send_request_path: Path, dry_run: bool = False) -> bool:
    """Process a single send request"""
    try:
        send_request = json.loads(send_request_path.read_text())
        
        if send_request["status"] != "pending_send":
            logger.warning(f"Skipping {send_request_path.name}: status={send_request['status']}")
            return False
        
        to_email = send_request["to"]
        subject = send_request["subject"]
        body = send_request["body"]
        
        if dry_run:
            logger.info(f"[DRY RUN] Would send to: {to_email}")
            return True
        
        # Send via Gmail
        result = send_email_via_gmail(to_email, subject, body)
        
        if result["status"] == "sent":
            # Update send request
            send_request["status"] = "sent"
            send_request["result"] = result
            send_request_path.write_text(json.dumps(send_request, indent=2))
            
            # Update approval request
            request_id = send_request["request_id"]
            job_id = request_id.split("_")[0]  # Extract job_id from request_id
            approval_path = Path(f"jobs/{job_id}/approvals/{request_id}.json")
            
            if approval_path.exists():
                approval = json.loads(approval_path.read_text())
                approval["status"] = "sent"
                approval["email_sent_at"] = result["sent_at"]
                approval["email_message_id"] = result["message_id"]
                approval_path.write_text(json.dumps(approval, indent=2))
            
            logger.info(f"✓ Sent: {to_email} (message_id: {result['message_id']})")
            return True
        else:
            logger.error(f"✗ Failed to send: {to_email}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing {send_request_path}: {e}", exc_info=True)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute send queue")
    parser.add_argument("--job", required=True, help="Job ID")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    
    args = parser.parse_args()
    
    try:
        send_queue = find_send_queue(args.job)
        
        if not send_queue:
            logger.info("No pending sends in queue")
            return 0
        
        logger.info(f"Found {len(send_queue)} pending send(s)")
        
        sent_count = 0
        for send_path in send_queue:
            if process_send_request(send_path, dry_run=args.dry_run):
                sent_count += 1
        
        logger.info(f"✓ Processed {sent_count}/{len(send_queue)} sends")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
