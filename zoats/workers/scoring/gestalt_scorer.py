#!/usr/bin/env python3
import sys as _sys
from pathlib import Path as _Path
_REPO_ROOT = _Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))
from pathlib import Path
"""
Gestalt Evaluation System

Evaluates candidates as a bundle of capabilities rather than numeric scores.
Decides: Is this person worth talking to?

Decisions:
- STRONG_INTERVIEW: Clear fit OR compelling unusual combination
- INTERVIEW: Promising, needs verification in conversation
- MAYBE: Intriguing but needs clarification (triggers email with 1-3 questions)
- PASS: Not a fit for this role

Output includes:
- Decision + confidence
- Key strengths (what makes them compelling)
- Concerns (what gives us pause)
- Interview focus areas
- For MAYBE: Specific clarification questions
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from workers.scoring.zo_llm_extractors import extract_signals_with_zo_llm

from workers.ai_detection.llm_detector import detect_ai_resume_llm as detect_ai_resume

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class KeyStrength:
    """What makes this candidate compelling"""
    category: str  # e.g., "Elite Pedigree", "Quantified Impact", "Transferable Skills"
    evidence: str  # Specific resume evidence
    relevance: str  # Why this matters for the role


@dataclass
class Concern:
    """What gives us pause"""
    issue: str  # e.g., "No direct consulting experience"
    severity: str  # "minor" | "moderate" | "major"
    can_mitigate: bool  # Can this be addressed in interview/clarification?


@dataclass
class ClarificationQuestion:
    """Specific question to resolve uncertainty"""
    question: str
    why_asking: str  # Context for employer approval
    deal_breaker: bool  # Is this a potential disqualifier?


@dataclass
class GestaltEvaluation:
    """Complete gestalt evaluation"""
    candidate_id: str
    job_id: str
    decision: str  # STRONG_INTERVIEW | INTERVIEW | MAYBE | PASS
    confidence: str  # high | medium | low
    
    # Core assessment
    key_strengths: List[KeyStrength]
    concerns: List[Concern]
    overall_narrative: str  # 2-3 sentence gestalt
    
    # Actionable guidance
    interview_focus: List[str]  # What to probe in interview
    clarification_questions: Optional[List[ClarificationQuestion]]  # For MAYBE only
    
    # Meta signals
    ai_detection: Dict
    elite_signals: List[Dict]
    business_impact: List[Dict]
    
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


def generate_clarification_questions(concerns: List[Concern], resume_text: str, job_id: str) -> List[str]:
    """Generate targeted clarification questions for major concerns"""
    questions = []
    
    for concern in concerns[:3]:  # Max 3
        if concern.issue == "Unclear analytical depth":
            questions.append("Can you describe a specific situation where you used quantitative analysis to solve a complex business problem? What methodologies did you use and what was the outcome?")
        elif concern.issue == "Limited consulting experience":
            questions.append("While your background isn't in traditional consulting, can you share an example where you advised stakeholders, developed strategic recommendations, and drove implementation?")
        elif concern.issue == "Industry misalignment":
            questions.append(f"This role focuses on [industry from JD]. How would your experience transfer, and what specifically attracts you to this domain?")
        elif "career progression" in concern.issue.lower():
            questions.append("Could you walk us through your career trajectory and explain the strategic rationale behind your key transitions?")
        elif "gap" in concern.issue.lower():
            questions.append("We noticed a potential gap in your timeline. Could you help us understand what you were focused on during that period?")
        else:
            questions.append(f"Regarding {concern.issue.lower()}: can you provide specific examples or context that would help us better evaluate your fit?")
    
    return questions


def evaluate_gestalt(
    resume_text: str,
    rubric: Dict,
    job_id: str,
    candidate_id: str,
    candidate_dir: Path = None
) -> GestaltEvaluation:
    """Main evaluation function"""
    
    # Run AI detection first
    ai_result = detect_ai_resume(resume_text)
    
    # Check for cached extraction first
    extraction_dict = None
    if candidate_dir:
        cache_path = candidate_dir / "outputs" / "signal_extraction_cache.json"
        if cache_path.exists():
            logger.info(f"Using cached LLM extraction from {cache_path}")
            extraction_dict = json.loads(cache_path.read_text())
    
    # If no cache, extract with LLM
    if not extraction_dict:
        extraction_dict = extract_signals_with_zo_llm(resume_text, job_context=job_id)
    
    # If extraction failed, try loading from cache
    if candidate_dir and (not extraction_dict.get("elite_signals") and not extraction_dict.get("business_impact")):
        cache_path = candidate_dir / "outputs" / "signal_extraction_cache.json"
        if cache_path.exists():
            logger.info(f"Loading signals from cache: {cache_path}")
            extraction_dict = json.loads(cache_path.read_text())
    
    # Convert dict to ExtractionResult
    from llm_extractors import ExtractionResult
    extraction = ExtractionResult(
        business_impact=extraction_dict.get("business_impact", []),
        elite_signals=extraction_dict.get("elite_signals", []),
        consulting_experience=extraction_dict.get("consulting_experience", {}),
        role_match=extraction_dict.get("role_match", {}),
        red_flags=extraction_dict.get("red_flags", [])
    )
    
    # Immediate PASS if red flags
    if extraction.red_flags:
        return GestaltEvaluation(
            candidate_id=candidate_id,
            job_id=job_id,
            decision="PASS",
            confidence="high",
            key_strengths=[],
            concerns=[Concern(issue=flag, severity="disqualifying", can_mitigate=False) for flag in extraction.red_flags],
            overall_narrative=f"Not a fit: {', '.join(extraction.red_flags)}",
            interview_focus=[],
            clarification_questions=None,
            ai_detection=ai_result,
            elite_signals=extraction.elite_signals,
            business_impact=extraction.business_impact,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    
    # Extract signals
    impacts = extraction.business_impact
    elite_signals = extraction.elite_signals
    consulting_exp = extraction.consulting_experience
    role_fit = extraction.role_match
    ai_result = detect_ai_resume(resume_text)
    
    resume_lower = resume_text.lower()
    job_lower = job_id.lower()
    
    # Initialize
    strengths = []
    concerns = []
    interview_focus = []
    clarifications = []
    
    # === PATTERN MATCHING ===
    
    # Check for direct company match (slam dunk)
    has_target_company = any(comp in resume_lower for comp in ['mckinsey', 'bain', 'bcg'] if comp in job_lower)
    
    # Check for consulting background
    has_consulting = consulting_exp.get('has_direct', False)
    
    # Check for elite pedigree
    has_elite = len(elite_signals) > 0
    elite_boost = 1.0 + sum(sig.get('boost', 1.0) - 1.0 for sig in elite_signals)
    elite_boost = min(elite_boost, 1.5)
    
    # Check for business impact
    has_major_impact = any(imp.get('value', 0) >= 50 for imp in impacts)  # $50M+
    has_impact = len(impacts) > 0
    
    # Check for analytical capability
    analytical_strength = 0.7 if role_fit.get('fit_score', 0) > 0.6 else 0.3
    
    # === BUILD STRENGTHS ===
    
    if has_target_company:
        strengths.append(KeyStrength(
            category="Direct Experience",
            evidence=f"Former employee at target company",
            relevance="Already knows the firm, culture, and work style"
        ))
    
    if has_major_impact:
        top_impact = max(impacts, key=lambda x: x.get('value', 0))
        strengths.append(KeyStrength(
            category="Quantified Impact",
            evidence=f"${top_impact.get('value', 0):.0f}M {top_impact.get('type', '')}",
            relevance="Demonstrated ability to drive large-scale business outcomes"
        ))
    
    if has_elite:
        top_signal = max(elite_signals, key=lambda x: x.get('boost', 1.0))
        strengths.append(KeyStrength(
            category="Elite Selection",
            evidence=top_signal.get('detail', ''),
            relevance="Proven ability to clear high bars"
        ))
    
    if has_consulting:
        strengths.append(KeyStrength(
            category="Consulting Background",
            evidence="Direct consulting/strategy experience",
            relevance="Familiar with consulting work and client engagement"
        ))
    
    if analytical_strength >= 0.7:
        strengths.append(KeyStrength(
            category="Analytical Capability",
            evidence="Strong quantitative/analytical background",
            relevance="Can handle data-driven problem solving"
        ))
    
    # === BUILD CONCERNS ===
    
    if not has_consulting and not has_target_company:
        concerns.append(Concern(
            issue="No direct consulting experience",
            severity="moderate",
            can_mitigate=True
        ))
        interview_focus.append("Assess ability to structure ambiguous problems")
        interview_focus.append("Gauge comfort with client-facing work")
    
    if not has_impact and not has_consulting:
        concerns.append(Concern(
            issue="Limited evidence of business outcomes",
            severity="moderate",
            can_mitigate=True
        ))
        clarifications.append(ClarificationQuestion(
            question="Can you share 1-2 examples of measurable business impact you've driven (with approximate scale)?",
            why_asking="Resume lacks quantified outcomes; need to assess results orientation",
            deal_breaker=False
        ))
    
    if analytical_strength < 0.5:
        concerns.append(Concern(
            issue="Unclear analytical depth",
            severity="major",
            can_mitigate=True
        ))
        clarifications.append(ClarificationQuestion(
            question="Can you describe your experience with quantitative analysis or data-driven problem solving?",
            why_asking="Consulting requires strong analytical capability; need evidence",
            deal_breaker=True
        ))
    
    if ai_result['likelihood'] == 'high':
        concerns.append(Concern(
            issue="Resume appears AI-generated (generic, low specificity)",
            severity="major",
            can_mitigate=False
        ))
    
    # === MAKE DECISION ===
    
    # Pre-compute decision variables
    has_any_business_signal = len(impacts) > 0 or len(elite_signals) > 0 or has_consulting
    role_mismatch_keywords = ["barista", "cashier", "retail", "server", "waiter", "sales associate", "manual labor"]
    has_role_mismatch = any(kw in resume_text.lower() for kw in role_mismatch_keywords)
    
    # Initialize defaults
    decision = "PASS"
    confidence = "medium"
    narrative = "Insufficient evidence of consulting-relevant capabilities for this role."
    
    # Immediate disqualifiers
    if ai_result['likelihood'] == 'high':
        decision = "PASS"
        confidence = "high"
        narrative = "Resume appears AI-generated with generic language and low specificity. Not a genuine candidate."
    
    # Check for direct target company match (HIGHEST PRIORITY)
    elif has_target_company:
        decision = "STRONG_INTERVIEW"
        confidence = "high"
        narrative = "Former employee at target company. Direct experience makes this a strong fit worth immediate conversation."
    
    # Elite consulting background + major impact
    elif has_consulting and has_major_impact and has_elite:
        decision = "STRONG_INTERVIEW"
        confidence = "high"
        narrative = f"Elite consulting background with 0M+ business impact. Strong traditional candidate."
    
    # Solid consulting background
    elif has_consulting and (has_elite or has_major_impact):
        decision = "STRONG_INTERVIEW"
        confidence = "medium"
        narrative = "Solid consulting background with strong supporting signals. Worth prioritizing."
    
    # Strong bundle (multiple strengths, minimal concerns)
    elif len(strengths) >= 3 and len(concerns) <= 1 and has_any_business_signal:
        decision = "STRONG_INTERVIEW"
        confidence = "medium"
        narrative = "Compelling combination of signals. Strong candidate worth interviewing."
    
    # Consulting experience alone
    elif has_consulting:
        decision = "INTERVIEW"
        confidence = "medium"
        narrative = "Consulting background. Standard interview to assess depth and fit."
    
    # Elite + analytical strength
    elif has_elite and analytical_strength >= 0.7:
        decision = "INTERVIEW"
        confidence = "medium"
        narrative = "Promising candidate with elite background and transferable skills. Worth exploring fit."
    
    # Maybe: elite + clarifiable gaps
    elif has_elite and len(clarifications) > 0 and len(clarifications) <= 3:
        decision = "MAYBE"
        confidence = "low"
        narrative = "Intriguing elite background but key gaps. Worth clarifying before deciding."
    
    # Maybe: major impact + analytical
    elif has_major_impact and analytical_strength >= 0.6 and len(clarifications) <= 3:
        decision = "MAYBE"
        confidence = "low"
        narrative = "Strong business outcomes but unclear consulting readiness. Clarification needed."
    
    # Backup list: too many questions
    elif len(clarifications) > 3:
        decision = "BACKUP_LIST"
        confidence = "low"
        narrative = "Too many fundamental gaps to clarify efficiently. Consider if shortlist insufficient."
    
    # Pass: role mismatch
    elif has_role_mismatch and not has_any_business_signal:
        decision = "PASS"
        confidence = "high"
        narrative = "Role mismatch for consulting position. Not a fit."
    
    # Pass: default (weak signals)
    else:
        if not has_elite and not has_impact:
            confidence = "high"
            narrative = "No compelling signals for consulting role. Not a fit."

    return GestaltEvaluation(
        candidate_id=candidate_id,
        job_id=job_id,
        decision=decision,
        confidence=confidence,
        key_strengths=strengths,
        concerns=concerns,
        overall_narrative=narrative,
        interview_focus=interview_focus if decision in ["STRONG_INTERVIEW", "INTERVIEW"] else [],
        clarification_questions=clarifications if decision == "MAYBE" else None,
        ai_detection=ai_result,
        elite_signals=elite_signals,
        business_impact=impacts,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


if __name__ == "__main__":
    # Test
    test_resume = """
    VRIJEN ATTAWAR
    Cornell MBA
    
    McKinsey & Company - Associate
    - Led strategy projects for Fortune 500 clients
    - Drove $4M revenue growth
    
    Education: Cornell MBA, Outstanding academic record
    """
    
    result = evaluate_gestalt(test_resume, {}, "test-fixture", "test")
    print(json.dumps(result.to_dict(), indent=2))
