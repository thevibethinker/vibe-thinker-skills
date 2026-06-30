#!/usr/bin/env python3
"""Regression checks for Research Engine CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "research_engine.py"
INSTALL_SCRIPT = SKILL_ROOT / "scripts" / "install.py"
TEST_WORKSPACE = Path(os.environ.get("RESEARCH_ENGINE_TEST_WORKSPACE", "/tmp/research-engine-test-workspace"))
TMP_ROOT = TEST_WORKSPACE / "Research" / "_engine" / "test-state"

sys.path.insert(0, str(SCRIPT.parent))


def run_cmd(*args: str, expect: int = 0) -> dict:
    env = os.environ.copy()
    env["ZO_WORKSPACE"] = str(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    env["RESEARCH_ENGINE_ROOT"] = str(TMP_ROOT / "repos")
    env["RESEARCH_ENGINE_STATE_ROOT"] = str(TMP_ROOT)
    env["ZO_WORKSPACE"] = str(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert result.returncode == expect, result.stderr + result.stdout
    return json.loads(result.stdout)


def setup_function() -> None:
    shutil.rmtree(TMP_ROOT, ignore_errors=True)
    (TMP_ROOT / "source" / "hiring" / "early-career").mkdir(parents=True)
    (TMP_ROOT / "source" / "acme" / "robotics").mkdir(parents=True)
    (TMP_ROOT / "source" / "hiring" / "early-career" / "notes.md").write_text("# Hiring Market\nEarly-career signals and internships.\n")
    (TMP_ROOT / "source" / "acme" / "robotics" / "dossier.md").write_text("# Robotics\nFounders and embodied AI map.\n")


def teardown_function() -> None:
    shutil.rmtree(TMP_ROOT, ignore_errors=True)


def test_scan_suggest_filters_generic_terms_and_preserves_evidence() -> None:
    data = run_cmd("suggest", "--root", str(TMP_ROOT / "source"), "--max-depth", "4", "--limit", "3")
    titles = [s["title"] for s in data["suggestions"]]
    assert "Hiring" in titles
    assert "Robotics" in titles
    assert "Source" not in titles
    assert "Market" not in titles
    assert any(s["evidence_paths"] for s in data["suggestions"] if s["title"] == "Hiring")


def test_repo_lifecycle_compendium_and_dedupe() -> None:
    rid = "repo_20260613_998"
    proposed = run_cmd("propose", "--title", "Early Career Hiring Market", "--objective", "Track signals", "--repo-id", rid)
    assert proposed["repo_id"] == rid
    active = run_cmd("activate", "--repo-id", rid)
    assert active["repo"]["status"] == "active"
    first = run_cmd("append", "--repo-id", rid, "--source", "smoke", "--source-ref", "test", "--summary", "Hiring signal", "--payload-json", '{"signal":"internships"}')
    second = run_cmd("append", "--repo-id", rid, "--source", "smoke", "--source-ref", "test", "--summary", "Hiring signal", "--payload-json", '{"signal":"internships"}')
    assert first["status"] == "appended"
    assert second["status"] == "duplicate_skipped"
    compact = run_cmd("compact", "--repo-id", rid)
    compendium = run_cmd("compendium")
    assert Path(compact["path"]).exists()
    assert Path(compendium["path"]).exists()


def test_append_failure_logs_repair_without_unhandled_error() -> None:
    result = run_cmd("append", "--repo-id", "missing", "--source", "smoke", "--source-ref", "bad", "--summary", "missing")
    assert result["ok"] is False
    assert result["repair_logged"] is True
    status = run_cmd("repair-status")
    assert status["count"] == 1
    assert status["reasons"]["repo_not_found"] == 1


EXAMPLES = SKILL_ROOT / "assets" / "examples"


def test_validate_accepts_valid_fixtures() -> None:
    data = run_cmd("validate", str(EXAMPLES / "valid"))
    assert data["all_valid"] is True
    assert data["count"] == 6
    assert all(r["valid"] for r in data["results"])


def test_validate_rejects_invalid_fixtures() -> None:
    data = run_cmd("validate", str(EXAMPLES / "invalid"))
    assert data["all_valid"] is False
    assert data["count"] >= 5
    assert all(not r["valid"] and r["errors"] for r in data["results"])


def test_promotion_target_must_be_knowledge() -> None:
    # Knowledge purity gate: promotion_candidate target outside Knowledge/ is invalid.
    bad = {
        "kind": "promotion_candidate",
        "candidate_id": "pc_1",
        "topic_id": "t_1",
        "target": "Research/_engine/notes.md",
        "claim_ids": ["c_1"],
        "rationale": "x",
        "review_status": "proposed",
        "provenance": "con_test",
    }
    import research_engine as re_mod  # type: ignore
    errors = re_mod.validate_record(bad)
    assert any("Knowledge/" in e for e in errors)
def test_overlay_seed_is_idempotent_and_populates_personal_nodes() -> None:
    first = run_cmd("overlay-seed")
    second = run_cmd("overlay-seed")
    assert first["ok"] is True
    assert second["added"] == []


def test_map_ontology_matches_aliases_and_suggests_unknowns() -> None:
    import sys as _sys
    _sys.path.insert(0, str(SCRIPT.parent))
    from profile_loader import profile_get  # type: ignore

    run_cmd("overlay-seed")
    venture = profile_get("venture_name")
    if venture:
        v = run_cmd("map-ontology", "--topic", venture)
        assert v["matched"] is True
        assert any(m["label"] == venture for m in v["matches"])
    unknown = run_cmd("map-ontology", "--topic", "Quantum Error Correction", "--suggest")
    assert unknown["matched"] is False
    assert unknown["candidate"]["label"] == "Quantum Error Correction"


def test_map_ontology_can_create_candidate_node() -> None:
    run_cmd("overlay-seed")
    created = run_cmd("map-ontology", "--topic", "Thermoelectric Control", "--suggest", "--create-node")
    assert created["created"] == "node_thermoelectric-control"
    state = json.loads((TMP_ROOT / "ontology" / "registry.json").read_text())
    assert any(node["node_id"] == "node_thermoelectric-control" for node in state["nodes"])


def test_one_shot_executes_without_approval_or_questions() -> None:
    fake = json.dumps([
        {"url": "https://example.com/a", "title": "A Source", "text": "Alpha evidence sentence. More text."},
        {"url": "https://example.com/b", "title": "B Source", "text": "Beta evidence sentence. More text."},
    ])
    env = os.environ.copy()
    env["ZO_WORKSPACE"] = str(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    env["RESEARCH_ENGINE_ROOT"] = str(TMP_ROOT / "repos")
    env["RESEARCH_ENGINE_STATE_ROOT"] = str(TMP_ROOT)
    env["RESEARCH_ENGINE_FAKE_EXA_RESULTS"] = fake
    result = subprocess.run([
        sys.executable, str(SCRIPT), "run", "--query", "What is alpha beta?", "--depth", "one-shot", "--mode", "explainer"
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr + result.stdout
    data = json.loads(result.stdout)
    assert data["status"] == "complete"
    assert data["approval_required"] is False
    assert Path(TEST_WORKSPACE, data["artifacts"]["synthesis"]).exists()
    assert Path(TEST_WORKSPACE, data["artifacts"]["topic_index"]).exists()


def test_standard_run_pauses_until_approval_then_executes() -> None:
    fake = json.dumps([
        {"url": "https://example.com/std", "title": "Standard Source", "text": "Standard evidence sentence."},
    ])
    env = os.environ.copy()
    env["ZO_WORKSPACE"] = str(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    env["RESEARCH_ENGINE_ROOT"] = str(TMP_ROOT / "repos")
    env["RESEARCH_ENGINE_STATE_ROOT"] = str(TMP_ROOT)
    env["RESEARCH_ENGINE_FAKE_EXA_RESULTS"] = fake
    created = subprocess.run([
        sys.executable, str(SCRIPT), "run", "--query", "Standard run query", "--depth", "standard", "--mode", "strategy-research"
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert created.returncode == 0, created.stderr + created.stdout
    data = json.loads(created.stdout)
    assert data["status"] == "awaiting_approval"
    assert data["approval_required"] is True
    approved = subprocess.run([
        sys.executable, str(SCRIPT), "approve-run", "--run-id", data["run_id"]
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert approved.returncode == 0, approved.stderr + approved.stdout
    approved_data = json.loads(approved.stdout)
    assert approved_data["status"] == "complete"


def test_local_workspace_scan_requires_explicit_authorization() -> None:
    fake = json.dumps([])
    env = os.environ.copy()
    env["ZO_WORKSPACE"] = str(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    env["RESEARCH_ENGINE_ROOT"] = str(TMP_ROOT / "repos")
    env["RESEARCH_ENGINE_STATE_ROOT"] = str(TMP_ROOT)
    env["RESEARCH_ENGINE_FAKE_EXA_RESULTS"] = fake
    no_scan = subprocess.run([
        sys.executable, str(SCRIPT), "run", "--query", "hiring robotics", "--depth", "one-shot", "--mode", "knowledge-scan"
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    yes_scan = subprocess.run([
        sys.executable, str(SCRIPT), "run", "--query", "hiring robotics", "--depth", "one-shot", "--mode", "knowledge-scan", "--allow-local-scan"
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert no_scan.returncode == 0, no_scan.stderr + no_scan.stdout
    assert yes_scan.returncode == 0, yes_scan.stderr + yes_scan.stdout
    no_data = json.loads(no_scan.stdout)
    yes_data = json.loads(yes_scan.stdout)
    no_sources = Path(TEST_WORKSPACE, no_data["artifacts"]["run_dir"], "SOURCES.jsonl").read_text()
    yes_sources = Path(TEST_WORKSPACE, yes_data["artifacts"]["run_dir"], "SOURCES.jsonl").read_text()
    assert "local_scan" not in no_sources
    assert "local_scan" in yes_sources




def test_promotion_candidate_dry_run_and_confirm_gate() -> None:
    fake = json.dumps([
        {"url": "https://example.com/promote", "title": "Promotion Source", "text": "Promotion-worthy evidence sentence."},
    ])
    env = os.environ.copy()
    env["ZO_WORKSPACE"] = str(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    env["RESEARCH_ENGINE_ROOT"] = str(TMP_ROOT / "repos")
    env["RESEARCH_ENGINE_STATE_ROOT"] = str(TMP_ROOT)
    env["RESEARCH_ENGINE_KNOWLEDGE_ROOT"] = str(TMP_ROOT / "Knowledge")
    env["RESEARCH_ENGINE_FAKE_EXA_RESULTS"] = fake
    run = subprocess.run([
        sys.executable, str(SCRIPT), "run", "--query", "Promotion gate topic", "--depth", "one-shot", "--mode", "explainer"
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert run.returncode == 0, run.stderr + run.stdout
    topic = json.loads(run.stdout)["topic_slug"]
    proposed = subprocess.run([
        sys.executable, str(SCRIPT), "propose-promotion", "--topic", topic, "--target", "Knowledge/research-engine-test/promotion.md"
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert proposed.returncode == 0, proposed.stderr + proposed.stdout
    pdata = json.loads(proposed.stdout)
    assert pdata["ok"] is True
    candidate_id = pdata["candidate_id"]
    target = TMP_ROOT / "Knowledge" / "research-engine-test" / "promotion.md"
    if target.exists():
        target.unlink()
    dry = subprocess.run([
        sys.executable, str(SCRIPT), "promote", "--candidate-id", candidate_id, "--dry-run"
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert dry.returncode == 0, dry.stderr + dry.stdout
    dry_data = json.loads(dry.stdout)
    assert dry_data["ok"] is True
    assert dry_data["dry_run"] is True
    assert not target.exists()
    blocked = subprocess.run([
        sys.executable, str(SCRIPT), "promote", "--candidate-id", candidate_id
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert blocked.returncode == 0, blocked.stderr + blocked.stdout
    assert json.loads(blocked.stdout)["ok"] is False
    confirmed = subprocess.run([
        sys.executable, str(SCRIPT), "promote", "--candidate-id", candidate_id, "--confirm"
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert confirmed.returncode == 0, confirmed.stderr + confirmed.stdout
    cdata = json.loads(confirmed.stdout)
    assert cdata["ok"] is True
    assert target.exists()
    assert "Promotion gate topic" in target.read_text()
    assert (TMP_ROOT / "promotions" / "PROMOTION_LOG.jsonl").exists()


def test_promotion_refuses_non_knowledge_target() -> None:
    fake = json.dumps([
        {"url": "https://example.com/promote2", "title": "Promotion Source", "text": "Evidence."},
    ])
    env = os.environ.copy()
    env["ZO_WORKSPACE"] = str(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    env["RESEARCH_ENGINE_ROOT"] = str(TMP_ROOT / "repos")
    env["RESEARCH_ENGINE_STATE_ROOT"] = str(TMP_ROOT)
    env["RESEARCH_ENGINE_KNOWLEDGE_ROOT"] = str(TMP_ROOT / "Knowledge")
    env["RESEARCH_ENGINE_FAKE_EXA_RESULTS"] = fake
    run = subprocess.run([
        sys.executable, str(SCRIPT), "run", "--query", "Bad promotion target", "--depth", "one-shot", "--mode", "explainer"
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert run.returncode == 0, run.stderr + run.stdout
    topic = json.loads(run.stdout)["topic_slug"]
    bad = subprocess.run([
        sys.executable, str(SCRIPT), "propose-promotion", "--topic", topic, "--target", "Research/not-knowledge.md"
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert bad.returncode == 0, bad.stderr + bad.stdout
    data = json.loads(bad.stdout)
    assert data["ok"] is False
    assert "Knowledge/" in data["error"]


def test_one_shot_plan_records_context_scan_and_worker_defaults() -> None:
    fake = json.dumps([
        {"url": "https://example.com/context", "title": "Context Source", "text": "Context evidence sentence."},
    ])
    env = os.environ.copy()
    env["ZO_WORKSPACE"] = str(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    env["RESEARCH_ENGINE_ROOT"] = str(TMP_ROOT / "repos")
    env["RESEARCH_ENGINE_STATE_ROOT"] = str(TMP_ROOT)
    env["RESEARCH_ENGINE_FAKE_EXA_RESULTS"] = fake
    result = subprocess.run([
        sys.executable, str(SCRIPT), "run", "--query", "What should one shot research do?", "--depth", "one-shot", "--mode", "explainer"
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr + result.stdout
    data = json.loads(result.stdout)
    plan = json.loads(Path(TEST_WORKSPACE, data["artifacts"]["run_dir"], "PLAN.json").read_text())
    assert plan["context_scan_authorized"] is True
    assert plan["zoask_worker_drops"] == 2
    assert plan["exa_num_results"] == 5


def test_diligence_one_shot_disables_internal_context_scan_by_default() -> None:
    import research_run  # type: ignore

    plan = research_run.plan_for(
        "Pre-meeting DD on Acme Ventures before investor call",
        "diligence",
        "one-shot",
        "acme-ventures-dd",
        [],
        False,
    )

    assert plan["context_scan_authorized"] is False
    assert plan["source_scope"] == "external_first_no_unrelated_internal_context"
    assert "prior" in plan["source_policy"].lower()


def test_diligence_worker_prompt_preserves_source_isolation() -> None:
    import research_run  # type: ignore

    plan = research_run.plan_for(
        "Pre-meeting DD on Acme Ventures before investor call",
        "diligence",
        "one-shot",
        "acme-ventures-dd",
        [],
        False,
    )
    prompt = research_run.build_worker_prompt(plan, 0, [], [])

    assert "same stakeholder" in prompt
    assert "outputs" in prompt.lower()


def test_investor_diligence_plan_records_manual_context_and_approved_internal_policy() -> None:
    import research_run  # type: ignore
    import sys as _sys
    _sys.path.insert(0, str(SCRIPT.parent))
    from profile_loader import profile_get  # type: ignore

    plan = research_run.plan_for(
        "Diligence Lux Capital for investor prep",
        "investor-diligence",
        "standard",
        "lux-capital-investor-diligence",
        [],
        False,
    )

    assert plan["manual_trigger_only"] is True
    assert plan["meeting_required"] is False
    assert plan["brief_size"] == "standard"
    assert plan["allowed_calendar_accounts"] == profile_get("allowed_calendar_accounts")
    assert plan["allowed_private_email_accounts"] == profile_get("allowed_private_email_accounts")
    assert plan["excluded_calendar_accounts"] == profile_get("excluded_calendar_accounts")
    assert plan["evergreen_internal_sources"] == profile_get("evergreen_internal_sources")
    assert any(item["class"] == "complementary" for item in plan["portfolio_classification_schema"])


def test_investor_diligence_brief_size_can_be_overridden() -> None:
    import research_run  # type: ignore

    plan = research_run.plan_for(
        "Diligence Founders Fund for Acme",
        "investor-diligence",
        "quick",
        None,
        [],
        False,
        "full-dossier",
    )

    assert plan["brief_size"] == "full-dossier"


def test_one_shot_synthesis_includes_citations_and_worker_drop_section() -> None:
    fake = json.dumps([
        {"url": "https://example.com/cited", "title": "Cited Source", "text": "Cited evidence sentence. More text."},
    ])
    env = os.environ.copy()
    env["ZO_WORKSPACE"] = str(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    env["RESEARCH_ENGINE_ROOT"] = str(TMP_ROOT / "repos")
    env["RESEARCH_ENGINE_STATE_ROOT"] = str(TMP_ROOT)
    env["RESEARCH_ENGINE_FAKE_EXA_RESULTS"] = fake
    result = subprocess.run([
        sys.executable, str(SCRIPT), "run", "--query", "How should citations work?", "--depth", "one-shot", "--mode", "explainer"
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr + result.stdout
    data = json.loads(result.stdout)
    synthesis = Path(TEST_WORKSPACE, data["artifacts"]["synthesis"]).read_text()
    assert "Cited Source [^1]" in synthesis
    assert "[^1]: https://example.com/cited" in synthesis
    assert "## Zoask Worker Drops" in synthesis
    assert "WORKER_DROPS.jsonl" not in synthesis or "Zoask" in synthesis


def test_persisted_mode_registry_cannot_downgrade_explainer_one_shot_source_count() -> None:
    import research_run  # type: ignore
    mode_dir = TMP_ROOT / "modes"
    mode_dir.mkdir(parents=True, exist_ok=True)
    (mode_dir / "explainer.json").write_text(json.dumps({
        "mode": "explainer",
        "version": "1.0",
        "label": "Explainer",
        "sections": [],
        "exa_num_results": {"one-shot": 3, "quick": 5, "standard": 8, "deep": 12},
    }))
    old_modes = research_run.MODES_DIR
    try:
        research_run.MODES_DIR = mode_dir
        mode = research_run.load_mode("explainer")
        assert mode["exa_num_results"]["one-shot"] == 5
    finally:
        research_run.MODES_DIR = old_modes


def test_investor_diligence_collects_evergreen_and_approved_content_library(tmp_path) -> None:
    import research_run  # type: ignore
    import profile_loader  # type: ignore

    old_workspace = research_run.WORKSPACE
    old_disable = os.environ.get("RESEARCH_ENGINE_DISABLE_CONTENT_LIBRARY_SCAN")
    old_profile_env = os.environ.get("RESEARCH_ENGINE_PROFILE")
    old_fake_exa = os.environ.get("RESEARCH_ENGINE_FAKE_EXA_RESULTS")
    fixture_profile = str(SKILL_ROOT / "assets" / "examples" / "profile.test.json")
    try:
        os.environ["RESEARCH_ENGINE_PROFILE"] = fixture_profile
        os.environ["RESEARCH_ENGINE_FAKE_EXA_RESULTS"] = json.dumps([
            {"url": "https://vc.example.com/lux", "title": "Lux Capital", "text": "External investor evidence."}
        ])
        profile_loader.clear_cache()
        research_run.WORKSPACE = tmp_path
        source = tmp_path / "Knowledge" / "content-library" / "positions" / "canonical.md"
        source.parent.mkdir(parents=True)
        source.write_text("# Venture\nPhysical AI hospital contact data thesis.\n")
        app = tmp_path / "Knowledge" / "content-library" / "applications" / "yc.md"
        app.parent.mkdir(parents=True)
        app.write_text("# YC application\nApplication narrative.\n")
        os.environ.pop("RESEARCH_ENGINE_DISABLE_CONTENT_LIBRARY_SCAN", None)
        plan = research_run.plan_for(
            "Diligence Lux Capital for investor prep",
            "investor-diligence",
            "standard",
            "lux-capital-investor-diligence",
            [],
            False,
            None,
        )
        sources = research_run.collect_sources(plan)
        uris = [s["uri"] for s in sources]
        assert "https://example.test/evergreen-memo" in uris
        assert "https://example.test/evergreen-deck" in uris
        assert any("Knowledge/content-library/positions/canonical.md" == uri for uri in uris)
        assert not any("applications/yc.md" in uri for uri in uris)
    finally:
        research_run.WORKSPACE = old_workspace
        if old_profile_env is None:
            os.environ.pop("RESEARCH_ENGINE_PROFILE", None)
        else:
            os.environ["RESEARCH_ENGINE_PROFILE"] = old_profile_env
        if old_fake_exa is None:
            os.environ.pop("RESEARCH_ENGINE_FAKE_EXA_RESULTS", None)
        else:
            os.environ["RESEARCH_ENGINE_FAKE_EXA_RESULTS"] = old_fake_exa
        profile_loader.clear_cache()
        if old_disable is None:
            os.environ.pop("RESEARCH_ENGINE_DISABLE_CONTENT_LIBRARY_SCAN", None)
        else:
            os.environ["RESEARCH_ENGINE_DISABLE_CONTENT_LIBRARY_SCAN"] = old_disable


def test_investor_diligence_still_runs_external_search_despite_internal_sources() -> None:
    """Internal approved sources must NOT suppress external VC evidence (external-first)."""
    import research_run  # type: ignore

    calls = {"n": 0}

    def fake_exa(query, num_results):
        calls["n"] += 1
        return [{"url": "https://vc.example.com/fund", "title": "Fund Page", "text": "External VC evidence."}]

    old_exa = research_run.exa_search
    old_cl = research_run.approved_content_library_scan
    try:
        research_run.exa_search = fake_exa
        # Simulate 2+ internal approved content-library rows present.
        research_run.approved_content_library_scan = lambda q, max_files=6: [
            {"uri": "Knowledge/content-library/positions/a.md", "title": "a.md", "text": "Internal A.", "type": "approved_content_library", "provided": False},
            {"uri": "Knowledge/content-library/positions/b.md", "title": "b.md", "text": "Internal B.", "type": "approved_content_library", "provided": False},
        ]
        plan = research_run.plan_for(
            "Diligence Lux Capital for Acme investor prep",
            "investor-diligence",
            "standard",
            "lux-capital-investor-diligence",
            [],
            False,
            None,
        )
        sources = research_run.collect_sources(plan)
        assert calls["n"] >= 1, "external Exa search must run for investor diligence even with internal sources"
        assert any(s.get("type") == "exa" for s in sources), "external rows must be present"
    finally:
        research_run.exa_search = old_exa
        research_run.approved_content_library_scan = old_cl


def test_product_diligence_plan_records_preference_discovery_and_review_policy() -> None:
    import research_run  # type: ignore

    plan = research_run.plan_for(
        "Find the best on-person AI recorder for in-person meetings, walks, and voice notes",
        "product-diligence",
        "standard",
        "ai-recorder-product-diligence",
        [],
        False,
    )

    assert plan["mode"] == "product-diligence"
    assert plan["source_scope"] == "external_product_reviews_first_with_preference_discovery"
    assert plan["context_scan_authorized"] is False
    assert plan["socratic_preference_discovery"] is True
    assert plan["brief_size"] == "standard"
    assert any("hands-on professional reviews" in item for item in plan["source_quality_order"])
    assert any(item["criterion"] == "Workflow/export/API fit" for item in plan["default_ranking_criteria"])
    assert "affiliate" in plan["source_policy"].lower()
    assert "purchase" in plan["source_policy"].lower()


def test_product_diligence_one_shot_states_assumptions_instead_of_pausing() -> None:
    import research_run  # type: ignore

    plan = research_run.plan_for(
        "Quickly compare Plaud, Fieldy, and similar AI recorders",
        "product-diligence",
        "one-shot",
        "ai-recorder-quick-compare",
        [],
        False,
    )

    assert plan["socratic_preference_discovery"] is False
    assert "Do not pause" in plan["one_shot_preference_behavior"]
    assert plan["zoask_worker_drops"] == 2


def test_product_diligence_brief_size_can_be_overridden() -> None:
    import research_run  # type: ignore

    plan = research_run.plan_for(
        "Diligence Plaud NotePin for in-person meeting capture",
        "product-diligence",
        "quick",
        "plaud-notepin-product-diligence",
        [],
        False,
        "full-dossier",
    )

    assert plan["brief_size"] == "full-dossier"


def test_product_diligence_worker_prompt_includes_socratic_and_source_quality_context() -> None:
    import research_run  # type: ignore

    plan = research_run.plan_for(
        "Find the best AI recorder for meetings and walks",
        "product-diligence",
        "standard",
        "ai-recorder-product-diligence",
        [],
        False,
    )
    prompt = research_run.build_worker_prompt(plan, 0, [], [])

    assert "Socratic preference" in prompt
    assert "independent reviews" in prompt
    assert "Workflow/export/API fit" in prompt


def test_product_diligence_one_shot_executes_with_fake_external_sources() -> None:
    fake = json.dumps([
        {"url": "https://example.com/recorder-review", "title": "Recorder Review", "text": "Hands-on recorder review evidence."},
        {"url": "https://example.com/recorder-api", "title": "Recorder API Docs", "text": "API and export documentation evidence."},
    ])
    env = os.environ.copy()
    env["ZO_WORKSPACE"] = str(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    env["RESEARCH_ENGINE_ROOT"] = str(TMP_ROOT / "repos")
    env["RESEARCH_ENGINE_STATE_ROOT"] = str(TMP_ROOT)
    env["RESEARCH_ENGINE_FAKE_EXA_RESULTS"] = fake
    result = subprocess.run([
        sys.executable,
        str(SCRIPT),
        "run",
        "--query",
        "Find the best AI recorder for in-person meetings and voice notes",
        "--depth",
        "one-shot",
        "--mode",
        "product-diligence",
        "--topic",
        "ai-recorder-product-diligence",
    ], cwd=str(TEST_WORKSPACE), env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr + result.stdout
    data = json.loads(result.stdout)
    assert data["status"] == "complete"
    plan = json.loads(Path(TEST_WORKSPACE, data["artifacts"]["run_dir"], "PLAN.json").read_text())
    assert plan["mode"] == "product-diligence"
    assert plan["topic_slug"] == "ai-recorder-product-diligence"
    assert plan["context_scan_authorized"] is False
    assert plan["source_scope"] == "external_product_reviews_first_with_preference_discovery"
    sources = Path(TEST_WORKSPACE, data["artifacts"]["run_dir"], "SOURCES.jsonl").read_text()
    assert "Recorder Review" in sources
    assert "local_scan" not in sources


def test_one_shot_context_scan_does_not_mask_missing_exa_key(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    prior_repo = workspace / "Research" / "repos" / "prior-topic"
    prior_repo.mkdir(parents=True)
    (prior_repo / "INDEX.md").write_text("# Prior Topic\nUnrelated prior local context.\n", encoding="utf-8")
    env = os.environ.copy()
    env.update({
        "ZO_WORKSPACE": str(workspace),
        "RESEARCH_ENGINE_ROOT": str(workspace / "Research" / "repos"),
        "RESEARCH_ENGINE_STATE_ROOT": str(workspace / "Research" / "_engine"),
        "EXA_N5OS_KEY": "",
        "EXA_API_KEY": "",
        "RESEARCH_ENGINE_DISABLE_ZOASK_WORKERS": "1",
    })
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "run",
            "--query",
            "Needs external evidence",
            "--mode",
            "explainer",
            "--depth",
            "one-shot",
            "--topic",
            "missing-exa-regression",
        ],
        cwd=str(workspace),
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "External search requires EXA_N5OS_KEY or EXA_API_KEY" in result.stderr



def test_install_apply_reports_post_write_profile_state(tmp_path: Path) -> None:
    copied_skill = tmp_path / "Skills" / "research-engine"
    shutil.copytree(SKILL_ROOT, copied_skill, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "profile.json"))
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)
    env = os.environ.copy()
    env["ZO_WORKSPACE"] = str(workspace)
    result = subprocess.run(
        [sys.executable, str(copied_skill / "scripts" / "install.py"), "--apply"],
        cwd=str(tmp_path),
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    data = json.loads(result.stdout)
    assert data["status"]["local_profile"] is True
    assert (copied_skill / "config" / "profile.json").exists()
    assert not any("No local profile" in item for item in data["degraded_capabilities"])


def test_packaged_router_and_legacy_shim_work_after_install_apply(tmp_path: Path) -> None:
    copied_skill = tmp_path / "Skills" / "research-engine"
    shutil.copytree(SKILL_ROOT, copied_skill, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "profile.json"))
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)
    env = os.environ.copy()
    env["ZO_WORKSPACE"] = str(workspace)

    dry = subprocess.run(
        [sys.executable, str(copied_skill / "scripts" / "install.py")],
        cwd=str(workspace),
        env=env,
        text=True,
        capture_output=True,
    )
    assert dry.returncode == 0, dry.stderr + dry.stdout
    dry_data = json.loads(dry.stdout)
    assert dry_data["status"]["research_router"] is True
    assert dry_data["status"]["legacy_research_router"] is False

    applied = subprocess.run(
        [sys.executable, str(copied_skill / "scripts" / "install.py"), "--apply"],
        cwd=str(workspace),
        env=env,
        text=True,
        capture_output=True,
    )
    assert applied.returncode == 0, applied.stderr + applied.stdout
    applied_data = json.loads(applied.stdout)
    assert applied_data["status"]["research_router"] is True
    assert applied_data["status"]["legacy_research_router"] is True

    packaged = subprocess.run(
        [sys.executable, str(copied_skill / "scripts" / "research_router.py"), "Diligence Acme Robotics", "--create", "--slug", "acme-robotics", "--json"],
        cwd=str(workspace),
        env=env,
        text=True,
        capture_output=True,
    )
    assert packaged.returncode == 0, packaged.stderr + packaged.stdout
    packaged_data = json.loads(packaged.stdout)
    assert packaged_data["category"] == "market-intel"
    assert Path(packaged_data["item_path"]).exists()

    legacy = subprocess.run(
        [sys.executable, str(workspace / "N5" / "scripts" / "research_router.py"), "Health device market scan", "--slug", "health-device", "--json"],
        cwd=str(workspace),
        env=env,
        text=True,
        capture_output=True,
    )
    assert legacy.returncode == 0, legacy.stderr + legacy.stdout
    legacy_data = json.loads(legacy.stdout)
    assert legacy_data["item_slug"] == "health-device"
    assert legacy_data["router"] == "Skills/research-engine/scripts/research_router.py"
