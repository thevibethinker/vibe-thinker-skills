#!/usr/bin/env python3
"""Deterministic stylistic scoring for pre-seed pitch decks."""

from __future__ import annotations

import argparse
import json
import logging
import math
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from voice_mode_detector import HEDGES, VOICE_MODE_LABELS, detect_voice_mode, load_slides, normalize_text, slide_number, slide_text, tokenize
except ImportError:  # pragma: no cover - package-style import fallback
    from .voice_mode_detector import HEDGES, VOICE_MODE_LABELS, detect_voice_mode, load_slides, normalize_text, slide_number, slide_text, tokenize

LOGGER = logging.getLogger("stylistic_scorer")

STYLE_DIMENSIONS: dict[str, dict[str, Any]] = {
    "punch_density": {"label": "Punch / Density", "weight": 16},
    "specificity_quantification": {"label": "Specificity / Quantification", "weight": 16},
    "voice_register_fit": {"label": "Voice + Register Fit", "weight": 14},
    "claim_hygiene": {"label": "Claim Hygiene", "weight": 16},
    "hierarchy_scannability": {"label": "Hierarchy + Scannability", "weight": 14},
    "anti_buzzword_discipline": {"label": "Anti-Buzzword Discipline", "weight": 12},
    "narrative_cohesion": {"label": "Narrative Cohesion", "weight": 12},
}

PROMPT_QUESTIONS: dict[str, list[str]] = {
    "punch_density": [
        "Can a smart investor state what the company does after slide 1 or slide 2?",
        "Do the first five slides contain the minimum attention-earning claims?",
        "Does each slide carry one main point?",
    ],
    "specificity_quantification": [
        "Which claims use adjectives where numbers or examples are available?",
        "Does the product description name a user action the reader can picture?",
        "Are the most important traction or demand claims quantified?",
    ],
    "voice_register_fit": [
        "Which voice mode best describes the first five slides?",
        "Does confidence match the amount of proof shown?",
        "Are hedges honest uncertainty markers or signs of weak conviction?",
    ],
    "claim_hygiene": [
        "For each major claim, is it fact, belief, plan, or hypothesis?",
        "Does the slide show proof near the claim?",
        "Are unsupported claims made more forceful by copy polish?",
    ],
    "hierarchy_scannability": [
        "If the reader only reads headlines, can they understand the argument?",
        "Does each slide have one obvious top claim?",
        "Are proof points placed before attention is lost?",
    ],
    "anti_buzzword_discipline": [
        "Which sentence most clearly says what the product does?",
        "Which phrases could be used by any startup in the category?",
        "Would a smart outsider understand the product without insider jargon?",
    ],
    "narrative_cohesion": [
        "What is the deck’s one-sentence through-line?",
        "Do later slides use the same customer, wedge, and product model introduced early?",
        "Does each slide advance the previous slide’s logic?",
    ],
}


def build_llm_scoring_prompt(slides: Sequence[str | Mapping[str, Any]], dimension_id: str, heuristic_reasoning: str, config: Mapping[str, Any] | None = None) -> str:
    """Build an optional style-review prompt without calling a model.

    The v1 scorer is deterministic, but this prompt gives an orchestrator a
    rubric-aligned verification payload if an explicit LLM check is later enabled.
    """

    del config
    questions = PROMPT_QUESTIONS.get(dimension_id, [])
    slide_lines = []
    for index, slide in enumerate(slides, start=1):
        slide_lines.append(f"S{slide_number(index - 1, slide)}: {normalize_text(slide_text(slide))[:700]}")
    return "\n".join([
        f"Score stylistic dimension `{dimension_id}` independently from substance.",
        "Use only evidence present in the deck. Do not invent metrics or customers.",
        "Rubric questions:",
        *(f"- {question}" for question in questions),
        f"Heuristic pre-read: {heuristic_reasoning}",
        "Slides:",
        *slide_lines,
        "Return score 0-5, reasoning, evidence slide refs, and one safe rewrite instruction.",
    ])

