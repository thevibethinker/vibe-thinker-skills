#!/usr/bin/env python3
"""Integration test: run pipeline against fixtures in dry-run mode.

This verifies:
- pipeline/run.py executes successfully in --dry-run
- printed JSON has expected structure
- decision_breakdown includes PASS_quick_test and PASS_scoring keys
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.paths import ZOATS_HOME


def main() -> int:
    root = ZOATS_HOME
    pipeline = root / "pipeline" / "run.py"
    job = "test-fixture"

    cmd = [sys.executable, str(pipeline), "--job", job, "--dry-run"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("PIPELINE FAILED")
        print(res.stdout)
        print(res.stderr, file=sys.stderr)
        return res.returncode

    try:
        data = json.loads(res.stdout)
    except Exception as e:
        print("FAILED TO PARSE PIPELINE JSON OUTPUT")
        print(res.stdout)
        print(res.stderr, file=sys.stderr)
        print(f"parse_error: {e}", file=sys.stderr)
        return 1

    for k in ["job", "stages", "candidate_results", "summary", "candidates_processed"]:
        if k not in data:
            print(f"missing_key: {k}")
            return 1

    summary = data["summary"]
    if "decision_breakdown" not in summary or not isinstance(summary["decision_breakdown"], dict):
        print("missing_or_invalid: summary.decision_breakdown")
        return 1

    db = summary["decision_breakdown"]
    for k in ["PASS_quick_test", "PASS_scoring"]:
        if k not in db:
            print(f"missing_decision_breakdown_key: {k}")
            return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
