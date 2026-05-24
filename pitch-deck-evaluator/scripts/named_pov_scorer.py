#!/usr/bin/env python3
"""Named-POV palette scoring for pitch-deck-evaluator."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

LOGGER = logging.getLogger("pitch_deck_evaluator.named_pov_scorer")
ANTI_COSPLAY_DISCLAIMER = (
    "Based on public writing/interviews, this lens emphasizes certain questions and heuristics. "
    "It is not a claim to know how any named person or firm would evaluate, invest in, or pass on this company."
)
DEFAULT_PALETTE_PATH = Path(__file__).resolve().parents[1] / "rubric" / "named_vc_palette.md"
POV_ID_ALIASES = {
    "hustle_fund": "hustle_fund_yin_bahn",
    "naval": "naval_ravikant",
    "pear": "pear_nozad_hershenson",
    "nfx": "nfx_currier_levy_weiss",
    "floodgate": "floodgate_maples_miura_ko",
    "bloomberg_beta": "bloomberg_beta_bahat",
    "precursor": "precursor_hudson",
    "boost": "boost_draper",
    "designer_fund": "designer_fund_blumenrose_allen",
    "k9": "k9_manu_kumar",
}
POV_HEURISTIC_KEYWORDS = {
    "hustle_fund_yin_bahn": ["team", "problem", "solution", "market", "traction", "customer"],
    "pear_nozad_hershenson": ["customer", "market", "story", "bottom-up", "team"],
    "nfx_currier_levy_weiss": ["network", "marketplace", "timing", "defensibility", "why now"],
    "floodgate_maples_miura_ko": ["insight", "breakthrough", "founder", "why now", "unique"],
    "bloomberg_beta_bahat": ["demo", "future of work", "extraordinary", "proof", "product"],
    "precursor_hudson": ["founder", "story", "people", "market", "customer"],
    "boost_draper": ["future", "weird", "frontier", "network", "founder"],
    "designer_fund_blumenrose_allen": ["design", "brand", "user", "experience", "product"],
    "2048_iskold": ["founder", "market", "technical", "health", "vertical", "ai"],
    "k9_manu_kumar": ["technical", "prototype", "product", "capital", "founder"],
    "naval_ravikant": ["high-concept", "exceptional", "prototype", "product", "network"],
    "jason_calacanis": ["traction", "product", "founder", "answer", "customers"],
    "sahil_lavingia": ["technical", "taste", "creator", "product", "scale"],
    "elad_gil": ["process", "fundraising", "market", "growth", "team"],
    "fabrice_grinda_fj_labs": ["marketplace", "unit economics", "take rate", "liquidity", "supply", "demand"],
}


class PovScoringError(ValueError):
    """Raised when named POV scoring cannot proceed."""


class PovClient(Protocol):
    """Protocol for model-backed POV scoring."""

    def score_pov(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Return a POV scorecard."""


