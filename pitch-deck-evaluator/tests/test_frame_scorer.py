from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from frame_scorer import LLMClient, score_frames
from rubric_loader import load_rubric


class MockClient:
    def score_dimension(self, prompt, context):
        return {
            "raw_score": 4.0,
            "reasoning": "Mock reasoning with evidence.",
            "evidence": [{"slide_ref": "slide_01", "excerpt": "Problem", "evidence_type": "mock"}],
            "stage_findings": [{"type": "stage_appropriate_evidence", "code": "mock"}],
            "top_fix": "Mock fix.",
            "confidence": "high",
        }


def test_frame_scorer_uses_mock_client_without_paid_calls() -> None:
    root = Path(__file__).resolve().parents[1]
    rubric = load_rubric(root / "rubric" / "rubric_v1.md", refresh=True)
    slides = [{"slide_num": 1, "slide_ref": "slide_01", "text": "Problem and team traction market solution"}]
    result = score_frames(slides, rubric, {"enabled_frames": ["F1", "F2"], "stage": "pre_seed"}, MockClient())
    assert len(result["frame_scorecards"]) == 2
    assert result["substantive_composite"] == 4.0
    assert all(score["top_fix"] == "Mock fix." for score in result["substantive_dimensions"])


def test_stage_caps_missing_founder_evidence() -> None:
    root = Path(__file__).resolve().parents[1]
    rubric = load_rubric(root / "rubric" / "rubric_v1.md", refresh=True)
    slides = [{"slide_num": 1, "slide_ref": "slide_01", "text": "Market size is $1B. Solution exists."}]
    result = score_frames(slides, rubric, {"enabled_frames": ["F1"], "stage": "pre_seed"})
    founder = next(s for s in result["substantive_dimensions"] if s["dimension_id"] == "founder_market_fit_team_capacity")
    assert founder["raw_score"] <= 2.0

def test_default_backend_ignores_ambient_anthropic_key(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-that-must-not-be-used")
    root = Path(__file__).resolve().parents[1]
    rubric = load_rubric(root / "rubric" / "rubric_v1.md", refresh=True)
    slides = [{"slide_num": 1, "slide_ref": "slide_01", "text": "Problem and team traction market solution"}]
    result = score_frames(slides, rubric, {"enabled_frames": ["F1"], "stage": "pre_seed"})
    assert result["frame_scorecards"][0]["frame_id"] == "F1"
    assert result["substantive_composite"] >= 0



def test_auto_backend_ignores_ambient_anthropic_key(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-that-must-not-be-used")
    root = Path(__file__).resolve().parents[1]
    rubric = load_rubric(root / "rubric" / "rubric_v1.md", refresh=True)
    slides = [{"slide_num": 1, "slide_ref": "slide_01", "text": "Problem and market traction solution"}]
    result = score_frames(slides, rubric, {"enabled_frames": ["F1"], "stage": "pre_seed", "scoring_backend": "auto"})
    assert result["frame_scorecards"][0]["frame_id"] == "F1"
