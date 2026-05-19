#!/usr/bin/env python3
"""Regression checks for the Simovian strategy memo CLI."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = THIS_DIR.parent
REPO = SKILL_ROOT.parent if (SKILL_ROOT / "SKILL.md").exists() else Path(__file__).resolve().parents[3]
CLI = THIS_DIR / "simovian_strategy_memo.py"
SNAPSHOT = REPO / "Skills/venture-intel/scripts/snapshot.py"


def run(cmd: list[str], *, env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True, check=True)


def run_json(cmd: list[str], *, env: dict[str, str], cwd: Path) -> dict:
    return json.loads(run(cmd, env=env, cwd=cwd).stdout)


def seed_workspace(root: Path) -> tuple[Path, Path]:
    memo = root / "Research/general/pi-venture-intel/CURRENT_MEMO.md"
    memo.parent.mkdir(parents=True, exist_ok=True)
    memo.write_text("# Current Memo\n\nBaseline Simovian strategy.\n", encoding="utf-8")
    source = root / "scratch/source-memo.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Source Memo\n\nSurgeon buyer signal reinforces task-specific datasets.\n", encoding="utf-8")
    return memo, source


def test_memo_workflow(root: Path, env: dict[str, str]) -> None:
    memo, source = seed_workspace(root)
    base = ["python3", str(CLI)]

    status = run_json(base + ["status", "--json"], env=env, cwd=REPO)
    assert status["status"] == "ok"
    assert status["old_writer_risk"] is None

    candidate = run_json(
        base + [
            "commit",
            "--source",
            str(source),
            "--intent",
            "Add surgeon buyer signal",
            "--pathway",
            "surgical-dexterity-data",
            "--candidate-id",
            "cand_test",
            "--local",
            "--json",
        ],
        env=env,
        cwd=REPO,
    )
    assert candidate["status"] == "candidate_created"

    failed = subprocess.run(
        base + ["apply", "--candidate-id", "cand_test", "--approve", "APPROVE wrong", "--json"],
        cwd=REPO,
        env=env,
        text=True,
        capture_output=True,
    )
    assert failed.returncode != 0

    applied = run_json(
        base + ["apply", "--candidate-id", "cand_test", "--approve", "APPROVE cand_test", "--json"],
        env=env,
        cwd=REPO,
    )
    assert applied["status"] == "candidate_applied"
    assert "Add surgeon buyer signal" in memo.read_text(encoding="utf-8")

    history = run_json(base + ["history", "--json"], env=env, cwd=REPO)
    assert len(history["commits"]) == 1

    blame = run_json(base + ["blame", "--text", "cand_test", "--json"], env=env, cwd=REPO)
    assert blame["matches"]

    positioning = run_json(
        base + [
            "generate-positioning",
            "--local",
            "--output",
            "Research/general/pi-venture-intel/POSITIONING.md",
            "--json",
        ],
        env=env,
        cwd=REPO,
    )
    assert positioning["status"] == "positioning_generated"
    assert (root / "Research/general/pi-venture-intel/POSITIONING.md").exists()


def test_snapshot_dry_run(root: Path, env: dict[str, str]) -> None:
    if not SNAPSHOT.exists():
        return
    ledger = root / "Research/general/pi-venture-intel/ledger"
    snapshots = root / "Research/general/pi-venture-intel/snapshots"
    manifest = root / "Research/general/pi-venture-intel/manifest.json"
    memo = root / "Research/general/pi-venture-intel/CURRENT_MEMO.md"
    ledger.mkdir(parents=True, exist_ok=True)
    snapshots.mkdir(parents=True, exist_ok=True)

    run(
        [
            "python3",
            str(SNAPSHOT),
            "--date",
            "2026-05-19",
            "--ledger-dir",
            str(ledger),
            "--snapshot-dir",
            str(snapshots),
            "--current-memo-path",
            str(memo),
            "--manifest-path",
            str(manifest),
            "--dry-run",
        ],
        env=env,
        cwd=REPO,
    )
    assert not manifest.exists()
    assert not (snapshots / "2026-05-19.md").exists()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="simovian-memo-test-") as tmp:
        root = Path(tmp)
        env = os.environ.copy()
        env["SIMOVIAN_MEMO_WORKSPACE"] = str(root)
        env["VENTURE_INTEL_WORKSPACE"] = str(root)
        test_memo_workflow(root, env)
        test_snapshot_dry_run(root, env)
    print("simovian strategy memo regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
