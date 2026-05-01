---
created: 2026-05-01
last_edited: 2026-05-01
version: 1.0
provenance: con_CICEmalXAepToekB
---
# Workspace Policy

## Purpose

This file defines placement rules, workspace hygiene, and root-level discipline.

## Root Hygiene

- Keep the workspace root intentional.
- Do not create new top-level folders casually.
- Prefer existing canonical homes for docs, code, data, research, and scratch.

## Placement Discipline

- Put durable shared operating docs at root.
- Put tool-specific local state in tool-owned folders.
- Put project-specific instructions near the project.
- Put temporary scratch in an ephemeral or clearly marked scratch area.

## Conflict Rule

If a subdirectory has its own `POLICY.md`, that more specific policy overrides this one inside that subtree.