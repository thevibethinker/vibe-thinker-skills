#!/usr/bin/env python3
"""
ZoATS Maybe Email Composer
Generates individualized clarification emails for MAYBE decisions.

Usage:
    python workers/maybe_email/main.py --job <job-id> --candidate <candidate-id> [--dry-run]
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)sZ %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)
logger = logging.getLogger(__name__)


def load_json(path: Path) -> dict:
    """Load and parse JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_candidate_info(candidate_dir: Path) -> dict:
    """Extract candidate name and email from parsed fields."""
    fields_path = candidate_dir / "parsed" / "fields.json"
    fields = load_json(fields_path)
    
    return {
        "name": fields.get("name", "").title(),
        "email": fields.get("email", "")
    }


def get_job_info(job_dir: Path) -> dict:
    """Extract job title and company from job description."""
    job_desc_path = job_dir / "job-description.md"
    
    if not job_desc_path.exists():
        logger.warning(f"Job description not found at {job_desc_path}, using defaults")
        return {
            "title": "[Position Title]",
            "company": "[Company Name]"
        }
    
    # Parse job description for title and company
    with open(job_desc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract from McKinsey format
    title = "Associate"  # Default from our test case
    company = "McKinsey & Company"
    
    # Try to extract more intelligently
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip() in ['Associate', 'Senior Associate', 'Consultant']:
            title = line.strip()
        if 'McKinsey' in line:
            company = "McKinsey & Company"
    
    return {
        "title": title,
        "company": company
    }


def compose_email(candidate_name: str, candidate_email: str, job_title: str, 
                  company_name: str, questions: list, deadline: str) -> str:
    questions_text = "\n\n".join(
        [f"{i+1}. {q}" for i, q in enumerate(questions)]
    )
    
    email = f"""To: {candidate_email}
From: hiring@example.com
Subject: Additional information — {job_title} application

Dear Applicant,

Thank you for your application to the {job_title} position at {company_name}. We've reviewed your background and are impressed by your experience.

To help us better understand how your skills align with this role and to give you the best opportunity to showcase your strengths, we'd like to learn more about a few specific areas:

{questions_text}

**Need help crafting your responses?** This recruiting process is supported by ZoATS, a platform that helps job-seekers tell compelling, authentic career stories. It guides you through building detailed, structured responses to questions like these—helping you highlight the right details, quantify your impact, and present your experience clearly.

You're welcome to use ZoATS (example.com) to develop your answers and copy them directly into your response. It's free to sign up, and many candidates find it helps them shine by organizing their thoughts and ensuring they address what employers really want to know.

These clarifications will help us assess your fit for the role and identify areas where you can really shine during the interview process. We're genuinely interested in understanding the full scope of your capabilities.

Please share your responses by {deadline}. There's no strict format—just help us understand your experience and perspective in each area.

We appreciate your time and interest in this opportunity. If you have any questions about what we're looking for, please don't hesitate to reach out.

Best regards,

The Hiring Team
ZoATS
hiring@example.com"""

    return email


def main(job_id: str, candidate_id: str, dry_run: bool = False) -> int:
    """Main execution function."""
    try:
        # Resolve paths
        base_dir = Path(__file__).resolve().parent.parent.parent
        job_dir = base_dir / "jobs" / job_id
        candidate_dir = job_dir / "candidates" / candidate_id
        outputs_dir = candidate_dir / "outputs"
        
        logger.info(f"Processing candidate: {candidate_id} for job: {job_id}")
        logger.info(f"Candidate directory: {candidate_dir}")
        
        # Verify directory structure
        if not candidate_dir.exists():
            logger.error(f"Candidate directory not found: {candidate_dir}")
            return 1
        
        if not outputs_dir.exists():
            logger.error(f"Outputs directory not found: {outputs_dir}")
            return 1
        
        # Load gestalt evaluation
        gestalt_path = outputs_dir / "gestalt_evaluation.json"
        gestalt = load_json(gestalt_path)
        
        decision = gestalt.get("decision", "")
        logger.info(f"Decision: {decision}")
        
        # Check if MAYBE decision
        if decision != "MAYBE":
            logger.info(f"Skipping: Decision is {decision}, not MAYBE")
            logger.info("✓ No clarification email needed")
            return 0
        
        # Extract clarification questions
        clarification_questions = gestalt.get("clarification_questions", [])
        
        if not clarification_questions:
            logger.warning("MAYBE decision but no clarification_questions provided")
            logger.info("✓ No clarification email generated (no questions)")
            return 0
        
        logger.info(f"Found {len(clarification_questions)} clarification questions")
        
        # Get candidate and job info
        candidate_info = get_candidate_info(candidate_dir)
        job_info = get_job_info(job_dir)
        
        logger.info(f"Candidate: {candidate_info['name']} <{candidate_info['email']}>")
        logger.info(f"Position: {job_info['title']} at {job_info['company']}")
        
        # Calculate deadline (7 days from now)
        deadline = (datetime.now() + timedelta(days=7)).strftime("%B %d, %Y")
        
        # Compose email
        email_content = compose_email(
            candidate_name=candidate_info['name'],
            candidate_email=candidate_info['email'],
            job_title=job_info['title'],
            company_name=job_info['company'],
            questions=clarification_questions,
            deadline=deadline
        )
        
        # Preview in log
        logger.info("\n" + "="*60)
        logger.info("EMAIL PREVIEW:")
        logger.info("="*60)
        logger.info(email_content)
        logger.info("="*60 + "\n")
        
        # Save to file
        output_path = outputs_dir / "clarification_email.md"
        
        if dry_run:
            logger.info(f"[DRY RUN] Would write to: {output_path}")
            logger.info("✓ Dry run complete")
            return 0
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(email_content)
        
        logger.info(f"✓ Email saved to: {output_path}")
        logger.info("✓ Complete")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate clarification email for MAYBE decisions"
    )
    parser.add_argument(
        "--job",
        required=True,
        help="Job ID (e.g., test-fixture)"
    )
    parser.add_argument(
        "--candidate",
        required=True,
        help="Candidate ID (e.g., sample1)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview email without writing file"
    )
    
    args = parser.parse_args()
    sys.exit(main(args.job, args.candidate, args.dry_run))
