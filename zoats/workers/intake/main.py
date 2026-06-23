#!/usr/bin/env python3
"""
ZoATS Email Intake Worker (Night 1)

- Ingest candidate application files from a local inbox drop folder
- Group multiple files per candidate using name/date heuristics
- Organize into jobs/<job>/candidates/<slug>/raw and write metadata.json

Safety & Defaults:
- Default action is copy; --move requires --confirm unless --dry-run
- Do NOT auto-create jobs/<job> or candidates/; error out if missing
- Console logging only; dry-run supported

Slug format:
  <name-prefix>--<YYYYMMDD>--<shortid>
Where
  name-prefix: first-last (or f-last) lowercase, hyphenated
  YYYYMMDD: applied date (JSON > filename > mtime in ET)
  shortid: 8-char Crockford base32 (lowercase)
"""

from __future__ import annotations
import argparse
import json
import logging
import os
import re
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger("email_intake")

ALLOWED_EXTS = {".pdf", ".docx", ".md", ".json"}
KEYWORDS = {"resume", "cv", "cover", "coverletter", "letter", "application", "portfolio", "profile"}
ET_TZ = ZoneInfo("America/New_York")
CROCKFORD32 = "0123456789abcdefghjkmnpqrstvwxyz"  # lowercase variant, no i/l/o/u


@dataclass
class FileInfo:
    path: Path
    stem: str
    ext: str
    mtime_et: datetime  # timezone-aware


@dataclass
class CandidateGroup:
    name_prefix: str
    applied_date: str  # YYYYMMDD
    files: List[FileInfo]
    source_action: str  # "copy" or "move"
    shortid: Optional[str] = None

    @property
    def slug(self) -> str:
        sid = self.shortid or "xxxxxxxx"
        return f"{self.name_prefix}--{self.applied_date}--{sid}"


# ---------- Helpers ----------

def iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_et(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(ET_TZ)


def list_allowed_files(src: Path) -> List[FileInfo]:
    items: List[FileInfo] = []
    for p in sorted(src.iterdir()):
        if not p.is_file():
            continue
        if p.name.startswith('.'):
            continue
        ext = p.suffix.lower()
        if ext not in ALLOWED_EXTS:
            logger.debug(f"Skipping disallowed file type: {p}")
            continue
        items.append(FileInfo(path=p, stem=p.stem, ext=ext, mtime_et=to_et(p.stat().st_mtime)))
    return items


def crockford32_encode_40bits(n: int) -> str:
    # Encodes lower 40 bits of n into 8 Crockford base32 chars (8 * 5 = 40)
    out = []
    for i in range(8):
        idx = (n >> (35 - 5 * i)) & 0x1F
        out.append(CROCKFORD32[idx])
    return "".join(out)


def gen_shortid() -> str:
    # Use 40 bits from UUID4 for compactness
    n = uuid.uuid4().int & ((1 << 40) - 1)
    return crockford32_encode_40bits(n)


def slugify_token(token: str) -> str:
    # Keep letters/numbers, lowercase
    return re.sub(r"[^a-z0-9]", "", token.lower())


def name_from_json(path: Path) -> Tuple[Optional[str], Optional[str]]:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None, None
    first = None
    last = None
    if isinstance(data, dict):
        # Try common keys
        if isinstance(data.get("first_name"), str):
            first = data.get("first_name")
        if isinstance(data.get("last_name"), str):
            last = data.get("last_name")
        if (not first or not last) and isinstance(data.get("name"), str):
            parts = [t for t in re.split(r"\s+", data["name"].strip()) if t]
            if parts:
                first = first or parts[0]
                last = last or (parts[-1] if len(parts) > 1 else None)
    if not first and not last:
        return None, None
    return first, last


def date_from_json(path: Path) -> Optional[str]:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    val = None
    if isinstance(data, dict):
        val = data.get("applied_at") or data.get("applied") or data.get("date")
    if not isinstance(val, str):
        return None
    # Try to parse ISO-like date/time
    try:
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
        # If naive, assume ET
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ET_TZ)
        dt_et = dt.astimezone(ET_TZ)
        return dt_et.strftime("%Y%m%d")
    except Exception:
        pass
    # Try simple YYYY-MM-DD or YYYYMMDD
    m = re.search(r"(20\d{2})[-_/]?(\d{2})[-_/]?(\d{2})", val)
    if m:
        return f"{m.group(1)}{m.group(2)}{m.group(3)}"
    return None


