#!/usr/bin/env python3
"""Research Engine: deterministic research-repository and compendium maintenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from research_run import register_run_subcommands
from research_promotion import register_promotion_subcommands
from profile_loader import profile_get

WORKSPACE = Path(os.environ.get("ZO_WORKSPACE", "/home/workspace"))
ROOT = Path(os.environ.get("RESEARCH_ENGINE_ROOT", str(WORKSPACE / "Research" / "repos")))
REGISTRY_PATH = ROOT / "registry.json"
REGISTRY_MD_PATH = ROOT / "REGISTRY.md"
COMPENDIUM_PATH = ROOT / "COMPENDIUM.md"
REPAIR_DIR = ROOT / ".repair"
FAILED_APPENDS_PATH = REPAIR_DIR / "FAILED_APPENDS.jsonl"
DEFAULT_SCAN_ROOTS = [WORKSPACE / "Research", WORKSPACE / "Knowledge", WORKSPACE / "Personal" / "Knowledge"]
EXCLUDED_DIR_NAMES = {".git", ".venv", "node_modules", "__pycache__", ".repair", "repos", "Trash"}
TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".jsonl", ".csv"}
STOPWORDS = {
    "source", "sources", "research", "market", "markets", "workspace", "home", "file", "files",
    "note", "notes", "dossier", "report", "reports", "archive", "archives", "draft", "drafts",
    "tmp", "temp", "test", "smoke", "meeting", "summary", "final", "package", "index",
    "the", "and", "for", "with", "from", "that", "this", "into", "your", "you", "are",
    "was", "were", "have", "has", "not", "but", "about",
}

# ---------------------------------------------------------------------------
# Ontology engine paths (Phase 2). Engine state lives under Research/_engine,
# independent of where research repos/topic folders live.
# ---------------------------------------------------------------------------
ENGINE_ROOT = Path(os.environ.get("RESEARCH_ENGINE_STATE_ROOT", str(WORKSPACE / "Research" / "_engine")))
ONTOLOGY_DIR = ENGINE_ROOT / "ontology"
ONTOLOGY_REGISTRY_PATH = ONTOLOGY_DIR / "registry.json"
ONTOLOGY_OVERLAY_PATH = ONTOLOGY_DIR / "personal_overlay.jsonl"
ONTOLOGY_MAPPINGS_PATH = ONTOLOGY_DIR / "mappings.jsonl"
ONTOLOGY_CACHE_PATH = ONTOLOGY_DIR / "cache" / "wikidata.jsonl"
# Knowledge ontology is referenced by path, never written by research runs.
KNOWLEDGE_ONTOLOGY_DIR = WORKSPACE / "Knowledge" / "semantic-memory" / "ontology"

ONTOLOGY_NODE_KINDS = {"concept", "entity", "domain", "method", "market", "person", "org", "technology"}


def _build_personal_overlay_seed() -> list[dict[str, Any]]:
    """Personal overlay seed, derived from the active profile (no hardcoded identity)."""
    seed: list[dict[str, Any]] = []
    venture = profile_get("venture_name", "")
    if venture:
        seed.append({
            "label": venture,
            "kind": "org",
            "aliases": list(profile_get("venture_aliases", [])),
            "notes": profile_get("venture_notes", "Owner's venture."),
        })
    seed.extend([
        {"label": "AI Fluency", "kind": "concept", "aliases": ["ai fluency", "agentic fluency"], "notes": "Observed-skill framing."},
        {"label": "Agentic Research Behavior", "kind": "method", "aliases": ["agentic research", "observed research behavior"], "notes": "How an operator actually researches through an agent."},
    ])
    for node in profile_get("overlay_extra_nodes", []):
        if isinstance(node, dict) and node.get("label"):
            seed.append(node)
    return seed


PERSONAL_OVERLAY_SEED = _build_personal_overlay_seed()

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
logger = logging.getLogger("research-engine")


# ---------------------------------------------------------------------------
# Schema validation (stdlib only; Phase 1 primitive contracts)
# ---------------------------------------------------------------------------

CONFIDENCE_VALUES = {"low", "medium", "high"}
CLAIM_STATUS_VALUES = {"open", "supported", "contested", "refuted", "promoted"}
REVIEW_STATUS_VALUES = {"proposed", "approved", "rejected", "promoted"}

# Required fields per primitive kind. Provenance is required everywhere.
SCHEMA_REQUIRED: dict[str, list[str]] = {
    "source": ["source_id", "type", "title", "retrieved_at", "provenance"],
    "extract": ["extract_id", "source_id", "text", "provenance"],
    "claim": ["claim_id", "claim", "supporting_extracts", "confidence", "status", "provenance"],
    "topic": ["topic_id", "slug", "title", "folder", "provenance"],
    "synthesis": ["topic_id", "mode", "generated_at", "inputs", "provenance"],
    "promotion_candidate": [
        "candidate_id", "topic_id", "target", "claim_ids", "rationale", "review_status", "provenance",
    ],
}


def validate_record(record: Any) -> list[str]:
    """Return a list of human-readable validation errors (empty == valid)."""
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["record is not a JSON object"]
    kind = record.get("kind")
    if kind not in SCHEMA_REQUIRED:
        return [f"unknown kind: {kind!r} (expected one of {sorted(SCHEMA_REQUIRED)})"]
    for field in SCHEMA_REQUIRED[kind]:
        if field not in record or record[field] in (None, "", []):
            errors.append(f"missing required field: {field}")
    if kind == "claim":
        if record.get("confidence") not in CONFIDENCE_VALUES:
            errors.append(f"confidence must be one of {sorted(CONFIDENCE_VALUES)}")
        if record.get("status") not in CLAIM_STATUS_VALUES:
            errors.append(f"status must be one of {sorted(CLAIM_STATUS_VALUES)}")
        if not isinstance(record.get("supporting_extracts"), list):
            errors.append("supporting_extracts must be a list")
    if kind == "promotion_candidate":
        if record.get("review_status") not in REVIEW_STATUS_VALUES:
            errors.append(f"review_status must be one of {sorted(REVIEW_STATUS_VALUES)}")
        target = record.get("target") or ""
        if not str(target).startswith("Knowledge/"):
            errors.append("target must be under Knowledge/ (Knowledge purity gate)")
        if not isinstance(record.get("claim_ids"), list):
            errors.append("claim_ids must be a list")
    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate one or more primitive records against Phase 1 schemas."""
    paths: list[Path] = []
    if args.path:
        for raw in args.path:
            p = Path(raw)
            if p.is_dir():
                paths.extend(sorted(p.rglob("*.json")))
            else:
                paths.append(p)
    results = []
    all_valid = True
    for p in paths:
        if not p.exists():
            results.append({"path": str(p), "valid": False, "errors": ["file not found"]})
            all_valid = False
            continue
        try:
            record = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            results.append({"path": str(p), "valid": False, "errors": [f"json_decode_error: {exc}"]})
            all_valid = False
            continue
        errs = validate_record(record)
        results.append({"path": safe_relative(p), "valid": not errs, "errors": errs})
        if errs:
            all_valid = False
    return emit({"ok": True, "all_valid": all_valid, "count": len(results), "results": results})


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "research-repo"