@dataclass(frozen=True)
class HeuristicPovClient:
    """Deterministic fallback named POV scorer."""

    def score_pov(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        pov = context["pov"]
        slides = context["slides"]
        keywords = POV_HEURISTIC_KEYWORDS.get(pov["id"], [])
        deck_text = "\n".join(slide.get("text", "") for slide in slides).lower()
        hits = [keyword for keyword in keywords if keyword.lower() in deck_text]
        score = min(5.0, 1.5 + 0.7 * len(hits))
        if score > 4.5:
            score = 4.5
        commentary = render_pov_commentary(pov, hits, score)
        return {
            "score": round(score * 2) / 2,
            "commentary": commentary,
            "emphasized_terms": hits,
            "prompt_preview": prompt[:500],
        }


def score_named_povs(
    slides: list[dict[str, Any]],
    config: dict[str, Any],
    palette: dict[str, Any] | None = None,
    pov_client: PovClient | None = None,
) -> list[dict[str, Any]]:
    """Score enabled named POV palette entries; return [] when none enabled."""
    enabled = [normalize_pov_id(pov_id) for pov_id in (config.get("enabled_pov_palette") or [])]
    if not enabled:
        return []
    palette = palette or load_pov_palette()
    client = pov_client or HeuristicPovClient()
    reads: list[dict[str, Any]] = []
    for pov_id in enabled:
        pov = palette.get(pov_id)
        if not pov:
            valid = ", ".join(sorted(palette))
            raise PovScoringError(f"Unknown POV '{pov_id}'. Valid IDs: {valid}")
        prompt = build_pov_prompt(slides, pov)
        scored = client.score_pov(prompt, {"slides": slides, "pov": pov})
        reads.append(
            {
                "pov_id": pov_id,
                "label": pov["label"],
                "anti_cosplay_disclaimer": ANTI_COSPLAY_DISCLAIMER,
                "score": scored["score"],
                "commentary": scored["commentary"],
                "output_style": pov.get("output_style", "source-inspired, specific, and non-predictive"),
                "emphasized_terms": scored.get("emphasized_terms", []),
            }
        )
    return reads


def normalize_pov_id(pov_id: str) -> str:
    """Normalize short aliases from config into canonical POV IDs."""
    cleaned = pov_id.strip().lower().replace("-", "_").replace(" ", "_")
    return POV_ID_ALIASES.get(cleaned, cleaned)


def load_pov_palette(path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Load POV definitions from synthesis markdown, falling back to rubric summary."""
    candidates = [Path(path).expanduser().resolve()] if path else [DEFAULT_PALETTE_PATH]
    for candidate in candidates:
        if candidate.exists():
            return parse_pov_palette(candidate.read_text(encoding="utf-8"))
    return fallback_palette()


def parse_pov_palette(markdown: str) -> dict[str, dict[str, Any]]:
    """Parse D2.3 named POV markdown into canonical IDs and output styles."""
    palette: dict[str, dict[str, Any]] = {}
    overview = parse_overview_labels(markdown)
    sections = re.finditer(r"^##\s+\d+\.\s+(?P<label>.+?)\s+lens\n(?P<body>.*?)(?=^##\s+\d+\.|\Z)", markdown, flags=re.S | re.M)
    for section in sections:
        label = section.group("label").strip() + " lens"
        pov_id = label_to_id(label, overview)
        body = section.group("body")
        palette[pov_id] = {
            "id": pov_id,
            "label": label,
            "definition": compact_section(body, ["What this POV grants", "What this POV interrogates", "Signature heuristics"]),
            "output_style": extract_subsection(body, "Output style note") or "source-inspired, specific, and non-predictive",
        }
    if palette:
        return palette
    return fallback_palette()


def parse_overview_labels(markdown: str) -> dict[str, str]:
    """Map overview labels to canonical IDs from config schema."""
    mapping: dict[str, str] = {}
    canonical_ids = list(POV_HEURISTIC_KEYWORDS)
    for index, line in enumerate(markdown.splitlines()):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0].isdigit():
            try:
                mapping[cells[1].lower()] = canonical_ids[int(cells[0]) - 1]
            except (IndexError, ValueError):
                continue
    return mapping


def label_to_id(label: str, overview: dict[str, str]) -> str:
    """Convert label to known ID when possible."""
    lower = label.lower()
    for overview_label, pov_id in overview.items():
        if overview_label.lower() in lower or lower in overview_label.lower():
            return pov_id
    if "hustle fund" in lower:
        return "hustle_fund_yin_bahn"
    if "pear" in lower:
        return "pear_nozad_hershenson"
    if "naval" in lower:
        return "naval_ravikant"
    return re.sub(r"[^a-z0-9]+", "_", lower).strip("_")


def extract_subsection(body: str, heading: str) -> str:
    """Extract a markdown subsection body by heading text."""
    match = re.search(rf"^###\s+{re.escape(heading)}\n(?P<text>.*?)(?=^###\s+|\Z)", body, flags=re.S | re.M)
    return re.sub(r"\s+", " ", match.group("text")).strip() if match else ""


def compact_section(body: str, headings: list[str]) -> str:
    """Compact selected subsections into one definition string."""
    parts = [extract_subsection(body, heading) for heading in headings]
    return " ".join(part for part in parts if part)[:4000]


def fallback_palette() -> dict[str, dict[str, Any]]:
    """Return minimal valid palette definitions when markdown is unavailable."""
    return {
        pov_id: {
            "id": pov_id,
            "label": pov_id.replace("_", " ").title(),
            "definition": "Source-inspired opt-in lens from the D2.3 palette.",
            "output_style": "specific, non-predictive commentary",
        }
        for pov_id in POV_HEURISTIC_KEYWORDS
    }


def build_pov_prompt(slides: list[dict[str, Any]], pov: dict[str, Any]) -> str:
    """Build prompt text for a real POV model adapter."""
    deck_text = "\n\n".join(f"Slide {slide.get('slide_num')}: {slide.get('text', '')}" for slide in slides)
    return (
        f"{ANTI_COSPLAY_DISCLAIMER}\n\n"
        f"POV: {pov['label']}\nDefinition: {pov.get('definition', '')}\n"
        f"Output style: {pov.get('output_style', '')}\n\nDeck:\n{deck_text}\n\n"
        "Return a source-inspired scorecard, not an investment prediction."
    )


def render_pov_commentary(pov: dict[str, Any], hits: list[str], score: float) -> str:
    """Render deterministic POV commentary."""
    if hits:
        terms = ", ".join(hits[:6])
        return f"This lens finds some surface area to engage because the deck touches {terms}. It would still ask for sharper proof tied to the lens's public heuristics."
    return f"This lens has little extracted evidence to work with. Add the concrete proof this POV tends to emphasize before relying on this read."


def main(argv: list[str] | None = None) -> int:
    """CLI for named POV scoring from slides JSON."""
    parser = argparse.ArgumentParser(description="Score enabled named POV lenses.")
    parser.add_argument("slides_json")
    parser.add_argument("--enabled", nargs="*", default=[])
    parser.add_argument("--out")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        slides = json.loads(Path(args.slides_json).read_text(encoding="utf-8"))
        result = score_named_povs(slides, {"enabled_pov_palette": args.enabled})
        if args.dry_run:
            print(json.dumps({"pov_count": len(result)}, indent=2))
        elif args.out:
            out_path = Path(args.out).expanduser().resolve()
            out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(str(out_path))
        else:
            print(json.dumps(result, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, PovScoringError) as exc:
        LOGGER.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
