#!/usr/bin/env python3
"""Research Engine portable installer / acclimatizer.

Run this once after importing the skill onto a new Zo. It:
  1. Detects the workspace root and the local research/knowledge layout.
  2. Probes for soft dependencies (content library, meeting-ingestion,
     research_router, Exa key) and reports degrade-vs-full status.
  3. Scaffolds Research/_engine, Research/repos, and the content-library
     root if missing (spins up the *concept* where only docs exist).
  4. Creates config/profile.json from profile.default.json if absent, so
     the operator has a local file to edit (never overwrites an existing one).
  5. Prints a remapping checklist of what the operator must fill in.

Idempotent. Safe to re-run. Read-only unless --apply is passed.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = SKILL_DIR / "config"
DEFAULT_PROFILE = CONFIG_DIR / "profile.default.json"
LOCAL_PROFILE = CONFIG_DIR / "profile.json"
ROUTER_SCRIPT = SKILL_DIR / "scripts" / "research_router.py"
LEGACY_ROUTER = Path("N5/scripts/research_router.py")


def workspace_root() -> Path:
    return Path(os.environ.get("ZO_WORKSPACE", "/home/workspace"))


def probe(ws: Path) -> dict:
    cl_root = ws / "Knowledge" / "content-library"
    cl_docs = list((ws / "docs").glob("content-library*")) if (ws / "docs").exists() else []
    return {
        "workspace": str(ws),
        "research_repos": (ws / "Research" / "repos").exists(),
        "engine_state": (ws / "Research" / "_engine").exists(),
        "content_library_dir": cl_root.exists() and any(cl_root.rglob("*")),
        "content_library_docs_only": bool(cl_docs) and not cl_root.exists(),
        "meeting_ingestion": (ws / "Skills" / "meeting-ingestion").exists(),
        "research_router": ROUTER_SCRIPT.exists(),
        "legacy_research_router": (ws / LEGACY_ROUTER).exists(),
        "exa_key": bool(os.environ.get("EXA_N5OS_KEY") or os.environ.get("EXA_API_KEY")),
        "local_profile": LOCAL_PROFILE.exists(),
    }


def scaffold(ws: Path, apply: bool) -> list[str]:
    actions = []
    targets = [
        ws / "Research" / "repos",
        ws / "Research" / "_engine",
        ws / "Knowledge" / "content-library" / "positions",
    ]
    for t in targets:
        if not t.exists():
            actions.append(f"mkdir {t}")
            if apply:
                t.mkdir(parents=True, exist_ok=True)
    if not LOCAL_PROFILE.exists():
        actions.append(f"create {LOCAL_PROFILE} from default")
        if apply:
            shutil.copy(DEFAULT_PROFILE, LOCAL_PROFILE)
    legacy_router = ws / LEGACY_ROUTER
    if ROUTER_SCRIPT.exists() and not legacy_router.exists():
        actions.append(f"create compatibility shim {legacy_router}")
        if apply:
            legacy_router.parent.mkdir(parents=True, exist_ok=True)
            rel_target = os.path.relpath(ROUTER_SCRIPT, legacy_router.parent)
            shim = "\n".join([
                "#!/usr/bin/env python3",
                "from __future__ import annotations",
                "import runpy",
                "from pathlib import Path",
                f"runpy.run_path(str((Path(__file__).resolve().parent / {rel_target!r}).resolve()), run_name='__main__')",
                "",
            ])
            legacy_router.write_text(shim, encoding="utf-8")
            legacy_router.chmod(0o755)
            if not legacy_router.exists():
                raise RuntimeError(f"router shim verification failed: {legacy_router}")
    return actions


def main() -> int:
    ap = argparse.ArgumentParser(description="Research Engine portable installer")
    ap.add_argument("--apply", action="store_true", help="Create missing dirs/profile (default: dry-run report only)")
    args = ap.parse_args()

    ws = workspace_root()
    status = probe(ws)
    actions = scaffold(ws, args.apply)
    if args.apply:
        status = probe(ws)

    degraded = []
    if not status["exa_key"]:
        degraded.append("No Exa key -> external search disabled until EXA_N5OS_KEY or EXA_API_KEY is set; explicit --source still works.")
    if not status["content_library_dir"]:
        if status["content_library_docs_only"]:
            degraded.append("Content library is docs-only (concept present, no data) -> seed Knowledge/content-library/positions/ to enable approved-internal scan.")
        else:
            degraded.append("No content library -> approved-internal scan returns nothing until Knowledge/content-library/ is populated.")
    if not status["research_router"]:
        degraded.append("No packaged research_router.py -> canonical-deliverable routing is manual; reinstall or restore Skills/research-engine/scripts/research_router.py.")
    elif not status["legacy_research_router"] and not args.apply:
        degraded.append("Legacy N5/scripts/research_router.py shim not installed -> run install.py --apply or call Skills/research-engine/scripts/research_router.py directly.")
    if not status["meeting_ingestion"]:
        degraded.append("No meeting-ingestion skill -> repair-sweep for meeting-derived appends is inert (engine still works standalone).")
    if not status["local_profile"] and not args.apply:
        degraded.append("No local profile -> running on neutral default; create config/profile.json (re-run with --apply) and edit identity.")

    remap_checklist = [
        "Edit config/profile.json: owner_name, venture_name, venture_aliases, venture_notes.",
        "Set evergreen_internal_sources to this owner's canonical links (or []).",
        "Set allowed/excluded calendar + private email accounts (or [] to disable those layers).",
        "Set content_library_root if not Knowledge/content-library.",
        "Set EXA_N5OS_KEY (or EXA_API_KEY) in Settings > Advanced for external search.",
        "Route deliverables: python3 scripts/research_router.py \"<topic>\" --create --slug <slug> --json.",
        "Compatibility shim: re-run scripts/install.py --apply to create N5/scripts/research_router.py for legacy prompts.",
        "Run: python3 scripts/research_engine.py overlay-seed  (seeds profile-driven ontology nodes).",
        "Verify: python3 -m pytest -q scripts/test_research_engine.py",
    ]

    report = {
        "mode": "apply" if args.apply else "dry-run",
        "status": status,
        "actions": actions,
        "degraded_capabilities": degraded,
        "remap_checklist": remap_checklist,
        "ok": True,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
