#!/usr/bin/env python3
"""CLI for the startup-memo-generator skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import sys
import time
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


REQUIRED_SKILLS = [
    "teach-impeccable",
    "frontend-design",
    "clarify",
    "arrange",
    "typeset",
    "polish",
    "adapt",
    "harden",
]

DEFAULT_DATA_ROOT = Path("N5/data/startup-memo-generator")
ACCESS_MODES = {"whitelist-only", "email+pin", "pin-only-with-email-capture"}
STAKEHOLDER_STATUSES = {"approved", "candidate", "blocked", "revoked"}


@dataclass
class Context:
    workspace: Path
    skill_dir: Path
    data_root: Path
    dry_run: bool
    actor: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(message: str) -> None:
    print(f"[{now_iso()}] {message}")


def fail(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def uuid7_like() -> str:
    timestamp_ms = int(time.time() * 1000)
    time_hex = f"{timestamp_ms:012x}"
    rand_hex = uuid.uuid4().hex[12:]
    raw = f"{time_hex}7{rand_hex[:19]}"
    return str(uuid.UUID(raw[:32]))


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "memo"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON at {path}: {exc}")


def write_json(path: Path, payload: Any, dry_run: bool) -> None:
    if dry_run:
        log(f"DRY RUN: would write {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    loaded = load_json(path, None)
    if loaded is None:
        fail(f"State verification failed after writing {path}")


def append_jsonl(path: Path, payload: dict[str, Any], dry_run: bool) -> None:
    line = json.dumps(payload, sort_keys=True)
    if dry_run:
        log(f"DRY RUN: would append to {path}: {line}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(line + "\n")


def find_workspace(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "WORKSPACE_MAP.md").exists() and (candidate / "Skills").exists():
            return candidate
    return Path("/home/workspace")


def make_context(args: argparse.Namespace) -> Context:
    workspace = Path(args.workspace).resolve() if args.workspace else find_workspace(Path.cwd())
    skill_dir = Path(__file__).resolve().parents[1]
    config_path = workspace / DEFAULT_DATA_ROOT / "config.json"
    config = load_json(config_path, {})
    data_root = Path(args.data_root or config.get("data_root") or DEFAULT_DATA_ROOT)
    if not data_root.is_absolute():
        data_root = workspace / data_root
    return Context(
        workspace=workspace,
        skill_dir=skill_dir,
        data_root=data_root.resolve(),
        dry_run=bool(args.dry_run),
        actor=args.actor,
    )


def audit(ctx: Context, action: str, entity_type: str, entity_id: str, details: dict[str, Any]) -> None:
    append_jsonl(
        ctx.data_root / "audit.jsonl",
        {
            "ts": now_iso(),
            "actor": ctx.actor,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details,
        },
        ctx.dry_run,
    )


def command_doctor(args: argparse.Namespace) -> int:
    ctx = make_context(args)
    missing = []
    for skill in REQUIRED_SKILLS:
        if not (ctx.workspace / "Skills" / skill / "SKILL.md").exists():
            missing.append(skill)
    impeccable = list(ctx.workspace.glob("**/.impeccable.md"))
    print(json.dumps({
        "workspace": str(ctx.workspace),
        "skill_dir": str(ctx.skill_dir),
        "data_root": str(ctx.data_root),
        "missing_required_skills": missing,
        "impeccable_files_found": [str(path.relative_to(ctx.workspace)) for path in impeccable[:20]],
        "ok": not missing and bool(impeccable),
    }, indent=2))
    return 0 if not missing and impeccable else 1


def command_setup(args: argparse.Namespace) -> int:
    ctx = make_context(args)
    disclosure = args.analytics_disclosure or (
        f"Please be aware that this page's analytics are being collected and used by {args.org}."
    )
    config = {
        "org_name": args.org,
        "gmail_sender": args.gmail_sender,
        "data_root": str(ctx.data_root.relative_to(ctx.workspace) if ctx.data_root.is_relative_to(ctx.workspace) else ctx.data_root),
        "default_replay_retention_days": args.replay_retention_days,
        "analytics_disclosure": disclosure,
        "default_locale": args.default_locale,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    write_json(ctx.data_root / "config.json", config, ctx.dry_run)
    for dirname in ["memos", "sources", "blocks", "analytics", "replay", "exports"]:
        path = ctx.data_root / dirname
        if ctx.dry_run:
            log(f"DRY RUN: would create {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)
    audit(ctx, "setup", "config", "global", {"org_name": args.org, "gmail_sender": args.gmail_sender})
    log(f"Configured startup-memo-generator at {ctx.data_root}")
    return 0


def snapshot_source(ctx: Context, source: Path, memo_id: str) -> dict[str, Any]:
    if not source.exists():
        fail(f"Source does not exist: {source}")
    snapshot_id = uuid7_like()
    target_dir = ctx.data_root / "sources" / snapshot_id
    ext = source.suffix.lower()
    text = source.read_text(errors="replace") if ext in {".md", ".txt", ".html", ".csv", ".json"} else ""
    if not ctx.dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target_dir / source.name)
        if ext == ".md":
            (target_dir / "source.md").write_text(text)
            (target_dir / "source.txt").write_text(strip_markdown(text))
            (target_dir / "source.html").write_text(f"<pre>{html_escape(text)}</pre>\n")
        elif ext == ".html":
            (target_dir / "source.html").write_text(text)
            (target_dir / "source.txt").write_text(strip_html(text))
            (target_dir / "source.md").write_text(strip_html(text))
        elif text:
            (target_dir / "source.txt").write_text(text)
            (target_dir / "source.md").write_text(text)
            (target_dir / "source.html").write_text(f"<pre>{html_escape(text)}</pre>\n")
    else:
        log(f"DRY RUN: would snapshot {source} to {target_dir}")
    return {
        "id": snapshot_id,
        "memo_id": memo_id,
        "original_path": str(source),
        "stored_path": str(target_dir),
        "created_at": now_iso(),
        "formats": ["original", "html", "markdown", "text"],
    }


def strip_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    return text


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def command_create_memo(args: argparse.Namespace) -> int:
    ctx = make_context(args)
    if args.category not in {"investor-memos", "customer-memos"}:
        fail("category must be investor-memos or customer-memos")
    if args.auth_mode not in ACCESS_MODES:
        fail(f"auth mode must be one of: {', '.join(sorted(ACCESS_MODES))}")
    memo_id = uuid7_like()
    version_id = uuid7_like()
    route_path = f"/{args.category}/{slugify(args.title)}-{memo_id}"
    source_snapshot = snapshot_source(ctx, Path(args.source).resolve(), memo_id)
    shared_pin_visible: str | None = None
    shared_pin_hash_value: str | None = None
    if args.auth_mode == "pin-only-with-email-capture":
        shared_pin_visible = args.shared_pin or generate_pin()
        shared_pin_hash_value = shared_pin_hash(memo_id, shared_pin_visible)
    memo = {
        "id": memo_id,
        "title": args.title,
        "category": args.category,
        "route_path": route_path,
        "auth_mode": args.auth_mode,
        "default_version_id": version_id,
        "shared_pin_hash": shared_pin_hash_value,
        "shared_pin_updated_at": now_iso() if shared_pin_hash_value else None,
        "versions": [{
            "id": version_id,
            "label": args.version_label,
            "source_snapshot_id": source_snapshot["id"],
            "content_block_ids": [],
            "created_at": now_iso(),
        }],
        "stakeholders": [],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    write_json(ctx.data_root / "memos" / memo_id / "memo.json", memo, ctx.dry_run)
    write_json(ctx.data_root / "sources" / source_snapshot["id"] / "snapshot.json", source_snapshot, ctx.dry_run)
    audit(ctx, "create_memo", "memo", memo_id, {"title": args.title, "route_path": route_path, "shared_pin_set": shared_pin_hash_value is not None})
    print(json.dumps({"memo_id": memo_id, "version_id": version_id, "route_path": route_path, "shared_pin": shared_pin_visible}, indent=2))
    return 0


def memo_path(ctx: Context, memo_id: str) -> Path:
    return ctx.data_root / "memos" / memo_id / "memo.json"


def load_memo(ctx: Context, memo_id: str) -> dict[str, Any]:
    path = memo_path(ctx, memo_id)
    if not path.exists():
        fail(f"Memo not found: {memo_id}")
    return load_json(path, {})


def pin_hash(email: str, pin: str) -> str:
    return hashlib.sha256(f"{email.lower()}:{pin}".encode()).hexdigest()


def shared_pin_hash(memo_id: str, pin: str) -> str:
    return hashlib.sha256(f"memo:{memo_id}:{pin}".encode()).hexdigest()


def safe_pin_matches(email: str, pin: str, expected_hash: str) -> bool:
    if not expected_hash or not pin:
        return False
    return hashlib.sha256(f"{email.lower()}:{pin}".encode()).hexdigest() == expected_hash


def generate_pin() -> str:
    return f"{random.SystemRandom().randint(0, 9999):04d}"


def command_add_stakeholder(args: argparse.Namespace) -> int:
    ctx = make_context(args)
    if args.status not in STAKEHOLDER_STATUSES:
        fail(f"status must be one of: {', '.join(sorted(STAKEHOLDER_STATUSES))}")
    memo = load_memo(ctx, args.memo_id)
    email = args.email.strip().lower()
    existing = next((s for s in memo.get("stakeholders", []) if s.get("email") == email), None)
    others = [s for s in memo.get("stakeholders", []) if s.get("email") != email]
    pin_returned: str | None = None
    if args.pin:
        pin_hash_value = pin_hash(email, args.pin)
        pin_updated_at = now_iso()
        pin_returned = args.pin
    elif existing and existing.get("pin_hash"):
        pin_hash_value = existing["pin_hash"]
        pin_updated_at = existing.get("pin_updated_at") or now_iso()
    else:
        new_pin = generate_pin()
        pin_hash_value = pin_hash(email, new_pin)
        pin_updated_at = now_iso()
        pin_returned = new_pin
    stakeholder = {
        "email": email,
        "name": args.name or (existing.get("name") if existing else "") or "",
        "org": args.org or (existing.get("org") if existing else "") or "",
        "role": args.role or (existing.get("role") if existing else "") or "",
        "status": args.status,
        "locale": args.locale,
        "version_id": args.version_id or (existing.get("version_id") if existing else None) or memo["default_version_id"],
        "pin_hash": pin_hash_value,
        "pin_updated_at": pin_updated_at,
        "session_revoked_at": (existing.get("session_revoked_at") if existing else None),
        "custom_fields": (existing.get("custom_fields") if existing else {}) or {},
    }
    others.append(stakeholder)
    memo["stakeholders"] = sorted(others, key=lambda item: item["email"])
    memo["updated_at"] = now_iso()
    write_json(memo_path(ctx, args.memo_id), memo, ctx.dry_run)
    audit(ctx, "add_stakeholder", "memo", args.memo_id, {"email": email, "status": args.status, "pin_regenerated": pin_returned is not None and not args.pin})
    print(json.dumps({"email": email, "pin": pin_returned, "status": args.status, "pin_preserved": pin_returned is None}, indent=2))
    return 0


def command_set_memo_pin(args: argparse.Namespace) -> int:
    ctx = make_context(args)
    memo = load_memo(ctx, args.memo_id)
    if memo.get("auth_mode") != "pin-only-with-email-capture":
        fail("set-memo-pin only applies when auth_mode is pin-only-with-email-capture")
    pin = args.pin or generate_pin()
    memo["shared_pin_hash"] = shared_pin_hash(memo["id"], pin)
    memo["shared_pin_updated_at"] = now_iso()
    memo["updated_at"] = now_iso()
    write_json(memo_path(ctx, args.memo_id), memo, ctx.dry_run)
    audit(ctx, "set_memo_pin", "memo", args.memo_id, {})
    print(json.dumps({"memo_id": args.memo_id, "shared_pin": pin}, indent=2))
    return 0


def command_reset_pin(args: argparse.Namespace) -> int:
    ctx = make_context(args)
    memo = load_memo(ctx, args.memo_id)
    email = args.email.strip().lower()
    pin = args.pin or generate_pin()
    found = False
    for stakeholder in memo.get("stakeholders", []):
        if stakeholder.get("email") == email:
            stakeholder["pin_hash"] = pin_hash(email, pin)
            stakeholder["pin_updated_at"] = now_iso()
            found = True
    if not found:
        fail(f"Stakeholder not found for memo: {email}")
    memo["updated_at"] = now_iso()
    write_json(memo_path(ctx, args.memo_id), memo, ctx.dry_run)
    audit(ctx, "reset_pin", "memo", args.memo_id, {"email": email})
    print(json.dumps({"email": email, "pin": pin}, indent=2))
    return 0


def command_email_pin(args: argparse.Namespace) -> int:
    ctx = make_context(args)
    memo = load_memo(ctx, args.memo_id)
    config = load_json(ctx.data_root / "config.json", {})
    email = args.email.strip().lower()
    stakeholder = next((item for item in memo.get("stakeholders", []) if item.get("email") == email), None)
    if not stakeholder:
        fail(f"Stakeholder not found for memo: {email}")
    if not args.pin:
        fail("email-pin requires --pin. PINs are hashed and cannot be recovered; run reset-pin first if the PIN is unknown.")
    pin = args.pin
    if not safe_pin_matches(email, pin, stakeholder.get("pin_hash", "")):
        fail("Provided --pin does not match this stakeholder's PIN hash. Run reset-pin to issue a new PIN.")
    subject = args.subject or f"Access details for {memo['title']}"
    body = args.body or (
        f"Hi {stakeholder.get('name') or 'there'},\n\n"
        f"Here is your access PIN for {memo['title']}: {pin}\n\n"
        f"Memo link: {memo['route_path']}\n\n"
        "Please do not forward this PIN."
    )
    payload = {
        "from": config.get("gmail_sender", ""),
        "to": email,
        "subject": subject,
        "body": body,
        "pin": pin,
    }
    append_jsonl(ctx.data_root / "outbox.jsonl", {"ts": now_iso(), "kind": "pin_email", **payload}, ctx.dry_run)
    audit(ctx, "prepare_pin_email", "memo", args.memo_id, {"email": email})
    print(json.dumps(payload, indent=2))
    return 0


def command_revoke(args: argparse.Namespace) -> int:
    ctx = make_context(args)
    memo = load_memo(ctx, args.memo_id)
    email = args.email.strip().lower()
    found = False
    for stakeholder in memo.get("stakeholders", []):
        if stakeholder.get("email") == email:
            stakeholder["status"] = args.status
            stakeholder["session_revoked_at"] = now_iso()
            found = True
    if not found:
        fail(f"Stakeholder not found for memo: {email}")
    memo["updated_at"] = now_iso()
    write_json(memo_path(ctx, args.memo_id), memo, ctx.dry_run)
    audit(ctx, "revoke_access", "memo", args.memo_id, {"email": email, "status": args.status})
    return 0


def extract_links_from_text(text: str) -> list[str]:
    return sorted(set(re.findall(r"https?://[^\s)>'\"]+", text)))


def check_url(url: str, timeout: int) -> tuple[bool, str]:
    request = Request(url, method="HEAD", headers={"User-Agent": "startup-memo-generator/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 400, str(response.status)
    except URLError as exc:
        return False, str(exc.reason)
    except Exception as exc:
        return False, str(exc)


REQUIRED_TEMPLATES = ["memo-page.tsx", "admin-page.tsx", "api-auth.ts", "api-content.ts", "api-analytics.ts"]


def command_gate(args: argparse.Namespace) -> int:
    ctx = make_context(args)
    memo = load_memo(ctx, args.memo_id)
    failures = []
    warnings = []
    if memo.get("auth_mode") not in ACCESS_MODES:
        failures.append("invalid auth mode")
    if memo.get("auth_mode") == "pin-only-with-email-capture" and not memo.get("shared_pin_hash"):
        failures.append("pin-only-with-email-capture mode requires shared_pin_hash; run set-memo-pin")
    if not memo.get("versions"):
        failures.append("missing versions")
    for version in memo.get("versions", []):
        snapshot_id = version.get("source_snapshot_id")
        snapshot_path = ctx.data_root / "sources" / snapshot_id / "snapshot.json"
        if not snapshot_id or not snapshot_path.exists():
            failures.append(f"missing source snapshot for version {version.get('id')}")
            continue
        source_text_path = ctx.data_root / "sources" / snapshot_id / "source.txt"
        if source_text_path.exists():
            text = source_text_path.read_text(errors="replace")
            if re.search(r"\b(ssn|social security|passport|bank account)\b", text, re.I):
                warnings.append(f"possible PII/PR-sensitive content in version {version.get('id')}")
            if args.check_links:
                for url in extract_links_from_text(text):
                    ok, detail = check_url(url, args.timeout)
                    if not ok:
                        failures.append(f"dead link: {url} ({detail})")

    template_dir = ctx.skill_dir / "assets" / "zo-space"
    for template_name in REQUIRED_TEMPLATES:
        if not (template_dir / template_name).exists():
            failures.append(f"missing template: {template_name}")
    memo_page = template_dir / "memo-page.tsx"
    if memo_page.exists() and "MEMO_SOURCE_TEXT_JSON" in memo_page.read_text():
        failures.append("memo-page.tsx still embeds source text; content must be fetched server-side")

    bundle_dir = ctx.data_root / "exports" / args.memo_id / "zo-space"
    if bundle_dir.exists():
        for path in bundle_dir.glob("*.ts*"):
            content = path.read_text(errors="replace")
            leftovers = re.findall(r"\{\{[^}]+\}\}", content)
            if leftovers:
                failures.append(f"unresolved placeholders in {path.name}: {sorted(set(leftovers))}")

    report = {"memo_id": args.memo_id, "failures": failures, "warnings": warnings, "ok": not failures}
    write_json(ctx.data_root / "memos" / args.memo_id / "gate-report.json", report, ctx.dry_run)
    audit(ctx, "gate", "memo", args.memo_id, report)
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


def command_report(args: argparse.Namespace) -> int:
    ctx = make_context(args)
    path = ctx.data_root / "analytics" / f"{args.memo_id}.jsonl"
    counts: dict[str, int] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            name = event.get("event", "unknown")
            counts[name] = counts.get(name, 0) + 1
    print(json.dumps({"memo_id": args.memo_id, "event_counts": counts}, indent=2))
    return 0


def render_template(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def command_generate_route_bundle(args: argparse.Namespace) -> int:
    ctx = make_context(args)
    memo = load_memo(ctx, args.memo_id)
    config = load_json(ctx.data_root / "config.json", {})
    template_dir = ctx.skill_dir / "assets" / "zo-space"
    if not template_dir.exists():
        fail(f"Missing template directory: {template_dir}")
    output_dir = Path(args.output_dir).resolve() if args.output_dir else ctx.data_root / "exports" / args.memo_id / "zo-space"
    values = {
        "MEMO_ID": memo["id"],
        "MEMO_TITLE_JSON": json.dumps(memo["title"]),
        "MEMO_ROUTE_JSON": json.dumps(memo["route_path"]),
        "ANALYTICS_DISCLOSURE_JSON": json.dumps(config.get("analytics_disclosure", "")),
        "ORG_NAME_JSON": json.dumps(config.get("org_name", "")),
        "DEFAULT_LOCALE_JSON": json.dumps(config.get("default_locale", "en-US")),
        "DATA_ROOT_JSON": json.dumps(str(ctx.data_root)),
    }
    outputs = {
        "memo-page.tsx": f"page{memo['route_path'].replace('/', '__')}.tsx",
        "admin-page.tsx": f"page__{memo['category']}__admin.tsx",
        "api-auth.ts": f"api__startup-memo-generator__auth__{memo['id']}.ts",
        "api-content.ts": f"api__startup-memo-generator__content__{memo['id']}.ts",
        "api-analytics.ts": f"api__startup-memo-generator__analytics__{memo['id']}.ts",
    }
    if ctx.dry_run:
        log(f"DRY RUN: would generate route bundle in {output_dir}")
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        for template_name, output_name in outputs.items():
            template_path = template_dir / template_name
            if not template_path.exists():
                fail(f"Missing template: {template_path}")
            rendered = render_template(template_path.read_text(), values)
            leftovers = re.findall(r"\{\{[^}]+\}\}", rendered)
            if leftovers:
                fail(f"Unresolved placeholders in {template_name}: {sorted(set(leftovers))}")
            (output_dir / output_name).write_text(rendered)
        manifest = {
            "memo_id": memo["id"],
            "route_path": memo["route_path"],
            "generated_at": now_iso(),
            "files": outputs,
            "suggested_routes": {
                outputs["memo-page.tsx"]: {"path": memo["route_path"], "route_type": "page", "public": True},
                outputs["admin-page.tsx"]: {"path": f"/{memo['category']}/admin", "route_type": "page", "public": False},
                outputs["api-auth.ts"]: {"path": f"/api/startup-memo-generator/auth/{memo['id']}/:action", "route_type": "api"},
                outputs["api-content.ts"]: {"path": f"/api/startup-memo-generator/content/{memo['id']}", "route_type": "api"},
                outputs["api-analytics.ts"]: {"path": f"/api/startup-memo-generator/analytics/{memo['id']}/:action", "route_type": "api"},
            },
            "notes": "Templates are generated for review. Publish through Zo Space route tools after gates pass. Set MEMO_ADMIN_TOKEN env var on the analytics route to authorize admin summary reads.",
        }
        write_json(output_dir / "manifest.json", manifest, ctx.dry_run)
    audit(ctx, "generate_route_bundle", "memo", args.memo_id, {"output_dir": str(output_dir)})
    print(json.dumps({"memo_id": args.memo_id, "output_dir": str(output_dir), "files": outputs}, indent=2))
    return 0


def command_export_zip(args: argparse.Namespace) -> int:
    ctx = make_context(args)
    output = Path(args.output).resolve()
    if ctx.dry_run:
        log(f"DRY RUN: would export {ctx.skill_dir} to {output}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in ctx.skill_dir.rglob("*"):
            ignored_parts = {"__pycache__", "data", ".pytest_cache"}
            if any(part in ignored_parts for part in path.parts):
                continue
            if path.name.endswith(".pyc") or path.name == ".DS_Store":
                continue
            if path.is_file():
                archive.write(path, path.relative_to(ctx.skill_dir.parent))
    log(f"Exported {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage gated startup memo pages.")
    parser.add_argument("--workspace", help="Workspace root. Defaults to auto-detected /home/workspace.")
    parser.add_argument("--data-root", help="Runtime data root. Defaults to config or N5/data/startup-memo-generator.")
    parser.add_argument("--dry-run", action="store_true", help="Preview writes without changing state.")
    parser.add_argument("--actor", default=os.environ.get("USER", "zo"), help="Audit actor label.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Validate dependencies and local design context.").set_defaults(func=command_doctor)

    setup = sub.add_parser("setup", help="Create or update local configuration.")
    setup.add_argument("--org", required=True)
    setup.add_argument("--gmail-sender", required=True)
    setup.add_argument("--replay-retention-days", type=int, default=90)
    setup.add_argument("--analytics-disclosure")
    setup.add_argument("--default-locale", default="en-US")
    setup.set_defaults(func=command_setup)

    create = sub.add_parser("create-memo", help="Create memo metadata and source snapshot.")
    create.add_argument("--title", required=True)
    create.add_argument("--category", required=True)
    create.add_argument("--source", required=True)
    create.add_argument("--auth-mode", default="email+pin")
    create.add_argument("--version-label", default="A")
    create.add_argument("--shared-pin", help="Shared PIN for pin-only-with-email-capture mode. Generated if omitted.")
    create.set_defaults(func=command_create_memo)

    set_pin = sub.add_parser("set-memo-pin", help="Set or rotate the shared memo PIN (pin-only-with-email-capture mode).")
    set_pin.add_argument("--memo-id", required=True)
    set_pin.add_argument("--pin")
    set_pin.set_defaults(func=command_set_memo_pin)

    stakeholder = sub.add_parser("add-stakeholder", help="Add or update a stakeholder.")
    stakeholder.add_argument("--memo-id", required=True)
    stakeholder.add_argument("--email", required=True)
    stakeholder.add_argument("--name")
    stakeholder.add_argument("--org")
    stakeholder.add_argument("--role", default="investor")
    stakeholder.add_argument("--status", default="approved")
    stakeholder.add_argument("--locale", default="en-US")
    stakeholder.add_argument("--version-id")
    stakeholder.add_argument("--pin")
    stakeholder.set_defaults(func=command_add_stakeholder)

    reset = sub.add_parser("reset-pin", help="Reset stakeholder PIN.")
    reset.add_argument("--memo-id", required=True)
    reset.add_argument("--email", required=True)
    reset.add_argument("--pin")
    reset.set_defaults(func=command_reset_pin)

    email_pin = sub.add_parser("email-pin", help="Prepare a Gmail-ready PIN email payload and outbox entry.")
    email_pin.add_argument("--memo-id", required=True)
    email_pin.add_argument("--email", required=True)
    email_pin.add_argument("--pin", help="Existing visible PIN to send. PINs are hashed; use reset-pin first if unknown.")
    email_pin.add_argument("--subject")
    email_pin.add_argument("--body")
    email_pin.set_defaults(func=command_email_pin)

    revoke = sub.add_parser("revoke", help="Revoke or block stakeholder access.")
    revoke.add_argument("--memo-id", required=True)
    revoke.add_argument("--email", required=True)
    revoke.add_argument("--status", choices=["blocked", "revoked"], default="revoked")
    revoke.set_defaults(func=command_revoke)

    gate = sub.add_parser("gate", help="Run publish gate checks.")
    gate.add_argument("--memo-id", required=True)
    gate.add_argument("--check-links", action="store_true")
    gate.add_argument("--timeout", type=int, default=5)
    gate.set_defaults(func=command_gate)

    report = sub.add_parser("analytics-report", help="Summarize local analytics JSONL.")
    report.add_argument("--memo-id", required=True)
    report.set_defaults(func=command_report)

    bundle = sub.add_parser("generate-route-bundle", help="Generate reviewable zo.space route templates for a memo.")
    bundle.add_argument("--memo-id", required=True)
    bundle.add_argument("--output-dir")
    bundle.set_defaults(func=command_generate_route_bundle)

    export = sub.add_parser("export-zip", help="Create a simple skill ZIP export.")
    export.add_argument("--output", required=True)
    export.set_defaults(func=command_export_zip)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        fail("Interrupted", 130)


if __name__ == "__main__":
    raise SystemExit(main())
