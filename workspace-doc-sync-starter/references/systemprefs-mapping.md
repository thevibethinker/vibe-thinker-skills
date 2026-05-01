---
created: 2026-05-01
last_edited: 2026-05-01
version: 1.0
provenance: con_CICEmalXAepToekB
---
# systemprefs Mapping

This starter kit assumes some systems have a `systemprefs` or equivalent preferences layer.

The clean replication pattern is to **decompose systemprefs by concern** instead of treating it as one giant catch-all file.

## Recommended mapping

| Concern | Recommended file |
|---|---|
| Global operating rules | `AGENTS.md` |
| Folder and placement policy | `POLICY.md` |
| Cross-harness behavior | `system/HARNESS_CONTRACT.md` |
| Session-state usage | `system/SESSION_STATE_POLICY.md` |
| Identity / personality | `SOUL.md` + `IDENTITY.md` |
| Human-specific preferences | `USER.md` |
| Local environment quirks and machine notes | `TOOLS.md` |
| Harness-specific instructions | `CLAUDE.md`, `CODEX.md`, etc. |

## Practical translation rule

If you are migrating from a monolithic `systemprefs` file:

- move durable workspace-wide behavior into `AGENTS.md`
- move folder rules into `POLICY.md`
- move tool-entry logic into harness adapters
- move identity and human context into explicit identity files
- keep adapters thin and avoid copying the same text into multiple places

## Why this is better

A monolithic preferences file often mixes:
- operating policy
- identity
- user preferences
- tool-specific quirks
- environment notes

That makes synchronization harder.

This starter kit instead turns one mixed surface into several clearer surfaces with narrower responsibilities.