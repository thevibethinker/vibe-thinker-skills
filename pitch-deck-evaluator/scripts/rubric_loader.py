#!/usr/bin/env python3
"""Rubric markdown parser and JSON cache generator."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger("pitch_deck_evaluator.rubric_loader")
DEFAULT_FRAMES = {
    "F1": "Warm Believer",
    "F2": "Curious Skeptic",
    "F3": "Cold Partner Read",
    "F4": "Hostile Diligence",
}
DEFAULT_RUBRIC_PATH = Path(__file__).resolve().parents[1] / "rubric" / "rubric_v1.md"


class RubricLoaderError(ValueError):
    """Raised when rubric parsing or validation fails."""


@dataclass(frozen=True)
class RubricPaths:
    """Rubric source and cache paths."""

    markdown_path: Path
    json_path: Path


def setup_logging(verbose: bool = False) -> None:
    """Configure timestamped stderr logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    logging.Formatter.converter = lambda *_: datetime.now(timezone.utc).timetuple()


def rubric_paths(markdown_path: str | Path | None = None) -> RubricPaths:
    """Resolve rubric markdown and sibling JSON cache paths."""
    md_path = Path(markdown_path).expanduser().resolve() if markdown_path else DEFAULT_RUBRIC_PATH
    return RubricPaths(markdown_path=md_path, json_path=md_path.with_suffix(".json"))


def display_path(path: str | Path) -> str:
    """Return a portable package-relative path for metadata and public reports."""
    resolved = Path(path).expanduser().resolve()
    skill_root = Path(__file__).resolve().parents[1]
    try:
        return resolved.relative_to(skill_root).as_posix()
    except ValueError:
        return resolved.name


