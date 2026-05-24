#!/usr/bin/env python3
"""Detect pitch-deck voice/register mode using deterministic D2.5 heuristics."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

LOGGER = logging.getLogger("voice_mode_detector")

VOICE_MODE_LABELS: Mapping[str, str] = {
    "sharp_declarative": "sharp-declarative",
    "concrete_operator": "concrete/operator",
    "earnest_founder": "earnest-founder",
    "visionary_narrative": "visionary narrative",
    "consultative_analytical": "consultative/analytical",
    "mixed": "mixed",
}

HEDGES = {
    "we believe",
    "we think",
    "may",
    "might",
    "could",
    "potentially",
    "hope",
    "aim",
    "aims",
    "seek",
    "seeks",
    "intend",
    "intends",
}

VISIONARY_TERMS = {
    "future",
    "will",
    "every",
    "new default",
    "category",
    "infrastructure",
    "world where",
    "what happens when",
}

EARNEST_MARKERS = {
    "we learned",
    "we believe",
    "we do not yet know",
    "we don't yet know",
    "customers told us",
    "after interviewing",
    "we started with",
    "we heard",
}

CONSULTATIVE_MARKERS = {
    "thesis:",
    "evidence:",
    "implication:",
    "assumption",
    "segment",
    "driver",
    "constraint",
    "scenario",
    "base case",
}

OPERATOR_MARKERS = {
    "workflow",
    "pilot",
    "pilots",
    "signed",
    "converted",
    "retention",
    "cac",
    "payback",
    "loi",
    "lois",
    "review",
    "submit",
    "route",
    "dashboard",
    "clinic",
    "claims",
    "customer",
    "customers",
}

SHARP_MARKERS = {
    "now beats",
    "made",
    "we do",
    "we help",
    "for ",
    "because",
    "replaces",
    "turns",
}

HIGH_CLAIM_ADJECTIVES = {
    "huge",
    "massive",
    "seamless",
    "powerful",
    "sticky",
    "revolutionary",
    "world-class",
    "category-defining",
    "inevitable",
    "unique",
    "proprietary",
}

COVER_PATTERNS = re.compile(r"^(?:[A-Z][\w&.-]+\s*){1,5}(?:\n\s*(?:seed|pre-seed|series|deck|confidential))?\s*$", re.I)
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'%-]*")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class VoiceSlideAnalysis:
    """Per-slide voice-mode feature result."""

    slide_num: int
    assigned_mode: str
    mode_scores: dict[str, int]
    headline: str
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class VoiceModeResult:
    """Deck-level voice-mode detection result."""

    mode: str
    confidence: str
    mode_scores: dict[str, int]
    mode_share: dict[str, float]
    sampled_slide_count: int
    slide_modes: list[VoiceSlideAnalysis]
    rationale: str
    warnings: list[str] = field(default_factory=list)


def setup_logging(verbose: bool = False) -> None:
    """Configure timestamped CLI logging."""

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    logging.Formatter.converter = time_gmt


def time_gmt(*_: object) -> tuple[int, ...]:
    """Return UTC time tuple for logging formatter."""

    return datetime.now(timezone.utc).timetuple()


def normalize_text(text: str) -> str:
    """Return whitespace-normalized text."""

    return re.sub(r"\s+", " ", text or "").strip()


def slide_text(slide: str | Mapping[str, Any]) -> str:
    """Extract text from either a raw string or slide object."""

    if isinstance(slide, str):
        return slide
    if isinstance(slide, Mapping):
        return str(slide.get("text") or slide.get("raw_text") or "")
    return str(slide)


def slide_number(index: int, slide: str | Mapping[str, Any]) -> int:
    """Extract a 1-indexed slide number."""

    if isinstance(slide, Mapping):
        value = slide.get("slide_num") or slide.get("slide") or slide.get("page")
        try:
            return int(value)
        except (TypeError, ValueError):
            return index + 1
    return index + 1


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase word-ish tokens."""

    return [token.lower() for token in WORD_RE.findall(text)]


def contains_any(text: str, phrases: Iterable[str]) -> list[str]:
    """Return matching phrases found in lowercased text."""

    lower = text.lower()
    return [phrase for phrase in phrases if phrase in lower]


