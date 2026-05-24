from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from output_renderer import render_markdown


def sample_evaluation():
    return {
        "deck_metadata": {"deck_name": "sample.pdf"},
        "evaluation_date": "2026-05-24",
        "config": {"stage": "pre_seed", "enabled_frames": ["F1"], "enabled_pov_palette": [], "output_verbosity": "standard", "include_action_list": True},
        "substantive_composite": 3.2,
        "stylistic_composite": None,
        "advisory_overall": 3.2,
        "hard_gates": [],
        "frame_scorecards": [
            {
                "frame_id": "F1",
                "frame_name": "Warm Believer",
                "frame_definition": "F1 Warm Believer",
                "substantive_score": 3.2,
                "dimension_scores": [
                    {
                        "dimension_name": "Founder-market fit",
                        "dimension_id": "founder_market_fit_team_capacity",
                        "raw_score": 3.0,
                        "evidence": [{"slide_ref": "slide_01"}],
                        "top_fix": "Add proof.",
                        "reasoning": "Reason.",
                    }
                ],
            }
        ],
        "substantive_dimensions": [],
        "cross_frame_synthesis": {"summary": "Synthesis.", "spread": 0, "frame_scores": {"F1": 3.2}},
        "named_pov_reads": [],
        "prioritized_action_list": ["Add proof."],
    }


def test_render_markdown_contains_required_sections() -> None:
    markdown = render_markdown(sample_evaluation())
    for section in ["# Pitch Deck Evaluation", "## Frame Scorecards", "## Cross-Frame Synthesis", "## Prioritized Action List"]:
        assert section in markdown


def test_render_markdown_matches_golden() -> None:
    markdown = render_markdown(sample_evaluation())
    golden = Path(__file__).resolve().parent / "fixtures" / "output_renderer_golden.md"
    assert golden.exists(), "golden fixture must be checked in"
    assert markdown == golden.read_text(encoding="utf-8")
