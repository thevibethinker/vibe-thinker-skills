#!/usr/bin/env python3
"""Deliberate, traceable updates for the Simovian strategy memo."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import textwrap
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def find_workspace_root() -> Path:
    override = os.environ.get("SIMOVIAN_MEMO_WORKSPACE")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[3]


WORKSPACE = find_workspace_root()
DEFAULT_MEMO = "Research/general/pi-venture-intel/CURRENT_MEMO.md"
DEFAULT_POSITIONING = "Research/general/pi-venture-intel/POSITIONING.md"
SOURCE_LIBRARY = "Knowledge/content-library/memos/simovian-strategy-ingest"
MODEL = "byok:8a1176d8-10bf-44e8-a25c-30329932843c"


class CliError(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return (WORKSPACE / p if not p.is_absolute() else p).resolve()


def rel(path: str | Path) -> str:
    p = resolve(path)
    try:
        return str(p.relative_to(WORKSPACE))
    except ValueError:
        return str(p)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise CliError(f"File not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise CliError(f"File is not UTF-8 text: {path}") from exc


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if path.read_text(encoding="utf-8") != text:
        raise CliError(f"Write verification failed: {path}")


def write_json(path: Path, payload: Any) -> None:
    write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    before = path.stat().st_size if path.exists() else 0
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    if path.stat().st_size <= before:
        raise CliError(f"Append verification failed: {path}")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-") or "item"


def state_root(memo: Path) -> Path:
    return memo.parent / ".strategy-memo"


def ensure_state(memo: Path) -> Path:
    if not memo.exists() or not memo.is_file():
        raise CliError(f"Canonical memo missing: {memo}")
    root = state_root(memo)
    for name in ["sources", "candidates", "commits", "rollback", "pathways", "derived", "indexes"]:
        (root / name).mkdir(parents=True, exist_ok=True)
    config = root / "config.json"
    if not config.exists():
        write_json(config, {"created_at": now(), "skill": "simovian-strategy-memo", "canonical_memo_path": rel(memo), "source_library": SOURCE_LIBRARY})
    pathways = root / "pathways" / "pathways.json"
    if not pathways.exists():
        write_json(pathways, {"default": {"slug": "default", "title": "General Simovian Strategy", "created_at": now(), "source_count": 0, "commit_count": 0}})
    return root


def emit(payload: dict[str, Any], as_json: bool) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True) if as_json else payload.get("message", json.dumps(payload)))


def old_writer_risk() -> dict[str, Any] | None:
    path = WORKSPACE / "Skills/venture-intel/scripts/snapshot.py"
    if not path.exists():
        return None
    text = read(path)
    if "CURRENT_MEMO.md" in text and "--write-current-memo" not in text:
        return {"risk_id": "legacy-current-memo-writer", "severity": "high", "path": rel(path)}
    return None


def update_pathway(root: Path, pathway: str, source_delta: int = 0, commit_delta: int = 0) -> None:
    path = root / "pathways" / "pathways.json"
    data = json.loads(read(path))
    data.setdefault(pathway, {"slug": pathway, "title": pathway.replace("-", " ").title(), "created_at": now(), "source_count": 0, "commit_count": 0})
    data[pathway]["last_updated_at"] = now()
    data[pathway]["source_count"] = int(data[pathway].get("source_count", 0)) + source_delta
    data[pathway]["commit_count"] = int(data[pathway].get("commit_count", 0)) + commit_delta
    write_json(path, data)


def copy_source(root: Path, source: Path, intent: str, pathway: str) -> dict[str, Any]:
    if not source.exists() or not source.is_file():
        raise CliError(f"Source must be an existing file: {source}")
    digest = sha(source)
    library = WORKSPACE / SOURCE_LIBRARY / f"{datetime.now(timezone.utc).date().isoformat()}_{slug(source.stem)}_{digest[:10]}{source.suffix or '.md'}"
    library.parent.mkdir(parents=True, exist_ok=True)
    if not library.exists():
        shutil.copy2(source, library)
    if sha(library) != digest:
        raise CliError(f"Source copy hash mismatch: {library}")
    record = {"source_path": rel(source), "library_path": rel(library), "sha256": digest, "bytes": source.stat().st_size, "intent": intent, "pathway": pathway, "ingested_at": now()}
    append_jsonl(root / "indexes" / "source_ingest.jsonl", {"event": "source_ingested", **record})
    return record


def source_manifest(root: Path, source: str | None, manifest: str | None, intent: str, pathway: str) -> dict[str, Any]:
    if bool(source) == bool(manifest):
        raise CliError("Use exactly one of --source or --source-manifest")
    records = []
    if source:
        records.append(copy_source(root, resolve(source), intent, pathway))
    else:
        data = json.loads(read(resolve(manifest)))
        for item in data.get("sources", []):
            records.append(copy_source(root, resolve(item["path"] if isinstance(item, dict) else item), intent, pathway))
    return {"created_at": now(), "intent": intent, "pathway": pathway, "sources": records}


def zo_json(prompt: str) -> dict[str, Any]:
    token = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")
    if not token:
        raise CliError("ZO_CLIENT_IDENTITY_TOKEN is unavailable")
    req = urllib.request.Request(
        "https://api.zo.computer/zo/ask",
        data=json.dumps({"input": prompt, "model_name": MODEL}).encode(),
        headers={"authorization": token, "content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            output = json.loads(response.read().decode()).get("output")
    except urllib.error.HTTPError as exc:
        raise CliError(f"/zo/ask failed: HTTP {exc.code}") from exc
    if isinstance(output, dict):
        return output
    text = output if isinstance(output, str) else ""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise CliError("/zo/ask did not return JSON")
    return json.loads(match.group(0))


def local_analysis(memo: str, manifest: dict[str, Any], intent: str, pathway: str) -> dict[str, Any]:
    snippets = []
    for src in manifest["sources"]:
        snippets.append(f"## Source: {src['library_path']}\n{read(resolve(src['library_path']))[:2500]}")
    source_lines = "\n".join(f"- `{s['library_path']}` ({s['sha256'][:10]})" for s in manifest["sources"])
    patch = f"""## Candidate Update: {intent}

