#!/usr/bin/env python3
"""End-to-end acceptance test for ZoATS.

Verifies: job API → apply form → intake trigger → candidate staging (→ pipeline if auto).

Usage:
    python3 tests/test_e2e.py --local                   # test against localhost
    python3 tests/test_e2e.py --base https://va.zo.space # test against live
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lib.paths import ZOATS_HOME

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

JOBS_DIR = ZOATS_HOME / "jobs"
INBOX_DIR = ZOATS_HOME / "inbox_drop"

# Test fixture job (created by tests/generate_fixtures.py)
TEST_JOB_ID = "test-fixture"


class _TestResult:
    def __init__(self):
        self.steps = []
        self.passed = 0
        self.failed = 0

    def ok(self, step: str, detail: str = ""):
        self.steps.append({"step": step, "result": "PASS", "detail": detail})
        self.passed += 1
        logger.info(f"  PASS  {step}" + (f" — {detail}" if detail else ""))

    def fail(self, step: str, detail: str = ""):
        self.steps.append({"step": step, "result": "FAIL", "detail": detail})
        self.failed += 1
        logger.error(f"  FAIL  {step}" + (f" — {detail}" if detail else ""))

    def skip(self, step: str, reason: str = ""):
        self.steps.append({"step": step, "result": "SKIP", "detail": reason})
        logger.warning(f"  SKIP  {step}" + (f" — {reason}" if reason else ""))

    def summary(self) -> dict:
        return {
            "total": self.passed + self.failed,
            "passed": self.passed,
            "failed": self.failed,
            "steps": self.steps,
        }


def http_get_json(url: str) -> tuple:
    """GET JSON API and return (status, body_dict)."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return e.code, {"error": body}
    except Exception as e:
        return 0, {"error": str(e)}


def http_get_text(url: str) -> tuple[int, str]:
    """GET any route and return (status, body_text)."""
    import urllib.request
    import urllib.error
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.status, resp.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace") if e.fp else ""
        return e.code, body
    except Exception as e:
        return 0, str(e)


def http_post_multipart(url: str, fields: dict, file_path: Path, file_field: str = "resume") -> tuple:
    """POST multipart form data with a file."""
    import urllib.request
    import urllib.error

    boundary = "----ZoATSTestBoundary"
    body = b""

    for key, val in fields.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
        body += f"{val}\r\n".encode()

    # File field
    fname = file_path.name
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="{file_field}"; filename="{fname}"\r\n'.encode()
    body += b"Content-Type: application/octet-stream\r\n\r\n"
    body += file_path.read_bytes()
    body += b"\r\n"
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode() if e.fp else ""
        return e.code, {"error": resp_body}
    except Exception as e:
        return 0, {"error": str(e)}


