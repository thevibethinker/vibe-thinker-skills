import json
from pathlib import Path
import subprocess
import sys


def run(cmd, cwd: Path):
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


def test_scoring_missing_rubric_fails_early(monkeypatch):
    repo = Path(__file__).resolve().parents[1]
    job_dir = repo / "jobs" / "test-fixture"
    rubric = job_dir / "rubric.json"

    if not rubric.exists():
        # Fixture generator should create it, but keep test resilient
        job_dir.mkdir(parents=True, exist_ok=True)
        rubric.write_text("{}", encoding="utf-8")

    backup = rubric.read_text(encoding="utf-8")
    try:
        rubric.unlink()
        res = run(
            [
                sys.executable,
                "workers/scoring/main_gestalt.py",
                "--job",
                "test-fixture",
                "--candidate",
                "candidate-alpha",
                "--dry-run",
            ],
            cwd=repo,
        )
        assert res.returncode != 0
        data = json.loads(res.stdout)
        assert data["ok"] is False
        assert data["error"]["code"] == "SCORING_FAILED"
        assert "Missing rubric.json" in data["error"]["message"]
    finally:
        rubric.write_text(backup, encoding="utf-8")


def test_scoring_llm_unavailable_still_outputs_schema(monkeypatch):
    repo = Path(__file__).resolve().parents[1]

    env = dict(**{k: v for k, v in __import__("os").environ.items() if k != "ANTHROPIC_API_KEY"})

    res = subprocess.run(
        [
            sys.executable,
            "workers/scoring/main_gestalt.py",
            "--job",
            "test-fixture",
            "--candidate",
            "candidate-alpha",
            "--dry-run",
        ],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    # GestaltEvaluation schema fields must exist
    for k in [
        "candidate_id",
        "job_id",
        "decision",
        "confidence",
        "key_strengths",
        "concerns",
        "overall_narrative",
        "interview_focus",
        "clarification_questions",
        "ai_detection",
        "elite_signals",
        "business_impact",
        "timestamp",
    ]:
        assert k in data
