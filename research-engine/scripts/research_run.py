#!/usr/bin/env python3
"""Research Engine Phase 3: self-driving research run pipeline.

Separate from research_engine.py on purpose: repo/ontology maintenance stays in the
main CLI, while run orchestration lives here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from profile_loader import load_profile, profile_get

WORKSPACE = Path(os.environ.get("ZO_WORKSPACE", "/home/workspace"))
REPO_ROOT = Path(os.environ.get("RESEARCH_ENGINE_ROOT", str(WORKSPACE / "Research" / "repos")))
ENGINE_ROOT = Path(os.environ.get("RESEARCH_ENGINE_STATE_ROOT", str(WORKSPACE / "Research" / "_engine")))
RUNS_DIR = ENGINE_ROOT / "runs"
MODES_DIR = ENGINE_ROOT / "modes"
EXA_SEARCH_URL = "https://api.exa.ai/search"
ZO_ASK_URL = "https://api.zo.computer/zo/ask"
DEFAULT_ZOASK_MODEL = os.environ.get("RESEARCH_ENGINE_ZOASK_MODEL", "openai:gpt-5.5-2026-04-23")
EXA_KEY_ENV_NAMES = ("EXA_N5OS_KEY", "EXA_API_KEY")
TEXT_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".csv"}
EXCLUDED_DIR_NAMES = {".git", ".venv", "node_modules", "__pycache__", "Trash", ".repair"}
CONTEXT_SCAN_ROOTS = (
    WORKSPACE / "Knowledge",
    WORKSPACE / "Research" / "repos",
    WORKSPACE / "Articles",
    WORKSPACE / "Personal" / "Meetings",
)
STOPWORDS = {
    "what", "which", "when", "where", "does", "from", "with", "about", "into", "that", "this",
    "research", "review", "analysis", "quick", "dirty", "please", "would", "could", "should",
}

DEPTHS: dict[str, dict[str, Any]] = {
    "one-shot": {
        "requires_approval": False,
        "clarification_policy": "none",
        "execution_policy": "always execute immediately; no questions; take the query at face value; infer broader user priorities from available context",
        "default_num_results": 5,
        "default_context_scan": True,
        "default_worker_drops": 2,
    },
    "quick": {
        "requires_approval": True,
        "clarification_policy": "summary approval only",
        "execution_policy": "create summary first; after approval, execute unattended",
        "default_num_results": 5,
    },
    "standard": {
        "requires_approval": True,
        "clarification_policy": "summary approval only",
        "execution_policy": "create summary first; after approval, execute unattended",
        "default_num_results": 8,
    },
    "deep": {
        "requires_approval": True,
        "clarification_policy": "summary approval only",
        "execution_policy": "create summary first; after approval, execute unattended",
        "default_num_results": 12,
    },
}

ISOLATED_SOURCE_MODES = {"diligence", "investor-diligence", "product-diligence"}
PRODUCT_DILIGENCE_DEFAULT_CRITERIA = [
    {"criterion": "Reliability / capture success", "default_weight": 25, "notes": "Does it consistently capture the needed event, audio, or workflow?"},
    {"criterion": "Output quality", "default_weight": 20, "notes": "Transcript accuracy, summary quality, searchability, and downstream usefulness."},
    {"criterion": "Workflow/export/API fit", "default_weight": 20, "notes": "Can the owner get audio, transcripts, notes, or records into the rest of their system?"},
    {"criterion": "Use-case fit / form factor", "default_weight": 15, "notes": "Does the product fit actual contexts of use and devices already carried?"},
    {"criterion": "Privacy/control", "default_weight": 10, "notes": "Cloud/local posture, retention, permissions, and policy clarity."},
    {"criterion": "Cost / lock-in", "default_weight": 10, "notes": "Hardware cost, subscription, cancellation, and export friction."},
]
_VENTURE = profile_get("venture_name", "the venture")
ISOLATED_SOURCE_POLICY = (
    "External/company/person evidence first. Do not use prior internal outputs, meeting artifacts, "
    "or internal strategy documents unless they involve the same stakeholder/company/fund/vendor/entity, "
    "or the owner explicitly asked to include that internal context. Clearly distinguish internal workspace retrieval "
    "from ordinary web/Exa/LinkedIn/app-integration sources."
)

DEFAULT_MODE_REGISTRY: dict[str, dict[str, Any]] = {
    "literature-review": {
        "label": "Literature Review",
        "objective": "Objective review of scientific or academic literature.",
        "sections": ["Question", "Search Strategy", "Evidence Table", "Consensus", "Disagreements", "Limitations", "Open Questions"],
        "exa_num_results": {"one-shot": 4, "quick": 5, "standard": 8, "deep": 12},
    },
    "market-research": {
        "label": "Market Research",
        "objective": "Market, company, category, and ecosystem analysis.",
        "sections": ["Question", "Landscape", "Players", "Evidence", "Signals", "Uncertainties", "Next Moves"],
        "exa_num_results": {"one-shot": 4, "quick": 6, "standard": 10, "deep": 15},
    },
    "diligence": {
        "label": "Diligence",
        "objective": "Person, organization, opportunity, or risk diligence.",
        "sections": ["Question", "Recommendation", "Positive Evidence", "Risks", "Red Flags", "Unknowns", "Reference Checks"],
        "exa_num_results": {"one-shot": 4, "quick": 6, "standard": 10, "deep": 15},
    },
    "investor-diligence": {
        "label": "Investor Diligence",
        "objective": f"Manual {_VENTURE} investor/VC diligence for fund, partner, portfolio, discourse, intro-path, and strategic-fit prep.",
        "sections": [
            "Invocation Context",
            "Bottom Line",
            "Investor/Fund Snapshot",
            "Partner/Decision-Maker Map",
            "Investment Thesis And Pattern",
            "Deeptech/Robotics/Physical-AI Fit",
            "Portfolio Classification",
            "Competitive Or Complementary Portcos",
            "Public Discourse And X Signals",
            "LinkedIn And Mutual Intro Paths",
            "Relevant Private History Summary",
            "Venture Fit And Narrative Hooks",
            "Risks, Conflicts, And Red Flags",
            "Questions To Ask",
            "Follow-Up Moves",
            "Source Scope / Tool Provenance",
        ],
        "exa_num_results": {"one-shot": 6, "quick": 8, "standard": 12, "deep": 18},
        "brief_sizes": ["skim", "standard", "full-dossier"],
        "brief_size_default": "standard",
    },
    "product-diligence": {
        "label": "Product Diligence",
        "objective": "Research a specific product, service, or product category; surface objective reviews, decision tradeoffs, and ranked recommendations after preference discovery.",
        "sections": [
            "Invocation Context",
            "Bottom Line Recommendation",
            "Preference Profile And Assumptions",
            "Socratic Preference Interview",
            "Category Map And Product Archetypes",
            "Candidate Shortlist",
            "Ranking Criteria And Weights",
            "Ranked Product Table",
            "Product Deep Dives",
            "Objective Review Evidence And Source Quality Notes",
            "Common Complaints And Failure Modes",
            "Privacy, Subscription, And Lock-In Analysis",
            "Workflow/API/Export Analysis",
            "Decision Recommendation",
            "Next Test Plan",
            "Source Scope / Tool Provenance",
        ],
        "exa_num_results": {"one-shot": 6, "quick": 8, "standard": 14, "deep": 22},
        "brief_sizes": ["skim", "standard", "full-dossier"],
        "brief_size_default": "standard",
    },
    "knowledge-scan": {
        "label": "Knowledge Scan",
        "objective": "Mine explicitly provided/local-authorized sources for relevant extracts.",
        "sections": ["Question", "Local Sources", "Relevant Prior Knowledge", "Candidate Extracts", "Promotion Candidates"],
        "exa_num_results": {"one-shot": 3, "quick": 4, "standard": 6, "deep": 10},
    },
    "explainer": {
        "label": "Explainer",
        "objective": "Create a structured primer and map the topic into the ontology.",
        "sections": ["Question", "Plain-English Explanation", "Key Concepts", "Examples", "Misconceptions", "Further Reading"],
        "exa_num_results": {"one-shot": 5, "quick": 5, "standard": 8, "deep": 12},
    },
    "strategy-research": {
        "label": "Strategy Research",
        "objective": "Research in service of a decision, options, or strategic recommendation.",
        "sections": ["Question", "Decision Context", "Options", "Evidence", "Tradeoffs", "Recommendation", "Assumptions"],
        "exa_num_results": {"one-shot": 4, "quick": 6, "standard": 10, "deep": 15},
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "topic"


def safe_relative(path: Path, base: Path = WORKSPACE) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path)


def emit(data: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(data, indent=2, sort_keys=True))
    return code


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_mode_registry() -> list[str]:
    MODES_DIR.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    for mode, body in DEFAULT_MODE_REGISTRY.items():
        path = MODES_DIR / f"{mode}.json"
        if path.exists():
            continue
        write_json(path, {"mode": mode, "version": "1.0", **body})
        created.append(safe_relative(path))
    return created


def merge_mode_defaults(mode: str, data: dict[str, Any]) -> dict[str, Any]:
    if mode not in DEFAULT_MODE_REGISTRY:
        return data
    merged = {"mode": mode, "version": "1.0", **DEFAULT_MODE_REGISTRY[mode], **data}
    default_counts = DEFAULT_MODE_REGISTRY[mode].get("exa_num_results")
    persisted_counts = data.get("exa_num_results")
    if isinstance(default_counts, dict):
        counts = dict(default_counts)
        if isinstance(persisted_counts, dict):
            counts.update(persisted_counts)
        if mode == "explainer" and int(counts.get("one-shot", 0)) < 5:
            counts["one-shot"] = 5
        merged["exa_num_results"] = counts
    return merged


def load_mode(mode: str) -> dict[str, Any]:
    ensure_mode_registry()
    path = MODES_DIR / f"{mode}.json"
    if path.exists():
        data = load_json(path, {})
        if data:
            return merge_mode_defaults(mode, data)
    if mode in DEFAULT_MODE_REGISTRY:
        return {"mode": mode, "version": "1.0", **DEFAULT_MODE_REGISTRY[mode]}
    raise ValueError(f"unknown mode: {mode}")


def query_topic_slug(query: str, explicit: str | None = None) -> str:
    if explicit:
        return slugify(explicit)
    tokens = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if t not in STOPWORDS and len(t) > 2]
    return slugify("-".join(tokens[:6]) or query[:50])


def make_run_id(query: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    digest = hashlib.sha256(query.encode("utf-8")).hexdigest()[:8]
    return f"run_{stamp}_{digest}"


def run_dir(run_id: str) -> Path:
    return RUNS_DIR / run_id


def topic_dir(topic_slug: str) -> Path:
    return REPO_ROOT / topic_slug


def source_id(uri: str, title: str = "") -> str:
    return "src_" + hashlib.sha256(f"{uri}\u241f{title}".encode()).hexdigest()[:16]


def extract_id(src_id: str, text: str) -> str:
    return "ext_" + hashlib.sha256(f"{src_id}\u241f{text}".encode()).hexdigest()[:16]


def claim_id(ext_id: str, claim: str) -> str:
    return "claim_" + hashlib.sha256(f"{ext_id}\u241f{claim}".encode()).hexdigest()[:16]


def get_exa_key() -> str | None:
    for name in EXA_KEY_ENV_NAMES:
        val = os.environ.get(name)
        if val:
            return val
    return None


def exa_search(query: str, num_results: int) -> list[dict[str, Any]]:
    fake = os.environ.get("RESEARCH_ENGINE_FAKE_EXA_RESULTS")
    if fake:
        return json.loads(fake)
    key = get_exa_key()
    if not key:
        raise RuntimeError("External search requires EXA_N5OS_KEY or EXA_API_KEY, unless sources are explicitly provided.")
    body = json.dumps({"query": query, "type": "auto", "numResults": num_results, "text": True}).encode()
    req = urllib.request.Request(
        EXA_SEARCH_URL,
        data=body,
        headers={"x-api-key": key, "content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise RuntimeError(f"Exa search failed HTTP {exc.code}: {detail}") from exc
    return data.get("results", []) if isinstance(data.get("results"), list) else []


def clean_html_text(raw: str) -> str:
    text = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", text).strip()


def fetch_url_text(url: str, max_chars: int = 12000) -> str:
    fake = os.environ.get("RESEARCH_ENGINE_FAKE_URL_TEXTS")
    if fake:
        mapped = json.loads(fake)
        return str(mapped.get(url, ""))[:max_chars]
    req = urllib.request.Request(url, headers={"user-agent": "Zo Research Engine/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            content_type = resp.headers.get("content-type", "")
            raw = resp.read(max_chars * 4)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return ""
    if "pdf" in content_type.lower():
        return ""
    decoded = raw.decode("utf-8", errors="replace")
    if "html" in content_type.lower() or "<html" in decoded[:1000].lower():
        return clean_html_text(decoded)[:max_chars]
    return re.sub(r"\s+", " ", decoded).strip()[:max_chars]


def enrich_source_text(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("text"):
        return row
    uri = str(row.get("uri", ""))
    if uri.startswith(("http://", "https://")):
        fetched = fetch_url_text(uri)
        if fetched:
            enriched = dict(row)
            enriched["text"] = fetched
            enriched["text_source"] = "url_fetch"
            return enriched
    return row


def text_excerpt(text: str, max_chars: int = 900) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    return clean[:max_chars].rstrip()


def match_score(text: str, terms: list[str]) -> int:
    lower = text.lower()
    return sum(lower.count(term) for term in terms)


def targeted_context_scan(query: str, max_files: int = 8) -> list[dict[str, Any]]:
    if os.environ.get("RESEARCH_ENGINE_FAKE_EXA_RESULTS") or os.environ.get("RESEARCH_ENGINE_DISABLE_CONTEXT_SCAN"):
        return []
    terms = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 3 and t not in STOPWORDS]
    if not terms:
        return []
    candidates: list[tuple[int, Path, str]] = []
    for root in CONTEXT_SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
                continue
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            rel = safe_relative(path)
            path_score = match_score(rel, terms) * 3
            try:
                text = path.read_text(encoding="utf-8", errors="replace")[:12000]
            except OSError:
                continue
            score = path_score + match_score(text, terms)
            if score <= 0:
                continue
            candidates.append((score, path, text))
    candidates.sort(key=lambda item: item[0], reverse=True)
    hits: list[dict[str, Any]] = []
    for score, path, text in candidates[:max_files]:
        hits.append({
            "uri": safe_relative(path, WORKSPACE),
            "title": path.name,
            "text": text_excerpt(text, 3000),
            "type": "context_scan",
            "score": score,
            "provided": False,
        })
    return hits


def read_explicit_source(raw: str) -> dict[str, Any]:
    if raw.startswith("http://") or raw.startswith("https://"):
        return {"uri": raw, "title": raw, "text": "", "type": "url_reference", "provided": True}
    path = Path(raw)
    if not path.is_absolute():
        path = WORKSPACE / raw
    resolved = path.resolve()
    if not str(resolved).startswith(str(WORKSPACE.resolve())):
        raise ValueError(f"source path must be under workspace: {raw}")
    if not resolved.exists():
        raise FileNotFoundError(f"source file not found: {raw}")
    if resolved.suffix.lower() not in TEXT_SUFFIXES:
        return {"uri": safe_relative(resolved), "title": resolved.name, "text": "", "type": "file_reference", "provided": True}
    text = resolved.read_text(encoding="utf-8", errors="replace")[:8000]
    return {"uri": safe_relative(resolved), "title": resolved.name, "text": text, "type": "file", "provided": True}


def local_workspace_scan(query: str, max_files: int = 30) -> list[dict[str, Any]]:
    terms = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 3 and t not in STOPWORDS]
    if not terms:
        return []
    hits: list[dict[str, Any]] = []
    roots = [WORKSPACE / "Research", WORKSPACE / "Knowledge", WORKSPACE / "Personal" / "Knowledge"]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if len(hits) >= max_files:
                return hits
            if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
                continue
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            rel = safe_relative(path)
            hay = rel.lower()
            if not any(term in hay for term in terms):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")[:4000]
            hits.append({"uri": rel, "title": path.name, "text": text, "type": "local_scan", "provided": False})
    return hits


def approved_content_library_scan(query: str, max_files: int = 6) -> list[dict[str, Any]]:
    root = WORKSPACE / profile_get("content_library_root", "Knowledge/content-library")
    if os.environ.get("RESEARCH_ENGINE_DISABLE_CONTENT_LIBRARY_SCAN"):
        return []
    if not root.exists():
        return []
    venture_terms = [t.lower() for t in [profile_get("venture_name", "")] + list(profile_get("venture_aliases", [])) if t]
    primary_term = venture_terms[0] if venture_terms else ""
    terms = list(venture_terms) + [t.lower() for t in profile_get("focus_terms", [])]
    terms.extend(t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 4 and t not in STOPWORDS)
    excluded_path_terms = tuple(t.lower() for t in profile_get("exclusion_terms", []))
    candidates: list[tuple[int, Path, str]] = []
    for path in root.rglob("*"):
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel = safe_relative(path, WORKSPACE)
        if excluded_path_terms and any(term in rel.lower() for term in excluded_path_terms):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")[:12000]
        except OSError:
            continue
        hay = f"{rel}\n{text}".lower()
        score = sum(hay.count(term) for term in terms)
        if primary_term and primary_term in hay:
            score += 5
        if "/positions/" in rel:
            score += 3
        if score <= 0:
            continue
        candidates.append((score, path, text))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "uri": safe_relative(path, WORKSPACE),
            "title": path.name,
            "text": text_excerpt(text, 3500),
            "type": "approved_content_library",
            "score": score,
            "provided": False,
        }
        for score, path, text in candidates[:max_files]
    ]




def plan_for(query: str, mode: str, depth: str, topic: str | None, sources: list[str], allow_local_scan: bool, brief_size: str | None = None) -> dict[str, Any]:
    if depth not in DEPTHS:
        raise ValueError(f"unknown depth: {depth}")
    mode_data = load_mode(mode)
    depth_data = DEPTHS[depth]
    counts = mode_data.get("exa_num_results", {}) if isinstance(mode_data.get("exa_num_results"), dict) else {}
    worker_drops = int(depth_data.get("default_worker_drops", 0)) if depth == "one-shot" else 0
    context_scan = bool(depth_data.get("default_context_scan", False)) if depth == "one-shot" else False
    source_scope = "standard_context_scan"
    source_policy = "Use explicitly provided resources first. Use Exa for external search when needed. For one-shot, run a targeted context scan across Knowledge/Research/Articles/recent meeting artifacts without asking; broad local workspace scan still requires --allow-local-scan."
    mode_extras: dict[str, Any] = {}
    if mode in ISOLATED_SOURCE_MODES:
        context_scan = False
        source_scope = "external_first_no_unrelated_internal_context"
        source_policy = ISOLATED_SOURCE_POLICY
    if mode == "investor-diligence":
        requested_brief_size = brief_size or mode_data.get("brief_size_default") or "standard"
        allowed_brief_sizes = mode_data.get("brief_sizes") or ["skim", "standard", "full-dossier"]
        if requested_brief_size not in allowed_brief_sizes:
            raise ValueError(f"unknown investor-diligence brief size: {requested_brief_size}")
        source_scope = "investor_diligence_external_plus_approved_internal"
        source_policy = (
            f"Manual investor/VC diligence. External fund/person/portfolio evidence first; always include approved evergreen "
            f"{_VENTURE} internal links and Content Library-derived context when needed. Do not use accelerator applications, application-specific "
            "materials, unrelated Research folders, or broad workspace owner-venture search. Meeting/calendar context is optional, not required. "
            "Private email use is summary-only with subject/date/source-account traceability. LinkedIn should be used for profiles, org/member "
            "signals, mutuals, and possible intro paths when available; otherwise label public-web fallback limitations. X/public discourse should "
            "be searched for what the investor publicly supports or talks about."
        )
        mode_extras = {
            "manual_trigger_only": True,
            "meeting_required": False,
            "default_lookahead_days": 14,
            "priority_window_hours": 72,
            "allowed_calendar_accounts": list(profile_get("allowed_calendar_accounts", [])),
            "excluded_calendar_accounts": list(profile_get("excluded_calendar_accounts", [])),
            "allowed_private_email_accounts": list(profile_get("allowed_private_email_accounts", [])),
            "private_email_policy": "Summaries only. Include subject line, date, counterparty, and source account for traceability. Do not dump full private email bodies into the brief.",
            "internal_context_policy": f"Use only approved {_VENTURE} Content Library material and evergreen internal source links. Do not use accelerator applications, application-specific materials, unrelated Research folders, or broad workspace owner-venture search.",
            "evergreen_internal_sources": list(profile_get("evergreen_internal_sources", [])),
            "content_library_policy": f"Search {profile_get('content_library_root', 'Knowledge/content-library')} for approved {_VENTURE} positions/context when needed; prefer canonical/position material and exclude applications unless explicitly approved.",
            "linkedin_policy": "Use connected LinkedIn actions where available for organization/member/profile signals and intro-path discovery; otherwise use public web-visible LinkedIn evidence and label limitations.",
            "x_discourse_policy": "Search X/public discourse for investor theses, portfolio support, robotics/deeptech/physical-AI commentary, and founder-facing tone; cite posts/accounts used.",
            "portfolio_classification_schema": [
                {"class": "competitive", "meaning": f"Could conflict with or compete against {_VENTURE}", "requires_rationale": True},
                {"class": "complementary", "meaning": f"Could partner with, buy from, or strengthen {_VENTURE}", "requires_rationale": True},
                {"class": "channel", "meaning": "Could open customers, hospitals, labs, robotics buyers, or strategic distribution", "requires_rationale": True},
                {"class": "capital", "meaning": "Signals fund capacity, follow-on behavior, syndicate quality, or relevant co-investors", "requires_rationale": True},
                {"class": "future-buyer", "meaning": "Potential acquirer, strategic partner, or downstream data buyer", "requires_rationale": True},
                {"class": "irrelevant", "meaning": f"No meaningful {_VENTURE} adjacency found", "requires_rationale": True},
                {"class": "unknown", "meaning": "Insufficient evidence", "requires_rationale": True},
            ],
            "brief_size": requested_brief_size,
            "brief_size_default": mode_data.get("brief_size_default", "standard"),
        }
    if mode == "product-diligence":
        requested_brief_size = brief_size or mode_data.get("brief_size_default") or "standard"
        allowed_brief_sizes = mode_data.get("brief_sizes") or ["skim", "standard", "full-dossier"]
        if requested_brief_size not in allowed_brief_sizes:
            raise ValueError(f"unknown product-diligence brief size: {requested_brief_size}")
        context_scan = False
        source_scope = "external_product_reviews_first_with_preference_discovery"
        source_policy = (
            "Product/category diligence. Use public external evidence first: hands-on professional reviews with methodology, "
            "customer reviews with volume/recency, forum reports with concrete first-hand usage details, independent comparisons, "
            "product documentation, API/support docs, pricing pages, privacy policies, changelogs, and public discourse. Treat affiliate "
            "listicles and vendor marketing as weak evidence unless corroborated. Do not use internal workspace notes unless explicitly "
            "provided via --source or --allow-local-scan. Never purchase, sign up, send outbound messages, or mutate external state without explicit owner approval."
        )
        mode_extras = {
            "manual_trigger_only": True,
            "socratic_preference_discovery": depth != "one-shot",
            "one_shot_preference_behavior": "Do not pause for questions; state preference assumptions and rank with confidence caveats.",
            "preference_discovery_policy": "Run an initial category scan, then ask a short Socratic interview focused on the tradeoffs that matter for this category before final ranking unless depth is one-shot.",
            "source_quality_order": [
                "hands-on professional reviews with stated testing methods",
                "customer reviews from retailer/app-store/SaaS marketplaces with volume and recency",
                "forum/community first-hand reports with concrete failure details",
                "independent comparison articles with methodology",
                "product documentation, support docs, API docs, pricing pages, privacy policies, and changelogs",
                "founder/company announcements for roadmap, availability, and policy claims",
                "social discourse as weak signal unless it contains concrete first-hand usage evidence",
            ],
            "default_ranking_criteria": PRODUCT_DILIGENCE_DEFAULT_CRITERIA,
            "dispositions": ["buy", "trial", "watch", "avoid", "not-enough-evidence"],
            "persona_lenses": [
                {"lens": "teacher", "use": "Explain unfamiliar category concepts and tradeoffs plainly."},
                {"lens": "builder", "use": "Inspect API/export/workflow feasibility."},
                {"lens": "debugger", "use": "Stress-test failure modes and reliability claims."},
                {"lens": "strategist", "use": "Make the final decision recommendation and opportunity-cost tradeoffs."},
            ],
            "brief_size": requested_brief_size,
            "brief_size_default": mode_data.get("brief_size_default", "standard"),
        }
    return {
        "query": query,
        "mode": mode,
        "mode_label": mode_data.get("label", mode),
        "depth": depth,
        "topic_slug": query_topic_slug(query, topic),
        "requires_approval": depth_data["requires_approval"],
        "clarification_policy": depth_data["clarification_policy"],
        "execution_policy": depth_data["execution_policy"],
        "unattended_after_approval": True,
        "local_workspace_scan_authorized": bool(allow_local_scan),
        "context_scan_authorized": context_scan,
        "source_scope": source_scope,
        "source_policy": source_policy,
        "provided_sources": sources,
        "exa_num_results": int(counts.get(depth, depth_data["default_num_results"])),
        "zoask_worker_drops": worker_drops,
        "zoask_model": DEFAULT_ZOASK_MODEL if worker_drops else None,
        "sections": mode_data.get("sections", []),
        **mode_extras,
    }

def initial_run(query: str, mode: str, depth: str, topic: str | None, sources: list[str], allow_local_scan: bool, brief_size: str | None = None) -> dict[str, Any]:
    rid = make_run_id(query)
    plan = plan_for(query, mode, depth, topic, sources, allow_local_scan, brief_size)
    return {
        "run_id": rid,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "status": "ready_to_execute" if depth == "one-shot" else "awaiting_approval",
        "approval_required": depth != "one-shot",
        "approved_at": None,
        "plan": plan,
    }


def render_run_md(run: dict[str, Any]) -> str:
    plan = run["plan"]
    return f"""---
