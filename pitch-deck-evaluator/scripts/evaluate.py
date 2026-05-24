#!/usr/bin/env python3
"""CLI entrypoint for pitch-deck-evaluator."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

try:
    from deck_reader import DeckReaderError, read_deck
    from frame_scorer import ScoringError, score_frames
    from named_pov_scorer import PovScoringError, score_named_povs
    from output_renderer import RenderError, render_markdown, write_outputs
    from rubric_loader import RubricLoaderError, load_rubric
except ImportError:  # pragma: no cover
    from .deck_reader import DeckReaderError, read_deck
    from .frame_scorer import ScoringError, score_frames
    from .named_pov_scorer import PovScoringError, score_named_povs
    from .output_renderer import RenderError, render_markdown, write_outputs
    from .rubric_loader import RubricLoaderError, load_rubric

LOGGER = logging.getLogger("pitch_deck_evaluator.evaluate")
SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = SKILL_ROOT / "config" / "default_config.yaml"
DEFAULT_RUBRIC_PATH = SKILL_ROOT / "rubric" / "rubric_v1.md"
VALID_STAGES = {"pre_seed", "seed", "series_a"}
VALID_FRAMES = {"F1", "F2", "F3", "F4"}
VALID_VERBOSITY = {"terse", "standard", "deep"}
VALID_REGISTERS = {"auto", "sharp_declarative", "concrete_operator", "earnest_founder", "visionary_narrative", "consultative_analytical"}


def display_path(path: str | Path) -> str:
    """Return a portable report path without embedding local absolute directories."""
    resolved = Path(path).expanduser().resolve()
    try:
        return resolved.relative_to(SKILL_ROOT).as_posix()
    except ValueError:
        pass
    try:
        return resolved.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return resolved.name


class EvaluationError(ValueError):
    """Raised when the evaluator cannot complete safely."""


def setup_logging(verbose: bool = False) -> None:
    """Configure timestamped stderr logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    logging.Formatter.converter = lambda *_: datetime.now(timezone.utc).timetuple()


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML/JSON config merged onto defaults."""
    defaults = default_config()
    path = Path(config_path).expanduser().resolve() if config_path else DEFAULT_CONFIG_PATH
    if path.exists():
        try:
            if path.suffix.lower() == ".json":
                loaded = json.loads(path.read_text(encoding="utf-8"))
            else:
                if yaml is None:
                    raise EvaluationError("PyYAML is required for YAML config files. Install with `pip install pyyaml`.")
                loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, json.JSONDecodeError) as exc:
            raise EvaluationError(f"Failed to load config {path}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise EvaluationError(f"Config must be a mapping/object: {path}")
        config = {**defaults, **loaded}
        config["config_source"] = display_path(path)
    elif config_path:
        raise EvaluationError(f"Config path not found: {path}")
    else:
        config = defaults
        config["config_source"] = "built_in_defaults"
    validate_config(config)
    return config


def default_config() -> dict[str, Any]:
    """Return built-in config defaults matching config/default_config.yaml."""
    return {
        "stage": "pre_seed",
        "enabled_frames": ["F1", "F2", "F3", "F4"],
        "enabled_pov_palette": [],
        "substantive_weight_overrides": {},
        "stylistic_weight_overrides": {},
        "register_override": "auto",
        "output_verbosity": "standard",
        "include_action_list": True,
        "include_advisory_overall": True,
        "model": "claude-sonnet-4-6",
        "scoring_backend": "heuristic",
        "emit_json": False,
    }


def validate_config(config: dict[str, Any]) -> None:
    """Validate config with field-level errors."""
    if config.get("stage") not in VALID_STAGES:
        raise EvaluationError(f"Invalid stage {config.get('stage')!r}; valid: {sorted(VALID_STAGES)}")
    frames = config.get("enabled_frames")
    if not isinstance(frames, list) or not frames or any(frame not in VALID_FRAMES for frame in frames):
        raise EvaluationError("enabled_frames must be a non-empty list containing only F1, F2, F3, F4.")
    if len(set(frames)) != len(frames):
        raise EvaluationError("enabled_frames must be unique.")
    if not isinstance(config.get("enabled_pov_palette", []), list):
        raise EvaluationError("enabled_pov_palette must be a list.")
    if config.get("register_override") not in VALID_REGISTERS:
        raise EvaluationError(f"Invalid register_override {config.get('register_override')!r}.")
    if config.get("output_verbosity") not in VALID_VERBOSITY:
        raise EvaluationError(f"Invalid output_verbosity {config.get('output_verbosity')!r}.")
    for key in ("substantive_weight_overrides", "stylistic_weight_overrides"):
        overrides = config.get(key, {}) or {}
        if not isinstance(overrides, dict):
            raise EvaluationError(f"{key} must be a mapping.")
        for override_key, value in overrides.items():
            if not isinstance(value, (int, float)) or not 0 <= float(value) <= 3:
                raise EvaluationError(f"{key}.{override_key} must be a number from 0 to 3.")


def evaluate_deck(deck_path: str | Path, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run deck_reader → frame_scorer → optional stylistic scorer → optional POV scorer."""
    config = config or load_config(None)
    resolved_deck = Path(deck_path).expanduser().resolve()
    LOGGER.info("reading deck: %s", resolved_deck)
    slides = read_deck(resolved_deck)
    LOGGER.info("loading rubric: %s", DEFAULT_RUBRIC_PATH)
    rubric = load_rubric(DEFAULT_RUBRIC_PATH, refresh=True)
    substantive = score_frames(slides, rubric, config)
    stylistic = maybe_score_stylistic(slides, config)
    pov_reads = score_named_povs(slides, config)
    evaluation = {
        "schema_version": "1.0",
        "deck_metadata": {
            "deck_name": resolved_deck.name,
            "deck_path": display_path(resolved_deck),
            "slide_count": len(slides),
        },
        "evaluation_date": datetime.now(timezone.utc).date().isoformat(),
        "config": sanitize_config(config),
        "slides": slides,
        **substantive,
        "named_pov_reads": pov_reads,
    }
    evaluation.update(normalize_stylistic_result(stylistic))
    if config.get("include_advisory_overall", True):
        evaluation["advisory_overall"] = compute_advisory_overall(
            evaluation.get("substantive_composite"), evaluation.get("stylistic_composite")
        )
    evaluation["prioritized_action_list"] = build_action_list(evaluation)
    return evaluation