def safe_relative(path: Path, base: Path = WORKSPACE) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path)


def emit(data: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(data, indent=2, sort_keys=True))
    return code


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Could not parse JSON %s: %s", path, exc)
        return default
    except OSError as exc:
        logger.warning("Could not read %s: %s", path, exc)
        return default


def load_registry() -> dict[str, Any]:
    data = load_json(REGISTRY_PATH, {"version": "1.0", "repos": []})
    data.setdefault("version", "1.0")
    data.setdefault("repos", [])
    return data


def verify_file(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"write verification failed: {path}")


def write_text_verified(path: Path, content: str, *, dry_run: bool = False) -> None:
    if dry_run:
        logger.info("DRY-RUN write skipped: %s", path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    verify_file(path)


def write_json_verified(path: Path, data: dict[str, Any], *, dry_run: bool = False) -> None:
    write_text_verified(path, json.dumps(data, indent=2, sort_keys=True) + "\n", dry_run=dry_run)


def render_registry_md(registry: dict[str, Any], *, dry_run: bool = False) -> None:
    lines = [
        "---",
        f"created: {today()}",
        f"last_edited: {today()}",
        "version: 1.0",
        "provenance: research-engine",
        "---",
        "",
        "# Research Repository Registry",
        "",
        "| Repo ID | Title | Status | Path | Objective |",
        "|---|---|---|---|---|",
    ]
    for repo in sorted(registry.get("repos", []), key=lambda r: r.get("repo_id", "")):
        lines.append(
            f"| {repo.get('repo_id', '')} | {repo.get('title', '')} | {repo.get('status', '')} | {repo.get('path', '')} | {repo.get('objective', '')} |"
        )
    write_text_verified(REGISTRY_MD_PATH, "\n".join(lines) + "\n", dry_run=dry_run)


def write_registry(registry: dict[str, Any], *, dry_run: bool = False) -> None:
    registry["updated_at"] = now_iso()
    write_json_verified(REGISTRY_PATH, registry, dry_run=dry_run)
    render_registry_md(registry, dry_run=dry_run)


def find_repo(registry: dict[str, Any], repo_id: str) -> dict[str, Any] | None:
    return next((repo for repo in registry.get("repos", []) if repo.get("repo_id") == repo_id), None)


def repo_id_for(index: int | None = None) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    existing = load_registry().get("repos", [])
    if index is None:
        nums = []
        for repo in existing:
            rid = repo.get("repo_id", "")
            if rid.startswith(f"repo_{stamp}_"):
                try:
                    nums.append(int(rid.rsplit("_", 1)[1]))
                except ValueError:
                    pass
        index = (max(nums) if nums else 0) + 1
    return f"repo_{stamp}_{index:03d}"


def repo_dir(repo: dict[str, Any]) -> Path:
    path = repo.get("path")
    if path:
        p = Path(path)
        if p.is_absolute():
            return p
        parts = p.parts
        if len(parts) >= 3 and parts[0] == "Research" and parts[1] == "repos":
            return ROOT.joinpath(*parts[2:])
        return ROOT / p
    return ROOT / slugify(repo.get("title", repo.get("repo_id", "repo")))


def init_repo_files(repo: dict[str, Any], *, dry_run: bool = False) -> list[str]:
    d = repo_dir(repo)
    intake = d / "INTAKE.jsonl"
    compact = d / "COMPACT.md"
    readme = d / "README.md"
    files = [str(intake), str(compact), str(readme)]
    if dry_run:
        logger.info("DRY-RUN repo init skipped: %s", d)
        return files
    d.mkdir(parents=True, exist_ok=True)
    if not intake.exists():
        write_text_verified(intake, "")
    if not compact.exists():
        write_text_verified(
            compact,
            "---\n"
            f"created: {today()}\n"
            f"last_edited: {today()}\n"
            "version: 1.0\n"
            "provenance: research-engine\n"
            "---\n\n"
            f"# {repo.get('title', repo.get('repo_id'))}: Compact\n\n"
            f"**Objective:** {repo.get('objective', '')}\n\n"
            "## Current Synthesis\n\nNo compacted findings yet.\n",
        )
    if not readme.exists():
        write_text_verified(
            readme,
            "---\n"
            f"created: {today()}\n"
            f"last_edited: {today()}\n"
            "version: 1.0\n"
            "provenance: research-engine\n"
            "---\n\n"
            f"# {repo.get('title', repo.get('repo_id'))}\n\n"
            f"**Repo ID:** `{repo.get('repo_id')}`\n\n"
            f"**Status:** {repo.get('status')}\n\n"
            f"**Objective:** {repo.get('objective', '')}\n\n"
            "## Files\n\n"
            "- `INTAKE.jsonl` — append-only raw findings.\n"
            "- `COMPACT.md` — periodic synthesis.\n",
        )
    return files


def make_dedupe_key(repo_id: str, source: str, source_ref: str, summary: str, payload: dict[str, Any]) -> str:
    payload_text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    raw = "\u241f".join([repo_id, source, source_ref, summary, payload_text])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def intake_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    if not path.exists():
        return keys
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("dedupe_key"):
            keys.add(item["dedupe_key"])
    return keys


def iter_intake_entries(repo: dict[str, Any]) -> Iterable[dict[str, Any]]:
    intake = repo_dir(repo) / "INTAKE.jsonl"
    if not intake.exists():
        return []
    entries = []
    for line in intake.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            logger.warning("Skipping malformed intake line in %s", intake)
    return entries


def log_failed_append(failure: dict[str, Any], *, dry_run: bool = False) -> None:
    if dry_run:
        logger.info("DRY-RUN failed append log skipped: %s", failure.get("reason"))
        return
    REPAIR_DIR.mkdir(parents=True, exist_ok=True)
    with FAILED_APPENDS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(failure, sort_keys=True) + "\n")
    verify_file(FAILED_APPENDS_PATH)


