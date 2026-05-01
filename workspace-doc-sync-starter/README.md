---
created: 2026-05-01
last_edited: 2026-05-01
version: 1.0
provenance: con_CICEmalXAepToekB
---
# workspace-doc-sync-starter

A standalone starter kit for building a synchronized AI workspace across multiple agent harnesses.

It gives you:
- a **shared canonical doc layer**
- **thin tool adapters** like `CLAUDE.md` and `CODEX.md`
- a first-class **identity layer** (`SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`)
- **local override patterns** for project subdirectories
- a **scaffold script** that can stamp the structure into a fresh workspace

## Why this exists

Most multi-agent setups drift because instructions get duplicated across:
- `AGENTS.md`
- `CLAUDE.md`
- tool prompts
- project notes
- system preference files

This starter kit uses a cleaner pattern:
- shared docs hold the durable contract
- harness adapters stay thin
- identity and user context are explicit files
- local rules live near the work
- monolithic `systemprefs` content gets decomposed by concern instead of copied around

## Included structure

```text
/workspace/
├── WORKSPACE_MAP.md
├── AGENTS.md
├── POLICY.md
├── SOUL.md
├── IDENTITY.md
├── USER.md
├── TOOLS.md
├── HEARTBEAT.md
├── CLAUDE.md
├── CODEX.md
├── system/
│   ├── HARNESS_CONTRACT.md
│   └── SESSION_STATE_POLICY.md
└── <subdirs>/
    └── AGENTS.md
```

## Quick start

### Preview scaffold

```bash
python3 Skills/workspace-doc-sync-starter/scripts/scaffold.py --target /home/workspace --dry-run
```

### Install scaffold

```bash
python3 Skills/workspace-doc-sync-starter/scripts/scaffold.py --target /home/workspace
```

### Install somewhere else

```bash
python3 Skills/workspace-doc-sync-starter/scripts/scaffold.py --target /path/to/new/workspace
```

## Safe behavior

The scaffold script:
- refuses to overwrite files unless `--force` is provided
- creates only the documented starter structure
- copies templates from the skill's bundled `assets/`
- prints exactly what it created or skipped

## What to customize first

After scaffolding, edit:
1. `SOUL.md`
2. `IDENTITY.md`
3. `USER.md`
4. `TOOLS.md`
5. `WORKSPACE_MAP.md`

## Recommended replication rule

When you want to support a new harness:
- add a thin adapter file
- point it back to the shared layer
- do not duplicate the whole manual

## Reference docs

See `references/architecture.md` for the conceptual model behind the structure.
See `references/systemprefs-mapping.md` for how to translate a monolithic `systemprefs` file into this starter structure.