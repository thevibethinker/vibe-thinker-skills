#!/usr/bin/env python3
"""
Clarification Email Composer

Generates personalized emails to MAYBE candidates requesting clarification.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ClarificationEmail:
    """Email requesting clarification from candidate"""
    candidate_id: str
    job_id: str
    to_email: str
    subject: str
    body: str
    questions: List[str]
    deadline: str  # ISO format
    status: str  # draft, pending_approval, sent, responded
    created_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


def compose_email(
    candidate_id: str,
    job_id: str,
    job_title: str,
    candidate_email: str,
    questions: List[str],
    company_name: str = "Our team",
    days_to_respond: int = 5
) -> ClarificationEmail:
    """
    Compose clarification email for MAYBE candidate.
    
    Args:
        candidate_id: Candidate identifier
        job_id: Job identifier
        job_title: Human-readable job title
        candidate_email: Candidate's email address
        questions: List of 1-3 clarification questions
        company_name: Company name for email
        days_to_respond: Days until deadline
    
    Returns:
        ClarificationEmail object ready for approval
    """
    
    # Format questions
    numbered_questions = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    
    # Calculate deadline
    deadline = datetime.now() + timedelta(days=days_to_respond)
    deadline_str = deadline.strftime("%B %d, %Y")
    
    # Compose email body
    body = f"""Dear Applicant,

Thank you for your application for the {job_title} position. We've reviewed your background and are interested in learning more about your experience.

Before scheduling an interview, we'd like to better understand a few aspects of your background:

{numbered_questions}

Please respond to these questions by {deadline_str}. We appreciate your time and look forward to hearing from you.

Best regards,
{company_name}

---
To respond, simply reply to this email with your answers.
"""
    
    subject = f"Additional information needed - {job_title} position"
    
    return ClarificationEmail(
        candidate_id=candidate_id,
        job_id=job_id,
        to_email=candidate_email,
        subject=subject,
        body=body,
        questions=questions,
        deadline=deadline.isoformat() + "Z",
        status="draft",
        created_at=datetime.utcnow().isoformat() + "Z"
    )


def save_email_draft(email: ClarificationEmail, job_dir: Path) -> Path:
    """Save email draft to candidate outputs directory"""
    candidate_dir = job_dir / "candidates" / email.candidate_id
    output_dir = candidate_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    email_path = output_dir / "clarification_email_draft.json"
    email_path.write_text(json.dumps(email.to_dict(), indent=2))
    
    return email_path


if __name__ == "__main__":
    # Test
    email = compose_email(
        candidate_id="sample1",
        job_id="test-fixture",
        job_title="Associate",
        candidate_email="candidate@example.com",
        questions=[
            "Can you describe a specific example of how you've applied analytical thinking to solve a complex business problem?",
            "What motivated your transition from technical roles to business management?",
            "How do you see your experience in data engineering translating to strategy consulting?"
        ],
        company_name="McKinsey & Company"
    )
    
    print(json.dumps(email.to_dict(), indent=2))
