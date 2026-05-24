import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from stylistic_scorer import score_stylistic


def strong_style_deck():
    return [
        {"slide_num": 1, "text": "AI catches missing claim evidence before clinics submit\n12 clinics tested it; 9 found denial-causing gaps in week one."},
        {"slide_num": 2, "text": "Independent clinics lose margin to avoidable denials\nBillers review claims manually across payer portals."},
        {"slide_num": 3, "text": "We are the pre-submit reviewer for billers\nThe dashboard checks each answer against payer documentation rules."},
        {"slide_num": 4, "text": "Demand evidence\n4 signed LOIs; 18 of 22 interviewed billers asked for pre-submit review."},
        {"slide_num": 5, "text": "Competition and risk\nIncumbent RCM tools manage appeals; our wedge is prevention before submission."},
    ]


def weak_style_deck():
    return [
        {"slide_num": 1, "text": "Problem\nWe are building an AI-powered next-gen end-to-end seamless intelligent platform designed to transform the future of healthcare through revolutionary automation and unlock productivity for everyone."},
        {"slide_num": 2, "text": "Solution\nOur powerful ecosystem leverages proprietary technology and world-class experience to empower all teams in order to supercharge workflow transformation."},
        {"slide_num": 3, "text": "Market\nThe market is huge and massive and sticky. We believe this could potentially be the biggest opportunity."},
        {"slide_num": 4, "text": "Product\nFeatures include dashboards, APIs, analytics, integrations, automations, modules, configuration, intelligence, activation, optimization."},
    ]


def test_strong_style_scores_higher_than_weak_style():
    strong = score_stylistic(strong_style_deck(), {"register_override": "auto"})
    weak = score_stylistic(weak_style_deck(), {"register_override": "auto"})
    assert strong["style_score"] > weak["style_score"]
    assert len(strong["dimensions"]) == 7
    assert all("evidence" in dimension for dimension in strong["dimensions"])


def test_weak_style_fixture_has_actionable_low_dimensions():
    weak = score_stylistic(weak_style_deck(), {})
    low = [dimension for dimension in weak["dimensions"] if dimension["score"] <= 3]
    assert low
    assert any(dimension["dimension_id"] == "anti_buzzword_discipline" for dimension in low)


def test_earnest_register_does_not_harshly_penalize_hedging():
    slides = [
        {"slide_num": 1, "text": "We started with denied claims\nCustomers told us they need checks before submission."},
        {"slide_num": 2, "text": "We believe billers will pay per reviewed claim\nBecause 18 of 22 interviewed billers asked for the workflow."},
        {"slide_num": 3, "text": "We do not yet know final pricing\nWe do know 9 clinics agreed to pilot."},
    ]
    result = score_stylistic(slides, {})
    voice = next(d for d in result["dimensions"] if d["dimension_id"] == "voice_register_fit")
    assert result["detected_voice_mode"] == "earnest_founder"
    assert voice["score"] >= 3.0
    assert voice["register_applied"] is True
