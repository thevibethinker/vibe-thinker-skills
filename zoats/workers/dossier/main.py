#!/usr/bin/env python3
"""
Dossier Generator (Gestalt-Aware)
Consumes gestalt_evaluation.json and produces:
  - dossier.md (human-readable)
  - dossier.json (machine-readable rollup)
"""
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime, UTC

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def error_json(code: str, message: str, **details) -> str:
    payload = {"ok": False, "error": {"code": code, "message": message}}
    if details:
        payload["error"].update(details)
    return json.dumps(payload, indent=2)


def read_json(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception as e:
        logger.warning(f"Could not read {p}: {e}")
        return None


def format_elite_signals(signals):
    """Format elite signals with confidence + boost factor."""
    if not signals:
        return ["No elite signals detected"]
    
    lines = []
    for sig in signals:
        detail = sig.get("detail", "Unknown")
        conf = sig.get("confidence", 0)
        boost = sig.get("boost_factor", 1.0)
        lines.append(f"- {detail} (confidence: {conf:.2f}, boost: {boost:.2f}x)")
    return lines


def format_business_impact(impacts):
    """Format business impact with dollar amounts and context."""
    if not impacts:
        return ["No quantified business impact found"]
    
    lines = []
    for imp in impacts:
        value = imp.get("value", 0)
        impact_type = imp.get("type", "unknown")
        context = (imp.get("context", "") or "").strip()
        conf = imp.get("confidence", 0)
        
        if value >= 1:
            value_str = f"${value:.1f}M"
        else:
            value_str = f"${value*1000:.0f}K"
        
        lines.append(f"- {value_str} {impact_type} (confidence: {conf:.2f})")
        if context:
            ctx = context
            if len(ctx) > 160:
                ctx = ctx[:157].rstrip() + "…"
            lines.append(f"  Context: {ctx}")
    return lines


def format_concerns(concerns):
    """Format concerns with severity and mitigation info."""
    if not concerns:
        return ["None identified"]
    
    lines = []
    for concern in concerns:
        issue = concern.get("issue", "Unknown issue")
        severity = concern.get("severity", "unknown")
        can_mitigate = concern.get("can_mitigate", False)
        mitigation_str = "✓ Can mitigate" if can_mitigate else "✗ Hard to mitigate"
        lines.append(f"- **{issue}** (severity: {severity}, {mitigation_str})")
    return lines


def format_strengths_table(strengths):
    """Format key strengths as markdown table."""
    if not strengths:
        return ["No key strengths identified"]
    
    lines = [
        "| Category | Evidence | Relevance |",
        "|----------|----------|-----------|"
    ]
    for s in strengths:
        category = s.get("category", "Unknown")
        evidence = s.get("evidence", "N/A")
        relevance = s.get("relevance", "N/A")
        lines.append(f"| {category} | {evidence} | {relevance} |")
    return lines


def format_clarification_questions(clarification_q):
    if not clarification_q:
        return []
    lines = []
    for i, q in enumerate(clarification_q, 1):
        if isinstance(q, str):
            lines.append(f"{i}. {q}")
            continue
        if isinstance(q, dict):
            question = q.get("question") or "(missing question)"
            why = q.get("why_asking")
            deal_breaker = q.get("deal_breaker")
            suffix = []
            if why:
                suffix.append(f"why: {why}")
            if deal_breaker is True:
                suffix.append("deal-breaker")
            if suffix:
                lines.append(f"{i}. {question} ({'; '.join(suffix)})")
            else:
                lines.append(f"{i}. {question}")
            continue
        lines.append(f"{i}. {str(q)}")
    return lines


def get_next_steps(decision, confidence, has_clarification_questions):
    """Generate decision-specific next steps."""
    if decision == "STRONG_INTERVIEW":
        return [
            "✓ **Priority scheduling** — Move to immediate interview scheduling",
            "✓ Prepare for deep-dive conversation on relevant experience",
            "✓ Consider fast-tracking through interview process"
        ]
    elif decision == "INTERVIEW":
        if confidence == "high":
            return [
                "✓ **Standard interview** — Schedule within normal timeline",
                "✓ Assess fit through standard interview process",
                "✓ Focus on areas highlighted in Interview Focus section"
            ]
        else:
            return [
                "✓ **Standard interview** — Schedule within normal timeline",
                "✓ Pay close attention to concerns during interview",
                "✓ Probe interview focus areas carefully"
            ]
    elif decision == "MAYBE":
        if has_clarification_questions:
            return [
                "⚠ **Clarification required** — Send clarification questions before interview",
                "⚠ Wait for response before making final decision",
                "⚠ Review response against concerns listed above"
            ]
        else:
            return [
                "⚠ **Review needed** — Manual review of concerns before proceeding",
                "⚠ Assess whether concerns can be addressed in interview",
                "⚠ Consider whether to request additional information"
            ]
    elif decision == "PASS":
        return [
            "✗ **No interview** — Does not meet minimum requirements",
            "✗ Send polite rejection notice",
            "✗ File for future reference if requirements change"
        ]
    else:
        return ["Unknown decision type — manual review required"]


def generate_dossier_md(gestalt, quick_test, fields):
    """Generate human-readable dossier markdown."""
    lines = []
    
    # Header
    name = fields.get("name", "Unknown")
    lines.append(f"# Candidate Dossier: {name}")
    lines.append("")
    decision = gestalt.get("decision") or "UNKNOWN"
    confidence = gestalt.get("confidence") or "unknown"
    lines.append(f"**Decision:** {decision}")
    lines.append(f"**Confidence:** {confidence}")
    lines.append(f"**Date:** {gestalt.get('timestamp', datetime.now(UTC).isoformat())}")
    lines.append(f"**Quick Test:** {quick_test.get('status', 'unknown')}")
    lines.append("")
    
    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(gestalt.get("overall_narrative", "No narrative available"))
    lines.append("")
    
    # Key Strengths
    lines.append("## Key Strengths")
    lines.append("")
    lines.extend(format_strengths_table(gestalt.get("key_strengths", [])))
    lines.append("")
    
    # Concerns
    lines.append("## Concerns")
    lines.append("")
    lines.extend(format_concerns(gestalt.get("concerns", [])))
    lines.append("")
    
    # Elite Signals
    lines.append("## Elite Signals")
    lines.append("")
    lines.extend(format_elite_signals(gestalt.get("elite_signals", [])))
    lines.append("")
    
    # Business Impact
    lines.append("## Business Impact")
    lines.append("")
    lines.extend(format_business_impact(gestalt.get("business_impact", [])))
    lines.append("")
    
    # AI Detection
    ai_det = gestalt.get("ai_detection", {})
    lines.append("## AI Detection")
    lines.append("")
    lines.append(f"**Likelihood:** {ai_det.get('likelihood', 'unknown')}")
    lines.append(f"**Confidence:** {ai_det.get('confidence', 0):.2f}")
    if ai_det.get("flags"):
        lines.append(f"**Flags:** {', '.join(ai_det['flags'])}")
    else:
        lines.append("**Flags:** None")
    
    scores = ai_det.get("scores", {})
    if scores:
        lines.append("")
        lines.append("**Scores:**")
        lines.append(f"- Burstiness: {scores.get('burstiness', 0):.2f}")
        lines.append(f"- Generic phrases: {scores.get('generic_phrase_count', 0)}")
        lines.append(f"- Specificity: {scores.get('specificity', 0):.2f}")
    lines.append("")
    
    # Interview Focus
    interview_focus = gestalt.get("interview_focus")
    if interview_focus:
        lines.append("## Interview Focus")
        lines.append("")
        for focus in interview_focus:
            lines.append(f"- {focus}")
        lines.append("")
    
    # Clarification Questions
    clarification_q = gestalt.get("clarification_questions")
    if clarification_q:
        lines.append("## Clarification Questions")
        lines.append("")
        lines.append("*Send these questions to the candidate before scheduling interview:*")
        lines.append("")
        lines.extend(format_clarification_questions(clarification_q))
        lines.append("")
    
    # Next Steps
    lines.append("## Next Steps")
    lines.append("")
    has_clarification = bool(clarification_q)
    next_steps = get_next_steps(
        decision,
        confidence,
        has_clarification
    )
    lines.extend(next_steps)
    lines.append("")
    
    # Contact Info
    lines.append("---")
    lines.append("")
    lines.append("## Contact Information")
    lines.append("")
    lines.append(f"**Name:** {fields.get('name', 'N/A')}")
    lines.append(f"**Email:** {fields.get('email', 'N/A')}")
    lines.append(f"**Phone:** {fields.get('phone', 'N/A')}")
    lines.append("")
    
    return "\n".join(lines)


def generate_dossier_json(gestalt, quick_test, fields, candidate_id, job_id):
    """Generate machine-readable dossier JSON."""
    strengths = gestalt.get("key_strengths", [])
    concerns = gestalt.get("concerns", [])
    
    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "decision": gestalt.get("decision", "UNKNOWN"),
        "confidence": gestalt.get("confidence", "unknown"),
        "quick_test_status": quick_test.get("status", "unknown"),
        "gestalt_summary": gestalt.get("overall_narrative", ""),
        "top_3_strengths": [
            s.get("category", "Unknown") for s in strengths[:3]
        ],
        "top_3_concerns": [
            c.get("issue", "Unknown") for c in concerns[:3]
        ],
        "elite_signal_count": len(gestalt.get("elite_signals", [])),
        "business_impact_count": len(gestalt.get("business_impact", [])),
        "ai_detection_likelihood": gestalt.get("ai_detection", {}).get("likelihood", "unknown"),
        "has_clarification_questions": bool(gestalt.get("clarification_questions")),
        "recommended_action": get_next_steps(
            gestalt.get("decision", "UNKNOWN"),
            gestalt.get("confidence", "unknown"),
            bool(gestalt.get("clarification_questions"))
        )[0],
        "contact": {
            "name": fields.get("name", "N/A"),
            "email": fields.get("email", "N/A"),
            "phone": fields.get("phone", "N/A")
        },
        "timestamp": datetime.now(UTC).isoformat()
    }


