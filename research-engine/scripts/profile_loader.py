#!/usr/bin/env python3
"""Profile loader for the portable Research Engine skill.

Identity and owner/venture context are NOT hardcoded. They live in a profile
JSON so the skill can ship to a public repo and be re-pointed on any Zo.

Resolution order (first hit wins):
  1. $RESEARCH_ENGINE_PROFILE  (explicit path override)
  2. config/profile.json       (local, git-ignored, owner-specific)
  3. config/profile.default.json (neutral public default, always present)

Missing keys fall back to the neutral default, so an incomplete local
profile never crashes the engine.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
DEFAULT_PROFILE_PATH = CONFIG_DIR / "profile.default.json"
LOCAL_PROFILE_PATH = CONFIG_DIR / "profile.json"


def _read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


@lru_cache(maxsize=1)
def load_profile() -> dict[str, Any]:
    base = _read(DEFAULT_PROFILE_PATH)
    override_path = os.environ.get("RESEARCH_ENGINE_PROFILE")
    if override_path:
        base.update({k: v for k, v in _read(Path(override_path)).items() if v not in (None, "")})
    elif LOCAL_PROFILE_PATH.exists():
        base.update({k: v for k, v in _read(LOCAL_PROFILE_PATH).items() if v not in (None, "")})
    return base


def profile_get(key: str, default: Any = None) -> Any:
    return load_profile().get(key, default)


def clear_cache() -> None:
    load_profile.cache_clear()
