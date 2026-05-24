#!/usr/bin/env python3
"""Frame-wise substantive scoring for pitch-deck-evaluator."""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

try:
    from rubric_loader import load_rubric
except ImportError:  # pragma: no cover
    from .rubric_loader import load_rubric

LOGGER = logging.getLogger("pitch_deck_evaluator.frame_scorer")

FRAME_DEFINITIONS = {
    "F1": "Warm Believer: relationship/thesis-aligned reader wanting a reason to say yes.",
    "F2": "Curious Skeptic: open institutional read that wants proof, sequence, and founder logic.",
    "F3": "Cold Partner Read: no-context scan; the deck must earn attention quickly.",
    "F4": "Hostile Diligence: adversarial pressure test for unsupported claims and contradictions.",
}

DIMENSION_KEYWORDS = {
    "founder_market_fit_team_capacity": ["founder", "team", "advisor", "experience", "built", "domain", "designer", "engineer"],
    "non_obvious_insight_thesis_clarity": ["insight", "belief", "thesis", "unique", "trend", "because", "why", "discovered"],
    "problem_urgency_icp_wedge": ["problem", "pain", "customer", "user", "local", "hotel", "expensive", "disconnected", "need"],
    "market_logic_venture_scale_path": ["market", "tam", "sam", "billion", "million", "available", "trips", "size", "scale"],
    "why_now_timing_pressure": ["now", "timing", "trend", "inflection", "event", "launch", "change", "growing"],
    "evidence_demand_learning_velocity": ["traction", "validation", "customers", "users", "waitlist", "revenue", "testimonial", "press", "growth"],
    "solution_product_clarity_proof": ["solution", "product", "platform", "search", "book", "profiles", "screenshot", "demo", "mvp"],
    "defensibility_compounding_advantage": ["moat", "advantage", "network", "data", "brand", "first", "proprietary", "compounding"],
    "competitive_landscape_differentiation": ["competition", "competitor", "craigslist", "couchsurfing", "alternative", "differentiation", "versus"],
    "gtm_plausibility_first_distribution": ["go-to-market", "gtm", "adoption", "channel", "partnership", "events", "craigslist", "distribution"],
    "business_model_economic_logic": ["business model", "revenue", "commission", "fee", "pricing", "margin", "take", "transaction"],
    "ask_milestones_next_round": ["ask", "raise", "funding", "runway", "milestone", "use of funds", "round", "seed"],
    "risk_honesty_derisking_plan": ["risk", "unknown", "assumption", "test", "prove", "learn", "de-risk", "milestone"],
}

FALSE_PRECISION_PATTERNS = [r"\b\d+(?:\.\d+)?%\b", r"\$\d+(?:\.\d+)?\s*(?:b|bn|m|mm|million|billion)\b", r"\bCAC\b", r"\bLTV\b"]
TRUST_RISK_WORDS = ["guaranteed", "no competitors", "monopoly", "everyone", "all users", "will definitely"]


class ScoringError(ValueError):
    """Raised when frame scoring cannot proceed."""