def extract_date_from_filename(stem: str) -> Optional[str]:
    # Prefer YYYYMMDD or YYYY-MM-DD in the stem
    m = re.search(r"(20\d{2})[-_\. ]?(\d{2})[-_\. ]?(\d{2})", stem)
    if m:
        return f"{m.group(1)}{m.group(2)}{m.group(3)}"
    return None


def tokens_from_stem(stem: str) -> List[str]:
    # split on separators and drop keyword tokens
    raw = re.split(r"[\s._-]+", stem)
    toks = []
    for t in raw:
        s = slugify_token(t)
        if not s:
            continue
        if s in KEYWORDS:
            continue
        toks.append(s)
    return toks


def derive_name_prefix_from_tokens(tokens: List[str]) -> Optional[str]:
    # Prefer first + last alphabetical tokens
    words = [t for t in tokens if t.isalpha()]
    if len(words) >= 2:
        return f"{words[0]}-{words[1]}"
    if len(tokens) >= 2:
        return f"{tokens[0]}-{tokens[1]}"
    if len(tokens) == 1:
        # f-last fallback not possible without 2 tokens; use token
        return tokens[0]
    return None


def name_prefix_from_filename(stem: str) -> Optional[str]:
    toks = tokens_from_stem(stem)
    return derive_name_prefix_from_tokens(toks)


def resolve_name_for_file(fi: FileInfo, json_hints: List[Tuple[Path, str, str]]) -> Optional[str]:
    # Try to match JSON-provided name tokens to filename tokens
    stem_toks = set(tokens_from_stem(fi.stem))
    for _, first_s, last_s in json_hints:
        # If both tokens appear in stem tokens, prefer this JSON name
        if first_s and last_s and first_s in stem_toks and last_s in stem_toks:
            return f"{first_s}-{last_s}"
    # Fallback to filename-derived name
    return name_prefix_from_filename(fi.stem)


def resolve_date_for_file(fi: FileInfo, json_dates: Dict[Path, str]) -> str:
    # 1) Any JSON date available? If exactly one JSON with date and its name matches, prefer that.
    # For Night 1 simplicity: if any JSON date exists, use filename-match preference; else filename date; else mtime ET
    date_from_stem = extract_date_from_filename(fi.stem)
    date_from_any_json = next(iter(json_dates.values()), None)
    if date_from_any_json:
        return date_from_any_json
    if date_from_stem:
        return date_from_stem
    return fi.mtime_et.strftime("%Y%m%d")


# ---------- Planner ----------

def plan_groups(files: List[FileInfo], src: Path) -> List[CandidateGroup]:
    # Gather JSON hints
    json_name_hints: List[Tuple[Path, str, str]] = []
    json_dates: Dict[Path, str] = {}
    for fi in files:
        if fi.ext == ".json":
            first, last = name_from_json(fi.path)
            if first and last:
                json_name_hints.append((fi.path, slugify_token(first), slugify_token(last)))
            d = date_from_json(fi.path)
            if d:
                json_dates[fi.path] = d

    # Group by (name_prefix, applied_date)
    tmp_groups: Dict[Tuple[str, str], List[FileInfo]] = {}
    for fi in files:
        name_prefix = resolve_name_for_file(fi, json_name_hints) or "unknown"
        applied_date = resolve_date_for_file(fi, json_dates)
        key = (name_prefix, applied_date)
        tmp_groups.setdefault(key, []).append(fi)

    groups: List[CandidateGroup] = []
    for (name_prefix, applied_date), fis in tmp_groups.items():
        groups.append(CandidateGroup(name_prefix=name_prefix, applied_date=applied_date, files=fis, source_action="copy"))
    return groups


# ---------- Execution ----------

def unique_dest_path(raw_dir: Path, basename: str) -> Path:
    dest = raw_dir / basename
    if not dest.exists():
        return dest
    stem = Path(basename).stem
    ext = Path(basename).suffix
    i = 1
    while True:
        cand = raw_dir / f"{stem}-{i}{ext}"
        if not cand.exists():
            return cand
        i += 1


