import json
from pathlib import Path
import subprocess
import sys


def run(cmd, cwd: Path):
    res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return res


def test_parser_zero_byte_returns_structured_error(tmp_path):
    repo = Path(__file__).resolve().parents[1]

    job = "test-fixture"
    cand = "test-empty"

    raw_dir = repo / "jobs" / job / "candidates" / cand / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "empty.txt").write_bytes(b"")

    res = run([sys.executable, "workers/parser/main.py", "--job", job, "--candidate", cand], cwd=repo)
    assert res.returncode != 0
    data = json.loads(res.stdout)
    assert data["ok"] is False
    assert data["error"]["code"] in {"PARSER_FAILED", "PARSER_CRASH"}


def test_parser_too_short_returns_structured_error(tmp_path):
    repo = Path(__file__).resolve().parents[1]

    job = "test-fixture"
    cand = "test-short"

    raw_dir = repo / "jobs" / job / "candidates" / cand / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "resume.txt").write_text("One line", encoding="utf-8")

    res = run([sys.executable, "workers/parser/main.py", "--job", job, "--candidate", cand], cwd=repo)
    assert res.returncode != 0
    data = json.loads(res.stdout)
    assert data["ok"] is False
    assert data["error"]["code"] == "PARSER_FAILED"
