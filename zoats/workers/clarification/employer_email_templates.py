#!/usr/bin/env python3
"""
Employer Email Templates

Generates email content for employer approval requests.
"""
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class ApprovalEmailContent:
    subject: str
    body_markdown: str
    summary: str


def format_approval_request_email(
    candidate_id: str,
    job_title: str,
    candidate_summary: str,
    rationale: str,
    questions: List[str],
    request_id: str
) -> ApprovalEmailContent:
    """Generate email for employer to approve/modify clarification questions"""
    
    subject = f"[ZoATS] Review clarification questions - {candidate_id}"
    
    body_markdown = f"""# Clarification Request Approval

**Candidate:** {candidate_id}  
**Position:** {job_title}

---

## Summary
{candidate_summary}

---

## Why Clarification Needed
{rationale}

---

## Proposed Questions

"""
    
    for i, q in enumerate(questions, 1):
        body_markdown += f"{i}. {q}\n"
    
    body_markdown += f"""

---

## Next Steps

**To approve these questions as-is:**
- Reply with: `APPROVE`

**To modify questions:**
- Reply with your revised questions (1-3 questions)
- Start each with a number: `1. Your question here`

**To reject this candidate:**
- Reply with: `REJECT`

---

**Request ID:** `{request_id}`

Once approved, the system will automatically send the clarification email to the candidate and track their response.
"""
    
    return ApprovalEmailContent(
        subject=subject,
        body_markdown=body_markdown,
        summary=f"Approval needed for {candidate_id} clarification ({len(questions)} questions)"
    )


def format_approval_received_email(
    candidate_id: str,
    job_title: str,
    action: str,  # APPROVED, MODIFIED, REJECTED
    modified_questions: List[str] = None
) -> ApprovalEmailContent:
    """Confirmation email after employer responds"""
    
    if action == "APPROVED":
        subject = f"[ZoATS] Questions approved - {candidate_id}"
        body = f"""# Clarification Questions Approved

**Candidate:** {candidate_id}  
**Position:** {job_title}

The clarification email has been sent to {candidate_id}. You'll receive a notification when they respond.

**Deadline:** 5 business days

The system will automatically re-evaluate them once they respond.
"""
    
    elif action == "MODIFIED":
        subject = f"[ZoATS] Modified questions sent - {candidate_id}"
        body = f"""# Modified Questions Sent

**Candidate:** {candidate_id}  
**Position:** {job_title}

Your revised questions have been sent to {candidate_id}:

"""
        for i, q in enumerate(modified_questions, 1):
            body += f"{i}. {q}\n"
        
        body += "\n**Deadline:** 5 business days"
    
    else:  # REJECTED
        subject = f"[ZoATS] Candidate rejected - {candidate_id}"
        body = f"""# Candidate Rejected

**Candidate:** {candidate_id}  
**Position:** {job_title}

{candidate_id} has been moved to the backup list and will not receive a clarification email.
"""
    
    return ApprovalEmailContent(
        subject=subject,
        body_markdown=body,
        summary=f"{candidate_id}: {action}"
    )


def format_response_received_email(
    candidate_id: str,
    job_title: str,
    answers: List[str],
    new_decision: str,
    old_decision: str = "MAYBE"
) -> ApprovalEmailContent:
    """Email to employer when candidate responds"""
    
    decision_emoji = {
        "STRONG_INTERVIEW": "🎯",
        "INTERVIEW": "✓",
        "PASS": "→"
    }
    
    emoji = decision_emoji.get(new_decision, "•")
    
    subject = f"[ZoATS] {emoji} Candidate responded - {candidate_id}"
    
    body = f"""# Candidate Response Received

**Candidate:** {candidate_id}  
**Position:** {job_title}

**Original Decision:** {old_decision}  
**New Decision:** {new_decision}

---

## Their Answers

"""
    
    for i, answer in enumerate(answers, 1):
        body += f"### Question {i}\n{answer}\n\n"
    
    body += f"""---

## Recommendation

"""
    
    if new_decision == "STRONG_INTERVIEW":
        body += "✅ **Strong candidate** - Priority scheduling recommended"
    elif new_decision == "INTERVIEW":
        body += "✓ **Good candidate** - Standard interview process"
    else:
        body += "→ **Moved to backup** - Responses did not address concerns"
    
    body += f"\n\nView full evaluation: `jobs/{job_title.lower().replace(' ', '-')}/candidates/{candidate_id}/outputs/gestalt_evaluation_v2.json`"
    
    return ApprovalEmailContent(
        subject=subject,
        body_markdown=body,
        summary=f"{candidate_id} responded: {old_decision} → {new_decision}"
    )


if __name__ == "__main__":
    # Test
    email = format_approval_request_email(
        candidate_id="sample1",
        job_title="Associate - Management Consulting",
        candidate_summary="Cornell MBA, $90M revenue impact, Elite IDF selection",
        rationale="Strong quantitative signals but no direct consulting experience",
        questions=[
            "Can you describe your problem-solving approach?",
            "What motivates your consulting interest?",
            "How do technical skills transfer?"
        ],
        request_id="test_123"
    )
    
    print(email.body_markdown)
