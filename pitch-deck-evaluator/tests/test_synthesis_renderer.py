import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from synthesis_renderer import render_cross_frame_synthesis


def test_renders_divergence_and_gap():
    frames = {
        "frames": {
            "F1": {"dimensions": [{"dimension_id": "insight", "label": "Insight", "score": 4.0, "rationale": "Founder context makes it plausible."}]},
            "F4": {"dimensions": [{"dimension_id": "insight", "label": "Insight", "score": 2.0, "rationale": "Cold diligence sees no proof."}]},
        }
    }
    md = render_cross_frame_synthesis(frames, {"substantive_score": 45}, {"style_score": 80})
    assert "Where frames diverge" in md
    assert "Strong style, weak substance" in md
    assert "F1" in md and "F4" in md
