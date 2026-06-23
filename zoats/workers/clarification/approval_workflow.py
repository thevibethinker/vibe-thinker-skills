#!/usr/bin/env python3
"""
Employer Approval Workflow

Manages approval process for clarification questions before sending to candidates.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ApprovalRequest:
    """Request for employer to approve clarification questions"""
    request_id: str
    candidate_id: str
    job_id: str
    questions: List[str]
    rationale: str  # Why we're asking these questions
    candidate_summary: str  # Brief summary of candidate
    status: str  # pending, approved, rejected, modified
    employer_feedback: Optional[str] = None
    modified_questions: Optional[List[str]] = None
    created_at: str = ""
    resolved_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


def create_approval_request(
    candidate_id: str,
    job_id: str,
    questions: List[str],
    rationale: str,
    candidate_summary: str
) -> ApprovalRequest:
    """
    Create an approval request for employer review.
    
    Args:
        candidate_id: Candidate identifier
        job_id: Job identifier  
        questions: Proposed clarification questions
        rationale: Why these questions matter
        candidate_summary: Brief candidate overview
    
    Returns:
        ApprovalRequest ready to send to employer
    """
    request_id = f"{job_id}_{candidate_id}_{int(datetime.now().timestamp())}"
    
    return ApprovalRequest(
        request_id=request_id,
        candidate_id=candidate_id,
        job_id=job_id,
        questions=questions,
        rationale=rationale,
        candidate_summary=candidate_summary,
        status="pending",
        created_at=datetime.utcnow().isoformat() + "Z"
    )


def format_approval_email(request: ApprovalRequest, job_title: str) -> Dict[str, str]:
    """
    Format approval request as email to employer.
    
    Returns:
        Dict with subject and body for email
    """
    numbered_questions = "\n".join([f"  {i+1}. {q}" for i, q in enumerate(request.questions)])
    
    body = f"""Clarification Request - {job_title}

CANDIDATE: {request.candidate_id}

SUMMARY:
{request.candidate_summary}

RATIONALE:
{request.rationale}

PROPOSED QUESTIONS:
{numbered_questions}

---

Please review and respond with one of:
1. APPROVE - Send these questions as-is
2. MODIFY - Suggest changes (reply with modified questions)
3. REJECT - Skip this candidate

To approve, simply reply "APPROVE" or click the approval link below:
[Approval Interface URL would go here]

---
Request ID: {request.request_id}
"""
    
    return {
        "subject": f"Review clarification questions - {request.candidate_id}",
        "body": body
    }


def save_approval_request(request: ApprovalRequest, job_dir: Path) -> Path:
    """Save approval request to tracking file"""
    approvals_dir = job_dir / "approvals"
    approvals_dir.mkdir(parents=True, exist_ok=True)
    
    request_path = approvals_dir / f"{request.request_id}.json"
    request_path.write_text(json.dumps(request.to_dict(), indent=2))
    
    logger.info(f"✓ Saved approval request: {request_path}")
    return request_path


def process_approval_response(
    request_id: str,
    job_dir: Path,
    response: str
) -> ApprovalRequest:
    """
    Process employer's response to approval request.
    
    Args:
        request_id: Approval request ID
        job_dir: Job directory
        response: Employer's response (APPROVE/REJECT/MODIFY + details)
    
    Returns:
        Updated ApprovalRequest
    """
    approvals_dir = job_dir / "approvals"
    request_path = approvals_dir / f"{request_id}.json"
    
    if not request_path.exists():
        raise FileNotFoundError(f"Approval request not found: {request_id}")
    
    request_data = json.loads(request_path.read_text())
    request = ApprovalRequest(**request_data)
    
    response_upper = response.strip().upper()
    
    if response_upper.startswith("APPROVE"):
        request.status = "approved"
        request.resolved_at = datetime.utcnow().isoformat() + "Z"
        logger.info(f"✓ Approved: {request_id}")
        
    elif response_upper.startswith("REJECT"):
        request.status = "rejected"
        request.resolved_at = datetime.utcnow().isoformat() + "Z"
        request.employer_feedback = response
        logger.info(f"✗ Rejected: {request_id}")
        
    elif response_upper.startswith("MODIFY"):
        request.status = "modified"
        request.resolved_at = datetime.utcnow().isoformat() + "Z"
        request.employer_feedback = response
        # Parse modified questions from response (simplified - would need better parsing)
        logger.info(f"⚠ Modified: {request_id}")
    
    # Save updated request
    request_path.write_text(json.dumps(request.to_dict(), indent=2))
    
    return request


if __name__ == "__main__":
    # Test
    request = create_approval_request(
        candidate_id="sample1",
        job_id="test-fixture",
        questions=[
            "Can you describe a specific example of analytical problem-solving?",
            "What motivated your transition from technical to business roles?",
            "How does your data engineering experience translate to consulting?"
        ],
        rationale="Candidate has strong quantitative background ($90M impact, elite selection) but no direct consulting experience. Need to assess problem-solving approach and motivation for consulting career.",
        candidate_summary="Cornell MBA, former Intel/eBay data engineer, $90M revenue impact, Elite IDF (4% acceptance). Strong analytical signals but unclear consulting fit."
    )
    
    print("=== APPROVAL REQUEST ===")
    print(json.dumps(request.to_dict(), indent=2))
    
    print("\n=== EMAIL TO EMPLOYER ===")
    email = format_approval_email(request, "Associate")
    print(f"Subject: {email['subject']}\n")
    print(email['body'])
