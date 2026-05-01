---
name: workspace-doc-sync-starter
description: |
  Shareable starter kit for a synchronized workspace-doc system across multiple agent harnesses.
  Defines the platonic structure for shared operating docs, thin tool adapters, identity/personality files,
  and local overrides. Use when setting up a fresh AI workspace or explaining how to replicate this pattern.
compatibility: Created for Zo Computer
metadata:
  author: va.zo.computer
---

# Workspace Doc Sync Starter

## Purpose

This skill packages a **generic, reusable document architecture** for AI workspaces where multiple harnesses
(Zo, Claude Code, Codex, or others) need to stay aligned without duplicating instructions.
It also serves as a migration pattern for teams currently storing mixed operating behavior in a monolithic `systemprefs`-style file.

The pattern is:

- **shared docs are canonical**
- **tool-specific root adapters are thin**
- **identity/personality files are first-class**
- **subdirectories can override locally with more specific docs**

This is not just a folder template. It is a design pattern for keeping agent context synchronized while minimizing drift.

## Core Model

Use a **hub-and-spoke** structure.

### 1. Shared layer

These files are the source of truth for all harnesses:

- `WORKSPACE_MAP.md` — fast routing index; what to load first
- `AGENTS.md` — shared workspace constitution
- `POLICY.md` — placement and hygiene rules
- `system/HARNESS_CONTRACT.md` — cross-harness operating contract
- `system/SESSION_STATE_POLICY.md` — when live session state is required

### 2. Adapter layer

Each tool gets a thin root adapter that points back to the shared docs:

- `CLAUDE.md`
- `CODEX.md`
- any other root adapter file for a tool or harness

Adapters should contain only harness-specific mechanics. They should not restate the entire workspace manual.

### 3. Identity layer

These files define the persistent “self” and human context:

- `SOUL.md` — personality and behavioral identity
- `IDENTITY.md` — self-definition
- `USER.md` — human profile and working preferences
- `TOOLS.md` — environment-specific notes
- `HEARTBEAT.md` — optional periodic check definitions

### 4. Local override layer

Subdirectories can add more specific docs:

- `<subdir>/AGENTS.md`
- `<subdir>/SOUL.md`
- `<subdir>/POLICY.md`

Most-specific guidance wins.

## Platonic Starter Structure

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
└── project-or-domain-subdirs/
    └── AGENTS.md
```

## Design Principles

1. **Shared before specific**
   - Put durable workspace-wide behavior in shared docs.
   - Put harness-only mechanics in thin adapters.

2. **Do not duplicate manuals**
   - If the same instructions appear in `AGENTS.md`, `CLAUDE.md`, and `CODEX.md`, the design is drifting.
   - The adapter should point back to the shared file, not re-copy it.

3. **Load the minimum safe context**
   - `WORKSPACE_MAP.md` should help the agent load only what is needed.
   - Avoid always loading a giant manual.

4. **Identity is part of the system**
   - Personality, user context, and local environment notes should be explicitly stored in files.
   - Do not bury these in prompts only.

5. **Local specificity beats global generality**
   - Project-specific instructions belong closer to the project.
   - Root docs should govern the workspace; subdir docs should govern the local domain.

## Recommended Load Order

For non-trivial work:

1. `WORKSPACE_MAP.md`
2. `AGENTS.md`
3. `system/HARNESS_CONTRACT.md`
4. `system/SESSION_STATE_POLICY.md`
5. tool adapter (`CLAUDE.md`, `CODEX.md`, etc.)
6. specialized local docs only if required

## How To Implement In A Fresh Workspace

1. Create the shared files from `assets/root/`.
2. Create the system contract files from `assets/system/`.
3. Copy or adapt the thin adapter files for each harness you use.
4. Fill in:
   - `SOUL.md`
   - `IDENTITY.md`
   - `USER.md`
   - `TOOLS.md`
5. Add local `AGENTS.md` or `POLICY.md` files only where true local specificity exists.
6. Keep a simple rule:
   - **shared rules live centrally**
   - **tool mechanics live in adapters**
   - **local exceptions live near the work**

## Drift Check Heuristic

Your system is healthy if:

- adapters are short
- the shared docs are clearly differentiated
- local overrides are rare and justified
- a change to global operating behavior usually modifies one shared file, not three adapters

Your system is drifting if:

- adapters become long manuals
- identical guidance appears in multiple files
- nobody knows which file is authoritative
- identity and behavior are hidden in tool prompts rather than explicit docs

## Assets Included

This skill includes copyable starter templates under:

- `assets/root/`
- `assets/system/`

Use them as a baseline, then adapt names and paths to your own workspace.
