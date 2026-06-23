#!/usr/bin/env python3
"""
Run Signal Extraction with Zo's LLM

This script is designed to be executed BY Zo (not via subprocess).
It has access to LLM capabilities and extracts signals for all candidates.
"""
import json
from pathlib import Path
import sys
from lib.paths import ZOATS_HOME

def extract_signals_for_candidate(resume_text: str, job_context: str) -> dict:
    """
    Extract signals using Zo's LLM capability.
    This function will have access to call_llm when executed by Zo.
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
    {{"type": "elite_company", "detail": "McKinsey", "boost_factor": 1.4}}
  ],
  "consulting_experience": {{
    "has_direct": true,
    "years": 4,
    "firms": ["Deloitte Consulting"],
    "confidence": 0.9
  }},
  "role_match": {{
    "fit_score": 0.85,
    "reasons": ["consulting experience", "top MBA"],
    "concerns": ["no direct industry experience"]
  }},
  "red_flags": []
}}

RULES:
- Business impact: Extract $ amounts, growth %, scale metrics
- Elite signals: Top schools (Harvard/Wharton/Stanford/MIT/Columbia/Cornell), MBB firms, FAANG
- Consulting: ONLY real consulting roles, not volunteer
- Red flags: "retail only", "no business exp", "major skill mismatch"
- Be strict but fair: recognize transferable skills

Return ONLY valid JSON."""

    # Try to use Zo's LLM
    try:
        import anthropic
        import os
        
        # Use Zo's AI proxy
        base_url = os.environ.get("ANTHROPIC_BASE_URL")
        api_key = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN", "dummy")
        
        client = anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url
        )
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20250131",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result_text = response.content[0].text
        return json.loads(result_text)
        
    except Exception as e:
        print(f"LLM extraction failed: {e}", file=sys.stderr)
        # Return empty structure
        return {
            "business_impact": [],
            "elite_signals": [],
            "consulting_experience": {"has_direct": False, "years": 0, "firms": [], "confidence": 0.5},
            "role_match": {"fit_score": 0.3, "reasons": [], "concerns": ["extraction failed"]},
            "red_flags": []
        }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    
    # Load resume
    resume_path = ZOATS_HOME / f"jobs/{args.job}/candidates/{args.candidate}/parsed/text.md"
    if not resume_path.exists():
        print(f"Resume not found: {resume_path}", file=sys.stderr)
        return 1
    
    resume_text = resume_path.read_text()
    
    # Extract signals
    signals = extract_signals_for_candidate(resume_text, args.job)
    
    # Save to cache
    cache_dir = ZOATS_HOME / f"jobs/{args.job}/candidates/{args.candidate}/outputs"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "signal_extraction_cache.json"
    cache_path.write_text(json.dumps(signals, indent=2))
    
    print(f"✓ Extracted signals for {args.candidate}")
    print(f"  Business impact: {len(signals['business_impact'])}")
    print(f"  Elite signals: {len(signals['elite_signals'])}")
    print(f"  Consulting: {signals['consulting_experience']['has_direct']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
