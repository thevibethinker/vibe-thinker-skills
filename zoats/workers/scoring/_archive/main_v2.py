#!/usr/bin/env python3
"""
Scoring Engine v2

Semantic batch scoring with transferable skills and transparency.

Usage:
  python workers/scoring/main_v2.py \\
    --job <job-id> \\
    --candidate <candidate-id> \\
    [--dry-run]

Design:
- Single LLM call scores all criteria at once
- Maps transferable skills (flags when doing so)
- Provides evidence + reasoning for each score
- Calculates meta-signals (trajectory, achievement density)
- Structured output (Pydantic)

Quality:
- Logging, --dry-run, error handling, verification
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
class CriterionScore:
    criterion_id: str
    criterion_name: str
    weight: float
    score: int  # 0-10
    weighted_score: float  # (score/10) * weight
    evidence: str  # Quote from resume
    reasoning: str  # Why this score
    match_type: Literal["direct", "transferable", "weak", "none"]


@dataclass
class MetaSignal:
    name: str
    value: str  # e.g., "ascending", "high", "coherent"
    evidence: str
    impact: str  # How this affects evaluation


@dataclass
class ScoringResult:
    timestamp: str
    candidate_id: str
    job_id: str
    total_score: float  # 0-100
    criterion_scores: List[CriterionScore]
    meta_signals: List[MetaSignal]
    overall_assessment: str
    recommendation: Literal["strong_yes", "yes", "maybe", "no", "strong_no"]
    source: str = "scoring_v2"
    
    def validate(self) -> bool:
        """Verify scoring integrity"""
        calculated_total = sum(cs.weighted_score for cs in self.criterion_scores)
        if abs(calculated_total - self.total_score) > 0.1:
            logger.error(f"Total score mismatch: {calculated_total} vs {self.total_score}")
            return False
        return True


def load_rubric(job_dir: Path) -> Dict:
    """Load rubric.json"""
    rubric_path = job_dir / "rubric.json"
    if not rubric_path.exists():
        raise FileNotFoundError(f"Rubric not found: {rubric_path}")
    
    with open(rubric_path) as f:
        return json.load(f)


def load_resume(candidate_dir: Path) -> Dict:
    """Load parsed resume"""
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


def score_all_criteria_llm(resume_data: Dict, rubric: Dict) -> tuple[List[CriterionScore], List[MetaSignal], str]:
    """
    Single LLM call to score all criteria + extract meta-signals.
    
    This is the core semantic reasoning engine.
    For MVP, we'll use heuristic fallback.
    """
    resume_text = resume_data["text"]
    fields = resume_data["fields"]
    criteria = rubric["criteria"]
    
    logger.info(f"Scoring {len(criteria)} criteria with semantic reasoning...")
    
    # TODO: Replace with actual LLM call
    # For MVP, use heuristic scoring with pattern matching
    criterion_scores = []
    
    for c in criteria:
        score, evidence, reasoning, match_type = _score_criterion_heuristic(
            c, resume_text, fields
        )
        
        weighted_score = (score / 10.0) * c["weight"]
        
        criterion_scores.append(CriterionScore(
            criterion_id=c["id"],
            criterion_name=c["name"],
            weight=c["weight"],
            score=score,
            weighted_score=weighted_score,
            evidence=evidence,
            reasoning=reasoning,
            match_type=match_type
        ))
    
    # Extract meta-signals
    meta_signals = _extract_meta_signals_heuristic(resume_text, fields)
    
    # Overall assessment
    total_score = sum(cs.weighted_score for cs in criterion_scores)
    assessment = _generate_assessment(total_score, criterion_scores, meta_signals)
    
    return criterion_scores, meta_signals, assessment


def _score_criterion_heuristic(criterion: Dict, resume_text: str, fields: Dict) -> tuple[int, str, str, str]:
    """
    Heuristic scoring for a single criterion.
    Returns: (score, evidence, reasoning, match_type)
    """
    keywords = criterion.get("keywords", [])
    description = criterion.get("description", "")
    name = criterion.get("name", "")
    
    # Count keyword matches
    matches = []
    for kw in keywords:
        pattern = rf'\b{re.escape(kw)}\b'
        found = list(re.finditer(pattern, resume_text, re.I))
        if found:
            matches.append((kw, len(found)))
    
    total_matches = sum(count for _, count in matches)
    match_ratio = total_matches / len(keywords) if keywords else 0
    
    # Extract evidence
    evidence_lines = []
    for kw, _ in matches[:3]:
        for line in resume_text.split('\n'):
            if kw.lower() in line.lower() and len(line.strip()) > 10:
                evidence_lines.append(line.strip()[:100])
                break
    
    evidence = " | ".join(evidence_lines) if evidence_lines else "No direct evidence"
    
    # Determine score based on match ratio and context
    if match_ratio >= 0.6:
        score = 8 + min(2, int(match_ratio * 2))
        match_type = "direct"
        reasoning = f"Strong keyword match ({total_matches}/{len(keywords)} keywords)"
    elif match_ratio >= 0.3:
        score = 5 + int(match_ratio * 5)
        match_type = "direct"
        reasoning = f"Moderate keyword match ({total_matches}/{len(keywords)} keywords)"
    elif match_ratio >= 0.1:
        # Check for transferable skills
        transferable = _check_transferable(criterion, resume_text)
        if transferable:
            score = 5 + transferable["strength"]
            match_type = "transferable"
            reasoning = f"Transferable: {transferable['explanation']}"
            evidence = transferable["evidence"]
        else:
            score = 2 + int(match_ratio * 10)
            match_type = "weak"
            reasoning = f"Weak match ({total_matches}/{len(keywords)} keywords)"
    else:
        score = 0
        match_type = "none"
        reasoning = "No evidence found"
    
    # Cap score at 10
    score = min(10, score)
    
    return score, evidence, reasoning, match_type


def _check_transferable(criterion: Dict, resume_text: str) -> Optional[Dict]:
    """
    Check for transferable skills.
    Returns: {strength: 0-3, explanation: str, evidence: str} or None
    """
    criterion_id = criterion.get("id", "")
    name = criterion.get("name", "").lower()
    
    # Define transferable skill mappings
    transferables = {
        "client": {
            "alternatives": ["customer", "stakeholder", "partner", "user"],
            "explanation": "Client engagement maps to customer/stakeholder management",
            "strength": 2
        },
        "analytical": {
            "alternatives": ["data", "research", "analysis", "quantitative", "metrics"],
            "explanation": "Analytical skills evident through data/research work",
            "strength": 2
        },
        "leadership": {
            "alternatives": ["led", "managed", "directed", "coached", "mentored"],
            "explanation": "Leadership through team management and mentoring",
            "strength": 2
        },
        "strategy": {
            "alternatives": ["planning", "roadmap", "vision", "initiative"],
            "explanation": "Strategic thinking through planning and initiative work",
            "strength": 2
        },
        "problem-solving": {
            "alternatives": ["solved", "resolved", "addressed", "improved", "optimized"],
            "explanation": "Problem-solving through improvement and optimization",
            "strength": 2
        }
    }
    
    for key, mapping in transferables.items():
        if key in name or key in criterion_id:
            for alt in mapping["alternatives"]:
                if alt in resume_text.lower():
                    # Find evidence
                    for line in resume_text.split('\n'):
                        if alt in line.lower() and len(line.strip()) > 10:
                            return {
                                "strength": mapping["strength"],
                                "explanation": mapping["explanation"],
                                "evidence": line.strip()[:100]
                            }
    
    return None


def _extract_meta_signals_heuristic(resume_text: str, fields: Dict) -> List[MetaSignal]:
    """
    Extract meta-signals from resume.
    """
    meta_signals = []
    
    # 1. Trajectory
    # Look for progression indicators
    promotions = resume_text.lower().count("promoted") + resume_text.lower().count("advanced")
    senior_titles = len(re.findall(r'\b(director|vp|head|chief|lead|senior|principal)\b', resume_text, re.I))
    
    if promotions >= 2 or senior_titles >= 3:
        trajectory = "ascending"
        evidence = f"{promotions} promotions, {senior_titles} senior titles"
        impact = "Strong upward trajectory indicates high potential"
    elif promotions >= 1 or senior_titles >= 1:
        trajectory = "positive"
        evidence = f"{promotions} promotions, {senior_titles} senior titles"
        impact = "Some growth visible"
    else:
        trajectory = "flat"
        evidence = "Limited progression indicators"
        impact = "Unclear career growth"
    
    meta_signals.append(MetaSignal(
        name="trajectory",
        value=trajectory,
        evidence=evidence,
        impact=impact
    ))
    
    # 2. Achievement density
    quantified = len(re.findall(r'\d+%|\$\d+|\d+x|increased.*\d+|reduced.*\d+|grew.*\d+|achieved.*\d+', resume_text, re.I))
    years_exp = fields.get("years_experience", 1)
    density = quantified / years_exp if years_exp > 0 else 0
    
    if density >= 3:
        ach_value = "high"
        ach_evidence = f"{quantified} quantified achievements over {years_exp} years ({density:.1f}/year)"
        ach_impact = "High-impact profile with measurable outcomes"
    elif density >= 1.5:
        ach_value = "medium"
        ach_evidence = f"{quantified} quantified achievements over {years_exp} years ({density:.1f}/year)"
        ach_impact = "Some impact visible"
    else:
        ach_value = "low"
        ach_evidence = f"{quantified} quantified achievements over {years_exp} years ({density:.1f}/year)"
        ach_impact = "Limited quantified impact"
    
    meta_signals.append(MetaSignal(
        name="achievement_density",
        value=ach_value,
        evidence=ach_evidence,
        impact=ach_impact
    ))
    
    # 3. Narrative coherence
    # Check for career story
    has_progression = promotions > 0 or "grew" in resume_text.lower() or "expanded" in resume_text.lower()
    has_theme = any(theme in resume_text.lower() for theme in ["passion", "focus", "specialized", "expertise"])
    
    if has_progression and has_theme:
        coherence = "strong"
        coh_evidence = "Clear career narrative with progression and focus"
        coh_impact = "Intentional career building"
    elif has_progression or has_theme:
        coherence = "moderate"
        coh_evidence = "Some narrative elements present"
        coh_impact = "Somewhat coherent story"
    else:
        coherence = "weak"
        coh_evidence = "Limited narrative clarity"
        coh_impact = "Unclear career story"
    
    meta_signals.append(MetaSignal(
        name="narrative_coherence",
        value=coherence,
        evidence=coh_evidence,
        impact=coh_impact
    ))
    
    return meta_signals


def _generate_assessment(total_score: float, criterion_scores: List[CriterionScore], meta_signals: List[MetaSignal]) -> str:
    """Generate overall assessment narrative"""
    
    # Strengths
    strong_criteria = [cs for cs in criterion_scores if cs.score >= 8]
    weak_criteria = [cs for cs in criterion_scores if cs.score <= 3]
    transferable_count = len([cs for cs in criterion_scores if cs.match_type == "transferable"])
    
    assessment = f"**Total Score: {total_score:.1f}/100**\n\n"
    
    if total_score >= 75:
        assessment += "**Overall: Strong candidate** - Exceeds role requirements.\n\n"
    elif total_score >= 60:
        assessment += "**Overall: Good candidate** - Meets most requirements.\n\n"
    elif total_score >= 40:
        assessment += "**Overall: Marginal candidate** - Mixed profile.\n\n"
    else:
        assessment += "**Overall: Weak candidate** - Below requirements.\n\n"
    
    # Strengths
    if strong_criteria:
        assessment += f"**Strengths:** {len(strong_criteria)} criteria scored 8+\n"
        for cs in strong_criteria[:3]:
            assessment += f"- {cs.criterion_name} ({cs.score}/10): {cs.reasoning}\n"
        assessment += "\n"
    
    # Gaps
    if weak_criteria:
        assessment += f"**Gaps:** {len(weak_criteria)} criteria scored 3 or below\n"
        for cs in weak_criteria[:3]:
            assessment += f"- {cs.criterion_name} ({cs.score}/10): {cs.reasoning}\n"
        assessment += "\n"
    
    # Transferable skills
    if transferable_count > 0:
        assessment += f"**Note:** {transferable_count} criteria scored using transferable skills (flagged in details).\n\n"
    
    # Meta-signals
    assessment += "**Meta-Signals:**\n"
    for ms in meta_signals:
        assessment += f"- {ms.name.replace('_', ' ').title()}: {ms.value} — {ms.impact}\n"
    
    return assessment


def run_scoring(job_id: str, candidate_id: str, job_dir: Path, candidate_dir: Path) -> ScoringResult:
    """
    Run full scoring on candidate.
    """
    # Load data
    rubric = load_rubric(job_dir)
    resume_data = load_resume(candidate_dir)
    
    # Score all criteria
    criterion_scores, meta_signals, assessment = score_all_criteria_llm(resume_data, rubric)
    
    # Calculate total
    total_score = sum(cs.weighted_score for cs in criterion_scores)
    
    # Determine recommendation
    if total_score >= 80:
        recommendation = "strong_yes"
    elif total_score >= 65:
        recommendation = "yes"
    elif total_score >= 50:
        recommendation = "maybe"
    elif total_score >= 35:
        recommendation = "no"
    else:
        recommendation = "strong_no"
    
    result = ScoringResult(
        timestamp=datetime.utcnow().isoformat() + "Z",
        candidate_id=candidate_id,
        job_id=job_id,
        total_score=total_score,
        criterion_scores=criterion_scores,
        meta_signals=meta_signals,
        overall_assessment=assessment,
        recommendation=recommendation
    )
    
    if not result.validate():
        raise ValueError("Scoring validation failed")
    
    return result


def write_output(result: ScoringResult, output_path: Path, dry_run: bool = False):
    """Write scoring result"""
    if dry_run:
        logger.info(f"[DRY RUN] Would write: {output_path}")
        logger.info(f"[DRY RUN] Total score: {result.total_score:.1f}, Recommendation: {result.recommendation}")
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(asdict(result), f, indent=2)
    
    logger.info(f"✓ Wrote scoring → {output_path}")
    logger.info(f"  Total: {result.total_score:.1f}/100, Recommendation: {result.recommendation}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scoring Engine v2")
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
        
        # Run scoring
        result = run_scoring(args.job, args.candidate, job_dir, candidate_dir)
        
        # Write output
        output_path = candidate_dir / "outputs" / "scores_v2.json"
        write_output(result, output_path, dry_run=args.dry_run)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