def write_metadata(cand_dir: Path, group: CandidateGroup) -> None:
    files_meta = []
    for fi in group.files:
        dest_path = cand_dir / "raw" / fi.path.name
        # account for potential suffixing; if not found, try to match by stem
        if not dest_path.exists():
            # find any file with same stem
            matches = list((cand_dir / "raw").glob(f"{fi.path.stem}*{fi.path.suffix}"))
            if matches:
                dest_path = matches[0]
        files_meta.append({
            "original_name": fi.path.name,
            "stored_relpath": str(dest_path.relative_to(cand_dir)),
            "size_bytes": dest_path.stat().st_size if dest_path.exists() else None,
        })
    meta = {
        "id": group.shortid,
        "slug": group.slug,
        "job": None,  # filled by caller
        "created_at": iso_utc_now(),
        "name": {
            "first": None,  # Night 1: unknown unless JSON provided per-file; keep None
            "last": None,
            "full": group.name_prefix.replace("-", " ")
        },
        "applied_date": group.applied_date,
        "source": {"action": group.source_action},
        "files": files_meta,
    }
    (cand_dir / "metadata.json").write_text(json.dumps(meta, indent=2))


def perform_ingest(job: str, src: Path, do_move: bool, dry_run: bool) -> int:
    # Validate job structure (must exist; no auto-create)
    job_root = Path("jobs") / job
    cand_root = job_root / "candidates"
    if not job_root.exists() or not cand_root.exists():
        logger.error(f"Required job path missing: {cand_root} (and/or {job_root}). Will not create.")
        return 2

    files = list_allowed_files(src)
    if not files:
        logger.info("No files to ingest.")
        return 0

    groups = plan_groups(files, src)
    for g in groups:
        g.source_action = "move" if do_move else "copy"
        g.shortid = gen_shortid()

    # Plan
    total_files = sum(len(g.files) for g in groups)
    logger.info(f"Planned {len(groups)} candidate group(s), {total_files} file(s) total.")
    for g in groups:
        cand_dir = cand_root / g.slug
        raw_dir = cand_dir / "raw"
        logger.info(f"Candidate: {g.slug}")
        for fi in g.files:
            dest = unique_dest_path(raw_dir, fi.path.name)
            logger.info(f"  {g.source_action.upper()}: {fi.path} -> {dest}")

    if dry_run:
        logger.info("[DRY RUN] No changes made.")
        return 0

    # Execute
    successes = 0
    failures = 0
    for g in groups:
        cand_dir = cand_root / g.slug
        raw_dir = cand_dir / "raw"
        try:
            raw_dir.mkdir(parents=True, exist_ok=False)  # expect new candidate
        except FileExistsError:
            # If already exists, we will continue but avoid overwriting files
            raw_dir.mkdir(parents=True, exist_ok=True)
        for fi in g.files:
            try:
                dest = unique_dest_path(raw_dir, fi.path.name)
                if do_move:
                    fi.path.replace(dest)
                else:
                    dest.write_bytes(fi.path.read_bytes())
                if not dest.exists() or dest.stat().st_size <= 0:
                    raise RuntimeError("Destination missing or empty after operation")
                logger.info(f"OK: {fi.path.name} -> {dest}")
                successes += 1
            except Exception as e:
                logger.error(f"Fail: {fi.path} -> {raw_dir} :: {e}", exc_info=True)
                failures += 1
        try:
            write_metadata(cand_dir, g)
            # patch job into metadata
            meta_path = cand_dir / "metadata.json"
            m = json.loads(meta_path.read_text())
            m["job"] = job
            meta_path.write_text(json.dumps(m, indent=2))
        except Exception as e:
            logger.error(f"Failed to write metadata for {g.slug}: {e}", exc_info=True)
            failures += 1

    logger.info(f"Complete. Success files: {successes}, Failures: {failures}")
    return 0 if failures == 0 else 4


# ---------- CLI ----------

def main() -> int:
    ap = argparse.ArgumentParser(description="ZoATS Email Intake (Night 1)")
    ap.add_argument("--job", required=True, help="Job key matching jobs/<job>/candidates")
    ap.add_argument("--from", dest="src", required=True, help="Path to inbox_drop folder")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--move", action="store_true", help="Move files instead of copy")
    g.add_argument("--copy", action="store_true", help="Copy files (default)")
    ap.add_argument("--dry-run", action="store_true", help="Plan only; no changes")
    ap.add_argument("--confirm", action="store_true", help="Required for --move without --dry-run")
    args = ap.parse_args()

    src = Path(args.src).resolve()
    if not src.exists() or not src.is_dir():
        logger.error(f"Source folder does not exist or is not a directory: {src}")
        return 2

    # default to copy
    do_move = True if args.move else False
    if not args.move and not args.copy:
        do_move = False

    if do_move and not args.dry_run and not args.confirm:
        logger.error("Refusing to --move without --dry-run and --confirm")
        return 3

    try:
        return perform_ingest(job=args.job, src=src, do_move=do_move, dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
