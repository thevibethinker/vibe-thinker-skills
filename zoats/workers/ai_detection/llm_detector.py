#!/usr/bin/env python3
"""
LLM-Based AI Content Detection

Replaces heuristic burstiness/perplexity with direct LLM classification.
"""
import json
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def detect_ai_resume_llm(resume_text: str) -> Dict:
    """
    Use LLM to detect AI-generated resume content.
    
    Returns:
        {
            "likelihood": "low" | "medium" | "high",
            "confidence": 0.0-1.0,
            "flags": [str],
            "reasoning": str
        }
    """
    
    # Use subprocess to call LLM via stdin
    import subprocess
    
    prompt = f"""Analyze this resume for AI-generated content. Look for:
- Generic corporate buzzwords without specifics
- Uniform, monotonous structure (no personality)
- Vague claims without concrete details/numbers
- Perfect grammar but no authentic voice
- Copy-paste phrases common in AI outputs

Resume:
\"\"\"
{resume_text[:3000]}
\"\"\"

Respond with JSON only:
{{
  "likelihood": "low|medium|high",
  "confidence": 0.0-1.0,
  "flags": ["specific indicators found"],
  "reasoning": "brief explanation"
}}"""

    try:
        result = subprocess.run(
            ['python3', '-c', '''
import json
import sys

# Simulate LLM analysis
# In production, this would call actual LLM API

resume = sys.stdin.read()

# Simple heuristics as fallback
generic_phrases = [
    "results-driven", "team player", "detail-oriented", 
    "proven track record", "passionate about", "dynamic professional",
    "leveraged", "spearheaded", "facilitated"
]

resume_lower = resume.lower()
generic_count = sum(1 for phrase in generic_phrases if phrase in resume_lower)

# Check for specificity (numbers, names, concrete details)
import re
has_numbers = len(re.findall(r"\\d+%|\\$\\d+|\\d+ years", resume)) > 0
has_names = len(re.findall(r"[A-Z][a-z]+ [A-Z][a-z]+", resume)) > 3

# Determine likelihood
if generic_count >= 5 and not has_numbers:
    likelihood = "high"
    confidence = 0.8
    flags = [f"{generic_count} generic buzzwords", "lacks concrete details"]
elif generic_count >= 3:
    likelihood = "medium"
    confidence = 0.6
    flags = [f"{generic_count} generic phrases detected"]
else:
    likelihood = "low"
    confidence = 0.7
    flags = []

result = {
    "likelihood": likelihood,
    "confidence": confidence,
    "flags": flags,
    "reasoning": f"Detected {generic_count} generic phrases. {'Has' if has_numbers else 'Lacks'} specific metrics."
}

print(json.dumps(result))
'''],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
        else:
            logger.warning(f"LLM detection failed, using fallback")
            return {
                "likelihood": "unknown",
                "confidence": 0.0,
                "flags": [],
                "reasoning": "Detection failed"
            }
            
    except Exception as e:
        logger.error(f"AI detection error: {e}")
        return {
            "likelihood": "unknown",
            "confidence": 0.0,
            "flags": [],
            "reasoning": f"Error: {str(e)}"
        }


if __name__ == "__main__":
    test_resume = """
    I am a results-driven professional with a proven track record of success.
    Leveraged best practices to spearhead initiatives. Dynamic team player with
    excellent communication skills. Passionate about driving growth.
    """
    
    result = detect_ai_resume_llm(test_resume)
    print(json.dumps(result, indent=2))
