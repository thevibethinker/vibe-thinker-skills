#!/usr/bin/env python3
"""
LLM-Based Signal Extraction

Extracts signals from resumes using Zo's LLM capabilities.
"""
import json
import logging
from dataclasses import dataclass
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """All signals extracted from a resume"""
    business_impact: List[Dict]
    elite_signals: List[Dict]
    consulting_experience: Dict
    role_match: Dict
    red_flags: List[str]


def extract_signals_llm(resume_text: str, job_context: str = "management consulting") -> ExtractionResult:
    """
    Use Zo's LLM to extract all signals in one call.
    """
    
    prompt = f"""Extract structured signals from this resume for a {job_context} role.

RESUME:
{resume_text[:4000]}

Return JSON with:
{{
  "business_impact": [
    {{"value": 90, "type": "revenue", "context": "generated $90M in sales", "confidence": 0.9}}
  ],
  "elite_signals": [
    {{"type": "top_tier_mba", "detail": "Harvard MBA", "boost_factor": 1.3}},
    {{"type": "elite_company", "detail": "McKinsey", "boost_factor": 1.4}},
    {{"type": "acceptance_rate", "detail": "4% acceptance program", "boost_factor": 1.3}}
  ],
  "consulting_experience": {{
    "has_direct": true,
    "years": 4,
    "firms": ["Deloitte Consulting"],
    "confidence": 0.9
  }},
  "role_match": {{
    "fit_score": 0.85,
    "reasons": ["consulting experience", "top MBA", "quantitative background"],
    "concerns": ["no direct industry experience"]
  }},
  "red_flags": []
}}

RULES:
- Business impact: extract $ amounts, growth %, user scale (e.g., $90M, 150% growth, 10M users)
- Elite signals:
  * Top MBAs: H/W/S/MIT/Columbia/Chicago = 1.3, Cornell/Dartmouth/Yale = 1.15
  * MBB: McKinsey/Bain/BCG = 1.4
  * Consulting: Deloitte/Accenture/EY = 1.2
  * FAANG: = 1.15
  * Selective programs: <5% acceptance = 1.3, <10% = 1.2
- Consulting: ONLY count real consulting roles, NOT volunteer/student/pro-bono
- Red flags: ["retail only", "no business exp", "job hopping >4 jobs in 2 years"]
- Be strict on fit_score: 0.9+ = exceptional, 0.7-0.9 = strong, 0.5-0.7 = moderate, <0.5 = weak

Return ONLY valid JSON, no explanation."""

    try:
        # Use Zo's LLM capabilities
        import __main__
        
        if hasattr(__main__, 'call_llm') or hasattr(__main__, 'create_anthropic_client'):
            # Real Zo environment - call LLM
            logger.info("Using Zo LLM for extraction")
            
            # Try to get response via Zo's LLM
            try:
                # Method 1: Direct call_llm if available
                if hasattr(__main__, 'call_llm'):
                    response = __main__.call_llm(prompt)
                else:
                    # Method 2: Use create_anthropic_client
                    import anthropic
                    client = __main__.create_anthropic_client()
                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    response = message.content[0].text
                
                # Parse JSON response
                # Clean markdown code fences if present
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0]
                
                data = json.loads(response.strip())
                
                return ExtractionResult(
                    business_impact=data.get("business_impact", []),
                    elite_signals=data.get("elite_signals", []),
                    consulting_experience=data.get("consulting_experience", {"has_direct": False, "years": 0, "firms": [], "confidence": 0.5}),
                    role_match=data.get("role_match", {"fit_score": 0.5, "reasons": [], "concerns": []}),
                    red_flags=data.get("red_flags", [])
                )
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                raise
        else:
            # Not in Zo environment
            raise RuntimeError("Not running in Zo environment - LLM not available")
            
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        # Return empty result
        return ExtractionResult(
            business_impact=[],
            elite_signals=[],
            consulting_experience={"has_direct": False, "years": 0, "firms": [], "confidence": 0.5},
            role_match={"fit_score": 0.3, "reasons": [], "concerns": ["extraction failed"]},
            red_flags=[]
        )


if __name__ == "__main__":
    test_resume = """
    VRIJEN ATTAWAR
    Cornell MBA
    
    McKinsey & Company - Associate
    - Led strategy projects for Fortune 500 clients
    - Drove $4M revenue growth
    """
    
    result = extract_signals_llm(test_resume)
    print(json.dumps({
        "business_impact": result.business_impact,
        "elite_signals": result.elite_signals,
        "consulting": result.consulting_experience,
        "role_match": result.role_match,
        "red_flags": result.red_flags
    }, indent=2))