created: {today()}
last_edited: {today()}
version: 1.0
provenance: research-engine
---

# Research Run: {run['run_id']}

**Status:** {run['status']}
**Query:** {plan['query']}
**Mode:** {plan['mode_label']} (`{plan['mode']}`)
**Depth:** {plan['depth']}
**Approval required:** {run['approval_required']}
**Local workspace scan authorized:** {plan['local_workspace_scan_authorized']}

## Contract

- `one-shot` always executes immediately with no approval and no clarification questions.
- Non-one-shot depths pause after this summary; `approve-run` executes unattended.
- Explicit sources are used first.
- Local workspace scan is forbidden unless `--allow-local-scan` was passed at run creation.
- Phase 3 never writes to `Knowledge/`.
"""


def render_summary(run: dict[str, Any]) -> str:
    plan = run["plan"]
    sections = "\n".join(f"- {s}" for s in plan.get("sections", []))
    sources = "\n".join(f"- {s}" for s in plan.get("provided_sources", [])) or "- (none provided)"
    return f"""---
created: {today()}
last_edited: {today()}
version: 1.0
provenance: research-engine
---

# Summary for Approval: {run['run_id']}

**Query:** {plan['query']}
**Mode:** {plan['mode_label']} (`{plan['mode']}`)
**Depth:** {plan['depth']}
**Execution policy:** {plan['execution_policy']}
**Exa target results:** {plan['exa_num_results']}
**Targeted context scan authorized:** {plan.get('context_scan_authorized', False)}
**Zoask worker drops:** {plan.get('zoask_worker_drops', 0)}
**Local workspace scan authorized:** {plan['local_workspace_scan_authorized']}