def append_entry(repo_id: str, source: str, source_ref: str, summary: str, payload: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    registry = load_registry()
    repo = find_repo(registry, repo_id)
    if not repo:
        failure = {"timestamp": now_iso(), "repo_id": repo_id, "source": source, "source_ref": source_ref, "summary": summary, "payload": payload, "reason": "repo_not_found"}
        log_failed_append(failure, dry_run=dry_run)
        return {"ok": False, "error": "repo_not_found", "repair_logged": not dry_run, "dry_run": dry_run, "failure": failure}
    if repo.get("status") != "active":
        failure = {"timestamp": now_iso(), "repo_id": repo_id, "source": source, "source_ref": source_ref, "summary": summary, "payload": payload, "reason": f"repo_status_{repo.get('status', 'unknown')}"}
        log_failed_append(failure, dry_run=dry_run)
        return {"ok": False, "error": "repo_not_active", "repair_logged": not dry_run, "dry_run": dry_run, "failure": failure}
    init_repo_files(repo, dry_run=dry_run)
    intake = repo_dir(repo) / "INTAKE.jsonl"
    dedupe_key = make_dedupe_key(repo_id, source, source_ref, summary, payload)
    if dedupe_key in intake_keys(intake):
        return {"ok": True, "repo_id": repo_id, "dedupe_key": dedupe_key, "status": "duplicate_skipped", "path": str(intake)}
    entry = {"timestamp": now_iso(), "repo_id": repo_id, "source": source, "source_ref": source_ref, "summary": summary, "payload": payload, "dedupe_key": dedupe_key}
    if not dry_run:
        with intake.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        verify_file(intake)
        repo["last_append_at"] = entry["timestamp"]
        repo["append_count"] = int(repo.get("append_count", 0)) + 1
        write_registry(registry)
    return {"ok": True, "repo_id": repo_id, "dedupe_key": dedupe_key, "status": "would_append" if dry_run else "appended", "dry_run": dry_run, "path": str(intake)}


def should_skip_dir(path: Path) -> bool:
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", text.lower()) if t not in STOPWORDS]


def read_text_sample(path: Path, max_chars: int = 4000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return ""


def first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def scan_folder(root: Path, *, max_files: int = 500, max_depth: int = 5) -> dict[str, Any]:
    root = root.resolve()
    files = []
    folders: Counter[str] = Counter()
    terms: Counter[str] = Counter()
    headings = []
    scanned = 0
    if not root.exists():
        return {"root": str(root), "exists": False, "files": [], "file_count": 0, "top_terms": [], "headings": [], "folders": []}
    for path in sorted(root.rglob("*")):
        rel_parts = path.relative_to(root).parts
        if len(rel_parts) > max_depth or should_skip_dir(path):
            continue
        if path.is_dir():
            folders[path.name] += 1
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        scanned += 1
        if scanned > max_files:
            break
        text = read_text_sample(path)
        heading = first_heading(text)
        if heading:
            headings.append({"path": safe_relative(path), "heading": heading})
        for token in tokenize(" ".join(path.parts[-4:]) + " " + text[:1200]):
            terms[token] += 1
        files.append({"path": safe_relative(path), "suffix": path.suffix.lower(), "bytes": path.stat().st_size, "heading": heading})
    return {
        "root": str(root),
        "exists": True,
        "file_count": len(files),
        "files": files,
        "folders": folders.most_common(40),
        "top_terms": terms.most_common(60),
        "headings": headings[:80],
        "truncated": scanned > max_files,
    }


def build_suggestions(scans: list[dict[str, Any]], *, limit: int = 10) -> list[dict[str, Any]]:
    aggregate: Counter[str] = Counter()
    evidence: dict[str, list[str]] = {}
    for scan in scans:
        for term, count in scan.get("top_terms", [])[:40]:
            aggregate[term] += int(count)
        for item in scan.get("files", [])[:120]:
            text = " ".join(tokenize(f"{item.get('path', '')} {item.get('heading') or ''}"))
            for token in text.split():
                evidence.setdefault(token, [])
                if len(evidence[token]) < 5:
                    evidence[token].append(item.get("path", ""))
    suggestions = []
    for term, score in aggregate.most_common(limit * 3):
        if term in STOPWORDS or len(term) < 4:
            continue
        title = term.replace("-", " ").title()
        suggestions.append({
            "title": title,
            "slug": slugify(title),
            "score": score,
            "objective": f"Maintain a compendium of evidence, claims, and open questions related to {title}.",
            "evidence_paths": evidence.get(term, [])[:5],
        })
        if len(suggestions) >= limit:
            break
    return suggestions


def render_compendium(registry: dict[str, Any]) -> str:
    lines = [
        "---",
        f"created: {today()}",
        f"last_edited: {today()}",
        "version: 1.0",
        "provenance: research-engine",
        "---",
        "",
        "# Research Compendium",
        "",
        "This is the wiki-style index for active research repositories. It is generated from `registry.json`, repo `README.md`, repo `COMPACT.md`, and append counts.",
        "",
        "## Active Repositories",
        "",
    ]
    repos = sorted(registry.get("repos", []), key=lambda r: (r.get("status", ""), r.get("title", "")))
    if not repos:
        lines.append("No repositories registered yet.")
    for repo in repos:
        d = repo_dir(repo)
        compact_rel = safe_relative(d / "COMPACT.md")
        intake_count = len(list(iter_intake_entries(repo))) if d.exists() else 0
        lines.extend([
            f"### {repo.get('title', repo.get('repo_id'))}",
            "",
            f"- **Repo ID:** `{repo.get('repo_id')}`",
            f"- **Status:** {repo.get('status', 'unknown')}",
            f"- **Objective:** {repo.get('objective', '')}",
            f"- **Path:** `{safe_relative(d)}`",
            f"- **Compact:** `{compact_rel}`",
            f"- **Intake entries:** {intake_count}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def load_failed_appends() -> list[dict[str, Any]]:
    if not FAILED_APPENDS_PATH.exists():
        return []
    items = []
    for line in FAILED_APPENDS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            items.append({"malformed": line, "reason": "json_decode_error"})
    return items


def write_failed_appends(items: list[dict[str, Any]], *, dry_run: bool = False) -> None:
    content = "".join(json.dumps(item, sort_keys=True) + "\n" for item in items)
    write_text_verified(FAILED_APPENDS_PATH, content, dry_run=dry_run)


def parse_payload_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    data = json.loads(value)
    if not isinstance(data, dict):
        raise ValueError("payload-json must decode to an object")
    return data


def cmd_scan(args: argparse.Namespace) -> int:
    roots = [Path(p) for p in (args.roots or [])] or DEFAULT_SCAN_ROOTS
    scans = [scan_folder(root, max_files=args.max_files, max_depth=args.max_depth) for root in roots]
    result = {"ok": True, "scanned_at": now_iso(), "roots": [str(r) for r in roots], "scans": scans, "suggestions": build_suggestions(scans, limit=args.suggestion_limit)}
    if args.output:
        write_json_verified(Path(args.output), result, dry_run=args.dry_run)
        result["output"] = args.output
    return emit(result)


def cmd_suggest(args: argparse.Namespace) -> int:
    if args.scan_json:
        data = load_json(Path(args.scan_json), {})
        scans = data.get("scans", [])
    else:
        roots = [Path(p) for p in (args.roots or [])] or DEFAULT_SCAN_ROOTS
        scans = [scan_folder(root, max_files=args.max_files, max_depth=args.max_depth) for root in roots]
    suggestions = build_suggestions(scans, limit=args.limit)
    if args.proposals_dir:
        out_dir = Path(args.proposals_dir)
        for suggestion in suggestions:
            content = (
                "---\n"
                f"created: {today()}\n"
                f"last_edited: {today()}\n"
                "version: 1.0\n"
                "provenance: research-engine\n"
                "---\n\n"
                f"# Research Repo Proposal: {suggestion['title']}\n\n"
                f"**Objective:** {suggestion['objective']}\n\n"
                f"**Score:** {suggestion['score']}\n\n"
                "## Evidence Paths\n\n"
                + "\n".join(f"- `{p}`" for p in suggestion.get("evidence_paths", []))
                + "\n"
            )
            write_text_verified(out_dir / f"{suggestion['slug']}.md", content, dry_run=args.dry_run)
    return emit({"ok": True, "suggestions": suggestions, "dry_run": args.dry_run})


def cmd_compendium(args: argparse.Namespace) -> int:
    registry = load_registry()
    content = render_compendium(registry)
    target = Path(args.output) if args.output else COMPENDIUM_PATH
    write_text_verified(target, content, dry_run=args.dry_run)
    return emit({"ok": True, "path": str(target), "repo_count": len(registry.get("repos", [])), "dry_run": args.dry_run})


def cmd_propose(args: argparse.Namespace) -> int:
    registry = load_registry()
    rid = args.repo_id or repo_id_for()
    if find_repo(registry, rid):
        return emit({"ok": False, "error": "repo_exists", "repo_id": rid})
    title = args.title.strip()
    rel_path = args.path or f"Research/repos/{slugify(title)}"
    repo = {"repo_id": rid, "title": title, "objective": args.objective.strip(), "status": "proposed", "path": rel_path, "created_at": now_iso(), "append_count": 0, "tags": args.tags or []}
    registry["repos"].append(repo)
    write_registry(registry, dry_run=args.dry_run)
    return emit({"ok": True, "repo_id": repo["repo_id"], "repo": repo, "dry_run": args.dry_run})


def cmd_activate(args: argparse.Namespace) -> int:
    registry = load_registry()
    repo = find_repo(registry, args.repo_id)
    if not repo:
        return emit({"ok": False, "error": "repo_not_found", "repo_id": args.repo_id})
    repo["status"] = "active"
    repo["activated_at"] = now_iso()
    init_repo_files(repo, dry_run=args.dry_run)
    write_registry(registry, dry_run=args.dry_run)
    return emit({"ok": True, "repo_id": repo["repo_id"], "repo": repo, "path": str(repo_dir(repo)), "dry_run": args.dry_run})


def cmd_list(args: argparse.Namespace) -> int:
    registry = load_registry()
    repos = registry.get("repos", [])
    if args.status:
        repos = [r for r in repos if r.get("status") == args.status]
    return emit({"ok": True, "repos": repos, "count": len(repos)})


def cmd_show(args: argparse.Namespace) -> int:
    registry = load_registry()
    repo = find_repo(registry, args.repo_id)
    if not repo:
        return emit({"ok": False, "error": "repo_not_found", "repo_id": args.repo_id})
    d = repo_dir(repo)
    intake = d / "INTAKE.jsonl"
    return emit({"ok": True, "repo": repo, "path": str(d), "intake_exists": intake.exists(), "intake_count": len(intake_keys(intake))})


def cmd_append(args: argparse.Namespace) -> int:
    try:
        payload = parse_payload_json(args.payload_json)
    except (json.JSONDecodeError, ValueError) as exc:
        return emit({"ok": False, "error": "invalid_payload_json", "message": str(exc)})
    result = append_entry(args.repo_id, args.source, args.source_ref, args.summary, payload, dry_run=args.dry_run)
    return emit(result)


def cmd_compact(args: argparse.Namespace) -> int:
    registry = load_registry()
    repo = find_repo(registry, args.repo_id)
    if not repo:
        return emit({"ok": False, "error": "repo_not_found", "repo_id": args.repo_id})
    init_repo_files(repo, dry_run=args.dry_run)
    entries = list(iter_intake_entries(repo))
    lines = [
        "---",
        f"created: {today()}",
        f"last_edited: {today()}",
        "version: 1.0",
        "provenance: research-engine",
        "---",
        "",
        f"# {repo.get('title', args.repo_id)}: Compact",
        "",
        f"**Objective:** {repo.get('objective', '')}",
        "",
        f"**Entries compacted:** {len(entries)}",
        "",
        "## Findings",
        "",
    ]
    for entry in entries[-args.limit :]:
        lines.append(f"- {entry.get('summary', '')} _(source: {entry.get('source', '')}; ref: {entry.get('source_ref', '')})_")
    compact = repo_dir(repo) / "COMPACT.md"
    write_text_verified(compact, "\n".join(lines) + "\n", dry_run=args.dry_run)
    if not args.dry_run:
        repo["last_compacted_at"] = now_iso()
        write_registry(registry)
    return emit({"ok": True, "repo_id": args.repo_id, "entries": len(entries), "path": str(compact), "dry_run": args.dry_run})


def cmd_repair_status(args: argparse.Namespace) -> int:
    items = load_failed_appends()
    reasons: dict[str, int] = {}
    for item in items:
        reason = item.get("reason", "unknown")
        reasons[reason] = reasons.get(reason, 0) + 1
    return emit({"ok": True, "failed_appends_path": str(FAILED_APPENDS_PATH), "count": len(items), "reasons": reasons})


def cmd_repair_sweep(args: argparse.Namespace) -> int:
    failures = load_failed_appends()
    remaining = []
    repaired = []
    for failure in failures:
        if failure.get("malformed"):
            remaining.append(failure)
            continue
        result = {"ok": False, "dry_run": True, "repo_id": failure.get("repo_id"), "reason": failure.get("reason")} if args.dry_run else append_entry(failure.get("repo_id", ""), failure.get("source", "repair"), failure.get("source_ref", ""), failure.get("summary", ""), failure.get("payload", {}))
        if result.get("ok") and not args.dry_run:
            repaired.append({"failure": failure, "result": result})
        else:
            remaining.append(failure)
    if not args.dry_run:
        write_failed_appends(remaining)
    return emit({"ok": True, "dry_run": bool(args.dry_run), "attempted": len(failures), "repaired": len(repaired), "remaining": len(remaining)})


# ---------------------------------------------------------------------------
# Ontology engine (Phase 2)
# ---------------------------------------------------------------------------

def load_ontology_registry() -> dict[str, Any]:
    data = load_json(ONTOLOGY_REGISTRY_PATH, {"version": "1.0", "nodes": []})
    data.setdefault("version", "1.0")
    data.setdefault("nodes", [])
    return data


def save_ontology_registry(registry: dict[str, Any], *, dry_run: bool = False) -> None:
    write_json_verified(ONTOLOGY_REGISTRY_PATH, registry, dry_run=dry_run)


def load_overlay() -> list[dict[str, Any]]:
    if not ONTOLOGY_OVERLAY_PATH.exists():
        return []
    items = []
    for line in ONTOLOGY_OVERLAY_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return items


def write_overlay(items: list[dict[str, Any]], *, dry_run: bool = False) -> None:
    content = "".join(json.dumps(item, sort_keys=True) + "\n" for item in items)
    write_text_verified(ONTOLOGY_OVERLAY_PATH, content, dry_run=dry_run)


def _node_id(label: str) -> str:
    return "node_" + slugify(label)


def _normalize_terms(*values: str) -> set[str]:
    terms: set[str] = set()
    for value in values:
        if not value:
            continue
        terms.add(value.lower().strip())
        terms.add(slugify(value))
    terms.discard("")
    return terms


def _node_match_score(node: dict[str, Any], query: str) -> float:
    """Deterministic alias-aware match score in [0, 1]."""
    q_terms = _normalize_terms(query)
    if not q_terms:
        return 0.0
    candidates = _normalize_terms(node.get("label", ""), *(node.get("aliases", []) or []))
    if q_terms & candidates:
        return 1.0
    # Token overlap fallback (substring/word-level), still fully deterministic.
    q_tokens = {t for term in q_terms for t in term.split("-") if len(t) > 2}
    c_tokens = {t for term in candidates for t in term.split("-") if len(t) > 2}
    if not q_tokens or not c_tokens:
        return 0.0
    overlap = q_tokens & c_tokens
    if not overlap:
        return 0.0
    return round(len(overlap) / max(len(q_tokens), 1), 3)


def ontology_nodes_combined() -> list[dict[str, Any]]:
    """Registry nodes plus overlay entries normalized into node shape."""
    nodes = list(load_ontology_registry().get("nodes", []))
    known_ids = {n.get("node_id") for n in nodes}
    for entry in load_overlay():
        nid = entry.get("node_id") or _node_id(entry.get("label", ""))
        if nid in known_ids:
            continue
        nodes.append({
            "node_id": nid,
            "label": entry.get("label", ""),
            "aliases": entry.get("aliases", []) or [],
            "kind": entry.get("kind", "concept"),
            "wikidata_qid": entry.get("wikidata_qid"),
            "wikipedia_title": entry.get("wikipedia_title"),
            "parent_ids": entry.get("parent_ids", []) or [],
            "related_ids": entry.get("related_ids", []) or [],
            "personal": True,
            "notes": entry.get("notes", ""),
        })
        known_ids.add(nid)
    return nodes


def cmd_overlay_seed(args: argparse.Namespace) -> int:
    """Seed personal overlay nodes (idempotent; never overwrites existing)."""
    existing = load_overlay()
    existing_keys = {slugify(e.get("label", "")) for e in existing}
    added = []
    for seed in PERSONAL_OVERLAY_SEED:
        key = slugify(seed["label"])
        if key in existing_keys:
            continue
        entry = dict(seed)
        entry["node_id"] = _node_id(seed["label"])
        existing.append(entry)
        existing_keys.add(key)
        added.append(entry["node_id"])
    if not args.dry_run and added:
        write_overlay(existing)
    return emit({"ok": True, "dry_run": bool(args.dry_run), "added": added, "total": len(existing)})


def cmd_map_ontology(args: argparse.Namespace) -> int:
    """Map a topic/query to ontology nodes. Local-first; no mandatory network."""
    nodes = ontology_nodes_combined()
    scored = []
    for node in nodes:
        score = _node_match_score(node, args.topic)
        if score > 0:
            scored.append({
                "node_id": node.get("node_id"),
                "label": node.get("label"),
                "kind": node.get("kind"),
                "personal": bool(node.get("personal")),
                "wikidata_qid": node.get("wikidata_qid"),
                "wikipedia_title": node.get("wikipedia_title"),
                "score": score,
            })
    scored.sort(key=lambda m: (-m["score"], m["label"] or ""))

    result: dict[str, Any] = {
        "ok": True,
        "topic": args.topic,
        "matches": scored,
        "matched": bool(scored),
    }

    if not scored and args.suggest:
        # Propose a candidate node; do NOT auto-persist unless --create-node.
        candidate = {
            "node_id": _node_id(args.topic),
            "label": args.topic.strip().title(),
            "aliases": [args.topic.strip().lower()],
            "kind": args.kind or "concept",
            "wikidata_qid": None,
            "wikipedia_title": None,
            "parent_ids": [],
            "related_ids": [],
            "personal": True,
            "notes": "Candidate node proposed by map-ontology; confirm with --create-node.",
        }
        result["candidate"] = candidate
        if args.create_node and not args.dry_run:
            registry = load_ontology_registry()
            registry["nodes"].append(candidate)
            save_ontology_registry(registry)
            result["created"] = candidate["node_id"]
        else:
            result["created"] = None

    return emit(result)


def add_dry_run(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true", help="Report intended writes without mutating state")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Research repo and compendium engine")
    sub = parser.add_subparsers(dest="command", required=True)

    register_run_subcommands(sub)
    register_promotion_subcommands(sub)

    p = sub.add_parser("scan", help="Scan existing folders before deciding what research repos should exist")
    p.add_argument("--roots", nargs="*", help="Folders to scan; defaults to Research, Knowledge, and Personal/Knowledge")
    p.add_argument("--max-files", type=int, default=500)
    p.add_argument("--max-depth", type=int, default=5)
    p.add_argument("--suggestion-limit", type=int, default=10)
    p.add_argument("--output")
    add_dry_run(p)
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("suggest", help="Generate candidate research repo proposals from a scan")
    p.add_argument("--scan-json")
    p.add_argument("--roots", nargs="*")
    p.add_argument("--max-files", type=int, default=500)
    p.add_argument("--max-depth", type=int, default=5)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--proposals-dir")
    add_dry_run(p)
    p.set_defaults(func=cmd_suggest)

    p = sub.add_parser("compendium", help="Render wiki-style compendium index from registered repos")
    p.add_argument("--output")
    add_dry_run(p)
    p.set_defaults(func=cmd_compendium)

    p = sub.add_parser("propose")
    p.add_argument("--title", required=True)
    p.add_argument("--objective", required=True)
    p.add_argument("--repo-id")
    p.add_argument("--path")
    p.add_argument("--tags", nargs="*")
    add_dry_run(p)
    p.set_defaults(func=cmd_propose)

    p = sub.add_parser("activate")
    p.add_argument("--repo-id", required=True)
    add_dry_run(p)
    p.set_defaults(func=cmd_activate)

    p = sub.add_parser("list")
    p.add_argument("--status")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show")
    p.add_argument("--repo-id", required=True)
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("append")
    p.add_argument("--repo-id", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--source-ref", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--payload-json")
    add_dry_run(p)
    p.set_defaults(func=cmd_append)

    p = sub.add_parser("compact")
    p.add_argument("--repo-id", required=True)
    p.add_argument("--limit", type=int, default=50)
    add_dry_run(p)
    p.set_defaults(func=cmd_compact)

    p = sub.add_parser("validate", help="Validate primitive JSON records against Phase 1 schemas")
    p.add_argument("path", nargs="*")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("overlay-seed", help="Seed V-specific personal overlay ontology nodes (idempotent)")
    add_dry_run(p)
    p.set_defaults(func=cmd_overlay_seed)

    p = sub.add_parser("map-ontology", help="Map a topic/query to ontology nodes; local-first, no mandatory network")
    p.add_argument("--topic", required=True)
    p.add_argument("--suggest", action="store_true", help="Propose a candidate node when no local match exists")
    p.add_argument("--create-node", action="store_true", help="Persist the proposed candidate into the registry")
    p.add_argument("--kind", help="Node kind for a proposed candidate (default: concept)")
    add_dry_run(p)
    p.set_defaults(func=cmd_map_ontology)

    p = sub.add_parser("repair-status")
    p.set_defaults(func=cmd_repair_status)

    p = sub.add_parser("repair-sweep")
    add_dry_run(p)
    p.set_defaults(func=cmd_repair_sweep)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except BrokenPipeError:
        return 0
    except Exception as exc:
        logger.exception("Framework error")
        return emit({"ok": False, "error": "framework_error", "message": str(exc)}, 1)


if __name__ == "__main__":
    raise SystemExit(main())
