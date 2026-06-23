#!/usr/bin/env python3
"""Verify the local ZoATS skill package shape without provisioning routes or touching external state."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "SKILL.md",
    "references/original-repo-readme.md",
    "references/migration/source-manifest.json",
    "config/settings.example.json",
    "config/commands.jsonl",
    "schemas/candidate.schema.json",
    "schemas/job.schema.json",
    "pipeline/run.py",
    "lib/paths.py",
    "workers/parser/main.py",
    "workers/scoring/main.py",
    "workers/rubric/main.py",
    "space-routes/manifest.json",
    "tests/test_pipeline.py",
]

FORBIDDEN = [
    ".git",
    "config/settings.json",
    "logs",
    "jobs/[redacted-private-job-slug-1]",
    "jobs/[redacted-private-job-slug-2]",
    "jobs/smoke-test",
    "placeholder_scan_report.json",
]

FORBIDDEN_DIR_NAMES = {"__pycache__", ".pytest_cache"}

PRIVATE_MARKERS = [
    "vsa6@cornell.edu",
    "careerspan.com",
    "mycareerspan.com",
    "growthmanager-1025",
    "mckinsey-associate-15264",
]

ALLOWED_EMAIL_SUBSTRINGS = (
    "example.com",
    "example.invalid",
    "test.zoats.local",
)


def main() -> int:
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    present_forbidden = [p for p in FORBIDDEN if (ROOT / p).exists()]
    generated_cache_dirs = [
        str(p.relative_to(ROOT))
        for p in ROOT.rglob("*")
        if p.is_dir() and p.name in FORBIDDEN_DIR_NAMES
    ]
    private_marker_hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.name.endswith((".pyc", ".png", ".jpg", ".pdf")):
            continue
        rel = str(path.relative_to(ROOT))
        if rel in {"scripts/verify_skill_package.py"}:
            continue
        text = path.read_text(errors="ignore")
        for marker in PRIVATE_MARKERS:
            if marker in text:
                private_marker_hits.append({"file": rel, "marker": marker})
        for token in text.replace("\n", " ").split():
            if "@" not in token:
                continue
            cleaned = token.strip('`",:;()[]{}<>')
            if any(ch in cleaned for ch in "\\[]{}|+"):
                continue
            if "." in cleaned and not any(allowed in cleaned for allowed in ALLOWED_EMAIL_SUBSTRINGS):
                private_marker_hits.append({"file": rel, "marker": cleaned})
    manifest_path = ROOT / "references/migration/source-manifest.json"
    manifest_ok = False
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text())
        manifest_ok = data.get("deletion_status") in {"not_deleted_pending_user_verification", "archived_not_deleted"}
    result = {
        "root": str(ROOT),
        "required_count": len(REQUIRED),
        "missing_required": missing,
        "forbidden_present": present_forbidden,
        "generated_cache_dirs": generated_cache_dirs,
        "private_marker_hits": private_marker_hits,
        "manifest_deletion_gate_ok": manifest_ok,
        "pass": not missing and not present_forbidden and not generated_cache_dirs and not private_marker_hits and manifest_ok,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
