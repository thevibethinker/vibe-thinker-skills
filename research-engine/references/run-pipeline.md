---
created: 2026-06-15
last_edited: 2026-06-15
version: 1.0
provenance: con_KbScuvu4sQ33UyDe
---

# Research Engine — Run Pipeline

Phase 3 adds a separate `research_run.py` module and wires its commands through `research_engine.py`.

## Commands

```bash
python3 Skills/research-engine/scripts/research_engine.py modes
python3 Skills/research-engine/scripts/research_engine.py run --query "..." --mode explainer --depth one-shot
python3 Skills/research-engine/scripts/research_engine.py run --query "..." --mode literature-review --depth standard --source Research/foo/source.md
python3 Skills/research-engine/scripts/research_engine.py approve-run --run-id run_YYYYMMDD_HHMMSS_xxxxxx_hash
python3 Skills/research-engine/scripts/research_engine.py run-status --run-id run_YYYYMMDD_HHMMSS_xxxxxx_hash
```

## Depth semantics

- `one-shot`: no approval, no questions, executes immediately. Use for quick/time-critical runs, but not as metadata-only search. One-shot should infer the user’s broader research intent from available context, capture citations, run targeted context scan over Research/Knowledge/Articles/recent meeting artifacts, and attempt up to 2 Zoask worker drops when credentials are available.
- `quick`, `standard`, `deep`: create `SUMMARY.md` and pause at `awaiting_approval`; after `approve-run`, execution is unattended.

## Source policy

- Explicit `--source` resources are preferred and should usually be provided at the outset.
- Exa is used for external search when the run needs external resources. One-shot explainer mode targets 5 results by default.
- One-shot performs a bounded targeted context scan across `Knowledge/`, `Research/repos/`, `Articles/`, and recent meeting artifacts. This is distinct from broad local workspace scan.
- Broad local workspace scan is **forbidden by default**. It only runs when `--allow-local-scan` is explicitly passed.
- One-shot attempts up to 2 `/zo/ask` worker drops when `ZO_CLIENT_IDENTITY_TOKEN` is available. Worker failures are recorded rather than fatal.
- Sources in `SYNTHESIS.md` must be citation-bearing; extraction failures must remain visible rather than being silently upgraded to claims.
- Phase 3 never writes to `Knowledge/`.

### Source isolation for pre-meeting DD

For pre-meeting due diligence, investor/vendor/person/company research, and stakeholder prep, do **not** automatically include prior venture outputs, meeting artifacts, or internal strategy documents. Prior internal venture material is allowed only when it involves the same stakeholder/company/fund/vendor/entity, or when the owner explicitly asks to include a specific artifact, thesis, meeting, deck, or internal context.

Research modes should stay distinct:

- **Pre-meeting DD:** external/company/person evidence first; same-stakeholder internal context only.
- **Investor diligence:** named-entity-first investor prep for the owner's venture. Meeting context is optional and manual; if used, inspect only the profile `allowed_calendar_accounts`, prioritize 72 hours, and look up to 14 days. Never inspect any account in the profile `excluded_calendar_accounts`.
- **Physical intelligence / science research:** field developments, papers, labs, datasets, robotics/data science evidence; internal venture context only on request or when directly relevant.
- **Travel/local search:** maps/web/local-source led; no internal strategic context unless requested.

`investor-diligence` requires approved internal context only: content library material plus current evergreen links from the profile `evergreen_internal_sources`. Do not use accelerator/grant applications, other applications, unrelated Research folders, or broad workspace venture search. Private email evidence is summarized only with subject/date/source-account/counterparty traceability. LinkedIn and X/public discourse are first-class evidence layers when available.

Outputs must include a short “Source scope / tool provenance” note whenever advanced or private tools are used, distinguishing ordinary web sources from Exa, Aviato, LinkedIn, app integrations, calendar/email, and internal workspace retrieval.

## Outputs

Each run writes under `Research/_engine/runs/<run-id>/`:

- `RUN.md`
- `SUMMARY.md`
- `PLAN.json`
- `STATE.json`
- `SOURCES.jsonl`
- `EXTRACTS.jsonl`
- `CLAIMS.jsonl`
- `SYNTHESIS.md`
- `WORKER_DROPS.jsonl`
- `PROMOTION_CANDIDATES.jsonl`

The engine also renders an in-place topic view at `Research/repos/<topic-slug>/INDEX.md`.

## Canonical human-facing deliverables

For one-shot due diligence, company/person research, meeting prep, or other V-facing briefing work, the raw run outputs above are **not** sufficient completion evidence. The run directory and repo index are provenance layers. The operator must also create or identify one canonical human-facing deliverable in the routed `Research/market-intel/<slug>/` or other `research_router.py` destination.

Expected shape:

- `README.md` in the routed folder, if more than one artifact folder exists.
- `MEETING_BRIEF.md`, `DILIGENCE_BRIEF.md`, or `BRIEF.md` as the primary document.
- A top-level pointer from `Research/repos/<topic-slug>/INDEX.md` back to the canonical human-facing deliverable when a repo view is generated.
- Final user report names the canonical deliverable first and raw run/repo artifacts second.

Acceptance criteria:

- Exactly one canonical human-facing deliverable is named.
- Duplicate empty sibling folders for the same topic are removed after protection checks.
- Non-empty sibling folders receive a pointer to the canonical deliverable or are explicitly classified as separate research questions.
- The synthesis is optimized for the requested use case, not just a generic source dump.

## Environment

External search uses Exa via `EXA_N5OS_KEY` or `EXA_API_KEY`. Zoask worker drops use `ZO_CLIENT_IDENTITY_TOKEN` and default to `openai:gpt-5.5-2026-04-23`, overrideable with `RESEARCH_ENGINE_ZOASK_MODEL`.