class LLMClient(Protocol):
    """Protocol for model-backed dimension scoring."""

    def score_dimension(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Return a dimension score object."""


@dataclass(frozen=True)
class AnthropicLLMClient:
    """Minimal Anthropic Messages API adapter for standalone LLM scoring."""

    model: str = "claude-sonnet-4-6"
    api_key_env: str = "ANTHROPIC_API_KEY"
    timeout_seconds: int = 90

    def score_dimension(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Call Anthropic and parse a rubric-constrained JSON score."""
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise ScoringError(f"{self.api_key_env} is required for anthropic scoring backend.")
        payload = {
            "model": self.model,
            "max_tokens": 900,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                    + "\n\nReturn ONLY JSON with keys: raw_score (0-5 number), reasoning (one paragraph), evidence (array of {slide_ref, excerpt, evidence_type}), stage_findings (array of {type, code}), top_fix, confidence.",
                }
            ],
        }
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:500]
            raise ScoringError(f"Anthropic scoring HTTP error {exc.code}: {body}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ScoringError(f"Anthropic scoring request failed: {exc}") from exc
        text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        try:
            parsed = json.loads(extract_json_object(text))
        except json.JSONDecodeError as exc:
            raise ScoringError(f"Anthropic scoring returned invalid JSON for {context['dimension']['id']} {context['frame_id']}: {text[:300]}") from exc
        return normalize_model_score(parsed)


@dataclass(frozen=True)
class HeuristicLLMClient:
    """Deterministic local scorer used for CI, smoke tests, and no-key standalone runs."""

    def score_dimension(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Score using extracted evidence density and stage rules."""
        slides = context["slides"]
        dimension = context["dimension"]
        frame_id = context["frame_id"]
        stage = context["stage"]
        keywords = DIMENSION_KEYWORDS.get(dimension["id"], [])
        evidence = find_evidence(slides, keywords, limit=3)
        deck_text = "\n".join(slide.get("text", "") for slide in slides).lower()
        raw_score = evidence_score(evidence, deck_text, dimension["id"], frame_id)
        stage_findings = apply_stage_discipline(dimension["id"], deck_text, evidence, stage)
        raw_score = apply_stage_caps(raw_score, dimension["id"], stage_findings)
        rationale = render_rationale(dimension, frame_id, raw_score, evidence, stage_findings)
        top_fix = suggest_fix(dimension["id"], stage_findings, bool(evidence))
        return {
            "raw_score": raw_score,
            "reasoning": rationale,
            "evidence": evidence,
            "stage_findings": stage_findings,
            "top_fix": top_fix,
            "confidence": "medium" if evidence else "low",
            "prompt_preview": prompt[:500],
        }


def score_frames(
    slides: list[dict[str, Any]],
    rubric: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    llm_client: LLMClient | None = None,
) -> dict[str, Any]:
    """Score every enabled frame and substantive dimension."""
    if not slides:
        raise ScoringError("No slides supplied for scoring.")
    rubric = rubric or load_rubric(refresh=True)
    config = config or {}
    enabled_frames = config.get("enabled_frames") or [frame["id"] for frame in rubric["frames"]]
    dimensions = rubric["dimensions"]
    client = llm_client or client_for_config(config)
    stage = config.get("stage", "pre_seed")
    overrides = config.get("substantive_weight_overrides", {}) or {}
    frame_scorecards: list[dict[str, Any]] = []
    all_dimension_scores: list[dict[str, Any]] = []

    for frame_id in enabled_frames:
        if frame_id not in FRAME_DEFINITIONS:
            raise ScoringError(f"Unknown frame ID: {frame_id}")
        dimension_scores: list[dict[str, Any]] = []
        for dimension in dimensions:
            frame_cell = rubric["frame_matrix"].get(dimension["id"], {}).get(frame_id, {"modifier": 1.0, "note": ""})
            config_modifier = float(overrides.get(dimension["id"], 1.0))
            weight_effective = float(dimension["weight"]) * float(frame_cell.get("modifier", 1.0)) * config_modifier
            prompt = build_dimension_prompt(slides, dimension, frame_id, stage, frame_cell)
            scored = client.score_dimension(prompt, {"slides": slides, "dimension": dimension, "frame_id": frame_id, "stage": stage})
            raw_score = clamp_score(scored["raw_score"])
            weighted_points = raw_score * weight_effective
            score_obj = {
                "dimension_id": dimension["id"],
                "dimension_name": dimension["name"],
                "frame_id": frame_id,
                "raw_score": raw_score,
                "weight_default": float(dimension["weight"]),
                "frame_modifier": float(frame_cell.get("modifier", 1.0)),
                "config_modifier": config_modifier,
                "weight_effective": round(weight_effective, 4),
                "weighted_points": round(weighted_points, 4),
                "reasoning": scored["reasoning"],
                "evidence": scored["evidence"],
                "stage_findings": scored["stage_findings"],
                "top_fix": scored["top_fix"],
                "confidence": scored["confidence"],
            }
            dimension_scores.append(score_obj)
            all_dimension_scores.append(score_obj)
        composite = weighted_average(dimension_scores)
        frame_scorecards.append(
            {
                "frame_id": frame_id,
                "frame_name": FRAME_DEFINITIONS[frame_id].split(":", 1)[0],
                "frame_definition": FRAME_DEFINITIONS[frame_id],
                "substantive_score": composite,
                "dimension_scores": dimension_scores,
            }
        )

    return {
        "stage": stage,
        "frame_scorecards": frame_scorecards,
        "substantive_dimensions": all_dimension_scores,
        "substantive_composite": weighted_average(all_dimension_scores),
        "hard_gates": collect_hard_gates(all_dimension_scores),
        "cross_frame_synthesis": synthesize_cross_frame(frame_scorecards),
    }



def client_for_config(config: dict[str, Any]) -> LLMClient:
    """Select the scoring backend without making tests pay for model calls."""
    backend = str(config.get("scoring_backend", "heuristic")).lower()
    model = str(config.get("model", "claude-sonnet-4-6"))
    if backend in {"anthropic", "claude"}:
        return AnthropicLLMClient(model=model)
    if backend == "auto":
        LOGGER.info("scoring_backend=auto resolves to deterministic heuristic backend; use anthropic explicitly for model scoring.")
    return HeuristicLLMClient()


def extract_json_object(text: str) -> str:
    """Extract the first JSON object from model text."""
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("no JSON object found", text, 0)
    return stripped[start : end + 1]


def normalize_model_score(parsed: dict[str, Any]) -> dict[str, Any]:
    """Normalize model JSON into the scorer's expected shape."""
    return {
        "raw_score": clamp_score(float(parsed.get("raw_score", 0))),
        "reasoning": str(parsed.get("reasoning", "")),
        "evidence": parsed.get("evidence", []) if isinstance(parsed.get("evidence", []), list) else [],
        "stage_findings": parsed.get("stage_findings", []) if isinstance(parsed.get("stage_findings", []), list) else [],
        "top_fix": str(parsed.get("top_fix", "Add clearer evidence for this dimension.")),
        "confidence": str(parsed.get("confidence", "medium")),
    }

def build_dimension_prompt(slides: list[dict[str, Any]], dimension: dict[str, Any], frame_id: str, stage: str, frame_cell: dict[str, Any]) -> str:
    """Build the prompt that a real LLM adapter would receive."""
    slide_text = "\n\n".join(f"Slide {slide.get('slide_num')}: {slide.get('text', '')}" for slide in slides)
    questions = "\n".join(f"- {question}" for question in dimension.get("prompt_questions", []))
    return (
        f"Evaluate a {stage} pitch deck through {FRAME_DEFINITIONS[frame_id]}.\n"
        f"Dimension: {dimension['name']} ({dimension['id']})\n"
        f"Definition: {dimension.get('definition', '')}\n"
        f"Frame note: {frame_cell.get('note', '')}\n"
        f"Questions:\n{questions}\n\nDeck slides:\n{slide_text}\n\n"
        "Return score 0-5, one-paragraph reasoning, and evidence slide refs."
    )


def find_evidence(slides: list[dict[str, Any]], keywords: list[str], limit: int = 3) -> list[dict[str, str]]:
    """Find simple keyword evidence snippets by slide."""
    evidence: list[dict[str, str]] = []
    for slide in slides:
        text = re.sub(r"\s+", " ", slide.get("text", "")).strip()
        lower = text.lower()
        matched = [keyword for keyword in keywords if keyword.lower() in lower]
        if matched:
            excerpt = text[:260] + ("…" if len(text) > 260 else "")
            evidence.append(
                {
                    "slide_ref": slide.get("slide_ref", f"slide_{int(slide.get('slide_num', 0)):02d}"),
                    "excerpt": excerpt,
                    "evidence_type": "keyword_match",
                    "matched_terms": ", ".join(matched[:5]),
                }
            )
        if len(evidence) >= limit:
            break
    return evidence


def evidence_score(evidence: list[dict[str, str]], deck_text: str, dimension_id: str, frame_id: str) -> float:
    """Convert evidence density to a conservative 0-5 score."""
    if not evidence:
        base = 1.0
    elif len(evidence) == 1:
        base = 2.5
    elif len(evidence) == 2:
        base = 3.25
    else:
        base = 3.75
    if any(re.search(pattern, deck_text, flags=re.I) for pattern in FALSE_PRECISION_PATTERNS):
        if dimension_id in {"market_logic_venture_scale_path", "business_model_economic_logic", "evidence_demand_learning_velocity"}:
            base += 0.3
    if any(word in deck_text for word in TRUST_RISK_WORDS):
        base -= 0.4 if frame_id in {"F3", "F4"} else 0.2
    if frame_id == "F1":
        base += 0.15
    if frame_id == "F4":
        base -= 0.2
    return clamp_score(base)


def apply_stage_discipline(dimension_id: str, deck_text: str, evidence: list[dict[str, str]], stage: str) -> list[dict[str, str]]:
    """Classify stage-related absences and overclaims before score caps."""
    findings: list[dict[str, str]] = []
    if stage != "pre_seed":
        if evidence:
            findings.append({"type": "stage_appropriate_evidence", "code": f"{stage}_evidence_present"})
        return findings
    if dimension_id == "evidence_demand_learning_velocity":
        if not any(term in deck_text for term in ["revenue", "arr", "mrr"]):
            findings.append({"type": "granted_at_pre_seed", "code": "revenue_scale_absent"})
        if not evidence:
            findings.append({"type": "missing_pre_seed_proof", "code": "no_non_revenue_validation"})
    if dimension_id == "founder_market_fit_team_capacity" and not evidence:
        findings.append({"type": "inverse_trap", "code": "missing_why_this_founder"})
    if dimension_id == "non_obvious_insight_thesis_clarity" and not evidence:
        findings.append({"type": "inverse_trap", "code": "missing_insight_slide"})
    if dimension_id == "market_logic_venture_scale_path":
        if "1%" in deck_text or "capture" in deck_text and "market" in deck_text:
            findings.append({"type": "false_precision", "code": "top_down_market_capture_risk"})
        if not evidence:
            findings.append({"type": "missing_pre_seed_proof", "code": "no_bottom_up_market_logic"})
    if dimension_id == "business_model_economic_logic":
        if not any(term in deck_text for term in ["cac", "ltv", "payback"]):
            findings.append({"type": "granted_at_pre_seed", "code": "unit_economics_absent"})
        if not evidence:
            findings.append({"type": "missing_pre_seed_proof", "code": "missing_who_pays_why_pay"})
    if dimension_id == "ask_milestones_next_round" and not evidence:
        findings.append({"type": "missing_pre_seed_proof", "code": "vague_or_missing_ask"})
    if any(term in deck_text for term in TRUST_RISK_WORDS):
        findings.append({"type": "credibility_risk", "code": "unsupported_absolute_claim"})
    if evidence and not findings:
        findings.append({"type": "stage_appropriate_evidence", "code": "scorable_pre_seed_evidence"})
    return findings


def apply_stage_caps(raw_score: float, dimension_id: str, findings: list[dict[str, str]]) -> float:
    """Apply D2.4-inspired caps for missing pre-seed-native evidence."""
    codes = {finding["code"] for finding in findings}
    if dimension_id == "founder_market_fit_team_capacity" and "missing_why_this_founder" in codes:
        raw_score = min(raw_score, 2.0)
    if dimension_id == "non_obvious_insight_thesis_clarity" and "missing_insight_slide" in codes:
        raw_score = min(raw_score, 2.0)
    if dimension_id == "market_logic_venture_scale_path" and "top_down_market_capture_risk" in codes:
        raw_score = min(raw_score, 2.5)
    if dimension_id == "evidence_demand_learning_velocity" and "no_non_revenue_validation" in codes:
        raw_score = min(raw_score, 2.0)
    if dimension_id == "ask_milestones_next_round" and "vague_or_missing_ask" in codes:
        raw_score = min(raw_score, 2.0)
    if any(finding["type"] == "credibility_risk" for finding in findings):
        raw_score = min(raw_score, 2.5)
    return clamp_score(raw_score)


def render_rationale(dimension: dict[str, Any], frame_id: str, score: float, evidence: list[dict[str, str]], findings: list[dict[str, str]]) -> str:
    """Render a one-paragraph rationale."""
    if evidence:
        refs = ", ".join(item["slide_ref"] for item in evidence)
        evidence_text = f"Evidence appears on {refs}."
    else:
        evidence_text = "The deck does not provide obvious extracted evidence for this dimension."
    finding_text = "; ".join(f"{item['type']}:{item['code']}" for item in findings) or "no stage flags"
    return f"{dimension['name']} scores {score:.1f}/5 in {frame_id}. {evidence_text} Stage handling: {finding_text}."


def suggest_fix(dimension_id: str, findings: list[dict[str, str]], has_evidence: bool) -> str:
    """Suggest a highest-impact repair."""
    codes = {finding["code"] for finding in findings}
    if "missing_why_this_founder" in codes:
        return "Add a concise why-this-founder/team capacity proof slide or tighten the team slide around domain access and builder ownership."
    if "missing_insight_slide" in codes:
        return "State the non-obvious insight in one retellable sentence and connect it to timing and wedge."
    if "no_non_revenue_validation" in codes:
        return "Add non-revenue validation: customer discovery, design partners, pilot pipeline, testimonials, or prototype usage."
    if "top_down_market_capture_risk" in codes:
        return "Replace top-down market capture with bottom-up wedge sizing and adoption assumptions."
    if "vague_or_missing_ask" in codes:
        return "Map the round ask to runway, milestones, and the next financing proof point."
    if not has_evidence:
        return f"Add explicit slide evidence for {dimension_id.replace('_', ' ')}."
    return "Make the evidence more concrete, earlier, and easier to quote in a partner memo."


def weighted_average(scores: list[dict[str, Any]]) -> float:
    """Return weighted average score out of 5."""
    denominator = sum(float(score.get("weight_effective", 0)) for score in scores)
    if denominator <= 0:
        return 0.0
    numerator = sum(float(score.get("raw_score", 0)) * float(score.get("weight_effective", 0)) for score in scores)
    return round(numerator / denominator, 2)


def collect_hard_gates(scores: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Collect credibility risks and very low scores."""
    gates: list[dict[str, str]] = []
    for score in scores:
        for finding in score.get("stage_findings", []):
            if finding.get("type") == "credibility_risk":
                gates.append({"frame_id": score["frame_id"], "dimension_id": score["dimension_id"], "code": finding["code"]})
        if score.get("raw_score", 0) <= 1.0:
            gates.append({"frame_id": score["frame_id"], "dimension_id": score["dimension_id"], "code": "very_low_dimension_score"})
    return gates


def synthesize_cross_frame(frame_scorecards: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize agreement and divergence across frames."""
    frame_scores = {card["frame_id"]: card["substantive_score"] for card in frame_scorecards}
    values = list(frame_scores.values())
    spread = round(max(values) - min(values), 2) if values else 0.0
    if spread >= 1.0:
        summary = "The deck is frame-sensitive: warm reads and hostile reads diverge meaningfully."
    elif values and min(values) >= 3.5:
        summary = "The deck holds up consistently across frames."
    else:
        summary = "The deck has consistent weaknesses across frames."
    return {"frame_scores": frame_scores, "spread": spread, "summary": summary}


def clamp_score(value: float) -> float:
    """Clamp score to the 0-5 half-point rubric scale."""
    return max(0.0, min(5.0, round(value * 2) / 2))


def main(argv: list[str] | None = None) -> int:
    """CLI for scoring pre-extracted slides JSON."""
    parser = argparse.ArgumentParser(description="Score slides across investor frames.")
    parser.add_argument("slides_json", help="Path to deck_reader JSON output")
    parser.add_argument("--rubric", help="Path to rubric_v1.md")
    parser.add_argument("--out", help="Output JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Validate scoring without writing")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        slides = json.loads(Path(args.slides_json).read_text(encoding="utf-8"))
        rubric = load_rubric(args.rubric, refresh=True) if args.rubric else load_rubric(refresh=True)
        result = score_frames(slides, rubric, {})
        if args.dry_run:
            print(json.dumps({"frames": len(result["frame_scorecards"]), "composite": result["substantive_composite"]}, indent=2))
        elif args.out:
            out_path = Path(args.out).expanduser().resolve()
            out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(str(out_path))
        else:
            print(json.dumps(result, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ScoringError) as exc:
        LOGGER.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
