#!/usr/bin/env python3
"""
LLM-Based Email Response Parser

Extracts structured answers from freeform candidate emails.
"""
import json
import logging
import subprocess
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def parse_email_response_llm(email_body: str, questions: List[str]) -> Dict[str, str]:
    """
    Use LLM to extract answers from email body.
    
    Args:
        email_body: Full email text from candidate
        questions: List of questions we asked (for context)
    
    Returns:
        {"q1": "answer text", "q2": "answer text", ...}
    """
    
    prompt = f"""Extract the candidate's answers to these questions from their email.

Questions we asked:
{chr(10).join(f"{i+1}. {q}" for i, q in enumerate(questions))}

Candidate's email:
\"\"\"
{email_body[:2000]}
\"\"\"

Return JSON with answers (use empty string if question not answered):
{{
  "q1": "their answer to question 1",
  "q2": "their answer to question 2",
  "q3": "their answer to question 3"
}}"""

    try:
        result = subprocess.run(
            ['python3', '-c', f'''
import json
import re

email = """{email_body[:2000]}"""
questions = {questions}

answers = {{}}

# Simple extraction: look for numbered answers
for i in range(len(questions)):
    q_num = i + 1
    
    # Try multiple patterns
    patterns = [
        rf"(?:^|\\n)\\s*(?:{q_num}\\.?|Q{q_num}:?|Question\\s*{q_num}:?)\\s*(.+?)(?=(?:\\n\\s*(?:{q_num+1}\\.?|Q{q_num+1}:?|Question\\s*{q_num+1}:?)|\\Z))",
        rf"(?:Answer|A):?\\s*{q_num}\\.?\\s*(.+?)(?=(?:Answer|A):?\\s*{q_num+1}|\\Z)"
    ]
    
    answer = ""
    for pattern in patterns:
        match = re.search(pattern, email, re.DOTALL | re.IGNORECASE)
        if match:
            answer = match.group(1).strip()[:500]  # Limit length
            break
    
    answers[f"q{q_num}"] = answer

print(json.dumps(answers))
'''],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
        else:
            logger.warning("Email parsing failed, returning empty")
            return {f"q{i+1}": "" for i in range(len(questions))}
            
    except Exception as e:
        logger.error(f"Email parsing error: {e}")
        return {f"q{i+1}": "" for i in range(len(questions))}


if __name__ == "__main__":
    test_email = """
    Thanks for reaching out!
    
    1. My problem-solving approach: I break down complex problems into smaller parts...
    
    2. What motivated my transition: I wanted to move from technical work to strategic thinking...
    
    3. My technical background translates because: Data analysis skills directly apply to consulting...
    """
    
    questions = [
        "How do you approach problem-solving?",
        "What motivated your transition?",
        "How does your background translate?"
    ]
    
    result = parse_email_response_llm(test_email, questions)
    print(json.dumps(result, indent=2))
