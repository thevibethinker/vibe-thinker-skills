---
created: 2026-05-01
last_edited: 2026-05-01
version: 1.0
provenance: con_CICEmalXAepToekB
---
# Architecture Reference

## The problem

A multi-agent workspace usually accumulates overlapping instruction surfaces:
- root operating docs
- per-harness adapter files
- persona prompts
- system preference files
- project-local conventions

Without structure, the same instruction gets copied in multiple places and eventually drifts.

## The solution

Use a four-layer model:

### 1. Shared canonical layer

The durable source of truth for workspace-wide behavior.

Typical files:
- `WORKSPACE_MAP.md`
- `AGENTS.md`
- `POLICY.md`
- `system/HARNESS_CONTRACT.md`
- `system/SESSION_STATE_POLICY.md`

### 2. Harness adapter layer

Thin files that tell a specific tool how to enter the system.

Typical files:
- `CLAUDE.md`
- `CODEX.md`
- other harness-specific boot files

Rule: adapters should be short and mostly point back to shared docs.

### 3. Identity layer

Persistent selfhood and human-context files.

Typical files:
- `SOUL.md`
- `IDENTITY.md`
- `USER.md`
- `TOOLS.md`
- `HEARTBEAT.md`

### 4. Local override layer

More specific docs placed near the work.

Typical files:
- `<project>/AGENTS.md`
- `<project>/POLICY.md`
- `<project>/SOUL.md`

Rule: most-specific guidance wins.

## The mapping

If someone asks how to replicate the pattern, the minimal mapping is:

| Need | File |
|---|---|
| Where do things live? | `WORKSPACE_MAP.md` |
| What are the global operating rules? | `AGENTS.md` |
| What are the file-placement rules? | `POLICY.md` |
| What do all harnesses share? | `system/HARNESS_CONTRACT.md` |
| When should session state exist? | `system/SESSION_STATE_POLICY.md` |
| How does Claude enter? | `CLAUDE.md` |
| How does Codex enter? | `CODEX.md` |
| Who is the AI in this workspace? | `SOUL.md` + `IDENTITY.md` |
| Who is the human? | `USER.md` |
| What is special about this machine? | `TOOLS.md` |

## Healthy vs unhealthy system

Healthy:
- shared docs are authoritative
- adapters are thin
- identity is explicit
- local overrides are limited and justified

Unhealthy:
- the same instructions are duplicated across harness files
- no one knows which doc is authoritative
- local exceptions creep into root docs
- identity and user preferences are hidden in random prompts

## Design heuristic

A global behavior change should usually require editing one shared file, not three adapters.

That is the easiest litmus test for whether the system is actually synchronized.