def count_any(text: str, phrases: Iterable[str]) -> int:
    """Count phrase occurrences across a phrase set."""

    lower = text.lower()
    return sum(len(re.findall(rf"\b{re.escape(phrase)}\b", lower)) for phrase in phrases)


def first_sentence(text: str) -> str:
    """Extract first non-empty sentence or bullet-ish line."""

    clean = normalize_text(text)
    if not clean:
        return ""
    return SENTENCE_RE.split(clean)[0]


def headline_from_slide(text: str) -> str:
    """Extract a likely headline from the first meaningful line."""

    for raw_line in (text or "").splitlines():
        line = raw_line.strip(" #\t-•")
        if line:
            return line[:180]
    return first_sentence(text)[:180]


def is_title_or_appendix(text: str) -> bool:
    """Return true for title-only cover or appendix markers."""

    clean = normalize_text(text)
    if not clean:
        return True
    lower = clean.lower()
    if "appendix" in lower[:80]:
        return True
    words = tokenize(clean)
    if len(words) <= 5 and COVER_PATTERNS.match(clean):
        return True
    return False


def core_slides(slides: Sequence[str | Mapping[str, Any]], max_slides: int = 5) -> list[tuple[int, str]]:
    """Return first N core slide texts with slide numbers."""

    selected: list[tuple[int, str]] = []
    for index, slide in enumerate(slides):
        text = slide_text(slide)
        if is_title_or_appendix(text):
            continue
        selected.append((slide_number(index, slide), text))
        if len(selected) >= max_slides:
            break
    return selected


def adjective_density(tokens: Sequence[str]) -> float:
    """Estimate adjective density using the D2.5 high-claim adjective lexicon."""

    if not tokens:
        return 0.0
    return sum(1 for token in tokens if token in HIGH_CLAIM_ADJECTIVES) / len(tokens)


def score_slide_modes(slide_num: int, text: str) -> VoiceSlideAnalysis:
    """Score a single slide against the five D2.5 voice profiles."""

    headline = headline_from_slide(text)
    combined = f"{headline}\n{first_sentence(text)}"
    words = tokenize(combined)
    text_lower = combined.lower()
    numbers = len(re.findall(r"(?:\$\d|\d+(?:\.\d+)?%?|\d+\s*(?:of|/|x)\s*\d+)", combined))
    hedge_hits = count_any(combined, HEDGES)
    operator_hits = count_any(combined, OPERATOR_MARKERS)
    earnest_hits = count_any(combined, EARNEST_MARKERS)
    visionary_hits = count_any(combined, VISIONARY_TERMS)
    consultative_hits = count_any(combined, CONSULTATIVE_MARKERS)
    short_headline = len(tokenize(headline)) <= 12 and len(tokenize(headline)) >= 3
    has_direct_claim = any(marker in text_lower for marker in SHARP_MARKERS)
    adj_density = adjective_density(words)

    scores = {
        "sharp_declarative": 0,
        "concrete_operator": 0,
        "earnest_founder": 0,
        "visionary_narrative": 0,
        "consultative_analytical": 0,
    }
    evidence: list[str] = []

    if short_headline and hedge_hits == 0:
        scores["sharp_declarative"] += 1
        evidence.append("short unhedged headline")
    if has_direct_claim and hedge_hits == 0:
        scores["sharp_declarative"] += 1
        evidence.append("direct claim phrasing")
    if numbers and hedge_hits == 0 and len(words) <= 28 and not earnest_hits:
        scores["sharp_declarative"] += 1
        evidence.append("fact-first compressed phrasing")

    if operator_hits >= 2 and not earnest_hits:
        scores["concrete_operator"] += 2
        evidence.append("workflow/customer nouns")
    elif operator_hits == 1 and not earnest_hits:
        scores["concrete_operator"] += 1
    if numbers >= 2:
        scores["concrete_operator"] += 1
        evidence.append("early metrics/process facts")

    if earnest_hits >= 1:
        scores["earnest_founder"] += 2
        evidence.append("first-person learning language")
    if hedge_hits >= 2 and ("because" in text_lower or numbers or "interview" in text_lower):
        scores["earnest_founder"] += 1
        evidence.append("uncertainty paired with evidence")

    if visionary_hits >= 2 and not earnest_hits:
        scores["visionary_narrative"] += 2
        evidence.append("future/category framing")
    elif visionary_hits == 1 and not earnest_hits:
        scores["visionary_narrative"] += 1
    if "we start with" in text_lower or "new default" in text_lower:
        scores["visionary_narrative"] += 1

    if consultative_hits >= 2:
        scores["consultative_analytical"] += 2
        evidence.append("thesis/evidence/assumption structure")
    elif consultative_hits == 1:
        scores["consultative_analytical"] += 1
    if ":" in headline and any(marker.strip(":") in text_lower for marker in CONSULTATIVE_MARKERS):
        scores["consultative_analytical"] += 1

    if adj_density > 0.06 and not numbers:
        scores["visionary_narrative"] += 1

    scores = {key: min(3, value) for key, value in scores.items()}
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if not ranked or ranked[0][1] == 0:
        assigned = "ambiguous"
    elif len(ranked) > 1 and ranked[0][1] - ranked[1][1] < 1:
        assigned = "ambiguous"
    else:
        assigned = ranked[0][0]
    return VoiceSlideAnalysis(slide_num=slide_num, assigned_mode=assigned, mode_scores=scores, headline=headline, evidence=evidence[:4])


