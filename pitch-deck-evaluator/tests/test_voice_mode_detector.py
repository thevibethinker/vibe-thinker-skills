import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from voice_mode_detector import detect_voice_mode


def test_sharp_declarative_fixture():
    slides = [
        "AI made claim QA cheaper than rework\nWe are the pre-submit reviewer for independent clinics.",
        "Denied claims now cost clinics $30B\nOur reviewer catches missing evidence before submission.",
        "We replace manual review\nBillers submit cleaner claims in one workflow.",
        "12 clinics tested it\n9 found missing documentation in week one.",
    ]
    result = detect_voice_mode(slides)
    assert result.mode in {"sharp_declarative", "concrete_operator"}
    assert result.confidence in {"high", "medium"}


def test_earnest_founder_fixture():
    slides = [
        "We started with denied claims\nCustomers told us the painful step was pre-submit review.",
        "We believe billers need a second set of eyes\nAfter interviewing 22 billers, 18 asked us to check claims before submission.",
        "We do not yet know pricing\nWe do know 9 clinics agreed to pilot the reviewer.",
        "What we learned\nTrust comes from showing the missing evidence, not auto-submitting claims.",
    ]
    result = detect_voice_mode(slides)
    assert result.mode == "earnest_founder"
    assert result.confidence in {"high", "medium"}


def test_visionary_fixture():
    slides = [
        "Every regulated workflow will have a pre-submit AI reviewer\nWe start with denied medical claims.",
        "The future of compliance is preflight\nTeams will check work before systems reject it.",
        "A new default for regulated work\nHuman teams approve; AI verifies missing evidence.",
        "We start narrow\nClaims documentation is the wedge.",
    ]
    result = detect_voice_mode(slides)
    assert result.mode == "visionary_narrative"
    assert result.confidence in {"high", "medium"}


def test_consultative_fixture():
    slides = [
        "Thesis: independent clinics cannot absorb payer documentation complexity\nEvidence: denial rates rose 31%.",
        "Segment: clinics with outsourced billing\nConstraint: rework is cheaper to prevent than appeal.",
        "Implication: pre-submit checks become the control point\nAssumption: billers will pay per reviewed claim.",
        "Base case: land in claims review\nScenario: expand to prior authorization.",
    ]
    result = detect_voice_mode(slides)
    assert result.mode == "consultative_analytical"
    assert result.confidence in {"high", "medium"}


def test_mixed_fixture():
    slides = [
        "We believe this might become huge\nCustomers told us they are confused.",
        "AI made claims cheaper than rework\nWe are the pre-submit reviewer.",
        "The future of every workflow will be autonomous\nA new category is forming.",
        "Thesis: denial management is a cost center\nEvidence: rates rose 31%.",
        "12 clinics tested it\n9 found missing evidence.",
    ]
    result = detect_voice_mode(slides)
    assert result.mode == "mixed"