LABEL_HEADLINES = {"problem", "solution", "market", "product", "traction", "team", "ask", "competition", "business model", "roadmap"}
THROAT_CLEARING = {"we are building", "we're building", "in the process of", "designed to", "aims to", "seeks to", "in order to", "leveraging"}
BUZZWORDS = {"ai-powered", "next-gen", "end-to-end", "seamless", "intelligent", "platform", "ecosystem", "revolutionary", "transform", "unlock", "empower", "supercharge", "synergy", "future of"}
HIGH_CLAIM_ADJECTIVES = {"huge", "massive", "seamless", "powerful", "sticky", "revolutionary", "world-class", "experienced", "visionary", "strong", "large", "unique", "proprietary", "defensible"}
ABSTRACT_NOUNS = {"transformation", "optimization", "activation", "intelligence", "automation", "innovation", "solution", "platform", "ecosystem", "enablement"}
CONCRETE_NOUNS = {"clinic", "lawyer", "claims", "team", "billers", "founders", "pilot", "customer", "dashboard", "plug-in", "reviewer", "workflow", "doctor", "seller", "buyer", "restaurant", "school"}
PROOF_MARKERS = {"pilot", "pilots", "loi", "lois", "interview", "interviews", "survey", "surveys", "signed", "paid", "revenue", "retention", "source", "customers", "customer", "quote", "demo", "screenshot", "data", "observed"}
SUPERLATIVES = {"best", "only", "first", "largest", "fastest", "unique", "defensible", "proprietary", "no one else"}
RISK_TERMS = {"competition", "competitor", "risk", "incumbent", "alternative", "why now"}
MORALIZING = {"broken", "stupid", "lazy", "dinosaur", "crushed", "destroy"}
FEATURE_WORDS = {"feature", "features", "module", "modules", "integrations", "automations", "api", "analytics"}
CAUSAL_CONNECTORS = {"because", "therefore", "so", "which means", "this creates", "as a result"}
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class StyleEvidence:
    """Evidence pointer for a stylistic score."""

    slide_ref: str
    excerpt: str
    evidence_type: str


@dataclass(frozen=True)
class StyleDimensionScore:
    """Per-dimension stylistic score."""

    dimension_id: str
    label: str
    score: float
    weight_default: float
    weight_effective: float
    weighted_points: float
    reasoning: str
    evidence: list[StyleEvidence]
    register_applied: bool
    top_fix: str
    confidence: str = "medium"
    prompt_questions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StylisticScorecard:
    """Full style scorecard returned to evaluate.py."""

    detected_voice_mode: str
    voice_confidence: str
    style_score: float
    dimensions: list[StyleDimensionScore]
    strengths: list[str]
    weaknesses: list[str]
    gap_flag: str | None
    notes: list[str]


def setup_logging(verbose: bool = False) -> None:
    """Configure timestamped logging."""

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ")
    logging.Formatter.converter = lambda *_: datetime.now(timezone.utc).timetuple()


def split_sentences(text: str) -> list[str]:
    """Split normalized text into sentences."""

    clean = normalize_text(text)
    if not clean:
        return []
    return [sentence.strip() for sentence in SENTENCE_RE.split(clean) if sentence.strip()]


def headline(text: str) -> str:
    """Return first meaningful line as headline."""

    for raw_line in (text or "").splitlines():
        line = raw_line.strip(" #\t-•")
        if line:
            return line[:180]
    return normalize_text(text)[:180]


def count_phrase(text: str, phrase: str) -> int:
    """Count a phrase in text with rough word boundaries."""

    return len(re.findall(rf"\b{re.escape(phrase)}\b", text.lower()))


def count_phrases(text: str, phrases: set[str]) -> int:
    """Count phrase matches from a set."""

    return sum(count_phrase(text, phrase) for phrase in phrases)


def clamp_score(value: float) -> float:
    """Clamp and half-round a 0-5 score."""

    return max(0.0, min(5.0, round(value * 2) / 2))


def score_from_penalties(base: float, penalties: float, bonuses: float = 0.0) -> float:
    """Calculate clamped score from base, penalties, and bonuses."""

    return clamp_score(base - penalties + bonuses)


def evidence(slide_num: int, text: str, evidence_type: str) -> StyleEvidence:
    """Build concise evidence pointer."""

    excerpt = headline(text) or normalize_text(text)[:160]
    return StyleEvidence(slide_ref=f"S{slide_num}", excerpt=excerpt[:180], evidence_type=evidence_type)