def run_e2e(base_url: str) -> _TestResult:
    t = _TestResult()

    # Pre-check: test fixture job exists
    fixture_dir = JOBS_DIR / TEST_JOB_ID
    if not fixture_dir.exists():
        t.fail("preflight", f"Test fixture job not found. Run: python3 tests/generate_fixtures.py")
        return t
    t.ok("preflight", f"Test fixture job exists at {fixture_dir}")

    # Step 1: GET /api/zoats/jobs — list should include test-fixture
    status, data = http_get_json(f"{base_url}/api/zoats/jobs")
    if status == 200 and "jobs" in data:
        job_ids = [j["id"] for j in data["jobs"]]
        if TEST_JOB_ID in job_ids:
            t.ok("list_jobs", f"Found {TEST_JOB_ID} among {len(data['jobs'])} jobs")
        else:
            t.fail("list_jobs", f"{TEST_JOB_ID} not in job list (active jobs: {job_ids}). Check metadata.json status=active")
    else:
        t.fail("list_jobs", f"API returned status={status}")

    # Step 2: GET /api/zoats/jobs/:id — single job detail
    status, data = http_get_json(f"{base_url}/api/zoats/jobs/{TEST_JOB_ID}")
    if status == 200 and data.get("title"):
        t.ok("get_job", f"Title: {data['title']}")
    else:
        t.fail("get_job", f"status={status}, data={json.dumps(data)[:200]}")

    # Step 3: POST /api/zoats/apply — submit synthetic resume
    # Create a temp text resume
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
        f.write("Jane Doe\njane.doe@example.com\n\nExperience:\n- 5 years software engineering\n- Python, TypeScript, Go\n")
        resume_path = Path(f.name)

    try:
        fields = {
            "name": "Jane Doe (E2E Test)",
            "email": "jane.doe.e2e@test.zoats.local",
            "phone": "+1-555-0199",
            "cover_note": "This is an automated E2E test submission.",
            "job_id": TEST_JOB_ID,
        }
        status, data = http_post_multipart(f"{base_url}/api/zoats/apply", fields, resume_path)
        if status == 200 and data.get("success"):
            submission_id = data.get("submission_id", "")
            t.ok("apply_submit", f"submission_id={submission_id}")
        else:
            t.fail("apply_submit", f"status={status}, data={json.dumps(data)[:200]}")
            return t  # can't continue without submission
    finally:
        resume_path.unlink(missing_ok=True)

    # Step 4: Wait briefly for intake trigger (fire-and-forget)
    time.sleep(3)

    # Step 5: Check intake processed — look for candidate in job folder
    candidates_dir = JOBS_DIR / TEST_JOB_ID / "candidates"
    if candidates_dir.exists():
        # Find the most recent candidate folder (should match our test submission)
        candidates = sorted(candidates_dir.iterdir(), reverse=True)
        test_candidate = None
        for c in candidates:
            sub_json = c / "submission.json"
            if sub_json.exists():
                sub = json.loads(sub_json.read_text())
                if "e2e" in sub.get("email", "").lower() or "E2E Test" in sub.get("name", ""):
                    test_candidate = c
                    break

        if test_candidate:
            t.ok("intake_processed", f"Candidate folder: {test_candidate.name}")

            # Check resume exists
            raw_dir = test_candidate / "raw"
            if raw_dir.exists() and any(raw_dir.iterdir()):
                t.ok("resume_staged", f"Resume in {raw_dir}")
            else:
                t.fail("resume_staged", "raw/ directory empty or missing")

            # Check if pipeline ran (auto_pipeline)
            settings_path = ZOATS_HOME / "config" / "settings.json"
            auto = False
            if settings_path.exists():
                auto = json.loads(settings_path.read_text()).get("auto_pipeline", False)

            if auto:
                outputs_dir = test_candidate / "outputs"
                if outputs_dir.exists() and any(outputs_dir.iterdir()):
                    t.ok("pipeline_ran", "Pipeline outputs present")
                else:
                    t.fail("pipeline_ran", "auto_pipeline=true but no outputs found")
            else:
                t.skip("pipeline_ran", "auto_pipeline=false, skipping pipeline verification")
        else:
            t.fail("intake_processed", "No candidate folder matching E2E test found — intake may not have run yet")
    else:
        t.fail("intake_processed", f"No candidates directory at {candidates_dir}")

    # Step 6: Check inbox_drop processed
    processed_dir = INBOX_DIR / ".processed"
    if processed_dir.exists() and any(processed_dir.iterdir()):
        t.ok("inbox_cleaned", "Submission moved to .processed/")
    else:
        t.skip("inbox_cleaned", "No .processed/ entries (intake may still be running)")

    return t


def run_route_smoke(base_url: str) -> _TestResult:
    """Smoke test all provisioned routes for basic reachability."""
    t = _TestResult()

    api_routes = [
        ("/api/zoats/jobs", 200),
        (f"/api/zoats/jobs/{TEST_JOB_ID}", 200),
    ]
    page_routes = [
        ("/careers", 200),
    ]

    for path, expected in api_routes:
        url = f"{base_url}{path}"
        status, data = http_get_json(url)
        if status == expected:
            t.ok(f"route {path}", f"status={status}")
        else:
            t.fail(f"route {path}", f"expected={expected}, got={status}, data={json.dumps(data)[:160]}")

    for path, expected in page_routes:
        url = f"{base_url}{path}"
        status, body = http_get_text(url)
        if status == expected and "<!doctype html" in body.lower():
            t.ok(f"route {path}", f"status={status}")
        else:
            t.fail(f"route {path}", f"expected_html_status={expected}, got={status}")

    return t


def main() -> int:
    ap = argparse.ArgumentParser(description="ZoATS E2E Acceptance Test")
    ap.add_argument("--local", action="store_true", help="Test against localhost:3000")
    ap.add_argument("--base", type=str, help="Base URL to test against")
    ap.add_argument("--smoke-only", action="store_true", help="Only run route smoke tests")

    args = ap.parse_args()

    if args.base:
        base_url = args.base.rstrip("/")
    elif args.local:
        base_url = "http://localhost:3099"
    else:
        # Default: try va.zo.space
        base_url = "https://va.zo.space"

    logger.info(f"[e2e] Testing against: {base_url}")
    logger.info(f"[e2e] ZOATS_HOME: {ZOATS_HOME}")
    print()

    if args.smoke_only:
        result = run_route_smoke(base_url)
    else:
        # Run both
        logger.info("=== Route Smoke Tests ===")
        smoke = run_route_smoke(base_url)
        print()
        logger.info("=== E2E Pipeline Test ===")
        e2e = run_e2e(base_url)

        # Merge results
        result = _TestResult()
        result.steps = smoke.steps + e2e.steps
        result.passed = smoke.passed + e2e.passed
        result.failed = smoke.failed + e2e.failed

    print()
    summary = result.summary()
    logger.info(f"{'='*40}")
    logger.info(f"Results: {summary['passed']} passed, {summary['failed']} failed out of {summary['total']}")
    logger.info(f"{'='*40}")

    print(json.dumps(summary, indent=2))
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
