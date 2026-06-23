#!/usr/bin/env python3
"""
Zo LLM Signal Extraction

This module is designed to be called from Zo's environment where LLM tools are available.
It extracts signals using real LLM calls, not heuristics.
"""
import sys as _sys
from pathlib import Path as _Path
_REPO_ROOT = _Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

import json
import logging
from lib.prompt_standards import FULL_PROMPT_STANDARD

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _fallback_result(concern: str) -> dict:
    return {
        "business_impact": [],
        "elite_signals": [],
        "consulting_experience": {"has_direct": False, "years": 0, "firms": [], "confidence": 0.5},
        "role_match": {"fit_score": 0.3, "reasons": [], "concerns": [concern]},
        "red_flags": [],
    }


def extract_signals_with_zo_llm(resume_text: str, job_context: str = "management consulting") -> dict:
    prompt = f"""{FULL_PROMPT_STANDARD}

---

Extract structured signals from this resume for a {job_context} role.

RESUME:
{resume_text[:4000]}

Return JSON with:
{{
  "business_impact": [
    {{"value": 90, "type": "revenue", "context": "generated $90M in sales", "confidence": 0.9}}
  ],
  "elite_signals": [
    {{"type": "top_tier_mba", "detail": "Cornell MBA", "boost_factor": 1.15}},
    {{"type": "elite_company", "detail": "McKinsey", "boost_factor": 1.4}},
    {{"type": "acceptance_rate", "detail": "4% acceptance", "boost_factor": 1.3}}
  ],
  "consulting_experience": {{
    "has_direct": true,
    "years": 4,
    "firms": ["Deloitte Consulting"],
    "confidence": 0.9
  }},
  "role_match": {{
    "fit_score": 0.85,
    "reasons": ["consulting experience", "quantitative background"],
    "concerns": ["no direct industry experience"]
  }},
  "red_flags": []
}}

Return ONLY valid JSON."""

    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed; using structured fallback")
        return _fallback_result("llm extraction unavailable: anthropic package not installed")

    try:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        response = message.content[0].text
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        data = json.loads(response.strip())
        logger.info("✓ LLM extraction successful")
        return data
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return _fallback_result(f"llm extraction failed: {e}")