def deck_records(slides: Sequence[str | Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Normalize slide inputs to records with slide_num/text/headline."""

    records: list[dict[str, Any]] = []
    for index, slide in enumerate(slides):
        text = slide_text(slide)
        records.append({"slide_num": slide_number(index, slide), "text": text, "headline": headline(text), "words": tokenize(text)})
    return records


def config_value(config: Mapping[str, Any], key: str, default: Any) -> Any:
    """Get config value from dict-like object."""

    return config.get(key, default) if isinstance(config, Mapping) else default


def get_weight(config: Mapping[str, Any], dimension_id: str) -> float:
    """Return effective stylistic weight with config multiplier."""

    default_weight = float(STYLE_DIMENSIONS[dimension_id]["weight"])
    overrides = config_value(config, "stylistic_weight_overrides", {}) or {}
    try:
        multiplier = float(overrides.get(dimension_id, 1.0)) if isinstance(overrides, Mapping) else 1.0
    except (TypeError, ValueError):
        multiplier = 1.0
    return default_weight * max(0.0, min(3.0, multiplier))


def detect_numbers(text: str) -> int:
    """Count numeric anchors."""

    return len(re.findall(r"(?:\$\d[\d,.]*|\d+(?:\.\d+)?%?|\d+\s*(?:of|/|x)\s*\d+)", text))


def is_appendix(record: Mapping[str, Any]) -> bool:
    """Return true if slide appears to be appendix."""

    return "appendix" in str(record.get("text", "")).lower()[:120]


def score_punch(records: list[dict[str, Any]], mode: str, confidence: str) -> tuple[float, str, list[StyleEvidence], str, bool]:
    """Score punch/density."""

    core = [record for record in records if not is_appendix(record)] or records
    over_40 = [record for record in core if len(record["words"]) > 40]
    over_70 = [record for record in core if len(record["words"]) > 70]
    label_rate = sum(1 for record in core if record["headline"].strip().lower() in LABEL_HEADLINES) / max(1, len(core))
    throat = sum(count_phrases(record["text"], THROAT_CLEARING) for record in core)
    early = " ".join(record["text"] for record in core[:3]).lower()
    opening_signals = sum([
        bool(re.search(r"we (?:help|do|build|make|replace)", early)),
        any(noun in early for noun in CONCRETE_NOUNS),
        detect_numbers(early) > 0,
        any(phrase in early for phrase in ["what changed", "now", "because"]),
    ])
    penalties = len(over_40) * 0.35 + len(over_70) * 0.85 + max(0, throat - 3) * 0.25
    if label_rate > 0.4:
        penalties += 1.0
    if opening_signals < 2:
        penalties += 1.0
    if mode == "earnest_founder" and confidence in {"high", "medium"}:
        penalties *= 0.82
    if mode == "sharp_declarative" and confidence in {"high", "medium"}:
        penalties *= 1.18
    score = score_from_penalties(5.0, penalties)
    ev = [evidence(record["slide_num"], record["text"], "dense slide" if len(record["words"]) > 40 else "opening/headline signal") for record in (over_70 or over_40 or core[:2])[:3]]
    fix = "Rewrite the opening/core dense slides into claim headlines plus one proof point; move excess detail to appendix."
    reason = f"{len(over_40)} core slides exceed 40 words, {len(over_70)} exceed 70; label-headline rate {label_rate:.0%}; opening clarity signals {opening_signals}/4."
    return score, reason, ev, fix, confidence in {"high", "medium"}


def score_specificity(records: list[dict[str, Any]], mode: str, confidence: str) -> tuple[float, str, list[StyleEvidence], str, bool]:
    """Score specificity/quantification."""

    core = [record for record in records if not is_appendix(record)] or records
    number_count = sum(detect_numbers(record["text"]) for record in core)
    adjective_hits = sum(count_phrases(record["text"], HIGH_CLAIM_ADJECTIVES) for record in core)
    concrete_hits = sum(1 for record in core for word in record["words"] if word in CONCRETE_NOUNS)
    broad_customer = [record for record in core if re.search(r"\b(any company|every business|all teams|anyone who|everyone)\b", record["text"], re.I)]
    metric_named = [record for record in core if re.search(r"traction|market|growth|retention|cac|payback|demand", record["headline"], re.I)]
    metric_without_number = [record for record in metric_named if detect_numbers(record["text"]) == 0]
    proof_ratio = number_count + concrete_hits
    penalties = max(0, 5 - proof_ratio) * 0.35 + max(0, adjective_hits - number_count) * 0.25 + len(broad_customer) * 0.5 + len(metric_without_number) * 0.75
    if mode == "visionary_narrative" and confidence in {"high", "medium"} and concrete_hits == 0:
        penalties += 0.5
    bonuses = min(0.8, number_count * 0.12 + concrete_hits * 0.05)
    score = score_from_penalties(4.2, penalties, bonuses)
    ev_records = broad_customer or metric_without_number or core[:3]
    ev = [evidence(record["slide_num"], record["text"], "specificity signal") for record in ev_records[:3]]
    fix = "Replace adjectives and broad customer labels with numbers, concrete buyer/workflow nouns, or explicitly marked unknowns."
    reason = f"Found {number_count} numeric anchors, {concrete_hits} concrete noun hits, {adjective_hits} high-claim adjectives, {len(broad_customer)} broad-customer flags."
    return score, reason, ev, fix, confidence in {"high", "medium"}


def score_voice(records: list[dict[str, Any]], mode: str, confidence: str, voice_result: Mapping[str, Any]) -> tuple[float, str, list[StyleEvidence], str, bool]:
    """Score voice/register fit."""

    core = [record for record in records if not is_appendix(record)] or records
    hedge_count = sum(count_phrases(record["text"], set(HEDGES)) for record in core)
    swagger_count = sum(count_phrases(record["text"], {"own the market", "category-defining", "inevitable", "no one else", "winner-take-all", "revolutionary"}) for record in core)
    moralizing = sum(count_phrases(record["text"], MORALIZING) for record in core)
    long_sentences = sum(1 for record in core for sentence in split_sentences(record["text"]) if len(tokenize(sentence)) > 28)
    slide_modes = voice_result.get("slide_modes", []) if isinstance(voice_result, Mapping) else []
    mode_switches = len({item.get("assigned_mode") for item in slide_modes if isinstance(item, Mapping) and item.get("assigned_mode") not in {None, "ambiguous"}})
    penalties = long_sentences * 0.25 + swagger_count * 0.7 + moralizing * 0.5
    if mode == "mixed" or confidence == "low":
        penalties += 1.2
    if mode == "sharp_declarative" and confidence in {"high", "medium"}:
        penalties += hedge_count * 0.35
    elif mode == "earnest_founder" and confidence in {"high", "medium"}:
        penalties += max(0, hedge_count - 4) * 0.08
    else:
        penalties += hedge_count * 0.15
    if mode_switches >= 3:
        penalties += 0.75
    score = score_from_penalties(4.8, penalties)
    ev_records = core[: min(3, len(core))]
    ev = [evidence(record["slide_num"], record["text"], "voice/register sample") for record in ev_records]
    if mode == "mixed":
        fix = "Choose one dominant register for the core narrative, then reserve any mode shift for a clear proof or appendix section."
    elif mode == "earnest_founder":
        fix = "Keep honest learning language, but pair every belief or unknown with observed customer evidence."
    else:
        fix = "Align claim strength with proof: reduce unsupported swagger and use hedges only for true assumptions."
    reason = f"Voice detector returned {VOICE_MODE_LABELS.get(mode, mode)} ({confidence}); hedges {hedge_count}, swagger {swagger_count}, long sentences {long_sentences}, mode families {mode_switches}."
    return score, reason, ev, fix, confidence in {"high", "medium"}


def score_claim_hygiene(records: list[dict[str, Any]], mode: str, confidence: str) -> tuple[float, str, list[StyleEvidence], str, bool]:
    """Score claim hygiene."""

    core = [record for record in records if not is_appendix(record)] or records
    unsupported_superlatives = []
    belief_unbacked = []
    source_hits = 0
    for record in core:
        lower = record["text"].lower()
        proof_here = detect_numbers(record["text"]) > 0 or any(marker in lower for marker in PROOF_MARKERS)
        source_hits += sum(1 for marker in PROOF_MARKERS if marker in lower)
        if any(term in lower for term in SUPERLATIVES) and not proof_here:
            unsupported_superlatives.append(record)
        if re.search(r"\bwe (?:believe|think|expect)\b", lower) and not ("because" in lower or proof_here or "assumption" in lower or "hypothesis" in lower):
            belief_unbacked.append(record)
    risk_mentioned = any(any(term in record["text"].lower() for term in RISK_TERMS) for record in records)
    over_polish = sum(count_phrases(record["text"], BUZZWORDS | HIGH_CLAIM_ADJECTIVES) for record in core) > (source_hits + detect_numbers(" ".join(r["text"] for r in core)) + 4)
    penalties = len(unsupported_superlatives) * 0.8 + len(belief_unbacked) * 0.45 + (0 if risk_mentioned else 0.35) + (0.75 if over_polish else 0)
    if mode == "earnest_founder" and confidence in {"high", "medium"}:
        penalties -= min(0.5, len(belief_unbacked) * 0.2)
    score = score_from_penalties(4.4, max(0.0, penalties), min(0.6, source_hits * 0.05))
    ev_records = unsupported_superlatives or belief_unbacked or core[:3]
    ev = [evidence(record["slide_num"], record["text"], "claim hygiene signal") for record in ev_records[:3]]
    fix = "Label each major claim as fact, belief, plan, or hypothesis and put proof/source/assumption markers on the same slide."
    reason = f"Unsupported superlative slides {len(unsupported_superlatives)}, unbacked belief markers {len(belief_unbacked)}, source/proof marker hits {source_hits}, risk/competition mentioned={risk_mentioned}."
    return score, reason, ev, fix, confidence in {"high", "medium"}


def score_hierarchy(records: list[dict[str, Any]], mode: str, confidence: str) -> tuple[float, str, list[StyleEvidence], str, bool]:
    """Score hierarchy/scannability."""

    core = [record for record in records if not is_appendix(record)] or records
    labels = [record for record in core if record["headline"].strip().lower() in LABEL_HEADLINES]
    body_dominant = [record for record in core if len(record["words"]) > max(35, 5 * max(1, len(tokenize(record["headline"]))))]
    bullet_overload = [record for record in core if len(re.findall(r"(?:^|\n)\s*[-•*]", record["text"])) > 6]
    early = core[:5]
    early_proof = any(detect_numbers(record["text"]) > 0 or any(marker in record["text"].lower() for marker in PROOF_MARKERS) for record in early)
    headline_story = " ".join(record["headline"].lower() for record in core[:8])
    has_story_parts = sum([
        any(term in headline_story for term in ["why", "now", "changed", "problem"]),
        any(term in headline_story for term in ["we help", "product", "solution", "platform", "reviewer"]),
        any(term in headline_story for term in ["proof", "traction", "pilot", "customer", "signed"]),
        any(term in headline_story for term in ["market", "scale", "gtm", "ask", "milestone"]),
    ])
    penalties = len(labels) * 0.35 + len(body_dominant) * 0.35 + len(bullet_overload) * 0.4 + (0 if early_proof else 0.55) + max(0, 3 - has_story_parts) * 0.35
    if mode == "earnest_founder" and confidence in {"high", "medium"}:
        penalties *= 0.9
    score = score_from_penalties(4.6, penalties)
    ev_records = labels or body_dominant or bullet_overload or core[:3]
    ev = [evidence(record["slide_num"], record["text"], "hierarchy/scannability signal") for record in ev_records[:3]]
    fix = "Turn section labels into claim headlines and make proof visually/textually subordinate to one top claim per slide."
    reason = f"Label headlines {len(labels)}, body-dominant slides {len(body_dominant)}, overloaded bullet slides {len(bullet_overload)}, headline-story parts {has_story_parts}/4."
    return score, reason, ev, fix, confidence in {"high", "medium"}


def score_buzzwords(records: list[dict[str, Any]], mode: str, confidence: str) -> tuple[float, str, list[StyleEvidence], str, bool]:
    """Score anti-buzzword discipline."""

    core = [record for record in records if not is_appendix(record)] or records
    buzz_hits = sum(count_phrases(record["text"], BUZZWORDS) for record in core)
    abstract_hits = sum(1 for record in core for word in record["words"] if word in ABSTRACT_NOUNS)
    concrete_hits = sum(1 for record in core for word in record["words"] if word in CONCRETE_NOUNS)
    acronym_heavy = [record for record in core if len(re.findall(r"\b[A-Z]{2,}\b", record["text"])) > 5]
    adjective_stacks = [record for record in core if re.search(r"\b(?:\w+\s+){2,}(?:platform|solution|engine|ecosystem)\b", record["text"], re.I)]
    reusable = [record for record in core if re.search(r"empower .* unlock|unlock .* productivity|transform .* through ai|future of", record["text"], re.I)]
    penalties = buzz_hits * 0.22 + max(0, abstract_hits - concrete_hits) * 0.12 + len(acronym_heavy) * 0.35 + len(adjective_stacks) * 0.4 + len(reusable) * 0.5
    if mode == "sharp_declarative" and confidence in {"high", "medium"}:
        penalties *= 1.15
    if mode == "consultative_analytical" and confidence in {"high", "medium"}:
        penalties *= 0.92
    score = score_from_penalties(4.8, penalties, min(0.5, concrete_hits * 0.03))
    ev_records = reusable or adjective_stacks or acronym_heavy or core[:3]
    ev = [evidence(record["slide_num"], record["text"], "buzzword/abstraction signal") for record in ev_records[:3]]
    fix = "Replace category fog with the plain user-visible behavior: who does what, in which workflow, with what outcome."
    reason = f"Buzzword hits {buzz_hits}, abstract noun hits {abstract_hits}, concrete noun hits {concrete_hits}, acronym-heavy slides {len(acronym_heavy)}, adjective-stack slides {len(adjective_stacks)}."
    return score, reason, ev, fix, confidence in {"high", "medium"}


def score_cohesion(records: list[dict[str, Any]], mode: str, confidence: str, voice_result: Mapping[str, Any]) -> tuple[float, str, list[StyleEvidence], str, bool]:
    """Score narrative cohesion."""

    core = [record for record in records if not is_appendix(record)] or records
    all_words = [word for record in core for word in record["words"]]
    customer_hits = Counter(word for word in all_words if word in CONCRETE_NOUNS)
    top_customer_share = (customer_hits.most_common(1)[0][1] / max(1, sum(customer_hits.values()))) if customer_hits else 0.0
    feature_interruptions = [record for record in core if any(word in record["words"] for word in FEATURE_WORDS) and not any(word in record["words"] for word in CONCRETE_NOUNS)]
    connector_hits = sum(count_phrases(record["text"], CAUSAL_CONNECTORS) for record in core)
    has_ask = any("ask" in record["headline"].lower() or "use of funds" in record["text"].lower() or "raise" in record["text"].lower() for record in core)
    slide_modes = voice_result.get("slide_modes", []) if isinstance(voice_result, Mapping) else []
    assigned = [item.get("assigned_mode") for item in slide_modes if isinstance(item, Mapping) and item.get("assigned_mode") not in {None, "ambiguous"}]
    voice_churn = len(set(assigned)) >= 3 or mode == "mixed"
    penalties = (0.6 if top_customer_share and top_customer_share < 0.35 else 0.0) + len(feature_interruptions) * 0.45 + (0.5 if connector_hits == 0 and len(core) >= 4 else 0.0) + (0.35 if not has_ask and len(core) >= 8 else 0.0) + (0.8 if voice_churn else 0.0)
    if mode == "visionary_narrative" and confidence in {"high", "medium"} and top_customer_share == 0:
        penalties += 0.45
    score = score_from_penalties(4.4, penalties, min(0.5, connector_hits * 0.05))
    ev_records = feature_interruptions or core[:3]
    ev = [evidence(record["slide_num"], record["text"], "narrative cohesion signal") for record in ev_records[:3]]
    fix = "Make one through-line explicit: changed condition → customer pain → product wedge → proof → next milestone/ask."
    reason = f"Top customer/entity share {top_customer_share:.0%}, feature-list interruptions {len(feature_interruptions)}, causal connectors {connector_hits}, ask/milestone present={has_ask}, voice churn={voice_churn}."
    return score, reason, ev, fix, confidence in {"high", "medium"}


def call_optional_llm_style_check(_slides: Sequence[str | Mapping[str, Any]], _config: Mapping[str, Any]) -> None:
    """Reserved hook for optional external style verification.

    v1 intentionally performs no model call so tests and standalone runs are deterministic.
    """

    return None


def score_stylistic(slides: Sequence[str | Mapping[str, Any]], config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Score style independently from substantive scorecards.

    This interface is intentionally conservative for D4.1 orchestration:
    ``score_stylistic(slides, config) -> dict``. The function does not accept or
    inspect substantive scores.
    """

    config = config or {}
    records = deck_records(slides)
    voice = detect_voice_mode(slides, config)
    voice_dict = asdict(voice)
    mode = voice.mode
    confidence = voice.confidence
    scorers = {
        "punch_density": lambda: score_punch(records, mode, confidence),
        "specificity_quantification": lambda: score_specificity(records, mode, confidence),
        "voice_register_fit": lambda: score_voice(records, mode, confidence, voice_dict),
        "claim_hygiene": lambda: score_claim_hygiene(records, mode, confidence),
        "hierarchy_scannability": lambda: score_hierarchy(records, mode, confidence),
        "anti_buzzword_discipline": lambda: score_buzzwords(records, mode, confidence),
        "narrative_cohesion": lambda: score_cohesion(records, mode, confidence, voice_dict),
    }
    dimensions: list[StyleDimensionScore] = []
    total_points = 0.0
    total_weight = 0.0
    for dimension_id, run_scorer in scorers.items():
        score, reasoning, ev, fix, register_applied = run_scorer()
        weight = get_weight(config, dimension_id)
        weighted_points = (score / 5.0) * weight if weight else 0.0
        total_points += weighted_points
        total_weight += weight
        dimensions.append(
            StyleDimensionScore(
                dimension_id=dimension_id,
                label=STYLE_DIMENSIONS[dimension_id]["label"],
                score=score,
                weight_default=float(STYLE_DIMENSIONS[dimension_id]["weight"]),
                weight_effective=weight,
                weighted_points=round(weighted_points, 2),
                reasoning=reasoning,
                evidence=ev,
                register_applied=register_applied,
                top_fix=fix,
                confidence="medium" if records else "low",
                prompt_questions=PROMPT_QUESTIONS.get(dimension_id, []),
            )
        )
    style_score = round((total_points / total_weight) * 100, 1) if total_weight else 0.0
    ranked = sorted(dimensions, key=lambda item: item.score, reverse=True)
    strengths = [f"{item.label}: {item.reasoning}" for item in ranked[:3] if item.score >= 3.5]
    weaknesses = [f"{item.label}: {item.top_fix}" for item in sorted(dimensions, key=lambda item: item.score)[:3] if item.score <= 3.0]
    notes = []
    if mode == "mixed":
        notes.append("voice mode unclear or inconsistent; harsh register-specific penalties avoided except voice/cohesion inconsistency.")
    card = StylisticScorecard(
        detected_voice_mode=mode,
        voice_confidence=confidence,
        style_score=style_score,
        dimensions=dimensions,
        strengths=strengths[:3],
        weaknesses=weaknesses[:3],
        gap_flag=None,
        notes=notes,
    )
    return asdict(card)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""

    parser = argparse.ArgumentParser(description="Score pitch-deck style using deterministic D2.5 heuristics.")
    parser.add_argument("input", nargs="?", help="JSON, markdown, or text deck fixture")
    parser.add_argument("--config", help="Optional JSON config path")
    parser.add_argument("--out", help="Optional output JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Validate input/config without writing output")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""

    args = build_arg_parser().parse_args(argv)
    setup_logging(args.verbose)
    if not args.input:
        LOGGER.error("missing input path")
        return 1
    try:
        slides = load_slides(Path(args.input))
        config: dict[str, Any] = {}
        if args.config:
            config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        result = score_stylistic(slides, config)
        if args.dry_run:
            print(json.dumps({"dry_run": True, "slide_count": len(slides), "style_score_preview": result["style_score"]}, indent=2))
            return 0
        payload = json.dumps(result, indent=2)
        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(payload + "\n", encoding="utf-8")
            verify = json.loads(out_path.read_text(encoding="utf-8"))
            if "dimensions" not in verify:
                raise RuntimeError(f"State verification failed for {out_path}")
            LOGGER.info("wrote %s", out_path)
        else:
            print(payload)
        return 0
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        LOGGER.error("stylistic scoring failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