def load_rubric(markdown_path: str | Path | None = None, *, refresh: bool = False) -> dict[str, Any]:
    """Load structured rubric, regenerating JSON cache when needed."""
    paths = rubric_paths(markdown_path)
    if not paths.markdown_path.exists():
        raise RubricLoaderError(f"Rubric markdown not found: {paths.markdown_path}")
    if refresh or not paths.json_path.exists() or paths.json_path.stat().st_mtime < paths.markdown_path.stat().st_mtime:
        rubric = parse_rubric_markdown(paths.markdown_path.read_text(encoding="utf-8"), display_path(paths.markdown_path))
        write_rubric_json(rubric, paths.json_path)
        return rubric
    try:
        return json.loads(paths.json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RubricLoaderError(f"Invalid rubric JSON cache {paths.json_path}: {exc}") from exc


def write_rubric_json(rubric: dict[str, Any], json_path: Path) -> None:
    """Write and verify rubric JSON cache."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(rubric, indent=2, sort_keys=True), encoding="utf-8")
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    if loaded.get("dimension_count") != rubric.get("dimension_count"):
        raise RubricLoaderError(f"Rubric JSON verification failed: {json_path}")


def parse_rubric_markdown(markdown: str, source_path: str = "rubric_v1.md") -> dict[str, Any]:
    """Parse rubric markdown into dimensions, frame matrix, stage rules, and named POV IDs."""
    dimensions = parse_dimensions(markdown)
    frame_matrix = parse_frame_matrix(markdown, dimensions)
    stage_rules = parse_stage_rules(markdown)
    named_pov_palette = parse_named_povs(markdown)
    rubric = {
        "schema_version": "1.0",
        "source_path": source_path,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "frames": [{"id": key, "name": value} for key, value in DEFAULT_FRAMES.items()],
        "dimensions": dimensions,
        "dimension_count": len(dimensions),
        "frame_matrix": frame_matrix,
        "stage_rules": stage_rules,
        "named_pov_palette": named_pov_palette,
    }
    validate_rubric(rubric)
    return rubric


def parse_dimensions(markdown: str) -> list[dict[str, Any]]:
    """Parse substantive dimensions from the rubric table and sections."""
    table_match = re.search(r"## Substantive dimensions\n(?P<body>.*?)(?:\n###\s)", markdown, flags=re.S)
    if not table_match:
        raise RubricLoaderError("Could not find substantive dimensions table.")
    rows: list[dict[str, Any]] = []
    for line in table_match.group("body").splitlines():
        if not line.startswith("|") or "`" not in line or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0] == "ID":
            continue
        dim_id_match = re.search(r"`([^`]+)`", cells[0])
        if not dim_id_match:
            continue
        try:
            weight = float(cells[2])
        except ValueError as exc:
            raise RubricLoaderError(f"Invalid weight in dimension row: {line}") from exc
        rows.append({"id": dim_id_match.group(1), "name": cells[1], "weight": weight, "definition": cells[3]})
    sections = parse_dimension_sections(markdown)
    for row in rows:
        row.update(sections.get(row["id"], {}))
        row.setdefault("prompt_questions", [])
        row.setdefault("strong_signals", [])
        row.setdefault("weak_signals", [])
        row.setdefault("score_anchors", {})
        row.setdefault("frame_sensitivity", {})
    return rows


def parse_dimension_sections(markdown: str) -> dict[str, dict[str, Any]]:
    """Parse details from each ### dimension section."""
    pattern = re.compile(r"^###\s+(?P<name>.*?)\s+\(`(?P<id>[^`]+)`\)\n(?P<body>.*?)(?=\n---\n\n###|\n## Stylistic dimensions|\Z)", re.S | re.M)
    sections: dict[str, dict[str, Any]] = {}
    for match in pattern.finditer(markdown):
        body = match.group("body")
        sections[match.group("id")] = {
            "strong_signals": split_semicolon_field(extract_bold_value(body, "Strong signals")),
            "weak_signals": split_semicolon_field(extract_bold_value(body, "Weak signals")),
            "prompt_questions": parse_numbered_list_after(body, "**Prompt questions:**"),
            "frame_sensitivity": parse_frame_sensitivity(body),
            "score_anchors": parse_score_anchors(body),
            "stage_constraint": extract_bold_value(body, "Stage constraint"),
        }
    return sections


def extract_bold_value(body: str, label: str) -> str:
    """Extract a single-line **Label:** value."""
    match = re.search(rf"\*\*{re.escape(label)}:\*\*\s*(.*)", body)
    return match.group(1).strip() if match else ""


def split_semicolon_field(value: str) -> list[str]:
    """Split semicolon-delimited rubric field."""
    return [item.strip().rstrip(".") for item in value.split(";") if item.strip()]


def parse_numbered_list_after(body: str, marker: str) -> list[str]:
    """Parse numbered list after a marker until the next blank heading/table."""
    start = body.find(marker)
    if start == -1:
        return []
    tail = body[start + len(marker) :]
    questions: list[str] = []
    for line in tail.splitlines():
        stripped = line.strip()
        if not stripped:
            if questions:
                break
            continue
        match = re.match(r"\d+\.\s+(.*)", stripped)
        if match:
            questions.append(match.group(1).strip())
        elif questions:
            break
    return questions


def parse_frame_sensitivity(body: str) -> dict[str, dict[str, Any]]:
    """Parse per-frame modifiers from a dimension section table."""
    result: dict[str, dict[str, Any]] = {}
    for line in body.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 2 or not cells[0].startswith("F"):
            continue
        frame_id = cells[0].split()[0]
        modifier_match = re.search(r"([0-9.]+)x", cells[1])
        result[frame_id] = {
            "modifier": float(modifier_match.group(1)) if modifier_match else 1.0,
            "note": cells[1],
        }
    return result


def parse_score_anchors(body: str) -> dict[str, str]:
    """Parse score anchor table into a score-to-description map."""
    anchors: dict[str, str] = {}
    for line in body.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 2 or not re.match(r"^[0-5]$", cells[0]):
            continue
        anchors[cells[0]] = cells[1]
    return anchors


def parse_frame_matrix(markdown: str, dimensions: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    """Parse frame modifiers, falling back to per-dimension sensitivity sections."""
    matrix = {dimension["id"]: {frame: {"modifier": 1.0, "note": ""} for frame in DEFAULT_FRAMES} for dimension in dimensions}
    section_match = re.search(r"## Frame matrix\n(?P<body>.*?)(?:\n## Stage-discipline rules|\Z)", markdown, flags=re.S)
    if section_match:
        rows_by_name: dict[str, dict[str, str]] = {}
        for line in section_match.group("body").splitlines():
            if not line.startswith("|") or "---" in line or line.startswith("| Frame") or line.startswith("| Dimension"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) == 5:
                rows_by_name[cells[0].lower()] = dict(zip(DEFAULT_FRAMES.keys(), cells[1:]))
        for dimension in dimensions:
            row = rows_by_name.get(dimension["name"].lower())
            if not row:
                continue
            for frame_id, note in row.items():
                modifier_match = re.search(r"([0-9.]+)x", note)
                matrix[dimension["id"]][frame_id] = {
                    "modifier": float(modifier_match.group(1)) if modifier_match else 1.0,
                    "note": note,
                }
    for dimension in dimensions:
        for frame_id, details in dimension.get("frame_sensitivity", {}).items():
            matrix[dimension["id"]][frame_id] = details
    return matrix


def parse_stage_rules(markdown: str) -> dict[str, Any]:
    """Parse stage-discipline rule text and common cap rules."""
    match = re.search(r"## Stage-discipline rules\n(?P<body>.*?)(?:\n## Named-VC palette|\Z)", markdown, flags=re.S)
    body = match.group("body").strip() if match else ""
    caps: dict[str, float] = {}
    for phrase, dim_id in {
        "No why-this-founder": "founder_market_fit_team_capacity",
        "Thin traction plus missing insight": "non_obvious_insight_thesis_clarity",
        "top-down TAM theater": "market_logic_venture_scale_path",
        "no validation substitute": "evidence_demand_learning_velocity",
    }.items():
        cap_match = re.search(rf"{re.escape(phrase)}[^.]*?cap[s]? [^0-9.]*([0-9.]+)", body, flags=re.I)
        if cap_match:
            caps[dim_id] = float(cap_match.group(1).rstrip("."))
    return {
        "weakness_labels": [
            "granted_at_pre_seed",
            "stage_appropriate_evidence",
            "missing_pre_seed_proof",
            "false_precision",
            "inverse_trap",
            "credibility_risk",
        ],
        "text": body,
        "score_caps": caps,
    }


def parse_named_povs(markdown: str) -> list[dict[str, str]]:
    """Parse opt-in named POV IDs from rubric palette line."""
    match = re.search(r"## Named-VC palette\n(?P<body>.*?)(?:\n## Machine-readable output fields|\Z)", markdown, flags=re.S)
    if not match:
        return []
    ids = re.findall(r"`([^`]+)`", match.group("body"))
    return [{"id": pov_id, "label": pov_id.replace("_", " ").title()} for pov_id in ids]


def validate_rubric(rubric: dict[str, Any]) -> None:
    """Validate required rubric shape."""
    if rubric["dimension_count"] < 10:
        raise RubricLoaderError("Rubric must contain at least 10 substantive dimensions.")
    frame_ids = {frame["id"] for frame in rubric["frames"]}
    if frame_ids != set(DEFAULT_FRAMES):
        raise RubricLoaderError(f"Rubric frames must be F1-F4, got {sorted(frame_ids)}")
    dimension_ids = {dimension["id"] for dimension in rubric["dimensions"]}
    missing = [dim for dim in dimension_ids if dim not in rubric["frame_matrix"]]
    if missing:
        raise RubricLoaderError(f"Frame matrix missing dimensions: {missing}")


def main(argv: list[str] | None = None) -> int:
    """CLI for regenerating rubric JSON."""
    parser = argparse.ArgumentParser(description="Parse rubric_v1.md and emit rubric_v1.json.")
    parser.add_argument("--rubric", default=str(DEFAULT_RUBRIC_PATH), help="Path to rubric_v1.md")
    parser.add_argument("--out", help="Optional JSON output path; default is sibling .json")
    parser.add_argument("--dry-run", action="store_true", help="Parse and validate without writing")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    setup_logging(args.verbose)
    try:
        md_path = Path(args.rubric).expanduser().resolve()
        rubric = parse_rubric_markdown(md_path.read_text(encoding="utf-8"), str(md_path))
        out_path = Path(args.out).expanduser().resolve() if args.out else md_path.with_suffix(".json")
        if args.dry_run:
            print(json.dumps({"dimension_count": rubric["dimension_count"], "frames": [f["id"] for f in rubric["frames"]]}, indent=2))
        else:
            write_rubric_json(rubric, out_path)
            print(str(out_path))
        return 0
    except (OSError, RubricLoaderError) as exc:
        LOGGER.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
