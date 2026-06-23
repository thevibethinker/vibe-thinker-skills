"""
ZoATS path resolution — single source of truth for the install location.

Resolution order:
1. ZOATS_HOME environment variable (explicit override)
2. Parent of this file's directory (../  relative to lib/)
3. Fallback: /home/workspace/ZoATS
"""

import os
from pathlib import Path


def zoats_home() -> Path:
    env = os.environ.get("ZOATS_HOME")
    if env:
        return Path(env).expanduser().resolve()

    # Repo root: lib/ is one level under repo root
    repo_root = Path(__file__).resolve().parent.parent
    if repo_root.exists():
        return repo_root

    return Path("/home/workspace/ZoATS").resolve()


ZOATS_HOME = zoats_home().resolve()
