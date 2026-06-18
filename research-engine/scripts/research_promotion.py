#!/usr/bin/env python3
"""Research Engine Phase 4: explicit promotion gate into Knowledge.

Promotion is intentionally separate from research runs. Runs may create claims and
synthesis under Research, but only this module can prepare or perform writes into
Knowledge, and only with an explicit target plus --confirm.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path(os.environ.get("ZO_WORKSPACE", "/home/workspace"))
REPO_ROOT = Path(os.environ.get("RESEARCH_ENGINE_ROOT", str(WORKSPACE / "Research" / "repos")))
ENGINE_ROOT = Path(os.environ.get("RESEARCH_ENGINE_STATE_ROOT", str(WORKSPACE / "Research" / "_engine")))
KNOWLEDGE_ROOT = Path(os.environ.get("RESEARCH_ENGINE_KNOWLEDGE_ROOT", str(WORKSPACE / "Knowledge")))
PROMOTIONS_DIR = ENGINE_ROOT / "promotions"
CANDIDATES_DIR = PROMOTIONS_DIR / "candidates"
PROMOTION_LOG_PATH = PROMOTIONS_DIR / "PROMOTION_LOG.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def emit(data: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(data, indent=2, sort_keys=True))
    return code


def safe_relative(path: Path, base: Path = WORKSPACE) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path)


def topic_dir(topic: str) -> Path:
    return REPO_ROOT / topic


def candidate_path(candidate_id: str) -> Path:
    return CANDIDATES_DIR / f"{candidate_id}.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not path.exists():
        raise RuntimeError(f"write verification failed: {path}")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    if not path.exists():
        raise RuntimeError(f"append verification failed: {path}")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def knowledge_target_path(target: str) -> Path:
    if not target.startswith("Knowledge/"):
        raise ValueError("promotion target must be an explicit path under Knowledge/")
    suffix = target[len("Knowledge/"):]
    path = (KNOWLEDGE_ROOT / suffix).resolve()
    knowledge_root = KNOWLEDGE_ROOT.resolve()
    if not str(path).startswith(str(knowledge_root) + os.sep) and path != knowledge_root:
        raise ValueError("promotion target resolved outside Knowledge/")
    if path.suffix.lower() != ".md":
        raise ValueError("promotion target must be a markdown file under Knowledge/")
    return path


def candidate_id_for(topic: str, target: str, claim_ids: list[str]) -> str:
    payload = json.dumps({"topic": topic, "target": target, "claim_ids": sorted(claim_ids)}, sort_keys=True)
    return "pc_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def load_topic_claims(topic: str) -> list[dict[str, Any]]:
    return read_jsonl(topic_dir(topic) / "CLAIMS.jsonl")


def selected_claims(topic: str, claim_ids: list[str]) -> list[dict[str, Any]]:
    claims = load_topic_claims(topic)
    if claim_ids:
        wanted = set(claim_ids)
        return [c for c in claims if c.get("claim_id") in wanted]
    return claims


def validate_claims_for_promotion(claims: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if not claims:
        return ["no claims selected for promotion"]
    for claim in claims:
        cid = claim.get("claim_id", "<missing>")
        if not claim.get("provenance"):
            errors.append(f"claim {cid} missing provenance")
        if not claim.get("supporting_extracts"):
            errors.append(f"claim {cid} missing supporting_extracts")
        if not claim.get("claim"):
            errors.append(f"claim {cid} missing claim text")
    return errors


def render_promotion_section(candidate: dict[str, Any]) -> str:
    claim_lines = []
    for claim in candidate.get("claims", []):
        claim_lines.append(
            f"- **{claim.get('confidence', 'unknown')}** `{claim.get('claim_id')}`: {claim.get('claim', '')}\n"
            f"  - Provenance: `{claim.get('provenance', '')}`\n"
            f"  - Supporting extracts: {', '.join(claim.get('supporting_extracts', []))}"
        )
    claims_text = "\n".join(claim_lines) if claim_lines else "- No claims selected."
    return f"""

## Research Promotion: {candidate['topic_id']} ({today()})

**Candidate ID:** `{candidate['candidate_id']}`  
**Rationale:** {candidate.get('rationale', '')}  
**Source:** Research Engine promotion gate  
**Created:** {candidate.get('created_at', '')}  
**Promoted:** {now_iso()}  

### Promoted Working Claims

{claims_text}

### Boundary Note