def detect_voice_mode(slides: Sequence[str | Mapping[str, Any]], config: Mapping[str, Any] | None = None) -> VoiceModeResult:
    """Detect deck voice mode from the first five core slides.

    Args:
        slides: Sequence of raw slide texts or slide objects with a ``text`` field.
        config: Optional config. ``register_override`` may force a supported mode.

    Returns:
        A serializable :class:`VoiceModeResult`.
    """

    config = config or {}
    override = str(config.get("register_override", "auto") or "auto")
    if override != "auto":
        normalized_override = override.replace("-", "_")
        if normalized_override in VOICE_MODE_LABELS and normalized_override != "mixed":
            return VoiceModeResult(
                mode=normalized_override,
                confidence="high",
                mode_scores={normalized_override: 1},
                mode_share={normalized_override: 1.0},
                sampled_slide_count=0,
                slide_modes=[],
                rationale=f"register_override forced {VOICE_MODE_LABELS[normalized_override]}",
                warnings=[],
            )

    sampled = core_slides(slides, max_slides=5)
    warnings: list[str] = []
    if len(sampled) < 5:
        warnings.append("fewer than five core slides sampled; confidence may be lower")
    if not sampled:
        return VoiceModeResult(
            mode="mixed",
            confidence="low",
            mode_scores={},
            mode_share={},
            sampled_slide_count=0,
            slide_modes=[],
            rationale="No core slide text available for voice detection.",
            warnings=["no core slide text available"],
        )

    slide_results = [score_slide_modes(num, text) for num, text in sampled]
    totals: Counter[str] = Counter()
    for result in slide_results:
        totals.update(result.mode_scores)
    total_points = sum(totals.values())
    if total_points <= 0:
        return VoiceModeResult(
            mode="mixed",
            confidence="low",
            mode_scores=dict(totals),
            mode_share={key: 0.0 for key in VOICE_MODE_LABELS if key != "mixed"},
            sampled_slide_count=len(slide_results),
            slide_modes=slide_results,
            rationale="No voice mode reached a meaningful signal threshold.",
            warnings=warnings,
        )

    ranked = totals.most_common()
    top_mode, top_points = ranked[0]
    second_points = ranked[1][1] if len(ranked) > 1 else 0
    top_share = top_points / total_points
    shares = {key: round(totals.get(key, 0) / total_points, 4) for key in VOICE_MODE_LABELS if key != "mixed"}
    assigned_modes = [result.assigned_mode for result in slide_results if result.assigned_mode != "ambiguous"]
    distinct_assigned = set(assigned_modes)
    high_v1 = totals.get("sharp_declarative", 0) >= 4
    high_v3 = totals.get("earnest_founder", 0) >= 4
    second_mode = ranked[1][0] if len(ranked) > 1 else None
    compatible_operator_claim_pair = {top_mode, second_mode} == {"sharp_declarative", "concrete_operator"}
    near_tie = (top_points - second_points) < (0.10 * total_points) and not compatible_operator_claim_pair
    earnest_has_clear_markers = totals.get("earnest_founder", 0) >= 4 and top_mode == "earnest_founder"

    mixed = (
        top_share < 0.35
        or (len(distinct_assigned) >= 3 and not earnest_has_clear_markers and not compatible_operator_claim_pair)
        or (len(distinct_assigned) >= 3 and top_share < 0.40)
        or near_tie
        or (high_v1 and high_v3 and top_points - second_points < 3)
    )
    if not mixed and len(distinct_assigned) >= 2 and len([result for result in slide_results if result.assigned_mode == "ambiguous"]) >= 2 and top_share < 0.40:
        mixed = True

    if mixed:
        mode = "mixed"
        confidence = "low" if top_share < 0.35 or near_tie else "medium"
    else:
        mode = top_mode
        if top_share >= 0.45 and (top_points - second_points) >= 2:
            confidence = "high"
        elif top_share >= 0.35 and top_points > second_points:
            confidence = "medium"
        else:
            confidence = "low"

    if compatible_operator_claim_pair and confidence == "low" and top_share >= 0.45:
        confidence = "medium"
    mode_label = VOICE_MODE_LABELS.get(mode, mode)
    rationale = f"Detected {mode_label} from {len(slide_results)} core slides; top share {top_share:.0%}, lead {top_points - second_points} point(s)."
    return VoiceModeResult(
        mode=mode,
        confidence=confidence,
        mode_scores=dict(totals),
        mode_share=shares,
        sampled_slide_count=len(slide_results),
        slide_modes=slide_results,
        rationale=rationale,
        warnings=warnings,
    )


