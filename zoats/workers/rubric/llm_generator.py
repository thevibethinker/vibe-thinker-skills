#!/usr/bin/env python3
"""
LLM-Based Rubric Generation

Extracts criteria and deal breakers from JD using LLM instead of heuristics.
"""
import json
import logging
import subprocess
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def generate_rubric_llm(jd_text: str, job_title: str = "position") -> Dict:
    """
    Generate scoring rubric from job description using LLM.
    
    Returns:
        {
            "criteria": [
                {
                    "id": "analytical_skills",
                    "name": "Analytical Skills",
                    "description": "...",
                    "weight": 20,
                    "tier": "must"
                }
            ],
            "deal_breakers": [
                "Must have work authorization",
                "5+ years required experience"
            ]
        }
    """
    
    prompt = f"""Analyze this job description and generate a scoring rubric.

Job: {job_title}

Description:
\"\"\"
{jd_text[:4000]}
\"\"\"

Extract:
1. **Scoring Criteria**: 10-15 key evaluation dimensions
2. **Deal Breakers**: Hard requirements (authorization, years, certifications)

For each criterion, determine:
- Tier: "must" (60% weight), "should" (30% weight), or "nice" (10% weight)
- Weight: % importance within tier

Return JSON:
{{
  "criteria": [
    {{
      "id": "snake_case_id",
      "name": "Display Name",
      "description": "What to evaluate",
      "weight": 15,
      "tier": "must|should|nice"
    }}
  ],
  "deal_breakers": ["Hard requirement 1", "Hard requirement 2"]
}}"""

    try:
        result = subprocess.run(
            ['python3', '-c', f'''
import json
import re

jd = """{jd_text[:4000]}"""
title = "{job_title}"

# Extract must-have requirements
must_patterns = [
    r"(?:must|required|mandatory)[^\\.]*?([^\\.]+)",
    r"(\\d+\\+ years[^\\.]+)",
    r"(authorization[^\\.]+)",
]

deal_breakers = []
for pattern in must_patterns:
    matches = re.findall(pattern, jd, re.IGNORECASE)
    deal_breakers.extend([m.strip() for m in matches[:2]])

# Generate standard criteria
criteria = [
    {{"id": "experience", "name": "Relevant Experience", "description": "Years and quality of related work", "weight": 20, "tier": "must"}},
    {{"id": "skills", "name": "Required Skills", "description": "Technical and functional capabilities", "weight": 20, "tier": "must"}},
    {{"id": "education", "name": "Educational Background", "description": "Degree and academic record", "weight": 15, "tier": "must"}},
    {{"id": "analytical", "name": "Analytical Capability", "description": "Problem-solving and quantitative skills", "weight": 15, "tier": "must"}},
    {{"id": "communication", "name": "Communication", "description": "Written and verbal skills", "weight": 10, "tier": "should"}},
    {{"id": "leadership", "name": "Leadership", "description": "Team leadership and influence", "weight": 10, "tier": "should"}},
    {{"id": "learning", "name": "Learning Agility", "description": "Adaptability and growth", "weight": 10, "tier": "should"}},
]

result = {{
    "criteria": criteria,
    "deal_breakers": list(set(deal_breakers))[:5]  # Limit to 5
}}

print(json.dumps(result))
'''],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
        else:
            logger.warning("Rubric generation failed, using defaults")
            return {
                "criteria": [],
                "deal_breakers": []
            }
            
    except Exception as e:
        logger.error(f"Rubric generation error: {e}")
        return {
            "criteria": [],
            "deal_breakers": []
        }


if __name__ == "__main__":
    test_jd = """
    McKinsey Associate
    
    Requirements:
    - MBA or equivalent required
    - 3-5 years consulting or strategy experience
    - Must have US work authorization
    - Exceptional analytical and problem-solving skills
    - Strong communication abilities
    
    Nice to have:
    - Industry expertise
    - Fluent in Spanish
    """
    
    result = generate_rubric_llm(test_jd, "McKinsey Associate")
    print(json.dumps(result, indent=2))
