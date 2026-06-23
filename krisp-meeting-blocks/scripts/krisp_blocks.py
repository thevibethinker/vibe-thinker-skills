#!/usr/bin/env python3
"""Portable Krisp meeting transcript block pipeline for Zo Computer."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib import request, error

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: pip install pyyaml") from exc

WORKSPACE = Path(os.environ.get("KRISP_BLOCKS_WORKSPACE", "/home/workspace"))
SKILL_DIR = Path(__file__).resolve().parents[1]
BLOCK_SPECS_DIR = SKILL_DIR / "block_specs"
CONFIG_PATH = SKILL_DIR / "config.yaml"
MEETINGS_ROOT = WORKSPACE / "Personal" / "Meetings"
ACTIVE_DIR = MEETINGS_ROOT / "Active"
NEEDS_REVIEW_DIR = MEETINGS_ROOT / "Needs-Review"
REJECTED_DIR = MEETINGS_ROOT / "Rejected"
INTEGRATION_DIR = WORKSPACE / "Personal" / "Integrations" / "krisp-meeting-blocks"
INCOMING_DIR = INTEGRATION_DIR / "incoming"
PROCESSED_PAYLOAD_DIR = INTEGRATION_DIR / "processed"
REJECTED_PAYLOAD_DIR = INTEGRATION_DIR / "rejected"
NOTIFICATION_LEDGER = INTEGRATION_DIR / "notifications.jsonl"
RUN_LOG = INTEGRATION_DIR / "run.log"
DEFAULT_MODEL = os.environ.get("MEETING_BLOCK_MODEL_NAME") or os.environ.get("ZO_CURRENT_MODEL_NAME") or os.environ.get("ZO_LAUNCH_MODEL_NAME") or ""
ZO_API_URL = "https://api.zo.computer/zo/ask"
MIN_TRANSCRIPT_CHARS = 300
MIN_DURATION_SECONDS = 120
ALWAYS_BLOCKS = ("summary", "metadata", "decisions", "action_items")
AI_DETECTED_BLOCKS = ("intro", "blurb")
GENERIC_SPEAKER_RE = re.compile(r"^(Speaker\s*\d+)\s*(?::|\|)", re.MULTILINE)
NAMED_SPEAKER_RE = re.compile(r"^(?!Speaker\s*\d+\b)([A-Z][A-Za-z0-9 ._@'’+-]{1,80})\s*(?::|\|)", re.MULTILINE)


class PipelineError(RuntimeError):
    """Raised when a pipeline step cannot continue safely."""


@dataclass(frozen=True)
class Paths:
    """Resolved storage paths used by the portable pipeline."""

    workspace: Path = WORKSPACE
    meetings_root: Path = MEETINGS_ROOT
    active: Path = ACTIVE_DIR
    needs_review: Path = NEEDS_REVIEW_DIR
    rejected: Path = REJECTED_DIR
    integration: Path = INTEGRATION_DIR
    incoming: Path = INCOMING_DIR
    processed_payloads: Path = PROCESSED_PAYLOAD_DIR
    rejected_payloads: Path = REJECTED_PAYLOAD_DIR
    notification_ledger: Path = NOTIFICATION_LEDGER
    run_log: Path = RUN_LOG


PATHS = Paths()


def setup_logging(verbose: bool = False) -> None:
    """Configure timestamped logging to stderr and the local run log."""
    PATHS.integration.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(sys.stderr), logging.FileHandler(PATHS.run_log, encoding="utf-8")],
    )


def utc_now() -> str:
    """Return current UTC timestamp with Z suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def today() -> str:
    """Return current UTC date."""
    return datetime.now(timezone.utc).date().isoformat()


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk with explicit errors."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PipelineError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PipelineError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PipelineError(f"expected object JSON in {path}")
    return data


