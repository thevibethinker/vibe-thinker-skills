#!/usr/bin/env python3
"""Markdown and JSON renderer for pitch-deck-evaluator results."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger("pitch_deck_evaluator.output_renderer")


class RenderError(ValueError):
    """Raised when output rendering fails."""


def render_markdown(evaluation: dict[str, Any], config: dict[str, Any] | None = None, verbosity: str | None = None) -> str:
    """Render evaluation object to markdown per skill_design/OUTPUT_FORMAT.md."""
    config = config or evaluation.get("config", {}) or {}
    verbosity = verbosity or config.get("output_verbosity", "standard")
    deck_metadata = evaluation.get("deck_metadata", {})
    lines: list[str] = []
    lines.append(f"# Pitch Deck Evaluation — {deck_metadata.get('deck_name', 'Deck')}\n")
    lines.append("## Header\n")
    lines.append(f"- Evaluation date: {evaluation.get('evaluation_date', datetime.now(timezone.utc).date().isoformat())}")
    lines.append(f"- Stage: {config.get('stage', evaluation.get('stage', 'pre_seed'))}")
    lines.append(f"- Frames: {', '.join(config.get('enabled_frames', ['F1', 'F2', 'F3', 'F4']))}")
    lines.append(f"- POV palette: {', '.join(config.get('enabled_pov_palette', [])) or 'none'}")
    lines.append(f"- Verbosity: {verbosity}\n")
    lines.append("## Executive Read\n")
    lines.append(render_executive_read(evaluation))
    lines.append("\n## Score Snapshot\n")
    lines.extend(render_score_snapshot(evaluation))
    lines.append("\n## Frame Scorecards\n")
    for frame in evaluation.get("frame_scorecards", []):
        lines.extend(render_frame(frame, verbosity))
    lines.append("\n## Cross-Frame Synthesis\n")
    cross = evaluation.get("cross_frame_synthesis", {})
    lines.append(cross.get("summary", "No cross-frame synthesis available."))
    if cross.get("frame_scores"):
        lines.append(f"\n- Frame spread: {cross.get('spread', 0):.2f}")
        for frame_id, score in cross.get("frame_scores", {}).items():
            lines.append(f"- {frame_id}: {score}/5")
    lines.append("\n## Substantive vs. Stylistic Split\n")
    lines.append(render_style_substance_split(evaluation))
    pov_reads = evaluation.get("named_pov_reads", [])
    if pov_reads:
        lines.append("\n## Named-POV Reads\n")
        for read in pov_reads:
            lines.extend(render_pov_read(read))
    lines.append("\n## Per-Slide Annotations\n")
    lines.extend(render_slide_annotations(evaluation, verbosity))
    if config.get("include_action_list", True):
        lines.append("\n## Prioritized Action List\n")
        lines.extend(render_action_list(evaluation, verbosity))
    lines.append("\n## Appendix: Config Snapshot and Scoring Notes\n")
    lines.append("```json")
    lines.append(json.dumps(config, indent=2, sort_keys=True))
    lines.append("```")
    return "\n".join(lines).rstrip() + "\n"


def render_executive_read(evaluation: dict[str, Any]) -> str:
    """Render concise executive read."""
    substantive = evaluation.get("substantive_composite", 0)
    stylistic = evaluation.get("stylistic_composite")
    hard_gates = evaluation.get("hard_gates", [])
    sentence = f"Substantive composite: {substantive}/5."
    if stylistic is not None:
        sentence += f" Stylistic composite: {stylistic}/5."
    if hard_gates:
        sentence += f" {len(hard_gates)} hard-gate or credibility flags need review."
    else:
        sentence += " No hard-gate flags were detected by the current scorer."
    return sentence


def render_score_snapshot(evaluation: dict[str, Any]) -> list[str]:
    """Render score snapshot bullets."""
    lines = [f"- Substantive composite: **{evaluation.get('substantive_composite', 0)}/5**"]
    if evaluation.get("stylistic_composite") is not None:
        lines.append(f"- Stylistic composite: **{evaluation.get('stylistic_composite')}/5**")
    if evaluation.get("advisory_overall") is not None:
        lines.append(f"- Advisory overall: **{evaluation.get('advisory_overall')}/5**")
    for frame in evaluation.get("frame_scorecards", []):
        lines.append(f"- {frame['frame_id']} {frame.get('frame_name', '')}: **{frame.get('substantive_score', 0)}/5**")
    return lines


def render_frame(frame: dict[str, Any], verbosity: str) -> list[str]:
    """Render one frame scorecard."""
    lines = [f"### {frame['frame_id']} — {frame.get('frame_name', '')}", "", frame.get("frame_definition", ""), ""]
    lines.append(f"**Substantive score:** {frame.get('substantive_score', 0)}/5\n")
    limit = 5 if verbosity == "terse" else len(frame.get("dimension_scores", []))
    lines.append("| Dimension | Score | Evidence | Top fix |")
    lines.append("|---|---:|---|---|")
    for score in frame.get("dimension_scores", [])[:limit]:
        evidence_refs = ", ".join(item.get("slide_ref", "") for item in score.get("evidence", [])) or "none"
        lines.append(
            f"| {score.get('dimension_name', score.get('dimension_id'))} | {score.get('raw_score', 0)}/5 | {evidence_refs} | {escape_table(score.get('top_fix', ''))} |"
        )
    if verbosity == "deep":
        lines.append("\n**Rationale details**")
        for score in frame.get("dimension_scores", []):
            lines.append(f"- **{score.get('dimension_name')}**: {score.get('reasoning')}")
    lines.append("")
    return lines


def render_style_substance_split(evaluation: dict[str, Any]) -> str:
    """Render separate style/substance interpretation."""
    style = evaluation.get("stylistic_composite")
    substance = evaluation.get("substantive_composite", 0)
    if style is None:
        return "Stylistic scoring was not available in this run; substantive scoring is reported independently."
    gap = round(float(style) - float(substance), 2)
    if abs(gap) >= 1:
        return f"Style/substance gap: {gap:+.2f}. Treat this as a rewrite-priority signal, not a single overall verdict."
    return f"Style and substance are broadly aligned (gap {gap:+.2f})."


def render_pov_read(read: dict[str, Any]) -> list[str]:
    """Render one named POV read with required anti-cosplay disclaimer."""
    return [
        f"### {read.get('label', read.get('pov_id'))}",
        "",
        f"> {read.get('anti_cosplay_disclaimer', '')}",
        "",
        f"**POV score:** {read.get('score', 0)}/5",
        "",
        read.get("commentary", ""),
        "",
    ]


def render_slide_annotations(evaluation: dict[str, Any], verbosity: str) -> list[str]:
    """Render per-slide annotations from evidence refs."""
    annotations = evaluation.get("per_slide_annotations") or synthesize_slide_annotations(evaluation)
    if not annotations:
        return ["- No slide-level annotations available."]
    limit = 5 if verbosity == "terse" else len(annotations)
    return [f"- **{item['slide_ref']}**: {item['note']}" for item in annotations[:limit]]


def synthesize_slide_annotations(evaluation: dict[str, Any]) -> list[dict[str, str]]:
    """Create simple slide annotations from repeated evidence refs."""
    counts: dict[str, int] = {}
    for score in evaluation.get("substantive_dimensions", []):
        for evidence in score.get("evidence", []):
            ref = evidence.get("slide_ref", "unknown")
            counts[ref] = counts.get(ref, 0) + 1
    return [
        {"slide_ref": ref, "note": f"Referenced by {count} substantive scoring checks."}
        for ref, count in sorted(counts.items())
    ]


def render_action_list(evaluation: dict[str, Any], verbosity: str) -> list[str]:
    """Render ranked high-impact actions."""
    actions = evaluation.get("prioritized_action_list") or synthesize_actions(evaluation)
    if not actions:
        return ["- No actions generated."]
    limit = 3 if verbosity == "terse" else 8 if verbosity == "deep" else 5
    return [f"{idx}. {action}" for idx, action in enumerate(actions[:limit], start=1)]


def synthesize_actions(evaluation: dict[str, Any]) -> list[str]:
    """Collect lowest-score top fixes into a de-duplicated action list."""
    seen: set[str] = set()
    actions: list[str] = []
    scores = sorted(evaluation.get("substantive_dimensions", []), key=lambda score: score.get("raw_score", 5))
    for score in scores:
        fix = score.get("top_fix")
        if fix and fix not in seen:
            seen.add(fix)
            actions.append(fix)
    return actions


def render_json(evaluation: dict[str, Any]) -> str:
    """Render JSON companion output."""
    return json.dumps(evaluation, indent=2, sort_keys=True) + "\n"


def write_outputs(evaluation: dict[str, Any], out_path: str | Path, config: dict[str, Any] | None = None, *, emit_json: bool = False) -> list[Path]:
    """Write markdown and optional JSON outputs, then verify writes."""
    target = Path(out_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(evaluation, config), encoding="utf-8")
    outputs = [target]
    if emit_json:
        json_path = target.with_suffix(".json")
        json_path.write_text(render_json(evaluation), encoding="utf-8")
        outputs.append(json_path)
    for output in outputs:
        if not output.exists() or output.stat().st_size == 0:
            raise RenderError(f"Failed to verify output write: {output}")
    return outputs


def escape_table(value: str) -> str:
    """Escape markdown table pipes."""
    return value.replace("|", "\\|").replace("\n", " ")


def main(argv: list[str] | None = None) -> int:
    """CLI for rendering evaluation JSON."""
    parser = argparse.ArgumentParser(description="Render pitch deck evaluation output.")
    parser.add_argument("evaluation_json")
    parser.add_argument("--out", required=True)
    parser.add_argument("--emit-json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        evaluation = json.loads(Path(args.evaluation_json).read_text(encoding="utf-8"))
        markdown = render_markdown(evaluation, evaluation.get("config", {}))
        if args.dry_run:
            print(json.dumps({"markdown_chars": len(markdown), "frames": len(evaluation.get("frame_scorecards", []))}, indent=2))
        else:
            outputs = write_outputs(evaluation, args.out, evaluation.get("config", {}), emit_json=args.emit_json)
            for output in outputs:
                print(str(output))
        return 0
    except (OSError, json.JSONDecodeError, RenderError) as exc:
        LOGGER.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