def result_to_dict(result: VoiceModeResult) -> dict[str, Any]:
    """Serialize result dataclasses to plain dictionaries."""

    return asdict(result)


def load_slides(path: Path) -> list[dict[str, Any]]:
    """Load slides from JSON or markdown/text fixture."""

    if not path.exists():
        raise FileNotFoundError(f"Input path does not exist: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload = json.loads(text)
        if isinstance(payload, list):
            return [item if isinstance(item, dict) else {"slide_num": i + 1, "text": str(item)} for i, item in enumerate(payload)]
        if isinstance(payload, dict) and isinstance(payload.get("slides"), list):
            return [item if isinstance(item, dict) else {"slide_num": i + 1, "text": str(item)} for i, item in enumerate(payload["slides"])]
        raise ValueError("JSON input must be a list or object with slides[]")
    parts = re.split(r"\n\s*(?:---+|##\s+Slide\s+\d+[^\n]*)\s*\n", text)
    chunks = []
    for chunk in parts:
        cleaned = chunk.strip()
        if not cleaned:
            continue
        if cleaned.startswith("---") or cleaned.startswith("# "):
            continue
        chunks.append(cleaned)
    return [{"slide_num": index + 1, "text": chunk} for index, chunk in enumerate(chunks)]


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""

    parser = argparse.ArgumentParser(description="Detect pitch-deck voice/register mode.")
    parser.add_argument("input", nargs="?", help="JSON, markdown, or text deck fixture")
    parser.add_argument("--out", help="Optional JSON output path")
    parser.add_argument("--dry-run", action="store_true", help="Validate input and print intended action without writing files")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""

    parser = build_arg_parser()
    args = parser.parse_args(argv)
    setup_logging(args.verbose)
    if not args.input:
        parser.print_help(sys.stderr)
        return 1
    try:
        slides = load_slides(Path(args.input))
        result = result_to_dict(detect_voice_mode(slides))
        if args.dry_run:
            LOGGER.info("dry-run: would detect voice mode for %s slides", len(slides))
            print(json.dumps({"dry_run": True, "slide_count": len(slides), "result": result}, indent=2))
            return 0
        output = json.dumps(result, indent=2)
        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output + "\n", encoding="utf-8")
            verify = json.loads(out_path.read_text(encoding="utf-8"))
            if verify.get("mode") != result.get("mode"):
                raise RuntimeError(f"State verification failed for {out_path}")
            LOGGER.info("wrote %s", out_path)
        else:
            print(output)
        return 0
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        LOGGER.error("voice detection failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