def write_json(path: Path, data: dict[str, Any], *, dry_run: bool) -> None:
    """Write JSON and verify the result unless dry-run is active."""
    if dry_run:
        logging.info("dry-run: would write JSON %s", path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    check = read_json(path)
    if not isinstance(check, dict):
        raise PipelineError(f"state verification failed after writing {path}")


def write_text(path: Path, content: str, *, dry_run: bool) -> None:
    """Write text and verify exact bytes unless dry-run is active."""
    if dry_run:
        logging.info("dry-run: would write text %s", path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if path.read_text(encoding="utf-8") != content:
        raise PipelineError(f"state verification failed after writing {path}")


def append_jsonl(path: Path, event: dict[str, Any], *, dry_run: bool) -> None:
    """Append one JSONL event unless dry-run is active."""
    if dry_run:
        logging.info("dry-run: would append event to %s: %s", path, event)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def safe_slug(value: str, fallback: str = "meeting") -> str:
    """Return a filesystem-safe slug."""
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value or "").strip()).strip("-._")
    return slug[:96] or fallback


def load_config() -> dict[str, Any]:
    """Load optional local config."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise PipelineError(f"invalid YAML config at {CONFIG_PATH}: {exc}") from exc
    if not isinstance(data, dict):
        raise PipelineError(f"config must be a mapping: {CONFIG_PATH}")
    return data


def init_command(dry_run: bool) -> dict[str, Any]:
    """Initialize portable folders and default config."""
    directories = [
        PATHS.active,
        PATHS.needs_review,
        PATHS.rejected,
        PATHS.incoming,
        PATHS.processed_payloads,
        PATHS.rejected_payloads,
    ]
    for directory in directories:
        if dry_run:
            logging.info("dry-run: would create directory %s", directory)
        else:
            directory.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        config = {
            "min_transcript_chars": MIN_TRANSCRIPT_CHARS,
            "min_duration_seconds": MIN_DURATION_SECONDS,
            "addons_default": "auto",
            "notify_mode": "zo_ask",
            "notify_command": "",
            "archive": {"structure": "monthly", "root": str(MEETINGS_ROOT)},
        }
        write_text(CONFIG_PATH, yaml.safe_dump(config, sort_keys=False), dry_run=dry_run)
    return {"status": "initialized", "dry_run": dry_run, "directories": [str(d) for d in directories]}


def nested_get(data: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    """Try multiple top-level keys and return the first present value."""
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return default


def extract_payload_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize common Krisp payload shapes into pipeline fields."""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    meeting = data.get("meeting") if isinstance(data.get("meeting"), dict) else {}
    event_type = str(nested_get(payload, ("event_type", "type", "event"), "transcript_created"))
    event_id = str(nested_get(payload, ("event_id", "id"), ""))
    meeting_id = str(nested_get(meeting, ("id", "meeting_id"), nested_get(data, ("meeting_id", "id"), "")))
    title = str(nested_get(meeting, ("title", "name", "subject"), nested_get(data, ("title", "name", "subject"), "Krisp Meeting")))
    raw_content = data.get("raw_content") or data.get("transcript") or data.get("text") or ""
    content_items = data.get("content") if isinstance(data.get("content"), list) else []
    participants = meeting.get("participants") if isinstance(meeting.get("participants"), list) else data.get("participants", [])
    start = meeting.get("start_date") or meeting.get("started_at") or data.get("start_time") or data.get("started_at")
    end = meeting.get("end_date") or meeting.get("ended_at") or data.get("end_time") or data.get("ended_at")
    duration = meeting.get("duration") or data.get("duration") or data.get("duration_seconds")
    return {
        "event_type": event_type,
        "event_id": event_id,
        "meeting_id": meeting_id,
        "title": title,
        "raw_content": raw_content,
        "content_items": content_items,
        "participants": participants if isinstance(participants, list) else [],
        "start": start,
        "end": end,
        "duration_seconds": parse_int(duration),
        "recording_url": data.get("recording_url") or meeting.get("recording_url") or data.get("url") or "",
        "source_payload": payload,
    }


