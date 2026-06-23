#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
import secrets
import string

ROOT = Path(__file__).resolve().parents[2]  # ZoATS/
INBOX = ROOT / "inbox_drop"
JOBS_DIR = ROOT / "jobs"

RESUME_EXTS = {".pdf", ".docx", ".md", ".txt"}
META_FILENAME = "metadata.json"
TIME_WINDOW_SECONDS = 120  # bundle proximity window

SAFE_CHARS = string.ascii_lowercase + string.digits + "-"


def log(msg: str):
    print(msg, flush=True)


def slugify(text: str, fallback: str = "unknown") -> str:
    if not text:
        return fallback
    text = text.strip().lower()
    # replace non alnum with hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or fallback


def short_id(n: int = 6) -> str:
    # base32-ish: use secrets token and keep alnum
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


def ensure_job(job: str, dry_run: bool = False) -> Path:
    job_path = JOBS_DIR / job
    candidates = job_path / "candidates"
    created = []
    for p in [job_path, candidates]:
        if not p.exists():
            created.append(str(p))
            if not dry_run:
                p.mkdir(parents=True, exist_ok=True)
    if created:
        log(f"[init] created: {', '.join(created)}")
    return candidates


def detect_jobs() -> list[str]:
    if not JOBS_DIR.exists():
        return []
    return sorted([p.name for p in JOBS_DIR.iterdir() if p.is_dir()])


def resolve_job(job_arg: str | None, dry_run: bool) -> str:
    jobs = detect_jobs()
    if job_arg:
        return job_arg
    if len(jobs) == 1:
        log(f"[job] defaulting to single job: {jobs[0]}")
        return jobs[0]
    if len(jobs) == 0:
        # create a default job?
        default = "job-001"
        log(f"[job] no jobs found, initializing default: {default}")
        if not dry_run:
            ensure_job(default, dry_run=False)
        return default
    raise SystemExit("--job is required when multiple jobs exist")


def scan_inbox() -> list[Path]:
    INBOX.mkdir(parents=True, exist_ok=True)
    return sorted([p for p in INBOX.iterdir() if p.is_file()])


def group_bundles(files: list[Path]) -> list[list[Path]]:
    if not files:
        return []
    # Sort by mtime to use temporal proximity
    files = sorted(files, key=lambda p: p.stat().st_mtime)

    def key_for(p: Path) -> str:
        stem = p.stem.lower()
        # normalize common separators
        stem = re.sub(r"[^a-z0-9]+", "-", stem)
        stem = re.sub(r"-+", "-", stem).strip("-")
        return stem

    bundles: list[list[Path]] = []
    current: list[Path] = []
    prev_time = None
    prev_key = None

    for f in files:
        t = f.stat().st_mtime
        k = key_for(f)
        if not current:
            current = [f]
            prev_time = t
            prev_key = k
            continue
        # same key OR close in time → bundle together
        if k == prev_key or (prev_time is not None and abs(t - prev_time) <= TIME_WINDOW_SECONDS):
            current.append(f)
            prev_time = t
            prev_key = k
        else:
            bundles.append(current)
            current = [f]
            prev_time = t
            prev_key = k
    if current:
        bundles.append(current)

    # Post-process: if a bundle has clearly different stems, split conservatively
    refined: list[list[Path]] = []
    for b in bundles:
        stems = {key_for(x) for x in b}
        if len(stems) == 1:
            refined.append(b)
        else:
            # split by stem groups
            groups: dict[str, list[Path]] = {}
            for x in b:
                groups.setdefault(key_for(x), []).append(x)
            refined.extend(groups.values())
    return refined


def has_resume_like(bundle: list[Path]) -> bool:
    return any(x.suffix.lower() in RESUME_EXTS for x in bundle)


def read_metadata(bundle: list[Path]) -> dict:
    meta = {}
    for p in bundle:
        if p.name.lower() == META_FILENAME:
            try:
                meta = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                meta = {}
            break
    return meta


def date_from(meta: dict, bundle: list[Path]) -> str:
    # yyyymmdd
    if (d := meta.get("applied_date")):
        try:
            # accept YYYY-MM-DD or YYYY/MM/DD
            dt = datetime.fromisoformat(d.replace("/", "-"))
            return dt.strftime("%Y%m%d")
        except Exception:
            pass
    # fallback to newest file mtime date
    t = max(p.stat().st_mtime for p in bundle)
    return datetime.fromtimestamp(t).strftime("%Y%m%d")


