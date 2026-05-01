---
created: 2026-05-01
last_edited: 2026-05-01
version: 1.0
provenance: con_CICEmalXAepToekB
---
# Workspace Operating Contract

This file is the canonical, tool-agnostic operating contract for the workspace.

## Role Split

- `AGENTS.md` is the shared workspace constitution.
- `WORKSPACE_MAP.md` is the fast navigation index.
- `POLICY.md` governs placement and hygiene.
- `system/HARNESS_CONTRACT.md` is the shared cross-harness operating contract.
- `system/SESSION_STATE_POLICY.md` decides when session state is required.
- Tool-specific files such as `CLAUDE.md` and `CODEX.md` are thin adapters.

If an adapter starts re-stating the full workspace manual, slim the adapter instead of expanding it.

## Shared Defaults

- Prefer the smallest doc set that safely fits the task.
- Use workspace docs as source of truth.
- Keep scratch out of permanent workspace areas unless intentionally promoted.
- Declare permanent artifact placement before writing files.
- Prefer existing recipes, protocols, scripts, and local docs before inventing new flows.

## Precedence

Operating behavior:
1. Most specific local `AGENTS.md`
2. Root `AGENTS.md`
3. Tool adapters

If guidance conflicts, follow the more specific file and note the conflict explicitly.

## Drift Rule

Avoid duplicated instructions across harness adapters. Shared guidance belongs here; harness deltas belong in harness files.