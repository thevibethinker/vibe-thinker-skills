from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from rubric_loader import load_rubric, parse_rubric_markdown


def test_parse_rubric_v1_structure() -> None:
    root = Path(__file__).resolve().parents[1]
    rubric = load_rubric(root / "rubric" / "rubric_v1.md", refresh=True)
    assert rubric["dimension_count"] == 13
    assert {frame["id"] for frame in rubric["frames"]} == {"F1", "F2", "F3", "F4"}
    assert "founder_market_fit_team_capacity" in rubric["frame_matrix"]
    assert rubric["named_pov_palette"]


def test_parse_markdown_from_string() -> None:
    root = Path(__file__).resolve().parents[1]
    markdown = (root / "rubric" / "rubric_v1.md").read_text(encoding="utf-8")
    rubric = parse_rubric_markdown(markdown, "inline")
    first = rubric["dimensions"][0]
    assert first["prompt_questions"]
    assert first["score_anchors"]["3"].startswith("Adequate")