## Provided Resources

{sources}

## Planned Sections

{sections}

## Approval Behavior

If approved with `approve-run`, this run proceeds fully unattended. No additional clarification loop is required.
"""


def save_run_state(run: dict[str, Any]) -> None:
    d = run_dir(run["run_id"])
    d.mkdir(parents=True, exist_ok=True)
    write_json(d / "PLAN.json", run["plan"])
    write_json(d / "STATE.json", run)
    write_text(d / "RUN.md", render_run_md(run))
    write_text(d / "SUMMARY.md", render_summary(run))
    for name in ["SOURCES.jsonl", "EXTRACTS.jsonl", "CLAIMS.jsonl", "WORKER_DROPS.jsonl", "PROMOTION_CANDIDATES.jsonl"]:
        p = d / name
        if not p.exists():
            write_text(p, "")


def load_run(run_id: str) -> dict[str, Any]:
    p = run_dir(run_id) / "STATE.json"
    if not p.exists():
        raise FileNotFoundError(f"run not found: {run_id}")
    return load_json(p, {})


def collect_sources(plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in plan.get("provided_sources", []):
        rows.append(read_explicit_source(raw))
    if plan.get("mode") == "investor-diligence":
        for raw in plan.get("evergreen_internal_sources", []):
            rows.append(read_explicit_source(raw))
        rows.extend(approved_content_library_scan(plan["query"]))
    if plan.get("context_scan_authorized"):
        rows.extend(targeted_context_scan(plan["query"]))
    if plan.get("local_workspace_scan_authorized"):
        rows.extend(local_workspace_scan(plan["query"]))
    internal_only_types = {"url_reference", "file_reference", "approved_content_library"}
    external_rows = [r for r in rows if r.get("type") not in internal_only_types]
    if not external_rows or len(external_rows) < 2:
        for item in exa_search(plan["query"], int(plan["exa_num_results"])):
            rows.append({
                "uri": item.get("url", ""),
                "title": item.get("title") or item.get("url", "Untitled"),
                "text": item.get("text") or "",
                "type": "exa",
                "published_date": item.get("publishedDate"),
                "provided": False,
            })
    return [enrich_source_text(row) for row in rows]

def first_sentence(text: str) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if not clean:
        return "Source referenced; no extractable text captured."
    parts = re.split(r"(?<=[.!?])\s+", clean)
    return parts[0][:500]


def zoask_token() -> str | None:
    return os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")


def build_worker_prompt(plan: dict[str, Any], worker_index: int, sources: list[dict[str, Any]], extracts: list[dict[str, Any]]) -> str:
    source_brief = "\n".join(
        f"- {src.get('title', 'Untitled')} — {src.get('uri', '')}\n  excerpt: {extracts[i].get('text', '')[:350] if i < len(extracts) else ''}"
        for i, src in enumerate(sources[:8])
    ) or "- No sources captured yet."
    emphasis = "evidence gaps, trend surfaces, and missing source angles" if worker_index == 1 else "decision-grade synthesis and practical implications"
    source_policy = plan.get("source_policy") or "Use explicit and externally verifiable sources first."
    mode_context_keys = [
        "brief_size", "manual_trigger_only", "meeting_required", "allowed_calendar_accounts",
        "excluded_calendar_accounts", "allowed_private_email_accounts", "private_email_policy",
        "internal_context_policy", "evergreen_internal_sources", "content_library_policy",
        "linkedin_policy", "x_discourse_policy", "portfolio_classification_schema",
        "socratic_preference_discovery", "one_shot_preference_behavior", "preference_discovery_policy",
        "source_quality_order", "default_ranking_criteria", "dispositions", "persona_lenses",
    ]
    mode_context = "\n".join(
        f"- {key}: {json.dumps(plan[key], ensure_ascii=False)}"
        for key in mode_context_keys
        if key in plan
    ) or "- No mode-specific context."
    return f"""You are a Zo Research Engine one-shot worker drop. Work fast, but be source-grounded.

