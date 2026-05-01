---
created: 2026-05-01
last_edited: 2026-05-01
version: 1.0
provenance: con_CICEmalXAepToekB
---
# Harness Contract

This file is the shared operating contract for all agent harnesses that work in the workspace.

## Design Goal

Preserve capability while reducing always-on context.

## Shared Load Order

For non-trivial work, load in this order:
1. `WORKSPACE_MAP.md`
2. `AGENTS.md`
3. `system/SESSION_STATE_POLICY.md`
4. specialized local docs only if needed

## Shared Defaults

- Prefer the smallest doc set that safely fits the task.
- Use shared workspace docs as the primary source of truth.
- Keep tool-specific deltas in tool adapters.
- Keep project-specific rules near the project.

## Lanes

Declare a working lane for substantive tasks:
- `explore` — ideation, options, ambiguous work
- `commit` — implementation, mutation, deployment, irreversible steps

## Blast Radius

Classify the expected surface area:
- `small`
- `medium`
- `large`

## Invariants

- Do not hallucinate.
- Do not claim complete before checks pass.
- Do not externally send or publish without explicit permission.
- Follow placement policy and local overrides.