def maybe_score_stylistic(slides: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    """Compose with D4.2 stylistic_scorer if available; otherwise emit transparent null."""
    try:
        from stylistic_scorer import score_stylistic  # type: ignore
    except ImportError:
        LOGGER.info("stylistic_scorer not available; continuing with substantive-only style placeholder")
        return {
            "stylistic_dimensions": [],
            "stylistic_composite": None,
            "style_substance_gap": {"status": "not_scored", "reason": "D4.2 stylistic_scorer unavailable"},
        }
    result = score_stylistic(slides, config)
    if not isinstance(result, dict):
        raise EvaluationError("stylistic_scorer.score_stylistic must return a dict.")
    return result


def normalize_stylistic_result(stylistic: dict[str, Any]) -> dict[str, Any]:
    """Normalize D4.2 style scorecard into renderer-friendly fields."""
    normalized = dict(stylistic)
    if "style_score" in normalized and normalized.get("stylistic_composite") is None:
        normalized["stylistic_composite"] = round(float(normalized["style_score"]) / 20.0, 2)
    if "dimensions" in normalized and normalized.get("stylistic_dimensions") is None:
        normalized["stylistic_dimensions"] = normalized["dimensions"]
    return normalized


def compute_advisory_overall(substantive: Any, stylistic: Any) -> float | None:
    """Compute advisory overall composite, preserving separate score surfaces."""
    if substantive is None:
        return None
    if stylistic is None:
        return round(float(substantive), 2)
    style_value = float(stylistic)
    if style_value > 5:
        style_value = style_value / 20.0
    return round((float(substantive) * 0.75) + (style_value * 0.25), 2)


def build_action_list(evaluation: dict[str, Any]) -> list[str]:
    """Rank top fixes by low score and de-duplicate."""
    seen: set[str] = set()
    actions: list[str] = []
    scores = sorted(evaluation.get("substantive_dimensions", []), key=lambda score: score.get("raw_score", 5))
    for score in scores:
        fix = score.get("top_fix")
        if fix and fix not in seen:
            seen.add(fix)
            actions.append(fix)
    return actions


def sanitize_config(config: dict[str, Any]) -> dict[str, Any]:
    """Remove non-deterministic or private config keys before rendering."""
    sanitized = dict(config)
    for key in list(sanitized):
        if key.lower().endswith("key") or "secret" in key.lower() or "token" in key.lower():
            sanitized[key] = "[redacted]"
    return sanitized


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint: python evaluate.py <deck_path> [--config path] [--out path]."""
    parser = argparse.ArgumentParser(description="Evaluate a pre-seed/seed pitch deck across investor frames.")
    parser.add_argument("deck_path", help="PDF, text/markdown deck, or directory bundle")
    parser.add_argument("--config", help="YAML/JSON config path")
    parser.add_argument("--out", help="Markdown output path; if omitted, prints markdown")
    parser.add_argument("--json-out", help="Optional JSON output path")
    parser.add_argument("--emit-json", action="store_true", help="Also emit JSON companion next to --out")
    parser.add_argument("--dry-run", action="store_true", help="Validate deck/config/rubric without writing report")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    setup_logging(args.verbose)
    try:
        config = load_config(args.config)
        evaluation = evaluate_deck(args.deck_path, config)
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "deck": evaluation["deck_metadata"],
                        "frames": [frame["frame_id"] for frame in evaluation.get("frame_scorecards", [])],
                        "substantive_composite": evaluation.get("substantive_composite"),
                        "pov_count": len(evaluation.get("named_pov_reads", [])),
                    },
                    indent=2,
                )
            )
            return 0
        if args.json_out:
            json_out = Path(args.json_out).expanduser().resolve()
            json_out.parent.mkdir(parents=True, exist_ok=True)
            json_out.write_text(json.dumps(evaluation, indent=2, sort_keys=True), encoding="utf-8")
            if not json_out.exists() or json_out.stat().st_size == 0:
                raise EvaluationError(f"Failed to verify JSON output: {json_out}")
        if args.out:
            outputs = write_outputs(evaluation, args.out, config, emit_json=args.emit_json or config.get("emit_json", False))
            for output in outputs:
                print(str(output))
        else:
            print(render_markdown(evaluation, config), end="")
        return 0
    except (
        DeckReaderError,
        ScoringError,
        PovScoringError,
        RenderError,
        RubricLoaderError,
        EvaluationError,
        OSError,
    ) as exc:
        LOGGER.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
