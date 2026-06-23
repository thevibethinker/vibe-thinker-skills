import sys as _sys
from pathlib import Path as _Path
_REPO_ROOT = _Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))
import sys
from pathlib import Path
from workers.quick_test.llm_checker import check_deal_breakers_llm
#!/usr/bin/env python3
"""
Quick Test v2

Fast pre-screening before full scoring.
Goals: (a) Filter obvious duds, (b) Surface hidden gems, (c) Flag for review

Usage:
  python workers/quick_test/main.py \\
    --job <job-id> \\
    --candidate <candidate-id> \\
    [--dry-run]

Design:
- Hard disqualifiers (deal breakers): binary yes/no
- Soft disqualifiers: experience gap, trajectory concerns, achievement density
- Red flags: job hopping, unexplained gaps, declining trajectory
- Early scoring estimate (0-100) for obvious cases
- Recommendation: pass, reject, review

Quality:
- Logging, --dry-run, error handling, structured output
"""
import argparse
import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Literal
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class QuickTestResult:
    timestamp: str
    candidate_id: str
    job_id: str
    
    # Hard disqualifiers
    hard_disqualifiers: List[Dict[str, str]]  # [{"rule": "...", "status": "pass|fail"}]
    hard_disqualifier_status: Literal["pass", "fail"]
    
    # Soft disqualifiers
    soft_disqualifiers: List[Dict[str, any]]  # [{"flag": "...", "severity": "low|medium|high", "detail": "..."}]
    
    # Red flags
    red_flags: List[Dict[str, str]]  # [{"flag": "...", "evidence": "..."}]
    
    # Early score estimate
    early_score_estimate: Optional[int]  # 0-100, None if can't estimate
    confidence: Optional[Literal["high", "medium", "low"]]
    
    # Recommendation
    recommendation: Literal["pass", "reject", "review"]
    reasoning: str
    
    source: str = "quick_test_v2"


def load_deal_breakers(job_dir: Path) -> List[str]:
    """Load deal breakers from job directory"""
    db_path = job_dir / "deal_breakers.json"
    if not db_path.exists():
        logger.warning(f"No deal_breakers.json found at {db_path}")
        return []
    
    with open(db_path) as f:
        return json.load(f)


def load_parsed_resume(candidate_dir: Path) -> Dict:
    """Load parsed resume text and fields"""
    text_path = candidate_dir / "parsed" / "text.md"
    fields_path = candidate_dir / "parsed" / "fields.json"
    
    if not text_path.exists() or not fields_path.exists():
        raise FileNotFoundError(f"Parsed resume not found in {candidate_dir / 'parsed'}")
    
    resume_text = text_path.read_text()
    with open(fields_path) as f:
        fields = json.load(f)
    
    return {
        "text": resume_text,
        "fields": fields
    }


def check_hard_disqualifiers(resume_data: Dict, deal_breakers: List[str]) -> tuple[List[Dict], str]:
    """Wrapper for LLM checker"""
    return check_deal_breakers_llm(resume_data["text"], deal_breakers)