Question:
{plan['query']}

Your focus: {emphasis}.

Source policy:
{source_policy}

Mode-specific context:
{mode_context}

Use your available tools if useful, including web/search, LinkedIn, connected apps, or X search for trend/pattern discovery when relevant. Do not send outbound messages or mutate external state. Cite URLs or workspace source paths for any evidence you rely on. For investor diligence, do not broadly search the workspace for the owner's venture; use only approved Content Library sources and evergreen links unless the owner explicitly authorizes more. For product diligence, prioritize independent reviews, customer/community evidence, product docs, pricing/privacy/API/support docs, and concrete first-hand usage reports over vendor marketing; include Socratic preference questions when the depth is not one-shot.

Known sources from the coordinator:
{source_brief}

Return:
1. 5-8 evidence-backed bullets.
2. A short "what this changes" section.
3. Source list with URLs or workspace paths.
"""


def run_zoask_workers(plan: dict[str, Any], sources: list[dict[str, Any]], extracts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if os.environ.get("RESEARCH_ENGINE_FAKE_EXA_RESULTS") or os.environ.get("RESEARCH_ENGINE_DISABLE_ZOASK_WORKERS"):
        return []
    count = min(int(plan.get("zoask_worker_drops") or 0), 2)
    token = zoask_token()
    if count <= 0 or not token:
        return []
    drops: list[dict[str, Any]] = []
    for idx in range(count):
        prompt = build_worker_prompt(plan, idx, sources, extracts)
        body = {"input": prompt, "model_name": plan.get("zoask_model") or DEFAULT_ZOASK_MODEL}
        req = urllib.request.Request(
            ZO_ASK_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={"authorization": token, "content-type": "application/json", "accept": "application/json"},
            method="POST",
        )
        started = now_iso()
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            drops.append({"worker": idx + 1, "status": "complete", "started_at": started, "completed_at": now_iso(), "model": body["model_name"], "output": data.get("output", "")})
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:700]
            drops.append({"worker": idx + 1, "status": "failed", "started_at": started, "completed_at": now_iso(), "model": body["model_name"], "error": f"HTTP {exc.code}: {detail}"})
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            drops.append({"worker": idx + 1, "status": "failed", "started_at": started, "completed_at": now_iso(), "model": body["model_name"], "error": str(exc)})
    return drops


def execute_run(run: dict[str, Any]) -> dict[str, Any]:
    plan = run["plan"]
    d = run_dir(run["run_id"])
    tdir = topic_dir(plan["topic_slug"])
    tdir.mkdir(parents=True, exist_ok=True)

    raw_sources = collect_sources(plan)
    sources: list[dict[str, Any]] = []
    extracts: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = []

    for raw in raw_sources:
        sid = source_id(raw.get("uri", ""), raw.get("title", ""))
        srow = {
            "kind": "source",
            "source_id": sid,
            "type": raw.get("type", "unknown"),
            "title": raw.get("title", "Untitled"),
            "uri": raw.get("uri", ""),
            "retrieved_at": now_iso(),
            "provenance": f"research-engine:{run['run_id']}",
            "provided": bool(raw.get("provided")),
            "text_source": raw.get("text_source", "provided_text" if raw.get("text") else "metadata_only"),
        }
        sources.append(srow)
        etext = first_sentence(raw.get("text", ""))
        eid = extract_id(sid, etext)
        extracts.append({
            "kind": "extract",
            "extract_id": eid,
            "source_id": sid,
            "text": etext,
            "locator": raw.get("uri", ""),
            "provenance": f"research-engine:{run['run_id']}",
        })
        claim = f"Relevant source for: {plan['query']} — {srow['title']}"
        claims.append({
            "kind": "claim",
            "claim_id": claim_id(eid, claim),
            "claim": claim,
            "supporting_extracts": [eid],
            "confidence": "medium" if raw.get("text") else "low",
            "status": "open",
            "provenance": f"research-engine:{run['run_id']}",
        })

    write_text(d / "SOURCES.jsonl", "")
    write_text(d / "EXTRACTS.jsonl", "")
    write_text(d / "CLAIMS.jsonl", "")
    append_jsonl(d / "SOURCES.jsonl", sources)
    append_jsonl(d / "EXTRACTS.jsonl", extracts)
    append_jsonl(d / "CLAIMS.jsonl", claims)
    append_jsonl(tdir / "SOURCES.jsonl", sources)
    append_jsonl(tdir / "EXTRACTS.jsonl", extracts)
    append_jsonl(tdir / "CLAIMS.jsonl", claims)

    worker_drops = run_zoask_workers(plan, sources, extracts)
    write_text(d / "WORKER_DROPS.jsonl", "")
    if worker_drops:
        append_jsonl(d / "WORKER_DROPS.jsonl", worker_drops)

    synthesis = render_synthesis(run, sources, extracts, claims, worker_drops)
    write_text(d / "SYNTHESIS.md", synthesis)
    write_text(tdir / "INDEX.md", render_topic_index(plan, sources, claims))

    run["status"] = "complete"
    run["updated_at"] = now_iso()
    run["completed_at"] = now_iso()
    run["artifact_paths"] = {
        "run_dir": safe_relative(d),
        "synthesis": safe_relative(d / "SYNTHESIS.md"),
        "topic_index": safe_relative(tdir / "INDEX.md"),
    }
    save_run_state(run)
    return run


def render_cited_sources(sources: list[dict[str, Any]]) -> tuple[str, str]:
    lines: list[str] = []
    footnotes: list[str] = []
    for idx, source in enumerate(sources, start=1):
        title = source.get("title", "Untitled")
        uri = source.get("uri", "")
        stype = source.get("type", "unknown")
        retrieval = source.get("text_source", "provided_text" if source.get("text") else "metadata_only")
        lines.append(f"- {title} [^{idx}] — `{stype}`, `{retrieval}`")
        footnotes.append(f"[^{idx}]: {uri}")
    return "\n".join(lines) or "- No sources captured.", "\n".join(footnotes)


def render_worker_drops(worker_drops: list[dict[str, Any]]) -> str:
    if not worker_drops:
        return "- No Zoask worker drops completed or worker execution was unavailable."
    rows = []
    for drop in worker_drops:
        status = drop.get("status", "unknown")
        if status == "complete":
            output = str(drop.get("output", "")).strip()[:3000]
            rows.append(f"### Worker {drop.get('worker')} — complete\n\n{output}")
        else:
            rows.append(f"### Worker {drop.get('worker')} — failed\n\n`{drop.get('error', 'unknown error')}`")
    return "\n\n".join(rows)


def render_synthesis(run: dict[str, Any], sources: list[dict[str, Any]], extracts: list[dict[str, Any]], claims: list[dict[str, Any]], worker_drops: list[dict[str, Any]] | None = None) -> str:
    plan = run["plan"]
    source_lines, footnotes = render_cited_sources(sources)
    extract_lines = "\n".join(f"- {e['text']}" for e in extracts[:12]) or "- No extracts captured."
    claim_lines = "\n".join(f"- **{c['confidence']}**: {c['claim']}" for c in claims[:12]) or "- No claims captured."
    worker_lines = render_worker_drops(worker_drops or [])
    citation_block = f"\n\n{footnotes}" if footnotes else ""
    return f"""---