def name_from(meta: dict, bundle: list[Path]) -> str:
    if (n := meta.get("name")):
        return n
    # try derive from filename (first resume-like)
    for p in bundle:
        if p.suffix.lower() in RESUME_EXTS:
            # remove words like resume, cv, application
            stem = p.stem
            stem = re.sub(r"(?i)(resume|cv|application|candidate)", "", stem)
            stem = re.sub(r"[_-]+", " ", stem).strip()
            if stem:
                return stem
    return "unknown"


def build_candidate_id(job: str, meta: dict, bundle: list[Path]) -> str:
    role_code = slugify(meta.get("role_code") or job)
    name_slug = slugify(name_from(meta, bundle))
    date_part = date_from(meta, bundle)
    sid = short_id(6)
    return f"{role_code}-{name_slug}-{date_part}-{sid}"


def write_interactions_md(path: Path, meta: dict, files_moved: list[Path], source: str | None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append(f"# Interactions\n")
    lines.append(f"\n")
    lines.append(f"## {ts} — Intake\n")
    if source:
        lines.append(f"Source: {source}\n")
    if meta:
        safe_meta = {k: v for k, v in meta.items() if k in {"name", "email", "source", "applied_date", "role_code"}}
        if safe_meta:
            lines.append(f"Metadata: `{json.dumps(safe_meta)}`\n")
    lines.append("Files:\n")
    for f in files_moved:
        lines.append(f"- {f.name}\n")
    content = "".join(lines)
    path.write_text(content, encoding="utf-8")


def move_bundle(bundle: list[Path], dest_raw: Path, dry_run: bool) -> list[Path]:
    moved: list[Path] = []
    for src in bundle:
        target = dest_raw / src.name
        if dry_run:
            log(f"[dry-run] move {src} -> {target}")
            moved.append(target)
        else:
            shutil.move(str(src), str(target))
            moved.append(target)
    return moved


def process_bundle(job: str, bundle: list[Path], dry_run: bool):
    meta = read_metadata(bundle)
    candidate_id = build_candidate_id(job, meta, bundle)
    job_candidates_dir = ensure_job(job, dry_run=dry_run)

    candidate_dir = job_candidates_dir / candidate_id
    raw_dir = candidate_dir / "raw"
    parsed_dir = candidate_dir / "parsed"
    outputs_dir = candidate_dir / "outputs"

    # Idempotency: if raw_dir exists and contains any of these files, skip
    already = raw_dir.exists() and any((raw_dir / p.name).exists() for p in bundle)
    if already:
        log(f"[skip] {candidate_id} appears already processed (files present)")
        return

    if dry_run:
        log(f"[dry-run] mkdir -p {raw_dir}")
        log(f"[dry-run] mkdir -p {parsed_dir}")
        log(f"[dry-run] mkdir -p {outputs_dir}")
    else:
        raw_dir.mkdir(parents=True, exist_ok=True)
        parsed_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

    moved = move_bundle(bundle, raw_dir, dry_run=dry_run)

    interactions_md = candidate_dir / "interactions.md"
    source = meta.get("source") if isinstance(meta, dict) else None
    if dry_run:
        log(f"[dry-run] write {interactions_md}")
    else:
        write_interactions_md(interactions_md, meta, moved, source)
        log(f"[ok] {candidate_id} created; {len(moved)} file(s) moved")


def main():
    parser = argparse.ArgumentParser(description="Candidate Intake Processor")
    parser.add_argument("--job", help="Job code/name to route candidates; required if multiple jobs exist")
    parser.add_argument("--dry-run", action="store_true", help="Plan actions without writing")
    args = parser.parse_args()

    job = resolve_job(args.job, dry_run=args.dry_run)
    ensure_job(job, dry_run=args.dry_run)

    files = scan_inbox()
    if not files:
        log("[inbox] no files found in inbox_drop/")
        return 0

    bundles = group_bundles(files)
    log(f"[inbox] detected {len(bundles)} bundle(s)")

    processed = 0
    for b in bundles:
        if not has_resume_like(b):
            names = ", ".join(x.name for x in b)
            log(f"[hold] no resume-like files in bundle: {names} → staying in inbox_drop/")
            continue
        process_bundle(job, b, dry_run=args.dry_run)
        processed += 1

    log(f"[done] processed {processed} bundle(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
