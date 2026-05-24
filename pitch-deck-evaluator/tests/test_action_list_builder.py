import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from action_list_builder import build_action_list


def style_scorecard(score=82):
    return {
        "style_score": score,
        "dimensions": [
            {"dimension_id": "punch_density", "label": "Punch / Density", "score": 4.2, "weight_effective": 16, "top_fix": "Rewrite opening."},
            {"dimension_id": "claim_hygiene", "label": "Claim Hygiene", "score": 3.5, "weight_effective": 16, "top_fix": "Mark claims."},
        ],
    }


def substance_scorecard(score=48):
    return {
        "substantive_score": score,
        "dimensions": [
            {"dimension_id": "evidence_demand_learning_velocity", "label": "Evidence + Demand", "score": 1.5, "weight_effective": 14, "top_fix": "Add demand evidence from pilots or interviews.", "frames_helped": ["F2", "F3", "F4"]},
            {"dimension_id": "market_logic_venture_scale_path", "label": "Market Logic", "score": 2.0, "weight_effective": 12, "top_fix": "Show bottom-up market logic.", "frames_helped": ["F3", "F4"]},
        ],
    }


def test_top_n_respected_and_ranked():
    result = build_action_list(substance_scorecard(), style_scorecard(), top_n=1)
    assert len(result["actions"]) == 1
    assert result["actions"][0]["rank"] == 1
    assert "impact_per_effort" in result["actions"][0]


def test_style_substance_gap_prioritizes_substance():
    result = build_action_list(substance_scorecard(48), style_scorecard(82), top_n=5)
    assert result["style_substance_gap"]["label"] == "Strong style, weak substance"
    assert result["actions"][0]["surface"] == "substantive"


def test_all_high_emits_no_actions():
    result = build_action_list({"substantive_score": 88, "dimensions": [{"dimension_id": "evidence_demand_learning_velocity", "score": 4.4, "weight_effective": 14}]}, {"style_score": 86, "dimensions": [{"dimension_id": "punch_density", "score": 4.2, "weight_effective": 16}]}, top_n=5)
    assert result["actions"] == []


def test_all_low_emits_deduped_actions():
    result = build_action_list(substance_scorecard(30), {"style_score": 35, "dimensions": [{"dimension_id": "punch_density", "score": 1.0, "weight_effective": 16}, {"dimension_id": "punch_density", "score": 1.2, "weight_effective": 16}]}, top_n=5)
    ids = [action["dimension_id"] for action in result["actions"]]
    assert ids.count("punch_density") <= 1
    assert len(result["actions"]) <= 5