created: {today()}
last_edited: {today()}
version: 1.0
provenance: research-engine
---

# Synthesis: {plan['query']}

**Mode:** {plan['mode']}
**Depth:** {plan['depth']}
**Targeted context scan authorized:** {plan.get('context_scan_authorized', False)}
**Zoask worker drops requested:** {plan.get('zoask_worker_drops', 0)}
**Local workspace scan authorized:** {plan['local_workspace_scan_authorized']}

## Sources Consulted

{source_lines}

## Extracts

{extract_lines}

## Working Claims

{claim_lines}

## Zoask Worker Drops

{worker_lines}

## Limitations

- This Phase 3 synthesis is evidence-led and citation-bearing; it does not promote anything to Knowledge.
- Claims are working research claims, not pure Knowledge.
- One-shot runs prioritize speed, but they must still expose source coverage, citation provenance, extraction failures, and any worker-drop failures.
{citation_block}
"""

def render_topic_index(plan: dict[str, Any], sources: list[dict[str, Any]], claims: list[dict[str, Any]]) -> str:
    source_lines = "\n".join(f"- {s['title']} — `{s['uri']}`" for s in sources[:20]) or "- None yet."
    claim_lines = "\n".join(f"- {c['claim']}" for c in claims[:20]) or "- None yet."
    return f"""---
