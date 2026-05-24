#!/usr/bin/env python3
"""Build prioritized, impact-per-effort action lists from scorecards."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

LOGGER = logging.getLogger("action_list_builder")

EFFORT_POINTS = {
    "low": 1.0,
    "slide rewrite": 1.0,
    "medium": 2.0,
    "additional evidence required": 3.5,
    "high": 3.5,
    "founder positioning shift": 5.0,
    "very high": 5.0,
}

SUBSTANCE_DEFAULT_WEIGHTS = {
    "founder_market_fit_team_capacity": 14,
    "non_obvious_insight_thesis_clarity": 12,
    "problem_urgency_icp_wedge": 12,
    "market_logic_venture_scale_path": 12,
    "why_now_timing_pressure": 8,
    "evidence_demand_learning_velocity": 14,
    "solution_product_clarity_proof": 10,
    "defensibility_compounding_advantage": 8,
    "competitive_landscape_differentiation": 7,
    "gtm_plausibility_first_distribution": 9,
    "business_model_economic_logic": 7,
    "ask_milestones_next_round": 8,
    "risk_honesty_derisking_plan": 7,
}

STYLE_DEFAULT_WEIGHTS = {
    "punch_density": 16,
    "specificity_quantification": 16,
    "voice_register_fit": 14,
    "claim_hygiene": 16,
    "hierarchy_scannability": 14,
    "anti_buzzword_discipline": 12,
    "narrative_cohesion": 12,
}

DIMENSION_LABELS = {
    **{key: key.replace("_", " ").title() for key in SUBSTANCE_DEFAULT_WEIGHTS},
    "punch_density": "Punch / Density",
    "specificity_quantification": "Specificity / Quantification",
    "voice_register_fit": "Voice + Register Fit",
    "claim_hygiene": "Claim Hygiene",
    "hierarchy_scannability": "Hierarchy + Scannability",
    "anti_buzzword_discipline": "Anti-Buzzword Discipline",
    "narrative_cohesion": "Narrative Cohesion",
}

SUBSTANCE_FIXES = {
    "founder_market_fit_team_capacity": "Add concrete founder-market-fit proof: relevant hard things done, access, and who owns the build/sales motion.",
    "non_obvious_insight_thesis_clarity": "Replace generic market trend language with the specific customer truth the company discovered.",
    "problem_urgency_icp_wedge": "Narrow the ICP and show why this problem is urgent now for that first wedge.",
    "market_logic_venture_scale_path": "Show bottom-up market logic from the first wedge to a venture-scale path without false precision.",
    "why_now_timing_pressure": "Name the external change that makes this newly possible or newly urgent.",
    "evidence_demand_learning_velocity": "Add demand evidence: interviews, pilots, LOIs, usage, paid tests, or repeated customer behavior.",
    "solution_product_clarity_proof": "Show what the product does in a user-visible workflow and what proof exists today.",
    "defensibility_compounding_advantage": "Explain what compounds as the company grows and why it is not easy to copy.",
    "competitive_landscape_differentiation": "Name real alternatives and the specific axis where this wedge wins.",
    "gtm_plausibility_first_distribution": "Identify the first distribution path, buyer, sales motion, and reason it can work at pre-seed scale.",
    "business_model_economic_logic": "Make pricing/economic assumptions explicit and connect them to observed willingness to pay or workflow value.",
    "ask_milestones_next_round": "Tie the ask to the milestones that reduce the most important next-round risks.",
    "risk_honesty_derisking_plan": "State the top risks plainly and map each to a near-term derisking plan.",
}

STYLE_FIXES = {
    "punch_density": "Rewrite the opening/core dense slides into claim headlines plus one proof point; move excess detail to appendix.",
    "specificity_quantification": "Replace adjectives and broad customer labels with numbers, concrete buyer/workflow nouns, or explicitly marked unknowns.",
    "voice_register_fit": "Choose one dominant register and align claim strength with the evidence shown.",
    "claim_hygiene": "Label each major claim as fact, belief, plan, or hypothesis and put proof/source/assumption markers nearby.",
    "hierarchy_scannability": "Turn section labels into claim headlines and make the deck work as a headline-only read.",
    "anti_buzzword_discipline": "Replace reusable startup phrases with plain product behavior: who does what, in which workflow, with what outcome.",
    "narrative_cohesion": "Make one through-line explicit: changed condition → customer pain → product wedge → proof → next milestone/ask.",
}


@dataclass(frozen=True)
class ActionItem:
    """Single prioritized deck repair action."""

    rank: int
    dimension_id: str
    dimension_label: str
    surface: str
    action: str
    impact: str
    impact_score: float
    effort: str
    effort_score: float
    impact_per_effort: float
    frames_helped: list[str]
    why_this_is_first: str
    evidence: list[dict[str, Any]]


def setup_logging(verbose: bool = False) -> None:
    """Configure timestamped logging."""

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ")
    logging.Formatter.converter = lambda *_: datetime.now(timezone.utc).timetuple()


def as_mapping(value: Any) -> Mapping[str, Any]:
    """Return a mapping or empty mapping."""

    return value if isinstance(value, Mapping) else {}


def as_list(value: Any) -> list[Any]:
    """Return a list or empty list."""

    return value if isinstance(value, list) else []


def numeric(value: Any, default: float = 0.0) -> float:
    """Parse float safely."""

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed != parsed:
        return default
    return parsed


def score_to_100(score: float) -> float:
    """Normalize 0-5 or 0-100-ish scores to 0-100."""

    return score * 20 if score <= 5 else score


def gap_from_anchor(score: float, anchor: float = 4.0) -> float:
    """Return score gap from target anchor in 0-5 scale."""

    score_5 = score if score <= 5 else score / 20
    return max(0.0, anchor - score_5)


def impact_label(value: float) -> str:
    """Human label for impact score."""

    if value >= 18:
        return "High"
    if value >= 9:
        return "Medium"
    return "Low"


def estimate_effort(surface: str, dimension_id: str, action_text: str) -> str:
    """Estimate effort type from dimension and suggested fix."""

    text = action_text.lower()
    if surface == "substantive":
        if dimension_id in {"founder_market_fit_team_capacity", "market_logic_venture_scale_path", "defensibility_compounding_advantage", "business_model_economic_logic"}:
            return "founder positioning shift" if dimension_id == "founder_market_fit_team_capacity" else "additional evidence required"
        if any(term in text for term in ["evidence", "pilot", "loi", "usage", "paid", "demand"]):
            return "additional evidence required"
        return "medium"
    if dimension_id in {"punch_density", "hierarchy_scannability", "anti_buzzword_discipline", "voice_register_fit"}:
        return "slide rewrite"
    if dimension_id in {"claim_hygiene", "specificity_quantification"} and "proof" in text:
        return "additional evidence required"
    return "medium"


def effort_score(effort: str) -> float:
    """Return effort denominator."""

    return EFFORT_POINTS.get(effort, 2.0)


def frames_for_dimension(dimension: Mapping[str, Any], frame_matrix: Mapping[str, Any] | None = None) -> list[str]:
    """Extract frames a dimension would shift."""

    if isinstance(dimension.get("frames_helped"), list):
        return [str(item) for item in dimension["frames_helped"]]
    if isinstance(dimension.get("frame_scores"), Mapping):
        weak = [frame for frame, score in dimension["frame_scores"].items() if score_to_100(numeric(score)) < 70]
        if weak:
            return sorted(str(frame) for frame in weak)
    if isinstance(dimension.get("frames"), list):
        return [str(item) for item in dimension["frames"]]
    if frame_matrix and isinstance(frame_matrix.get("dimension_frames"), Mapping):
        values = frame_matrix["dimension_frames"].get(dimension.get("dimension_id") or dimension.get("id"), [])
        if isinstance(values, list):
            return [str(value) for value in values]
    return ["F1", "F2", "F3", "F4"]


def iter_substantive_dimensions(scorecard: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Normalize D4.1-ish substantive scorecard shapes to dimension rows."""

    rows: list[dict[str, Any]] = []
    if isinstance(scorecard.get("dimensions"), list):
        rows.extend(row for row in scorecard["dimensions"] if isinstance(row, Mapping))
    if isinstance(scorecard.get("substantive_dimensions"), list):
        rows.extend(row for row in scorecard["substantive_dimensions"] if isinstance(row, Mapping))
    frames = as_mapping(scorecard.get("frames") or scorecard.get("frame_scorecards"))
    for frame_id, frame_payload in frames.items():
        frame_dims = as_mapping(frame_payload).get("dimensions", []) if isinstance(frame_payload, Mapping) else []
        for row in frame_dims if isinstance(frame_dims, list) else []:
            if isinstance(row, Mapping):
                new_row = dict(row)
                new_row.setdefault("frames_helped", [frame_id])
                rows.append(new_row)
    merged: dict[str, dict[str, Any]] = {}
    for row in rows:
        dimension_id = str(row.get("dimension_id") or row.get("id") or row.get("dimension") or "").strip()
        if not dimension_id:
            continue
        current = merged.setdefault(dimension_id, dict(row, frame_scores={}, frames_helped=[]))
        score = numeric(row.get("score", row.get("raw_score", row.get("value"))), default=numeric(current.get("score"), 0))
        if not current.get("score") or score < numeric(current.get("score"), 999):
            current.update(row)
            current["score"] = score
        for frame in as_list(row.get("frames_helped")):
            if frame not in current["frames_helped"]:
                current["frames_helped"].append(str(frame))
    return list(merged.values())


