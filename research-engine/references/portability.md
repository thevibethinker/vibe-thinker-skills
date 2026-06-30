---
created: 2026-06-18
last_edited: 2026-06-18
version: 1.0
provenance: con_XbMMeD3u4MxlbvOE
---
# Portability & Acclimatization

This skill is designed to ship to a public skills repo and be imported onto any Zo
(including [n5os-ode](https://github.com/thevibethinker/n5os-ode)) without carrying the
original owner's identity. All owner/venture context is externalized to a **profile**.

## Identity model

Nothing in `scripts/` hardcodes an owner, venture, account, or link. Identity is resolved
at runtime by `scripts/profile_loader.py` in this order:

1. `$RESEARCH_ENGINE_PROFILE` — explicit path override (used by tests/CI).
2. `config/profile.json` — local, **git-ignored**, owner-specific. Edit this after import.
3. `config/profile.default.json` — neutral public default, always committed.

Missing keys fall back to the neutral default, so an incomplete local profile never crashes
the engine. The public repo only ever contains `profile.default.json`; the real
`profile.json` stays on the owner's machine (see `.gitignore`).

### Profile keys

| Key | Purpose | Empty behavior |
| --- | --- | --- |
| `owner_name` | Display name in prose/prompts | "Operator" |
| `venture_name` | Org the diligence is run *for* | "Primary venture" |
| `venture_aliases` | Ontology overlay aliases | no extra overlay |
| `venture_notes` | Ontology overlay note | generic note |
| `content_library_root` | Where approved-internal scan looks | `Knowledge/content-library` |
| `evergreen_internal_sources` | Always-included canonical links | none injected |
| `allowed_calendar_accounts` | Calendar scan allowlist | calendar layer disabled |
| `excluded_calendar_accounts` | Calendar scan denylist | nothing excluded |
| `allowed_private_email_accounts` | Email summary allowlist | email layer disabled |
| `exclusion_terms` | Paths excluded from CL scan (e.g. applications) | none excluded |
| `focus_terms` | CL scan relevance boosters | generic terms |
| `overlay_extra_nodes` | Extra personal ontology nodes | venture node only |

## Soft dependencies (detect-and-degrade)

The engine runs standalone. These integrations enhance it when present and degrade
gracefully when absent. `scripts/install.py` probes all of them.

| Dependency | If present | If absent |
| --- | --- | --- |
| Exa key (`EXA_N5OS_KEY`/`EXA_API_KEY`) | External search | Explicit `--source` only; external search errors clearly |
| `Knowledge/content-library/` (data) | Approved-internal scan | Scan returns `[]`; no crash. n5os-ode ships docs only — seed it |
| `Skills/research-engine/scripts/research_router.py` | Packaged canonical-deliverable routing | Installed with the skill; `scripts/install.py --apply` also creates legacy `N5/scripts/research_router.py` shim |
| `Skills/meeting-ingestion/` | `repair-sweep` replays meeting appends | `repair-sweep` is inert; engine unaffected |


## Public repo install snippet

```bash
slug="research-engine"; dest="Skills"; repo="https://github.com/thevibethinker/vibe-thinker-skills/archive/refs/heads/main.tar.gz"; archive_root="vibe-thinker-skills-main"; mkdir -p "$dest" && curl -L "$repo" | tar -xz -C "$dest" --strip-components=1 "$archive_root/$slug"
```

## Install on a new Zo

```bash
# 1. (after copying Skills/research-engine/ into the target workspace)
python3 Skills/research-engine/scripts/install.py            # dry-run report
python3 Skills/research-engine/scripts/install.py --apply    # scaffold dirs + local profile

# 2. edit identity
$EDITOR Skills/research-engine/config/profile.json

# 3. set Exa key in Settings > Advanced (EXA_N5OS_KEY), then seed + verify
python3 Skills/research-engine/scripts/research_engine.py overlay-seed
python3 -m pytest -q Skills/research-engine/scripts/test_research_engine.py
```

The test suite passes against both the neutral default and a populated profile, which is the
portability contract: **green on a fresh import, green after remapping.**