created: {today()}
last_edited: {today()}
version: 1.0
provenance: research-engine
---

# {plan['topic_slug'].replace('-', ' ').title()}

This `INDEX.md` is a Research Engine topic view rendered in place. It is **not** Knowledge.

## Current Question

{plan['query']}

## Sources

{source_lines}

## Working Claims

{claim_lines}

## Knowledge Boundary

Nothing on this page is promoted to `Knowledge/` without an explicit promotion command.
"""


def cmd_modes(args: argparse.Namespace) -> int:
    created = ensure_mode_registry()
    modes = [p.stem for p in sorted(MODES_DIR.glob("*.json"))]
    return emit({"ok": True, "created": created, "modes": modes})


def cmd_run(args: argparse.Namespace) -> int:
    run = initial_run(args.query, args.mode, args.depth, args.topic, args.source or [], bool(args.allow_local_scan), getattr(args, "brief_size", None))
    save_run_state(run)
    if args.depth == "one-shot":
        run = execute_run(run)
    return emit({
        "ok": True,
        "run_id": run["run_id"],
        "topic_slug": run.get("plan", {}).get("topic_slug"),
        "status": run["status"],
        "approval_required": run["approval_required"],
        "summary": safe_relative(run_dir(run["run_id"]) / "SUMMARY.md"),
        "run_dir": safe_relative(run_dir(run["run_id"])),
        "artifacts": run.get("artifact_paths", {}),
    })


def cmd_approve_run(args: argparse.Namespace) -> int:
    run = load_run(args.run_id)
    if run.get("status") == "complete":
        return emit({"ok": True, "run_id": args.run_id, "topic_slug": run.get("plan", {}).get("topic_slug"), "status": "complete", "already_complete": True, "artifacts": run.get("artifact_paths", {})})
    run["approved_at"] = now_iso()
    run["status"] = "approved"
    save_run_state(run)
    run = execute_run(run)
    return emit({"ok": True, "run_id": args.run_id, "topic_slug": run.get("plan", {}).get("topic_slug"), "status": run["status"], "artifacts": run.get("artifact_paths", {})})


def cmd_run_status(args: argparse.Namespace) -> int:
    run = load_run(args.run_id)
    return emit({
        "ok": True,
        "run_id": args.run_id,
        "topic_slug": run.get("plan", {}).get("topic_slug"),
        "status": run.get("status"),
        "approval_required": run.get("approval_required"),
        "approved_at": run.get("approved_at"),
        "artifacts": run.get("artifact_paths", {}),
    })


def register_run_subcommands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    p = sub.add_parser("modes", help="Initialize/list research run modes")
    p.set_defaults(func=cmd_modes)

    p = sub.add_parser("run", help="Create a research run; one-shot executes immediately")
    p.add_argument("--query", required=True)
    p.add_argument("--mode", default="explainer", choices=sorted(DEFAULT_MODE_REGISTRY))
    p.add_argument("--depth", default="standard", choices=sorted(DEPTHS))
    p.add_argument("--topic")
    p.add_argument("--source", action="append", help="Explicit source path or URL; may be repeated")
    p.add_argument("--brief-size", choices=["skim", "standard", "full-dossier"], help="Investor/product diligence brief size; defaults to standard for those modes")
    p.add_argument("--allow-local-scan", action="store_true", help="Authorize local workspace scan; otherwise forbidden")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("approve-run", help="Approve and execute a waiting research run unattended")
    p.add_argument("--run-id", required=True)
    p.set_defaults(func=cmd_approve_run)

    p = sub.add_parser("run-status", help="Show research run status")
    p.add_argument("--run-id", required=True)
    p.set_defaults(func=cmd_run_status)