This section was explicitly promoted from Research into Knowledge. The source research remains under `Research/`; this file is the curated Knowledge target.
""".strip() + "\n"


def render_new_knowledge_file(candidate: dict[str, Any]) -> str:
    title = Path(candidate["target"]).stem.replace("-", " ").title()
    return "\n".join([
        "---",
        f"created: {today()}",
        f"last_edited: {today()}",
        "version: 1.0",
        f"provenance: research-engine:{candidate['candidate_id']}",
        "---",
        "",
        f"# {title}",
        "",
        render_promotion_section(candidate).rstrip(),
        "",
    ])


def render_diff_preview(candidate: dict[str, Any], target_path: Path) -> dict[str, Any]:
    section = render_promotion_section(candidate)
    if target_path.exists():
        before = target_path.read_text(encoding="utf-8")
        after = before.rstrip() + "\n\n" + section
        action = "append"
    else:
        before = ""
        after = render_new_knowledge_file(candidate)
        action = "create"
    return {
        "action": action,
        "target": safe_relative(target_path),
        "before_sha256": hashlib.sha256(before.encode("utf-8")).hexdigest(),
        "after_sha256": hashlib.sha256(after.encode("utf-8")).hexdigest(),
        "added_preview": section,
        "would_write_bytes": len(after.encode("utf-8")),
    }


def cmd_propose_promotion(args: argparse.Namespace) -> int:
    try:
        target_path = knowledge_target_path(args.target)
    except ValueError as exc:
        return emit({"ok": False, "error": str(exc), "errors": [str(exc)], "candidate_created": False})
    claims = selected_claims(args.topic, args.claim_id or [])
    errors = validate_claims_for_promotion(claims)
    if errors:
        return emit({"ok": False, "errors": errors, "candidate_created": False})
    claim_ids = [c["claim_id"] for c in claims]
    cid = candidate_id_for(args.topic, args.target, claim_ids)
    candidate = {
        "kind": "promotion_candidate",
        "candidate_id": cid,
        "topic_id": args.topic,
        "target": args.target,
        "claim_ids": claim_ids,
        "claims": claims,
        "rationale": args.rationale or "Candidate generated from Research Engine topic claims; review before promotion.",
        "review_status": "proposed",
        "created_at": now_iso(),
        "provenance": f"research-engine:{args.topic}",
    }
    diff = render_diff_preview(candidate, target_path)
    if not args.dry_run:
        write_json(candidate_path(cid), candidate)
        append_jsonl(topic_dir(args.topic) / "PROMOTION_QUEUE.jsonl", candidate)
    return emit({
        "ok": True,
        "dry_run": bool(args.dry_run),
        "candidate_id": cid,
        "candidate_path": safe_relative(candidate_path(cid)),
        "candidate_created": not args.dry_run,
        "diff": diff,
    })


def load_candidate(candidate_id: str) -> dict[str, Any]:
    path = candidate_path(candidate_id)
    if not path.exists():
        raise FileNotFoundError(f"promotion candidate not found: {candidate_id}")
    candidate = load_json(path, {})
    if not isinstance(candidate, dict) or not candidate:
        raise ValueError(f"promotion candidate malformed: {candidate_id}")
    return candidate


def cmd_promote(args: argparse.Namespace) -> int:
    if args.confirm and args.dry_run:
        return emit({"ok": False, "error": "choose either --dry-run or --confirm, not both"})
    if not args.confirm and not args.dry_run:
        return emit({"ok": False, "error": "promotion requires --dry-run or --confirm"})
    candidate = load_candidate(args.candidate_id)
    target_path = knowledge_target_path(candidate.get("target", ""))
    errors = validate_claims_for_promotion(candidate.get("claims", []))
    if errors:
        return emit({"ok": False, "errors": errors, "promoted": False})
    diff = render_diff_preview(candidate, target_path)
    if args.dry_run:
        return emit({"ok": True, "dry_run": True, "candidate_id": args.candidate_id, "diff": diff})

    if target_path.exists():
        before = target_path.read_text(encoding="utf-8")
        after = before.rstrip() + "\n\n" + render_promotion_section(candidate)
    else:
        before = ""
        after = render_new_knowledge_file(candidate)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(after, encoding="utf-8")
    if not target_path.exists():
        raise RuntimeError(f"promotion write verification failed: {target_path}")

    candidate["review_status"] = "promoted"
    candidate["promoted_at"] = now_iso()
    candidate["target_sha256"] = hashlib.sha256(after.encode("utf-8")).hexdigest()
    write_json(candidate_path(args.candidate_id), candidate)
    log_row = {
        "timestamp": now_iso(),
        "candidate_id": args.candidate_id,
        "target": candidate["target"],
        "action": diff["action"],
        "before_sha256": hashlib.sha256(before.encode("utf-8")).hexdigest(),
        "after_sha256": candidate["target_sha256"],
        "claim_ids": candidate.get("claim_ids", []),
    }
    append_jsonl(PROMOTION_LOG_PATH, log_row)
    return emit({
        "ok": True,
        "promoted": True,
        "candidate_id": args.candidate_id,
        "target": safe_relative(target_path),
        "log_path": safe_relative(PROMOTION_LOG_PATH),
        "after_sha256": candidate["target_sha256"],
    })


def register_promotion_subcommands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    p = sub.add_parser("propose-promotion", help="Create a gated Knowledge promotion candidate from topic claims")
    p.add_argument("--topic", required=True, help="Topic slug under Research/repos")
    p.add_argument("--target", required=True, help="Explicit markdown target under Knowledge/")
    p.add_argument("--claim-id", action="append", help="Claim ID to promote; may repeat. Defaults to all topic claims")
    p.add_argument("--rationale")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_propose_promotion)

    p = sub.add_parser("promote", help="Dry-run or confirm a Knowledge promotion candidate")
    p.add_argument("--candidate-id", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--confirm", action="store_true")
    p.set_defaults(func=cmd_promote)
