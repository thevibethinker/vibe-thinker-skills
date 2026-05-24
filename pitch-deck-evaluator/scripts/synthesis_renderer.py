#!/usr/bin/env python3
"""Render cross-frame synthesis and style/substance gap callouts."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from action_list_builder import style_substance_gap
except ImportError:  # pragma: no cover
    from .action_list_builder import style_substance_gap

LOGGER = logging.getLogger("synthesis_renderer")
FRAME_LABELS = {
    "F1": "Warm Believer",
    "F2": "Curious Skeptic",
    "F3": "Cold Partner Read",
    "F4": "Hostile Diligence",
}


def setup_logging(verbose: bool = False) -> None:
    """Configure timestamped logging."""

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ")
    logging.Formatter.converter = lambda *_: datetime.now(timezone.utc).timetuple()


def numeric(value: Any, default: float = 0.0) -> float:
    """Parse float safely."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_score(value: Any) -> float:
    """Normalize scores to 0-5."""

    score = numeric(value)
    return score / 20 if score > 5 else score


def extract_dimension_frames(frame_outputs: Mapping[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    """Normalize frame scorecards into dimension -> frame -> score/rationale."""

    matrix: dict[str, dict[str, dict[str, Any]]] = {}
    frames = frame_outputs.get("frames") if isinstance(frame_outputs.get("frames"), Mapping) else frame_outputs
    if not isinstance(frames, Mapping):
        return matrix
    for frame_id, frame_payload in frames.items():
        if not isinstance(frame_payload, Mapping):
            continue
        dimensions = frame_payload.get("dimensions") or frame_payload.get("substantive_dimensions") or []
        if isinstance(dimensions, Mapping):
            dimensions = [{"dimension_id": key, **(value if isinstance(value, Mapping) else {"score": value})} for key, value in dimensions.items()]
        if not isinstance(dimensions, list):
            continue
        for row in dimensions:
            if not isinstance(row, Mapping):
                continue
            dimension_id = str(row.get("dimension_id") or row.get("id") or row.get("dimension") or "").strip()
            if not dimension_id:
                continue
            matrix.setdefault(dimension_id, {})[str(frame_id)] = {
                "score": normalize_score(row.get("score", row.get("raw_score", row.get("value")))),
                "rationale": str(row.get("rationale") or row.get("reasoning") or row.get("top_fix") or ""),
                "label": str(row.get("label") or dimension_id.replace("_", " ").title()),
            }
    return matrix


def frame_phrase(frame_id: str) -> str:
    """Return frame label phrase."""

    return f"{frame_id} {FRAME_LABELS.get(frame_id, '').strip()}".strip()


def render_agreement(dimension_id: str, label: str, frame_values: Mapping[str, Mapping[str, Any]]) -> str:
    """Render a concise convergence line."""

    scores = [numeric(value.get("score")) for value in frame_values.values()]
    avg = sum(scores) / max(1, len(scores))
    if avg >= 3.5:
        stance = "generally grants this dimension"
    elif avg >= 2.5:
        stance = "lands in a mixed middle"
    else:
        stance = "generally sees this as weak"
    frames = ", ".join(sorted(frame_values.keys()))
    return f"- **{label}:** {frames} {stance} (avg {avg:.1f}/5)."


def render_divergence(dimension_id: str, label: str, frame_values: Mapping[str, Mapping[str, Any]], threshold: float = 1.5) -> str | None:
    """Render actionable divergence when frame spread crosses threshold."""

    if len(frame_values) < 2:
        return None
    ordered = sorted(frame_values.items(), key=lambda item: numeric(item[1].get("score")))
    low_frame, low_payload = ordered[0]
    high_frame, high_payload = ordered[-1]
    spread = numeric(high_payload.get("score")) - numeric(low_payload.get("score"))
    if spread < threshold:
        return None
    high_reason = high_payload.get("rationale") or "grants the claim"
    low_reason = low_payload.get("rationale") or "does not see enough evidence"
    return (
        f"- **{label}:** {frame_phrase(high_frame)} grants more than {frame_phrase(low_frame)} "
        f"({numeric(high_payload.get('score')):.1f} vs {numeric(low_payload.get('score')):.1f}). "
        f"Actionable signal: make the evidence that {high_frame} is granting explicit enough for {low_frame}. "
        f"High-frame read: {high_reason} Low-frame pressure: {low_reason}"
    )


def render_style_substance_gap(substantive_scorecard: Mapping[str, Any], stylistic_scorecard: Mapping[str, Any]) -> str:
    """Render D2.5 style/substance gap callout if triggered."""

    gap = style_substance_gap(substantive_scorecard, stylistic_scorecard)
    if not gap:
        return "**Style/substance gap:** No major gap label triggered. Keep style and substance separate in interpretation."
    return f"**Style/substance gap — {gap['label']}:** {gap['note']}"


def render_cross_frame_synthesis(
    frame_matrix_outputs: Mapping[str, Any],
    substantive_scorecard: Mapping[str, Any] | None = None,
    stylistic_scorecard: Mapping[str, Any] | None = None,
    divergence_threshold: float = 1.5,
) -> str:
    """Render the cross-frame synthesis markdown block.

    Divergence lines are emphasized; convergent dimensions are summarized briefly.
    """

    dimensions = extract_dimension_frames(frame_matrix_outputs)
    lines = ["## Cross-Frame Synthesis", "", "### Where frames agree"]
    convergence_lines: list[str] = []
    divergence_lines: list[str] = []
    for dimension_id, frame_values in sorted(dimensions.items()):
        label = next((str(value.get("label")) for value in frame_values.values() if value.get("label")), dimension_id.replace("_", " ").title())
        divergence = render_divergence(dimension_id, label, frame_values, threshold=divergence_threshold)
        if divergence:
            divergence_lines.append(divergence)
        else:
            convergence_lines.append(render_agreement(dimension_id, label, frame_values))
    if convergence_lines:
        lines.extend(convergence_lines[:8])
        if len(convergence_lines) > 8:
            lines.append(f"- {len(convergence_lines) - 8} additional dimensions are convergent and less action-informative.")
    else:
        lines.append("- No convergent dimensions detected from the provided frame matrix.")
    lines.extend(["", "### Where frames diverge", ""])
    if divergence_lines:
        lines.extend(divergence_lines)
    else:
        lines.append("- No dimension diverges by ≥1.5 score points across enabled frames; prioritize the lowest convergent dimensions.")
    if substantive_scorecard is not None and stylistic_scorecard is not None:
        lines.extend(["", "### Style/Substance Gap", "", render_style_substance_gap(substantive_scorecard, stylistic_scorecard)])
    return "\n".join(lines).strip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""

    parser = argparse.ArgumentParser(description="Render cross-frame synthesis markdown.")
    parser.add_argument("--frames", required=True, help="Frame outputs JSON")
    parser.add_argument("--substantive", help="Optional substantive scorecard JSON for gap callout")
    parser.add_argument("--stylistic", help="Optional stylistic scorecard JSON for gap callout")
    parser.add_argument("--threshold", type=float, default=1.5, help="Divergence threshold in 0-5 score points")
    parser.add_argument("--out", help="Optional markdown output path")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without writing output")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def read_json(path: str | None) -> dict[str, Any] | None:
    """Read optional JSON object."""

    if not path:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""

    args = build_arg_parser().parse_args(argv)
    setup_logging(args.verbose)
    try:
        frames = read_json(args.frames) or {}
        substantive = read_json(args.substantive)
        stylistic = read_json(args.stylistic)
        rendered = render_cross_frame_synthesis(frames, substantive, stylistic, args.threshold)
        if args.dry_run:
            print(json.dumps({"dry_run": True, "dimension_count": len(extract_dimension_frames(frames)), "chars": len(rendered)}, indent=2))
            return 0
        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")
            if "## Cross-Frame Synthesis" not in out_path.read_text(encoding="utf-8"):
                raise RuntimeError(f"State verification failed for {out_path}")
            LOGGER.info("wrote %s", out_path)
        else:
            print(rendered)
        return 0
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        LOGGER.error("synthesis rendering failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