def iter_style_dimensions(scorecard: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Normalize stylistic scorecard dimensions."""

    return [dict(row) for row in as_list(scorecard.get("dimensions")) if isinstance(row, Mapping)]


def composite_score(scorecard: Mapping[str, Any], keys: Sequence[str]) -> float | None:
    """Extract a composite score from possible keys."""

    for key in keys:
        if key in scorecard:
            return score_to_100(numeric(scorecard[key]))
    return None


def style_substance_gap(substantive_scorecard: Mapping[str, Any], stylistic_scorecard: Mapping[str, Any]) -> dict[str, str] | None:
    """Detect D2.5 style/substance gap labels."""

    substance = composite_score(substantive_scorecard, ["substantive_score", "score", "composite", "overall_score"])
    style = composite_score(stylistic_scorecard, ["style_score", "stylistic_score", "score"])
    if substance is None or style is None:
        return None
    if style >= 75 and substance < 55:
        return {"label": "Strong style, weak substance", "note": "Polished copy may mask missing proof on first read; diligence will expose the gap."}
    if substance >= 75 and style < 55:
        return {"label": "Strong substance, weak style", "note": "Underlying claim may be fundable but is hard to parse; rewrite for investor comprehension."}
    if style >= 70 and substance < 50:
        return {"label": "Over-polished thinness", "note": "Copy carries unsupported claims; keep strong phrasing only where proof exists."}
    return None


def build_candidates(substantive_scorecard: Mapping[str, Any], stylistic_scorecard: Mapping[str, Any], frame_matrix: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Build candidate actions before ranking/deduplication."""

    candidates: list[dict[str, Any]] = []
    gap = style_substance_gap(substantive_scorecard, stylistic_scorecard)
    substance_composite = composite_score(substantive_scorecard, ["substantive_score", "score", "composite", "overall_score"])
    style_composite = composite_score(stylistic_scorecard, ["style_score", "stylistic_score", "score"])
    deprioritize_style = bool(gap and gap["label"] in {"Strong style, weak substance", "Over-polished thinness"})
    deprioritize_substance = bool(gap and gap["label"] == "Strong substance, weak style")

    for row in iter_substantive_dimensions(substantive_scorecard):
        dimension_id = str(row.get("dimension_id") or row.get("id") or row.get("dimension"))
        raw_score = numeric(row.get("score", row.get("raw_score", row.get("value"))), default=5)
        gap_points = gap_from_anchor(raw_score)
        if gap_points <= 0:
            continue
        weight = numeric(row.get("weight_effective", row.get("weight_default", row.get("weight"))), SUBSTANCE_DEFAULT_WEIGHTS.get(dimension_id, 8))
        action = str(row.get("top_fix") or row.get("suggested_fix") or SUBSTANCE_FIXES.get(dimension_id) or "Clarify the weakest substantive claim with proof, scope, and next milestone.")
        effort = estimate_effort("substantive", dimension_id, action)
        impact = weight * gap_points
        if deprioritize_substance:
            impact *= 0.85
        candidates.append({
            "dimension_id": dimension_id,
            "dimension_label": str(row.get("label") or DIMENSION_LABELS.get(dimension_id, dimension_id)),
            "surface": "substantive",
            "action": action,
            "impact_score": round(impact, 3),
            "effort": effort,
            "effort_score": effort_score(effort),
            "frames_helped": frames_for_dimension(row, frame_matrix),
            "evidence": as_list(row.get("evidence")),
            "reasoning": str(row.get("rationale") or row.get("reasoning") or "Low substantive score creates investor pass risk."),
        })

    for row in iter_style_dimensions(stylistic_scorecard):
        dimension_id = str(row.get("dimension_id") or row.get("id") or row.get("dimension"))
        raw_score = numeric(row.get("score", row.get("raw_score", row.get("value"))), default=5)
        gap_points = gap_from_anchor(raw_score)
        if gap_points <= 0:
            continue
        weight = numeric(row.get("weight_effective", row.get("weight_default", row.get("weight"))), STYLE_DEFAULT_WEIGHTS.get(dimension_id, 10))
        action = str(row.get("top_fix") or STYLE_FIXES.get(dimension_id) or "Rewrite the relevant slides so the claim is clearer and easier to evaluate.")
        effort = estimate_effort("style", dimension_id, action)
        impact = weight * gap_points
        if deprioritize_style:
            impact *= 0.55
        candidates.append({
            "dimension_id": dimension_id,
            "dimension_label": str(row.get("label") or DIMENSION_LABELS.get(dimension_id, dimension_id)),
            "surface": "style",
            "action": action,
            "impact_score": round(impact, 3),
            "effort": effort,
            "effort_score": effort_score(effort),
            "frames_helped": ["F2", "F3", "F4"] if dimension_id in {"punch_density", "hierarchy_scannability", "claim_hygiene"} else ["F1", "F2", "F3", "F4"],
            "evidence": as_list(row.get("evidence")),
            "reasoning": str(row.get("reasoning") or "Low style score reduces deck comprehension."),
        })

    if substance_composite is not None and style_composite is not None and gap:
        surface = "substantive" if style_composite > substance_composite else "style"
        candidates.append({
            "dimension_id": "style_substance_gap",
            "dimension_label": gap["label"],
            "surface": surface,
            "action": gap["note"],
            "impact_score": 22.0,
            "effort": "additional evidence required" if surface == "substantive" else "slide rewrite",
            "effort_score": 3.5 if surface == "substantive" else 1.0,
            "frames_helped": ["F2", "F3", "F4"],
            "evidence": [],
            "reasoning": "Style/substance split changes what repair should come first.",
        })

    return candidates


def dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate by dimension and normalized action phrase."""

    seen: set[tuple[str, str]] = set()
    output: list[dict[str, Any]] = []
    for item in candidates:
        normalized_action = re.sub(r"\W+", " ", item["action"].lower()).strip()[:80]
        key = (item["dimension_id"], normalized_action)
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def build_action_list(
    substantive_scorecard: Mapping[str, Any],
    stylistic_scorecard: Mapping[str, Any],
    frame_matrix_outputs: Mapping[str, Any] | None = None,
    top_n: int = 5,
) -> dict[str, Any]:
    """Return ranked, deduplicated action list.

    Ranking = impact (frame-weighted dimension weight × score gap from 4/5 anchor)
    divided by typed effort denominator. ``top_n`` is strictly enforced.
    """

    safe_top_n = max(0, int(top_n))
    candidates = dedupe_candidates(build_candidates(substantive_scorecard, stylistic_scorecard, frame_matrix_outputs or {}))
    for item in candidates:
        item["impact_per_effort"] = round(item["impact_score"] / max(0.1, item["effort_score"]), 3)
    ranked = sorted(candidates, key=lambda item: (-item["impact_per_effort"], -item["impact_score"], item["effort_score"], -len(item["frames_helped"])))[:safe_top_n]
    actions = []
    for index, item in enumerate(ranked, start=1):
        actions.append(asdict(ActionItem(
            rank=index,
            dimension_id=item["dimension_id"],
            dimension_label=item["dimension_label"],
            surface=item["surface"],
            action=item["action"],
            impact=impact_label(item["impact_score"]),
            impact_score=item["impact_score"],
            effort=item["effort"],
            effort_score=item["effort_score"],
            impact_per_effort=item["impact_per_effort"],
            frames_helped=sorted(set(item["frames_helped"])),
            why_this_is_first=item["reasoning"],
            evidence=item["evidence"],
        )))
    return {
        "top_n": safe_top_n,
        "actions": actions,
        "style_substance_gap": style_substance_gap(substantive_scorecard, stylistic_scorecard),
    }


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""

    parser = argparse.ArgumentParser(description="Build prioritized deck action list from scorecards.")
    parser.add_argument("--substantive", required=True, help="Substantive scorecard JSON")
    parser.add_argument("--stylistic", required=True, help="Stylistic scorecard JSON")
    parser.add_argument("--frame-matrix", help="Optional frame matrix JSON")
    parser.add_argument("--top-n", type=int, default=5, help="Maximum actions to emit")
    parser.add_argument("--out", help="Optional output JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without writing output")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def read_json(path: str) -> dict[str, Any]:
    """Read JSON object from path."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""

    args = build_arg_parser().parse_args(argv)
    setup_logging(args.verbose)
    try:
        substantive = read_json(args.substantive)
        stylistic = read_json(args.stylistic)
        frame_matrix = read_json(args.frame_matrix) if args.frame_matrix else {}
        result = build_action_list(substantive, stylistic, frame_matrix, top_n=args.top_n)
        if args.dry_run:
            print(json.dumps({"dry_run": True, "candidate_count": len(build_candidates(substantive, stylistic, frame_matrix)), "top_n": args.top_n}, indent=2))
            return 0
        output = json.dumps(result, indent=2)
        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output + "\n", encoding="utf-8")
            verify = json.loads(out_path.read_text(encoding="utf-8"))
            if len(verify.get("actions", [])) > args.top_n:
                raise RuntimeError(f"State verification failed: exceeded top_n in {out_path}")
            LOGGER.info("wrote %s", out_path)
        else:
            print(output)
        return 0
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        LOGGER.error("action list build failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