def check_soft_disqualifiers(resume_data: Dict, resume_text: str) -> List[Dict]:
    """
    Check soft flags that warrant review.
    Returns: List of soft disqualifier flags
    """
    flags = []
    fields = resume_data["fields"]
    
    # 1. Experience gap (candidate has < 50% of typical experience)
    years_exp = fields.get("years_experience", 0)
    if years_exp < 3:
        flags.append({
            "flag": "limited_experience",
            "severity": "medium",
            "detail": f"Only {years_exp} years experience (may be junior for role)"
        })
    
    # 2. Job hopping (6+ roles in 5 years, based on heuristic)
    role_count = resume_text.lower().count("position") + resume_text.lower().count("role") + resume_text.count("2024") + resume_text.count("2023") + resume_text.count("2022")
    # Rough heuristic - can be improved
    if role_count > 8:
        flags.append({
            "flag": "possible_job_hopping",
            "severity": "low",
            "detail": f"Many role mentions ({role_count}) - verify tenure"
        })
    
    # 3. Career gaps (heuristic: look for gap language)
    gap_patterns = [r'gap', r'break', r'sabbatical', r'hiatus', r'unemployed']
    for pattern in gap_patterns:
        if re.search(pattern, resume_text, re.I):
            flags.append({
                "flag": "career_gap_mentioned",
                "severity": "low",
                "detail": f"Possible gap detected (keyword: {pattern})"
            })
            break
    
    # 4. Declining trajectory (heuristic: more senior roles earlier)
    # Look for title patterns
    senior_early = False
    if re.search(r'(director|vp|head|chief)', resume_text[:len(resume_text)//3], re.I):
        if not re.search(r'(director|vp|head|chief)', resume_text[len(resume_text)//3:], re.I):
            senior_early = True
    
    if senior_early:
        flags.append({
            "flag": "possible_declining_trajectory",
            "severity": "medium",
            "detail": "Senior titles appear early but not later - verify progression"
        })
    
    return flags


def detect_red_flags(resume_text: str) -> List[Dict]:
    """
    Detect resume red flags.
    Returns: List of red flags with evidence
    """
    red_flags = []
    
    # 1. Very short employment stints (< 1 year, multiple times)
    short_stints = re.findall(r'(\d+)\s*months?', resume_text, re.I)
    if len(short_stints) >= 3:
        red_flags.append({
            "flag": "multiple_short_stints",
            "evidence": f"{len(short_stints)} roles with <1 year tenure"
        })
    
    # 2. Lack of quantified achievements
    numbers = re.findall(r'\d+%|\$\d+|\d+x|increased|decreased|reduced|improved', resume_text, re.I)
    if len(numbers) < 3:
        red_flags.append({
            "flag": "lack_of_quantified_impact",
            "evidence": f"Only {len(numbers)} quantified achievements"
        })
    
    # 3. Generic/vague language
    generic_count = sum(1 for phrase in ["responsible for", "worked on", "helped with", "assisted", "participated"] if phrase in resume_text.lower())
    if generic_count > 5:
        red_flags.append({
            "flag": "vague_descriptions",
            "evidence": f"{generic_count} instances of generic language"
        })
    
    # 4. Inconsistent formatting (hard to detect, skip for MVP)
    
    return red_flags


def estimate_early_score(resume_data: Dict, resume_text: str, deal_breaker_status: str) -> tuple[Optional[int], Optional[str]]:
    """
    Estimate score for obvious cases.
    Returns: (score, confidence)
    """
    # Fail hard disqualifiers → 0-20
    if deal_breaker_status == "fail":
        return 15, "high"
    
    # Check for strong signals
    fields = resume_data["fields"]
    years_exp = fields.get("years_experience", 0)
    
    # Strong positive signals
    top_companies = ["mckinsey", "bcg", "bain", "goldman", "google", "microsoft", "amazon", "apple", "meta", "netflix"]
    top_schools = ["harvard", "stanford", "mit", "yale", "princeton", "wharton", "columbia", "chicago", "berkeley"]
    
    has_top_company = any(co in resume_text.lower() for co in top_companies)
    has_top_school = any(school in resume_text.lower() for school in top_schools)
    has_leadership = any(kw in resume_text.lower() for kw in ["led team", "managed", "director", "vp", "head of"])
    has_impact = len(re.findall(r'\d+%|\$\d+|\d+x|increased.*\d+|reduced.*\d+', resume_text, re.I)) >= 5
    
    strong_signals = sum([has_top_company, has_top_school, has_leadership, has_impact])
    
    # Obvious pass: 3+ strong signals + adequate experience
    if strong_signals >= 3 and years_exp >= 5:
        return 85, "high"
    
    # Likely pass: 2 strong signals + good experience
    if strong_signals >= 2 and years_exp >= 4:
        return 70, "medium"
    
    # Obvious reject: weak everything
    if strong_signals == 0 and years_exp < 2:
        return 25, "high"
    
    # Likely reject: 1 weak signal
    if strong_signals <= 1 and years_exp < 3:
        return 35, "medium"
    
    # Ambiguous - needs full scoring
    return None, None


def run_quick_test(job_id: str, candidate_id: str, job_dir: Path, candidate_dir: Path) -> QuickTestResult:
    """
    Run quick test on candidate.
    """
    # Load data
    deal_breakers = load_deal_breakers(job_dir)
    resume_data = load_parsed_resume(candidate_dir)
    resume_text = resume_data["text"]
    
    # Run checks
    hard_results, hard_status = check_hard_disqualifiers(resume_data, deal_breakers)
    soft_flags = check_soft_disqualifiers(resume_data, resume_text)
    red_flags = detect_red_flags(resume_text)
    early_score, confidence = estimate_early_score(resume_data, resume_text, hard_status)
    
    # Determine recommendation
    if hard_status == "fail":
        recommendation = "reject"
        reasoning = "Failed hard disqualifier(s)"
    elif early_score is not None and confidence == "high":
        if early_score >= 70:
            recommendation = "pass"
            reasoning = f"Strong early signals (estimated score: {early_score})"
        elif early_score <= 30:
            recommendation = "reject"
            reasoning = f"Weak profile (estimated score: {early_score})"
        else:
            recommendation = "review"
            reasoning = f"Ambiguous (estimated score: {early_score})"
    elif len(soft_flags) >= 3 or any(f["severity"] == "high" for f in soft_flags):
        recommendation = "review"
        reasoning = f"{len(soft_flags)} soft flags detected"
    elif len(red_flags) >= 3:
        recommendation = "review"
        reasoning = f"{len(red_flags)} red flags detected"
    else:
        recommendation = "pass"
        reasoning = "No major concerns in quick test"
    
    return QuickTestResult(
        timestamp=datetime.utcnow().isoformat() + "Z",
        candidate_id=candidate_id,
        job_id=job_id,
        hard_disqualifiers=hard_results,
        hard_disqualifier_status=hard_status,
        soft_disqualifiers=soft_flags,
        red_flags=red_flags,
        early_score_estimate=early_score,
        confidence=confidence,
        recommendation=recommendation,
        reasoning=reasoning
    )


def write_output(result: QuickTestResult, output_path: Path, dry_run: bool = False):
    """Write quick test result"""
    if dry_run:
        logger.info(f"[DRY RUN] Would write: {output_path}")
        logger.info(f"[DRY RUN] Recommendation: {result.recommendation} ({result.reasoning})")
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(asdict(result), f, indent=2)
    
    logger.info(f"✓ Wrote quick test → {output_path}")
    logger.info(f"  Recommendation: {result.recommendation} ({result.reasoning})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Quick Test v2")
    parser.add_argument("--job", required=True, help="Job ID")
    parser.add_argument("--candidate", required=True, help="Candidate ID")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    try:
        # Locate directories
        job_dir = Path(f"jobs/{args.job}").resolve()
        candidate_dir = job_dir / "candidates" / args.candidate
        
        if not job_dir.exists():
            raise FileNotFoundError(f"Job not found: {job_dir}")
        if not candidate_dir.exists():
            raise FileNotFoundError(f"Candidate not found: {candidate_dir}")
        
        # Run quick test
        result = run_quick_test(args.job, args.candidate, job_dir, candidate_dir)
        
        # Write output
        output_path = candidate_dir / "outputs" / "quick_test.json"
        write_output(result, output_path, dry_run=args.dry_run)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