- Pathway: `{pathway}`
- Source(s):
{source_lines}

### Source-Supported Notes

{textwrap.shorten(' '.join(snippets), width=1200, placeholder='...')}
"""
    return {"semantic_summary": "Candidate staged from ingested source evidence.", "contradictions": [], "open_questions": ["Human review required before apply."], "derived_output_impacts": [{"output": DEFAULT_POSITIONING, "status": "stale_if_candidate_applied"}], "pathway_impacts": [{"pathway": pathway, "impact": "pending_review"}], "recommended_memo_patch": patch, "model_name_used": "local"}


def analyze(memo: str, manifest: dict[str, Any], intent: str, pathway: str, local: bool) -> dict[str, Any]:
    if local:
        return local_analysis(memo, manifest, intent, pathway)
    prompt = f"""Analyze source evidence for a Simovian strategy memo commit. Return only JSON with keys semantic_summary, contradictions, open_questions, derived_output_impacts, pathway_impacts, recommended_memo_patch.

Intent: {intent}
Pathway: {pathway}
Current memo:
{memo[:12000]}
Sources:
{json.dumps(manifest, indent=2)}
"""
    payload = zo_json(prompt)
    payload.setdefault("recommended_memo_patch", local_analysis(memo, manifest, intent, pathway)["recommended_memo_patch"])
    payload.setdefault("model_name_used", MODEL)
    return payload


def cmd_status(args: argparse.Namespace) -> None:
    root = ensure_state(resolve(args.memo))
    ledger = root / "indexes" / "source_ingest.jsonl"
    pending = [json.loads(read(p))["candidate_id"] for p in sorted((root / "candidates").glob("*/candidate.json")) if json.loads(read(p)).get("status") == "pending"]
    commits = list((root / "commits").glob("*.json"))
    emit({"status": "ok", "memo": rel(args.memo), "state_root": rel(root), "source_library": SOURCE_LIBRARY, "source_ingest_count": sum(1 for _ in ledger.open()) if ledger.exists() else 0, "pending_candidates": pending, "commit_count": len(commits), "old_writer_risk": old_writer_risk()}, args.json)


def cmd_ingest(args: argparse.Namespace) -> None:
    root = ensure_state(resolve(args.memo))
    manifest = source_manifest(root, args.source, None, args.intent, args.pathway)
    update_pathway(root, args.pathway, source_delta=len(manifest["sources"]))
    emit({"status": "source_ingested", "manifest": manifest}, args.json)


def cmd_commit(args: argparse.Namespace) -> None:
    memo = resolve(args.memo)
    root = ensure_state(memo)
    manifest = source_manifest(root, args.source, args.source_manifest, args.intent, args.pathway)
    update_pathway(root, args.pathway, source_delta=len(manifest["sources"]))
    analysis = analyze(read(memo), manifest, args.intent, args.pathway, args.local)
    candidate_id = args.candidate_id or f"cand_{stamp()}_{slug(args.intent)[:40]}"
    cdir = root / "candidates" / candidate_id
    cdir.mkdir(parents=True, exist_ok=True)
    candidate = {"candidate_id": candidate_id, "created_at": now(), "status": "pending", "intent": args.intent, "pathway": args.pathway, "memo_path": rel(memo), "source_manifest_path": rel(cdir / "source_manifest.json"), "analysis_path": rel(cdir / "analysis.json"), "proposed_patch_path": rel(cdir / "proposed_patch.md")}
    write_json(cdir / "source_manifest.json", manifest)
    write_json(cdir / "analysis.json", analysis)
    write(cdir / "proposed_patch.md", analysis["recommended_memo_patch"].rstrip() + "\n")
    write(cdir / "contradiction_report.md", "# Contradiction Report\n\n" + "\n".join(f"- {x}" for x in analysis.get("contradictions", []) or ["None identified."]) + "\n")
    write(cdir / "downstream_report.md", "# Downstream Impact Report\n\n" + "\n".join(f"- {json.dumps(x)}" for x in analysis.get("derived_output_impacts", [])) + "\n")
    write(cdir / "pathway_report.md", "# Pathway Impact Report\n\n" + "\n".join(f"- {json.dumps(x)}" for x in analysis.get("pathway_impacts", [])) + "\n")
    write_json(cdir / "candidate.json", candidate)
    append_jsonl(root / "indexes" / "candidate_events.jsonl", {"event": "candidate_created", **candidate})
    emit({"status": "candidate_created", "candidate": candidate, "approval_phrase": f"APPROVE {candidate_id}"}, args.json)


def cmd_apply(args: argparse.Namespace) -> None:
    memo = resolve(args.memo)
    root = ensure_state(memo)
    cdir = root / "candidates" / args.candidate_id
    candidate = json.loads(read(cdir / "candidate.json"))
    if candidate.get("status") != "pending":
        raise CliError(f"Candidate is not pending: {args.candidate_id}")
    if args.approve != f"APPROVE {args.candidate_id}":
        raise CliError(f"Approval phrase must exactly be: APPROVE {args.candidate_id}")
    risk = old_writer_risk()
    if risk and not args.ack_old_writer_risk:
        raise CliError(f"Blocking old writer risk: {risk['risk_id']}")
    before = read(memo)
    patch = read(cdir / "proposed_patch.md").rstrip()
    after = before.rstrip() + f"\n\n---\n\n{patch}\n\n*Applied via simovian-strategy-memo on {now()} from `{args.candidate_id}`.*\n"
    rollback = root / "rollback" / args.candidate_id
    write(rollback / "CURRENT_MEMO.before.md", before)
    write(memo, after)
    write(rollback / "CURRENT_MEMO.after.md", after)
    commit = {"commit_id": f"memo_{stamp()}_{slug(args.candidate_id)}", "candidate_id": args.candidate_id, "applied_at": now(), "memo_path": rel(memo), "before_sha256": hashlib.sha256(before.encode()).hexdigest(), "after_sha256": hashlib.sha256(after.encode()).hexdigest(), "rollback_dir": rel(rollback), "source_manifest_path": candidate["source_manifest_path"]}
    write_json(root / "commits" / f"{commit['commit_id']}.json", commit)
    candidate["status"] = "applied"
    candidate["commit_id"] = commit["commit_id"]
    candidate["applied_at"] = commit["applied_at"]
    write_json(cdir / "candidate.json", candidate)
    append_jsonl(root / "indexes" / "candidate_events.jsonl", {"event": "candidate_applied", **commit})
    append_jsonl(root / "indexes" / "memo_claims.jsonl", {"event": "memo_patch_applied", **commit})
    update_pathway(root, candidate["pathway"], commit_delta=1)
    emit({"status": "candidate_applied", "commit": commit}, args.json)


def cmd_history(args: argparse.Namespace) -> None:
    root = ensure_state(resolve(args.memo))
    commits = [json.loads(read(p)) for p in sorted((root / "commits").glob("*.json"))][-args.limit:]
    emit({"status": "ok", "commits": commits}, args.json)


def cmd_blame(args: argparse.Namespace) -> None:
    query = args.heading or args.text or args.claim_id or args.line_range
    root = ensure_state(resolve(args.memo))
    commits = [json.loads(read(p)) for p in sorted((root / "commits").glob("*.json"))]
    matches = [c for c in commits if query and query.lower() in json.dumps(c).lower()]
    emit({"status": "ok", "query": query, "matches": matches, "note": "Tracks skill-applied commits and source metadata; pre-skill memo lines have no line-level provenance."}, args.json)


def cmd_pathways(args: argparse.Namespace) -> None:
    root = ensure_state(resolve(args.memo))
    data = json.loads(read(root / "pathways" / "pathways.json"))
    emit({"status": "ok", "pathways": {args.pathway: data.get(args.pathway)} if args.pathway else data}, args.json)


def cmd_archive(args: argparse.Namespace) -> None:
    root = ensure_state(resolve(args.memo))
    archived = []
    for candidate_id in args.candidate_id:
        path = root / "candidates" / candidate_id / "candidate.json"
        candidate = json.loads(read(path))
        if candidate.get("status") == "pending":
            candidate["status"] = "archived"
            candidate["archived_at"] = now()
            candidate["archive_reason"] = args.reason
            write_json(path, candidate)
            append_jsonl(root / "indexes" / "candidate_events.jsonl", {"event": "candidate_archived", "candidate_id": candidate_id, "reason": args.reason, "archived_at": candidate["archived_at"]})
        archived.append(candidate_id)
    emit({"status": "archived", "candidate_ids": archived}, args.json)


def positioning_payload(memo_text: str, pathway: str, audience: str | None, context: str | None) -> dict[str, Any]:
    thesis = next((line.strip("#* ") for line in memo_text.splitlines() if line.startswith("We are building") or "data supply chain" in line), "Simovian is a regulated-environment data operator for physical intelligence.")
    return {"title": "Simovian Positioning", "pathway": pathway, "audience": audience or "general", "context": context or "derived from current memo", "core_position": thesis, "supporting_points": ["Access, capture operations, QA, and documentation are treated as one supply chain.", "The current wedge emphasizes task-specific datasets with explicit consent trail.", "Positioning is generated only from reviewed memo state."], "caveats": []}


def cmd_positioning(args: argparse.Namespace) -> None:
    memo = resolve(args.memo)
    root = ensure_state(memo)
    payload = positioning_payload(read(memo), args.pathway, args.audience, args.context) if args.local else zo_json(f"Generate derived Simovian positioning from this memo. Return JSON keys title, pathway, audience, context, core_position, supporting_points, caveats.\n\n{read(memo)[:14000]}")
    payload.setdefault("title", "Simovian Positioning")
    payload.setdefault("supporting_points", [])
    payload.setdefault("caveats", [])
    body = "\n".join(f"- {p}" for p in payload["supporting_points"])
    caveats = "\n".join(f"- {p}" for p in payload["caveats"]) or "- None."
    doc = f"---\ncreated: {datetime.now(timezone.utc).date().isoformat()}\nlast_edited: {datetime.now(timezone.utc).date().isoformat()}\nversion: 1.0\nprovenance: simovian-strategy-memo\n---\n\n# {payload['title']}\n\n## Core Position\n\n{payload.get('core_position', '')}\n\n## Supporting Points\n\n{body}\n\n## Caveats\n\n{caveats}\n"
    output = resolve(args.output)
    write(output, doc)
    event = {"event": "positioning_generated", "generated_at": now(), "memo_path": rel(memo), "output_path": rel(output), "pathway": args.pathway}
    append_jsonl(root / "derived" / "positioning.jsonl", event)
    emit({"status": "positioning_generated", "output_path": rel(output), "payload": payload}, args.json)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Stage, apply, and audit commits to the Simovian strategy memo.")
    p.add_argument("--verbose", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--memo", default=DEFAULT_MEMO)
        sp.add_argument("--json", action="store_true")

    s = sub.add_parser("status"); common(s); s.set_defaults(func=cmd_status)
    i = sub.add_parser("ingest-source"); common(i); i.add_argument("--source", required=True); i.add_argument("--intent", required=True); i.add_argument("--pathway", default="default"); i.set_defaults(func=cmd_ingest)
    c = sub.add_parser("commit"); common(c); g = c.add_mutually_exclusive_group(required=True); g.add_argument("--source"); g.add_argument("--source-manifest"); c.add_argument("--intent", required=True); c.add_argument("--pathway", default="default"); c.add_argument("--candidate-id"); c.add_argument("--local", action="store_true"); c.set_defaults(func=cmd_commit)
    a = sub.add_parser("apply"); common(a); a.add_argument("--candidate-id", required=True); a.add_argument("--approve", required=True); a.add_argument("--ack-old-writer-risk", action="store_true"); a.set_defaults(func=cmd_apply)
    h = sub.add_parser("history"); common(h); h.add_argument("--limit", type=int, default=20); h.set_defaults(func=cmd_history)
    b = sub.add_parser("blame"); common(b); bg = b.add_mutually_exclusive_group(required=True); bg.add_argument("--heading"); bg.add_argument("--text"); bg.add_argument("--claim-id"); bg.add_argument("--line-range"); b.set_defaults(func=cmd_blame)
    w = sub.add_parser("pathways"); common(w); w.add_argument("--pathway"); w.set_defaults(func=cmd_pathways)
    ar = sub.add_parser("archive-candidate"); common(ar); ar.add_argument("--candidate-id", action="append", required=True); ar.add_argument("--reason", required=True); ar.set_defaults(func=cmd_archive)
    gp = sub.add_parser("generate-positioning"); common(gp); gp.add_argument("--pathway", default="default"); gp.add_argument("--output", default=DEFAULT_POSITIONING); gp.add_argument("--audience"); gp.add_argument("--context"); gp.add_argument("--local", action="store_true"); gp.set_defaults(func=cmd_positioning)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        args.func(args)
        return 0
    except (CliError, json.JSONDecodeError, OSError, urllib.error.URLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