def main():
    ap = argparse.ArgumentParser(description="Generate candidate dossier from gestalt evaluation")
    ap.add_argument("--job", required=True, help="Job ID")
    ap.add_argument("--candidate", required=True, help="Candidate ID")
    ap.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    cdir = root / "jobs" / args.job / "candidates" / args.candidate
    parsed = cdir / "parsed"
    outputs = cdir / "outputs"
    
    # Verify inputs exist
    gestalt_path = outputs / "gestalt_evaluation.json"
    quick_test_path = outputs / "quick_test.json"
    fields_path = parsed / "fields.json"
    
    if not gestalt_path.exists():
        logger.error(f"Missing gestalt_evaluation.json at {gestalt_path}")
        print(error_json("DOSSIER_MISSING_INPUT", "gestalt_evaluation.json not found", path=str(gestalt_path)))
        return 1
    
    if not quick_test_path.exists():
        logger.warning(f"Missing quick_test.json at {quick_test_path}, using defaults")
    
    if not fields_path.exists():
        logger.warning(f"Missing fields.json at {fields_path}, using defaults")
    
    # Read inputs
    gestalt = read_json(gestalt_path) or {}
    quick_test = read_json(quick_test_path) or {"status": "unknown", "reasons": []}
    fields = read_json(fields_path) or {"name": "Unknown", "email": "N/A", "phone": "N/A"}
    
    # Generate outputs
    logger.info(f"Generating dossier for {args.candidate} (decision: {gestalt.get('decision', 'UNKNOWN')})")
    
    dossier_md = generate_dossier_md(gestalt, quick_test, fields)
    dossier_json = generate_dossier_json(gestalt, quick_test, fields, args.candidate, args.job)
    
    if args.dry_run:
        logger.info("[DRY RUN] Would write:")
        logger.info(f"  - {outputs / 'dossier.md'}")
        logger.info(f"  - {outputs / 'dossier.json'}")
        logger.info("")
        logger.info("Preview of dossier.md:")
        logger.info("=" * 60)
        logger.info(dossier_md[:500] + "..." if len(dossier_md) > 500 else dossier_md)
        logger.info("=" * 60)
        return 0
    
    # Write outputs
    outputs.mkdir(parents=True, exist_ok=True)
    (outputs / "dossier.md").write_text(dossier_md, encoding="utf-8")
    (outputs / "dossier.json").write_text(json.dumps(dossier_json, indent=2), encoding="utf-8")
    
    logger.info(f"✓ Dossier written to {outputs}")
    logger.info(f"  - dossier.md ({len(dossier_md)} bytes)")
    logger.info(f"  - dossier.json ({len(json.dumps(dossier_json))} bytes)")
    
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(error_json("DOSSIER_CRASH", str(e)))
        exit(1)
