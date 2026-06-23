#!/usr/bin/env python3
"""Generate minimal, runnable fixture data for ZoATS tests.

Creates:
- jobs/test-fixture/
  - job-description.md
  - rubric.json
  - deal_breakers.json
  - metadata.json
  - candidates/<candidate_id>/raw/resume.txt

Idempotent: re-running will not overwrite existing files.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.paths import ZOATS_HOME


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.write_text(content, encoding="utf-8")


def write_json_if_missing(path: Path, data: object) -> None:
    if path.exists():
        return
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    job_id = "test-fixture"
    job_dir = ZOATS_HOME / "jobs" / job_id
    candidates_dir = job_dir / "candidates"

    ensure_dir(job_dir)
    ensure_dir(candidates_dir)

    jd_path = job_dir / "job-description.md"
    rubric_path = job_dir / "rubric.json"
    deal_breakers_path = job_dir / "deal_breakers.json"
    metadata_path = job_dir / "metadata.json"

    write_if_missing(
        jd_path,
        (
            "# Test Fixture — Backend Engineer\n\n"
            "We are hiring a Backend Engineer to build reliable APIs and data pipelines.\n\n"
            "## Responsibilities\n"
            "- Build and maintain Python services\n"
            "- Work with SQL and data modeling\n"
            "- Ship pragmatic, well-tested code\n\n"
            "## Requirements\n"
            "- 3+ years Python\n"
            "- Production experience with databases\n"
            "- Clear written communication\n"
        ),
    )

    write_json_if_missing(
        rubric_path,
        {
            "criteria": [
                {
                    "name": "Python backend",
                    "weight": 0.35,
                    "description": "Evidence of building production Python services.",
                },
                {
                    "name": "Data/SQL",
                    "weight": 0.25,
                    "description": "Comfort with SQL, data modeling, and analytics.",
                },
                {
                    "name": "Systems & reliability",
                    "weight": 0.25,
                    "description": "Operational thinking: testing, monitoring, incident response.",
                },
                {
                    "name": "Communication",
                    "weight": 0.15,
                    "description": "Clear writing and stakeholder updates.",
                },
            ]
        },
    )

    write_json_if_missing(
        deal_breakers_path,
        {
            "deal_breakers": [
                {
                    "id": "no_python",
                    "description": "No evidence of Python experience.",
                    "severity": "hard",
                },
                {
                    "id": "no_prod",
                    "description": "No evidence of having shipped/maintained production systems.",
                    "severity": "soft",
                },
            ]
        },
    )

    desired_meta = {
        "id": job_id,
        "title": "Backend Engineer",
        "company": "FixtureCo",
        "location": "Remote",
        "type": "full-time",
        "posted_date": "2026-04-01",
        "status": "open",
        "description_summary": "Backend Engineer role for APIs and data pipelines.",
        "created_at": utc_now(),
    }

    if not metadata_path.exists():
        write_json_if_missing(metadata_path, desired_meta)
    else:
        # Patch-in missing required keys without overwriting existing user edits
        try:
            existing = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
        if not isinstance(existing, dict):
            existing = {}
        changed = False
        for k, v in desired_meta.items():
            if k not in existing:
                existing[k] = v
                changed = True

        # Normalize status if it doesn't match schema enum
        allowed_status = {"draft", "open", "on_hold", "filled", "closed"}
        if isinstance(existing.get("status"), str) and existing["status"] not in allowed_status:
            existing.setdefault("status_original", existing["status"])
            existing["status"] = "open"
            changed = True

        if changed:
            metadata_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")

    candidates = [
        {
            "id": "candidate-alpha",
            "name": "Candidate Alpha",
            "resume": """Candidate Alpha\n\nExperience\n- Backend Engineer, ExampleCorp (2021-2026)\n  - Built Python APIs (FastAPI), integrated PostgreSQL\n  - Owned on-call rotation; reduced p95 latency by 30%\n\nSkills\nPython, FastAPI, Postgres, Redis, Docker, AWS\n""",
        },
        {
            "id": "candidate-beta",
            "name": "Candidate Beta",
            "resume": """Candidate Beta\n\nExperience\n- Data Analyst (2020-2026)\n  - Heavy SQL and dbt, built dashboards\n  - Some scripting in Python for ETL\n\nSkills\nSQL, dbt, Python, Tableau\n""",
        },
    ]

    for c in candidates:
        cdir = candidates_dir / c["id"]
        raw_dir = cdir / "raw"
        parsed_dir = cdir / "parsed"
        outputs_dir = cdir / "outputs"
        ensure_dir(raw_dir)
        ensure_dir(parsed_dir)
        ensure_dir(outputs_dir)
        write_if_missing(raw_dir / "resume.txt", c["resume"])
        write_if_missing(parsed_dir / "text.md", c["resume"])

    print(f"[fixtures] ready: {job_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
