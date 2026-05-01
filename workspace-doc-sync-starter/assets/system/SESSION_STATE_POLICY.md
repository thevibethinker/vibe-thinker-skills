---
created: 2026-05-01
last_edited: 2026-05-01
version: 1.0
provenance: con_CICEmalXAepToekB
---
# Session State Policy

## Purpose

Decide when live session state should be initialized, refreshed, or skipped.

## Use Session State When

- work spans multiple steps and may be resumed later
- status checkpoints matter
- the task has meaningful branching or handoff risk
- the workspace expects explicit in-progress tracking

## Skip Session State When

- the task is trivial
- the work is one-shot and immediately verifiable
- a fuller persistent artifact already captures the state

## Rule

Use session state intentionally, not automatically. The goal is continuity without clutter.