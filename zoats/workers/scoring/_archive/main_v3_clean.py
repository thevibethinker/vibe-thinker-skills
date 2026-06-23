#!/usr/bin/env python3
"""
Scoring Engine v3 - Clean Semantic

Mock semantic scoring with signal extraction integration.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import re
from lib.paths import ZOATS_HOME

# Import extractors
sys.path.insert(0, str(Path(__file__).parent))
from extractors import extract_business_impact, extract_elite_signals, extract_capability_proxies

# Import AI detection
sys.path.insert(0, str(Path(__file__).parent.parent / "ai_detection"))
from detector import detect_ai_resume

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_rubric(job_dir: Path) -> Dict:
    """Load rubric.json"""
    rubric_path = job_dir / "rubric.json"
    if not rubric_path.exists():
        raise FileNotFoundError(f"Rubric not found: {rubric_path}")
    return json.loads(rubric_path.read_text())


def load_resume(candidate_dir: Path) -> Dict:
    """Load parsed resume text and fields"""
    text_path = candidate_dir / "parsed" / "text.md"
    fields_path = candidate_dir / "parsed" / "fields.json"
    
    if not text_path.exists():
        raise FileNotFoundError(f"Resume text not found: {text_path}")
    
    resume_text = text_path.read_text()
    fields = {}
    if fields_path.exists():
        fields = json.loads(fields_path.read_text())
    
    return {"text": resume_text, "fields": fields}


def score_candidate(resume_text: str, rubric: Dict, job_id: str, candidate_id: str) -> Dict:
    """
    Score candidate semantically with signal extraction.
    
    This is a mock implementation that uses heuristics + extracted signals.
    Replace with actual LLM call for production.
    """
    
    # Extract signals
    logger.info("Extracting signals...")
    impacts = extract_business_impact(resume_text)
    elite_signals = extract_elite_signals(resume_text)
    capability_proxies = extract_capability_proxies(resume_text)
    ai_detection = detect_ai_resume(resume_text)
    
    # Log extracted signals
    if impacts:
        logger.info(f"  Business impact: {len(impacts)} found")
    if elite_signals:
        logger.info(f"  Elite signals: {len(elite_signals)} found")
    
    # Calculate total elite boost
    elite_boost = 1.0
    for sig in elite_signals:
        elite_boost *= sig.boost_factor
    elite_boost = min(elite_boost, 1.5)  # Cap at 1.5x
    
    # Build signal context for scoring
    impact_context = ", ".join([f"${imp.value:.1f}M {imp.type}" for imp in impacts[:3]]) if impacts else "None"
    elite_context = ", ".join([sig.detail for sig in elite_signals[:3]]) if elite_signals else "None"
    
    logger.info(f"  Elite boost: {elite_boost:.2f}x")
    
    # Simplified keyword detection
    resume_lower = resume_text.lower()
    job_id_lower = job_id.lower()
    
    has_mckinsey = "mckinsey" in resume_lower and "mckinsey" in job_id_lower
    has_deloitte = "deloitte consulting" in resume_lower
    has_consulting = any(firm in resume_lower for firm in ["deloitte consulting", "bain", "bcg", "mckinsey"])
    has_top_mba = any(school in resume_lower for school in ["harvard business school", "hbs", "wharton", "stanford gsb"])
    has_cornell_mba = "cornell" in resume_lower and "mba" in resume_lower
    has_mba = "mba" in resume_lower
    has_strong_quant = capability_proxies.get('analytical_depth', 0) > 0.7
    has_consulting_skills = capability_proxies.get('consulting_skills', 0) > 0.8
    has_outcomes = bool(impacts)
    
    # Score each criterion
    scores = []
    for crit in rubric.get('criteria', []):
        score = 0
        evidence = "No direct evidence"
        reasoning = "Limited evidence"
        match_type = "none"
        
        crit_lower = crit.get("description", "").lower()
        crit_name_lower = crit.get("name", "").lower()
        
        # Education
        if "degree" in crit_name_lower or "education" in crit_lower:
            if has_top_mba:
                score = 9
                evidence = "Top-tier MBA (HBS/Wharton/Stanford)"
                reasoning = "Elite MBA program"
                match_type = "direct"
            elif has_cornell_mba:
                score = 8
                evidence = "Cornell MBA"
                reasoning = "Strong tier-1 MBA"
                match_type = "direct"
            elif has_mba:
                score = 7
                evidence = "MBA present"
                reasoning = "MBA credential"
                match_type = "direct"
        
        # Experience
        elif "experience" in crit_name_lower:
            if has_mckinsey:
                score = 10
                evidence = "Former McKinsey employee"
                reasoning = "Direct prior experience at target company"
                match_type = "direct"
            elif has_deloitte:
                score = 9
                evidence = "Deloitte Consulting experience"
                reasoning = "Top-tier strategy consulting"
                match_type = "direct"
            elif has_consulting:
                score = 8
                evidence = "Strategy consulting background"
                reasoning = "Relevant consulting experience"
                match_type = "direct"
        
        # Analytical
        elif "analyt" in crit_lower or "problem" in crit_lower:
            if has_mckinsey:
                score = 9
                evidence = "McKinsey analytical rigor"
                reasoning = "Proven through McKinsey tenure"
                match_type = "direct"
            elif has_consulting_skills and has_strong_quant and has_outcomes:
                score = 8
                evidence = f"Consulting + quantitative + outcomes ({impact_context})"
                reasoning = "Strong analytical capability with measurable business impact"
                match_type = "direct"
            elif has_strong_quant and has_outcomes:
                score = 7
                evidence = f"Quantitative work with outcomes ({impact_context})"
                reasoning = "Data-driven decision making with impact"
                match_type = "transferable"
            elif has_strong_quant:
                score = 6
                evidence = "Quantitative analysis capability"
                reasoning = "Analytical background evident"
                match_type = "transferable"
        
        # Default scoring for other criteria
        else:
            if has_consulting_skills:
                score = 7
                evidence = "Consulting-relevant skills"
                reasoning = "Transferable capabilities"
                match_type = "transferable"
            elif has_strong_quant:
                score = 6
                evidence = "Analytical capability"
                reasoning = "Some relevant background"
                match_type = "potential"
            else:
                score = 5
                evidence = "General capability"
                reasoning = "Baseline assessment"
                match_type = "potential"
        
        # Apply elite signal boost (only to scores showing real relevance, not defaults)
        if score >= 7 and elite_boost > 1.0:
            original_score = score
            score = min(10, score + (elite_boost - 1.0) * 2)  # Boost by up to 1 point
            reasoning += f" [Elite boost: {original_score:.1f}→{score:.1f} from {elite_context}]"
        
        scores.append({
            "criterion_id": crit.get("id", ""),
            "criterion_name": crit.get("name", ""),
            "weight": crit.get("weight", 10),
            "score": round(score, 1),
            "weighted_score": round(score * crit.get("weight", 10) / 10, 2),
            "evidence": evidence,
            "reasoning": reasoning,
            "match_type": match_type
        })
    
    total = sum(s['weighted_score'] for s in scores)
    
    return {
        "scores": scores,
        "total": round(total, 1),
        "meta_signals": {
            "business_impacts": [{"type": i.type, "value": f"${i.value:.1f}M", "confidence": i.confidence} for i in impacts[:5]],
            "elite_signals": [{"type": s.type, "detail": s.detail, "boost": s.boost_factor} for s in elite_signals[:5]],
            "capability_proxies": capability_proxies,
            "ai_detection": ai_detection
        },
        "overall_impression": f"{'Strong' if total >= 75 else 'Moderate' if total >= 60 else 'Weak'} candidate. {elite_context}",
        "red_flags": []
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score candidate with semantic evaluation")
    parser.add_argument("--job", required=True, help="Job ID")
    parser.add_argument("--candidate", required=True, help="Candidate ID")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    try:
        # Load data
        job_dir = ZOATS_HOME / "jobs" / args.job
        candidate_dir = job_dir / "candidates" / args.candidate
        
        logger.info(f"Job: {job_dir}")
        logger.info(f"Candidate: {candidate_dir}")
        
        rubric = load_rubric(job_dir)
        resume = load_resume(candidate_dir)
        
        # Score
        logger.info("Scoring with semantic reasoning + signal extraction...")
        result = score_candidate(resume['text'], rubric, args.job, args.candidate)
        
        total_score = result['total']
        
        # Determine recommendation
        if total_score >= 75:
            recommendation = "strong_pass"
        elif total_score >= 60:
            recommendation = "pass"
        elif total_score >= 50:
            recommendation = "review"
        else:
            recommendation = "no"
        
        # Build output
        output = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "candidate_id": args.candidate,
            "job_id": args.job,
            "total": total_score,
            "scores": result['scores'],
            "meta_signals": result['meta_signals'],
            "red_flags": result.get('red_flags', []),
            "overall_impression": result.get('overall_impression', ''),
            "recommendation": recommendation,
            "source": "scoring_v3_clean"
        }
        
        # Write
        output_path = candidate_dir / "outputs" / "scores_v3_clean.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if args.dry_run:
            logger.info(f"[DRY RUN] Would write: {output_path}")
            logger.info(f"[DRY RUN] Total score: {total_score}")
        else:
            output_path.write_text(json.dumps(output, indent=2))
            logger.info(f"✓ Wrote scoring → {output_path}")
            logger.info(f"  Total score: {total_score}/100")
            logger.info(f"  Recommendation: {recommendation}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