def parse_int(value: Any) -> int | None:
    """Parse an int or return None."""
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def parse_datetime(value: Any) -> datetime | None:
    """Parse common ISO datetime strings."""
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def duration_from_fields(fields: dict[str, Any]) -> int | None:
    """Resolve duration from explicit duration or start/end."""
    if fields.get("duration_seconds") is not None:
        return fields["duration_seconds"]
    start = parse_datetime(fields.get("start"))
    end = parse_datetime(fields.get("end"))
    if start and end and end >= start:
        return int((end - start).total_seconds())
    return None


def date_from_fields(fields: dict[str, Any]) -> str:
    """Resolve meeting date from start time or current date."""
    start = parse_datetime(fields.get("start"))
    return start.date().isoformat() if start else today()


def participant_name(item: Any) -> str:
    """Extract a displayable participant name from source metadata."""
    if isinstance(item, dict):
        return str(item.get("name") or item.get("email") or item.get("display_name") or item.get("label") or "").strip()
    return str(item or "").strip()


def build_transcript(fields: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """Build markdown transcript and structured utterances from Krisp fields."""
    utterances: list[dict[str, Any]] = []
    lines: list[str] = []
    raw_content = fields.get("raw_content")
    if isinstance(raw_content, str) and raw_content.strip():
        return raw_content.strip() + "\n", utterances
    for item in fields.get("content_items", []):
        if isinstance(item, str):
            text = item.strip()
            if text:
                lines.append(text)
            continue
        if not isinstance(item, dict):
            continue
        speaker = str(item.get("speaker") or item.get("speaker_name") or item.get("participant") or item.get("name") or "Speaker").strip()
        text = str(item.get("text") or item.get("content") or "").strip()
        if not text:
            continue
        start_ms = parse_int(item.get("start_ms") or item.get("start"))
        end_ms = parse_int(item.get("end_ms") or item.get("end"))
        utterances.append({"speaker": speaker, "text": text, "start_ms": start_ms, "end_ms": end_ms})
        lines.append(f"{speaker}: {text}")
    return "\n".join(lines).strip() + ("\n" if lines else ""), utterances


def transcript_analysis(transcript: str, participants: list[Any]) -> dict[str, Any]:
    """Analyze speaker reliability without inventing participant identity."""
    generic = []
    named = []
    for match in GENERIC_SPEAKER_RE.finditer(transcript):
        label = match.group(1).strip()
        if label not in generic:
            generic.append(label)
    for match in NAMED_SPEAKER_RE.finditer(transcript):
        label = match.group(1).strip()
        if label.lower() not in {"date", "title", "participants", "duration", "source", "transcript"} and label not in named:
            named.append(label)
    participant_names = [participant_name(p) for p in participants if participant_name(p)]
    if generic and participant_names:
        state = "generic_labeled_with_metadata"
    elif generic:
        state = "generic_labeled"
    elif named:
        state = "reliable_multi_speaker"
    elif transcript.strip():
        state = "single_stream_or_unlabeled"
    else:
        state = "missing_transcript"
    return {
        "state": state,
        "generic_labels": generic,
        "named_speakers": named,
        "participant_names": participant_names,
        "identity_policy": "do_not_infer_identity_from_generic_speakers",
        "analyzed_at": utc_now(),
    }


def quality_gate(fields: dict[str, Any], transcript: str, config: dict[str, Any]) -> dict[str, Any]:
    """Classify meeting quality into processable, partial, or needs_review."""
    min_chars = int(config.get("min_transcript_chars", MIN_TRANSCRIPT_CHARS))
    min_duration = int(config.get("min_duration_seconds", MIN_DURATION_SECONDS))
    duration = duration_from_fields(fields)
    reasons: list[str] = []
    warnings: list[str] = []
    if len(transcript.strip()) < min_chars:
        reasons.append(f"transcript_too_short:{len(transcript.strip())}<{min_chars}")
    if duration is not None and duration < min_duration:
        reasons.append(f"duration_too_short:{duration}<{min_duration}")
    analysis = transcript_analysis(transcript, fields.get("participants", []))
    if analysis["state"] == "generic_labeled" and not fields.get("title"):
        reasons.append("generic_speakers_without_context")
    if duration and transcript.strip():
        expected_low_words = max(40, int(duration / 60 * 60))
        actual_words = len(re.findall(r"\b\w+\b", transcript))
        if duration >= 600 and actual_words < expected_low_words * 0.35:
            warnings.append(f"appears_partial:words={actual_words},duration_seconds={duration}")
    status = "needs_review" if reasons else "partial" if warnings else "processable"
    return {"status": status, "reasons": reasons, "warnings": warnings, "duration_seconds": duration, "transcript_analysis": analysis}


def manifest_seed(fields: dict[str, Any], transcript: str, payload_path: Path) -> dict[str, Any]:
    """Create initial manifest for a portable meeting folder."""
    meeting_date = date_from_fields(fields)
    source_id = fields.get("meeting_id") or hashlib.sha256(transcript.encode()).hexdigest()[:16]
    title = fields.get("title") or "Krisp Meeting"
    return {
        "manifest_version": "1.0",
        "meeting_id": "",
        "title": title,
        "date": meeting_date,
        "status": "imported",
        "source": {
            "type": "krisp",
            "source_id": source_id,
            "event_id": fields.get("event_id") or "",
            "payload_path": str(payload_path),
            "recording_url": fields.get("recording_url") or "",
            "ingested_at": utc_now(),
        },
        "participants": [participant_name(p) for p in fields.get("participants", []) if participant_name(p)],
        "timestamps": {"created_at": utc_now(), "ingested_at": utc_now()},
        "quality": {},
        "block_completion": {"generated": [], "failed": [], "partial": False},
        "notifications": [],
    }


def render_enrichment(analysis: dict[str, Any]) -> str:
    """Render human-editable ENRICHMENT.yaml."""
    speaker_lines = ["speaker_map:"]
    labels = analysis.get("generic_labels") if isinstance(analysis.get("generic_labels"), list) else []
    if labels:
        for label in labels:
            speaker_lines.append(f'  {label}: ""')
    else:
        speaker_lines.append("  {}")
    return "\n".join([
        "# ENRICHMENT.yaml",
        '# Edit this file, then run: krisp_blocks.py reprocess <meeting-folder>',
        "# Do not invent speaker identities. Leave unknown labels blank.",
        *speaker_lines,
        'title_override: ""',
        'notes: ""',
        "",
    ])


def apply_enrichment(meeting_dir: Path, transcript: str) -> tuple[str, dict[str, Any]]:
    """Apply ENRICHMENT.yaml speaker/title hints to the working transcript."""
    enrichment_path = meeting_dir / "ENRICHMENT.yaml"
    if not enrichment_path.exists():
        return transcript, {}
    try:
        enrichment = yaml.safe_load(enrichment_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise PipelineError(f"invalid ENRICHMENT.yaml in {meeting_dir}: {exc}") from exc
    if not isinstance(enrichment, dict):
        return transcript, {}
    speaker_map = enrichment.get("speaker_map") if isinstance(enrichment.get("speaker_map"), dict) else {}
    updated = transcript
    for label, name in speaker_map.items():
        label_s = str(label).strip()
        name_s = str(name).strip()
        if not label_s or not name_s:
            continue
        updated = re.sub(rf"^{re.escape(label_s)}(\s*)(:|\|)", rf"{name_s}\1\2", updated, flags=re.MULTILINE)
    return updated, enrichment


def unique_folder(parent: Path, base_name: str) -> Path:
    """Return a non-existing folder path under parent."""
    candidate = parent / base_name
    counter = 1
    while candidate.exists():
        candidate = parent / f"{base_name}_{counter}"
        counter += 1
    return candidate


def import_payload(payload_path: Path, *, process: bool, dry_run: bool, addons: str) -> dict[str, Any]:
    """Import one Krisp payload into Active or review/rejected lanes."""
    config = load_config()
    payload = read_json(payload_path)
    fields = extract_payload_fields(payload)
    if fields["event_type"] != "transcript_created":
        return {"status": "skipped", "reason": f"event_type={fields['event_type']}", "payload_path": str(payload_path)}
    transcript, utterances = build_transcript(fields)
    gate = quality_gate(fields, transcript, config)
    manifest = manifest_seed(fields, transcript, payload_path)
    manifest["quality"] = gate
    manifest["transcript_analysis"] = gate["transcript_analysis"]
    manifest["utterance_count"] = len(utterances)
    date_part = manifest["date"]
    title_part = safe_slug(manifest["title"], "krisp-meeting")
    folder_name = f"{date_part}_{title_part}"
    target_root = PATHS.rejected if gate["status"] == "needs_review" and "transcript_too_short" in ";".join(gate["reasons"]) else PATHS.needs_review if gate["status"] == "needs_review" else PATHS.active
    meeting_dir = unique_folder(target_root, folder_name)
    manifest["meeting_id"] = meeting_dir.name
    if dry_run:
        logging.info("dry-run: would import payload %s to %s", payload_path, meeting_dir)
        return {"status": gate["status"], "meeting_dir": str(meeting_dir), "dry_run": True, "quality": gate}
    meeting_dir.mkdir(parents=True, exist_ok=False)
    write_text(meeting_dir / "transcript.original.md", transcript, dry_run=False)
    write_text(meeting_dir / "transcript.md", transcript, dry_run=False)
    write_text(meeting_dir / "transcript.jsonl", "\n".join(json.dumps(u, ensure_ascii=False) for u in utterances) + ("\n" if utterances else ""), dry_run=False)
    write_text(meeting_dir / "ENRICHMENT.yaml", render_enrichment(gate["transcript_analysis"]), dry_run=False)
    write_json(meeting_dir / "manifest.json", manifest, dry_run=False)
    destination = PATHS.rejected_payloads if target_root == PATHS.rejected else PATHS.processed_payloads
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(payload_path, destination / payload_path.name)
    if gate["status"] == "needs_review":
        notify(meeting_dir, manifest, "needs_review", "; ".join(gate["reasons"]), dry_run=False)
    elif gate["status"] == "partial":
        notify(meeting_dir, manifest, "partial", "; ".join(gate["warnings"]), dry_run=False)
    if process and gate["status"] == "processable":
        return process_meeting(meeting_dir, dry_run=False, addons=addons)
    return {"status": gate["status"], "meeting_dir": str(meeting_dir), "quality": gate}


def load_block_specs() -> dict[str, dict[str, Any]]:
    """Load block spec YAML files."""
    specs: dict[str, dict[str, Any]] = {}
    for path in sorted(BLOCK_SPECS_DIR.glob("*.yaml")):
        try:
            spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise PipelineError(f"invalid block spec {path}: {exc}") from exc
        if not isinstance(spec, dict) or not spec.get("id"):
            raise PipelineError(f"block spec missing id: {path}")
        specs[str(spec["id"])] = spec
    return specs


def cue_present(transcript: str, cues: Iterable[str]) -> bool:
    """Return true when any cue phrase appears on word boundaries."""
    lower = transcript.lower()
    for cue in cues:
        phrase = str(cue).strip().lower()
        if not phrase:
            continue
        pattern = r"\b" + r"\s+".join(re.escape(part) for part in phrase.split()) + r"\b"
        if re.search(pattern, lower):
            return True
    return False


def select_blocks(transcript: str, addons: str, specs: dict[str, dict[str, Any]]) -> list[str]:
    """Select blocks by always-on, ai-detected, and add-on policy."""
    selected = [block for block in ALWAYS_BLOCKS if block in specs]
    for block_id in AI_DETECTED_BLOCKS:
        spec = specs.get(block_id)
        if spec and cue_present(transcript, spec.get("detect_cue", [])):
            selected.append(block_id)
    addon_ids = [bid for bid, spec in specs.items() if spec.get("trigger") == "addon"]
    if addons == "all":
        selected.extend(addon_ids)
    elif addons == "auto":
        for block_id in addon_ids:
            if cue_present(transcript, specs[block_id].get("detect_cue", [])):
                selected.append(block_id)
    return list(dict.fromkeys(selected))


def call_zo(prompt: str, model: str | None) -> str:
    """Call /zo/ask and return block content."""
    token = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")
    if not token:
        raise PipelineError("ZO_CLIENT_IDENTITY_TOKEN is not set")
    body: dict[str, Any] = {"input": prompt}
    if model:
        body["model_name"] = model
    payload = json.dumps(body).encode("utf-8")
    req = request.Request(
        ZO_API_URL,
        data=payload,
        headers={"authorization": token, "content-type": "application/json", "accept": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise PipelineError(f"/zo/ask HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise PipelineError(f"/zo/ask network error: {exc.reason}") from exc
    output = data.get("output") if isinstance(data, dict) else ""
    return str(output).strip()


def fallback_block(block_id: str) -> str:
    """Return deterministic fallback content for failed block generation."""
    return f"## {block_id.replace('_', ' ').title()}\n\nNo reliable content generated. Review the transcript and rerun.\n"


def block_prompt(block_id: str, spec: dict[str, Any], manifest: dict[str, Any], transcript: str) -> str:
    """Build a concise block-generation prompt."""
    return textwrap.dedent(f"""
    Write the `{block_id}` meeting block for: {manifest.get('title') or manifest.get('meeting_id')}.

    Purpose: {spec.get('purpose')}

    Rules:
    - Use only the transcript and manifest facts below.
    - Do not invent participant identities from generic `Speaker N` labels.
    - Return only clean markdown body; do not include YAML frontmatter or code fences.
    - If the transcript does not support the block, say that explicitly.

    Manifest:
    {json.dumps(manifest, indent=2, ensure_ascii=False)[:4000]}

    Transcript:
    {transcript[:30000]}
    """).strip()


def render_frontmatter(block_id: str, manifest: dict[str, Any], partial: bool) -> str:
    """Render standard YAML frontmatter for generated blocks."""
    data = {
        "created": today(),
        "last_edited": today(),
        "version": "1.0",
        "provenance": "krisp-meeting-blocks",
        "block_id": block_id,
        "meeting_id": manifest.get("meeting_id", ""),
        "meeting_title": manifest.get("title", ""),
        "partial": partial,
    }
    return "---\n" + yaml.safe_dump(data, sort_keys=False).strip() + "\n---\n\n"


def generate_block(meeting_dir: Path, block_id: str, spec: dict[str, Any], manifest: dict[str, Any], transcript: str, *, dry_run: bool) -> tuple[bool, str]:
    """Generate one block file, falling back on error."""
    if dry_run:
        logging.info("dry-run: would generate block %s", block_id)
        return True, "dry_run"
    model = os.environ.get("MEETING_BLOCK_MODEL_NAME") or DEFAULT_MODEL or None
    try:
        body = call_zo(block_prompt(block_id, spec, manifest, transcript), model=model)
        if not body:
            raise PipelineError("empty block response")
        partial = False
    except PipelineError as exc:
        logging.warning("block generation failed for %s: %s", block_id, exc)
        body = fallback_block(block_id)
        partial = True
    content = render_frontmatter(block_id, manifest, partial) + body.strip() + "\n"
    write_text(meeting_dir / f"{block_id}.md", content, dry_run=False)
    return not partial, "ok" if not partial else "fallback_generated"


def process_meeting(meeting_dir: Path, *, dry_run: bool, addons: str) -> dict[str, Any]:
    """Process one meeting into block files and monthly archive."""
    if not meeting_dir.exists() or not meeting_dir.is_dir():
        raise PipelineError(f"meeting folder not found: {meeting_dir}")
    manifest = read_json(meeting_dir / "manifest.json")
    source = meeting_dir / "transcript.original.md"
    if not source.exists():
        source = meeting_dir / "transcript.md"
    if not source.exists():
        raise PipelineError(f"missing transcript in {meeting_dir}")
    original = source.read_text(encoding="utf-8")
    transcript, enrichment = apply_enrichment(meeting_dir, original)
    write_text(meeting_dir / "transcript.md", transcript, dry_run=dry_run)
    if enrichment.get("title_override"):
        manifest["title"] = str(enrichment["title_override"]).strip()
    manifest["status"] = "processing"
    manifest.setdefault("timestamps", {})["processing_started_at"] = utc_now()
    write_json(meeting_dir / "manifest.json", manifest, dry_run=dry_run)
    specs = load_block_specs()
    selected = select_blocks(transcript, addons, specs)
    generated: list[str] = []
    failed: list[dict[str, str]] = []
    for block_id in selected:
        ok, reason = generate_block(meeting_dir, block_id, specs[block_id], manifest, transcript, dry_run=dry_run)
        if ok:
            generated.append(block_id)
        else:
            failed.append({"block_id": block_id, "reason": reason})
    partial = bool(failed)
    manifest["status"] = "partial" if partial else "processed"
    manifest["block_completion"] = {"requested": selected, "generated": generated, "failed": failed, "partial": partial}
    manifest.setdefault("timestamps", {})["processed_at"] = utc_now()
    write_json(meeting_dir / "manifest.json", manifest, dry_run=dry_run)
    if partial:
        notify(meeting_dir, manifest, "partial", f"block failures: {failed}", dry_run=dry_run)
    archive_result = archive_monthly(meeting_dir, manifest, dry_run=dry_run)
    return {"status": manifest["status"], "meeting_dir": str(meeting_dir), "blocks": manifest["block_completion"], "archive": archive_result}


def archive_monthly(meeting_dir: Path, manifest: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    """Move a terminal meeting into YYYY/MM-Month archive structure."""
    date_value = str(manifest.get("date") or today())[:10]
    try:
        dt = datetime.strptime(date_value, "%Y-%m-%d")
    except ValueError:
        dt = datetime.now(timezone.utc)
    target_dir = MEETINGS_ROOT / f"{dt.year:04d}" / f"{dt.month:02d}-{dt.strftime('%B')}"
    target_path = target_dir / meeting_dir.name
    if target_path.exists():
        raise PipelineError(f"archive collision: {target_path}")
    if dry_run:
        logging.info("dry-run: would archive %s -> %s", meeting_dir, target_path)
        return {"archived": False, "dry_run": True, "target": str(target_path)}
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest["status"] = "archived_partial" if manifest.get("status") == "partial" else "archived"
    manifest.setdefault("timestamps", {})["archived_at"] = utc_now()
    write_json(meeting_dir / "manifest.json", manifest, dry_run=False)
    shutil.move(str(meeting_dir), str(target_path))
    if not target_path.exists():
        raise PipelineError(f"archive verification failed: {target_path}")
    return {"archived": True, "target": str(target_path)}


def notify(meeting_dir: Path, manifest: dict[str, Any], level: str, reason: str, *, dry_run: bool) -> None:
    """Record and optionally dispatch a portable notification event."""
    event = {
        "at": utc_now(),
        "level": level,
        "reason": reason,
        "meeting_id": manifest.get("meeting_id"),
        "title": manifest.get("title"),
        "meeting_dir": str(meeting_dir),
    }
    append_jsonl(PATHS.notification_ledger, event, dry_run=dry_run)
    if dry_run:
        return
    config = load_config()
    mode = str(config.get("notify_mode") or "ledger").strip().lower()
    command = str(config.get("notify_command") or "").strip()
    if mode == "command" and command:
        run_notify_command(command, event)
    elif mode == "zo_ask":
        notify_via_zo_ask(event)


def run_notify_command(command: str, event: dict[str, Any]) -> None:
    """Run a local notification command with event JSON on stdin."""
    try:
        subprocess.run(command, input=json.dumps(event), text=True, shell=True, check=False, timeout=30)
    except subprocess.SubprocessError as exc:
        logging.warning("notification command failed: %s", exc)


def notify_via_zo_ask(event: dict[str, Any]) -> None:
    """Ask this Zo to notify its owner using the owner's configured channel."""
    prompt = (
        "Notify this Zo's owner that a Krisp meeting pipeline item requires attention. "
        "Use the owner's configured direct notification channel if available. "
        "Keep it concise and include the meeting title, status, reason, and folder path. "
        "Do not message anyone except the Zo owner.\n\n"
        + json.dumps(event, indent=2, ensure_ascii=False)
    )
    try:
        call_zo(prompt, model=os.environ.get("MEETING_BLOCK_MODEL_NAME") or DEFAULT_MODEL or None)
    except PipelineError as exc:
        logging.warning("zo_ask notification failed: %s", exc)


def reprocess_meeting(meeting_dir: Path, *, dry_run: bool, addons: str) -> dict[str, Any]:
    """Reprocess from immutable transcript plus ENRICHMENT.yaml."""
    return process_meeting(meeting_dir, dry_run=dry_run, addons=addons)


def status_command() -> dict[str, Any]:
    """Summarize active/review/archive counts."""
    years = [p for p in MEETINGS_ROOT.glob("20[0-9][0-9]") if p.is_dir()]
    archived = sum(1 for year in years for _ in year.rglob("manifest.json"))
    return {
        "active": sum(1 for _ in PATHS.active.glob("*/manifest.json")) if PATHS.active.exists() else 0,
        "needs_review": sum(1 for _ in PATHS.needs_review.glob("*/manifest.json")) if PATHS.needs_review.exists() else 0,
        "rejected": sum(1 for _ in PATHS.rejected.glob("*/manifest.json")) if PATHS.rejected.exists() else 0,
        "archived": archived,
        "notification_ledger": str(PATHS.notification_ledger),
    }


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description="Portable Krisp meeting blocks pipeline")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create folders and default config")
    init.add_argument("--dry-run", action="store_true", help="Preview writes")

    imp = sub.add_parser("import", help="Import one Krisp payload")
    imp.add_argument("payload", help="Path to webhook JSON payload")
    imp.add_argument("--process", action="store_true", help="Process immediately when quality gate passes")
    imp.add_argument("--addons", choices=["auto", "all", "none"], default=None, help="Add-on block policy")
    imp.add_argument("--dry-run", action="store_true", help="Preview writes")

    proc = sub.add_parser("process", help="Process one meeting folder")
    proc.add_argument("meeting", help="Meeting folder path")
    proc.add_argument("--addons", choices=["auto", "all", "none"], default=None, help="Add-on block policy")
    proc.add_argument("--dry-run", action="store_true", help="Preview writes")

    rep = sub.add_parser("reprocess", help="Regenerate from transcript.original.md and ENRICHMENT.yaml")
    rep.add_argument("meeting", help="Meeting folder path")
    rep.add_argument("--addons", choices=["auto", "all", "none"], default=None, help="Add-on block policy")
    rep.add_argument("--dry-run", action="store_true", help="Preview writes")

    sub.add_parser("status", help="Show queue/archive status")
    return parser


def effective_addons(value: str | None) -> str:
    """Resolve add-on policy from CLI/config."""
    if value:
        return value
    config = load_config()
    configured = str(config.get("addons_default") or "auto")
    return configured if configured in {"auto", "all", "none"} else "auto"


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging(args.verbose)
    try:
        start = time.time()
        if args.command == "init":
            result = init_command(dry_run=args.dry_run)
        elif args.command == "import":
            result = import_payload(Path(args.payload).expanduser().resolve(), process=args.process, dry_run=args.dry_run, addons=effective_addons(args.addons))
        elif args.command == "process":
            result = process_meeting(Path(args.meeting).expanduser().resolve(), dry_run=args.dry_run, addons=effective_addons(args.addons))
        elif args.command == "reprocess":
            result = reprocess_meeting(Path(args.meeting).expanduser().resolve(), dry_run=args.dry_run, addons=effective_addons(args.addons))
        elif args.command == "status":
            result = status_command()
        else:  # pragma: no cover
            parser.error("unknown command")
        result["elapsed_seconds"] = round(time.time() - start, 3)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except PipelineError as exc:
        logging.error("%s", exc)
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
