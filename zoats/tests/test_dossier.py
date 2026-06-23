import json
from pathlib import Path
import subprocess
import sys


def run(cmd, cwd: Path):
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


def test_dossier_missing_gestalt_returns_structured_error():
    repo = Path(__file__).resolve().parents[1]

    job = "test-fixture"
    cand = "candidate-beta"
    outputs = repo / "jobs" / job / "candidates" / cand / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    gestalt_path = outputs / "gestalt_evaluation.json"
    if gestalt_path.exists():
        gestalt_path.unlink()

    res = run([sys.executable, "workers/dossier/main.py", "--job", job, "--candidate", cand], cwd=repo)
    assert res.returncode != 0
    data = json.loads(res.stdout)
    assert data["ok"] is False
    assert data["error"]["code"] == "DOSSIER_MISSING_INPUT"


def test_dossier_clarification_questions_rendering(tmp_path):
    repo = Path(__file__).resolve().parents[1]

    job = "test-fixture"
    cand = "dossier-clarif"

    cdir = repo / "jobs" / job / "candidates" / cand
    parsed = cdir / "parsed"
    outputs = cdir / "outputs"
    parsed.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)

    (parsed / "fields.json").write_text(json.dumps({"name": "Test", "email": "t@example.com"}), encoding="utf-8")
    (outputs / "quick_test.json").write_text(json.dumps({"status": "unknown"}), encoding="utf-8")

    gestalt = {
        "candidate_id": cand,
        "job_id": job,
        "decision": "MAYBE",
        "confidence": "low",
        "key_strengths": [],
        "concerns": [],
        "overall_narrative": "Maybe.",
        "interview_focus": [],
        "clarification_questions": [
            {"question": "Q1?", "why_asking": "Because", "deal_breaker": True},
            "Q2?",
        ],
        "ai_detection": {"likelihood": "low", "confidence": 0.7, "flags": []},
        "elite_signals": [],
        "business_impact": [],
        "timestamp": "2026-04-01T00:00:00Z",
    }
    (outputs / "gestalt_evaluation.json").write_text(json.dumps(gestalt), encoding="utf-8")

    res = run([sys.executable, "workers/dossier/main.py", "--job", job, "--candidate", cand], cwd=repo)
    assert res.returncode == 0
    md = (outputs / "dossier.md").read_text(encoding="utf-8")
    assert "## Clarification Questions" in md
    assert "Q1?" in md
    assert "why:" in md
    assert "deal-breaker" in md
    assert "Q2?" in md
