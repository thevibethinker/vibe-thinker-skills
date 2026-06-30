---
name: research-engine
description: Maintain research repositories and a wiki-style compendium under Research/repos; scans existing knowledge folders before proposing repos, supports append-only intake, compaction, and repair sweeps for failed meeting-derived appends. Portable: owner/venture identity is externalized to a profile so the skill can ship publicly and be re-pointed on any Zo.
compatibility: Created for Zo Computer
metadata:
  author: va.zo.computer
created: 2026-06-13
last_edited: 2026-06-18
version: 2.1
provenance: con_XbMMeD3u4MxlbvOE
---
# Research Engine

Use this skill when a workflow needs to maintain durable research repositories and a wiki-style compendium under `Research/repos/`.

> **Portable skill.** Owner/venture identity, accounts, and canonical links are **not** hardcoded — they live in `file config/profile.json` (git-ignored) with a neutral `file config/profile.default.json` fallback. After importing onto a new Zo, run `file scripts/install.py` and edit the profile. See `file Skills/research-engine/references/portability.md`.

Research Engine is intentionally separate from Pulse Orchestrator:

- **Research Engine owns knowledge state**: scans, repository proposals, append-only intake, compaction, compendium generation, repair queues, and the research ontology/index layer.
- **Pulse Orchestrator owns worker execution**: drop lifecycle, spawn/retry/recovery, validation, wave gates, and build status.
- Research workflows may borrow Pulse patterns such as waves, isolated workers, deposits, and recovery logs, but those concepts should be represented as Research Engine data structures rather than embedded in Pulse builds by default.

## Mental Model

A research repo is a living compendium and working index for a topic. The engine writes `file INDEX.md` in place inside the active research folder and keeps state under `Research/_engine/`.

```text
Research/
├── _engine/               # engine state, ontology registry, promotion queue
├── repos/                 # active research folders and their indexes
└── Knowledge/             # curated layer; only explicit promotions may write here
```

## Commands

### Scan before proposing repos

```bash
python3 Skills/research-engine/scripts/research_engine.py scan --root Research --max-depth 5
python3 Skills/research-engine/scripts/research_engine.py suggest --root Research --max-depth 5 --limit 10 --dry-run
python3 Skills/research-engine/scripts/research_engine.py suggest --root Research --max-depth 5 --limit 10
```

### Validate Phase 1 primitive records

```bash
python3 Skills/research-engine/scripts/research_engine.py validate Skills/research-engine/assets/examples/valid
python3 Skills/research-engine/scripts/research_engine.py validate Skills/research-engine/assets/examples/invalid
```

### Map topics to the ontology spine

```bash
python3 Skills/research-engine/scripts/research_engine.py overlay-seed
python3 Skills/research-engine/scripts/research_engine.py map-ontology --topic "Your Venture"
python3 Skills/research-engine/scripts/research_engine.py map-ontology --topic "Quantum Error Correction" --suggest
python3 Skills/research-engine/scripts/research_engine.py map-ontology --topic "Quantum Error Correction" --suggest --create-node
```

### Research run pipeline

```bash
python3 Skills/research-engine/scripts/research_engine.py modes
python3 Skills/research-engine/scripts/research_engine.py run --query "Explain X" --mode explainer --depth one-shot
python3 Skills/research-engine/scripts/research_engine.py run --query "Review evidence on X" --mode literature-review --depth standard --source Research/foo/source.md
python3 Skills/research-engine/scripts/research_engine.py run --query "Diligence <Fund> for <your venture> investor prep" --mode investor-diligence --depth standard --topic <fund>-investor-diligence
python3 Skills/research-engine/scripts/research_engine.py run --query "Diligence <Fund> for <your venture> investor prep" --mode investor-diligence --depth standard --brief-size full-dossier --topic <fund>-investor-diligence
python3 Skills/research-engine/scripts/research_engine.py run --query "Find the best on-person AI recorder / meeting transcription product for in-person meetings, walks, and voice notes" --mode product-diligence --depth standard --topic ai-recorder-product-diligence
python3 Skills/research-engine/scripts/research_engine.py run --query "Diligence Plaud NotePin for in-person meeting capture and voice note workflows" --mode product-diligence --depth standard --brief-size full-dossier --topic plaud-notepin-product-diligence
python3 Skills/research-engine/scripts/research_engine.py approve-run --run-id run_YYYYMMDD_HHMMSS_xxxxxx_hash
python3 Skills/research-engine/scripts/research_engine.py run-status --run-id run_YYYYMMDD_HHMMSS_xxxxxx_hash
```

`one-shot` always executes immediately with no approval and no questions. Other depth tiers create a summary and wait for `approve-run`; after approval the run proceeds unattended.

### One-shot quality bar

`one-shot` means the engine runs immediately without questions; it does **not** mean metadata-only or uncited. It should infer the user's broader research intent, use explicitly provided sources plus Exa, run bounded targeted context scan across existing Research/Knowledge/Articles/recent meeting artifacts, and attempt up to 2 Zoask worker drops when available. The synthesis must expose citations, source coverage, extraction failures, and worker-drop failures.

### Canonical deliverable contract for owner-facing DD / meeting prep

When the research run is for meeting prep, due diligence, a company/person briefing, or any other time-sensitive user-facing synthesis, the operator must create or identify exactly one **canonical human-facing deliverable** before reporting completion.

Required behavior:

1. Use `N5/scripts/research_router.py "<topic>" --create --slug <slug>` to establish the routed working folder when the output is meant for the owner to open. If `file research_router.py` is absent on this Zo, place the brief under `Research/<slug>/` manually.
2. Put the primary human-facing artifact in that routed folder, usually as `file MEETING_BRIEF.md`, `file DILIGENCE_BRIEF.md`, or `file BRIEF.md` depending on the task.
3. Treat `Research/_engine/runs/<run-id>/` and `Research/repos/<topic-slug>/` as provenance / machine-index layers unless the owner explicitly asks for raw engine artifacts.
4. Add a short `file README.md` or top-of-file pointer when more than one folder is involved, naming the canonical deliverable first and raw provenance second.
5. Final responses must surface the canonical human-facing artifact first; raw engine paths are secondary references only.
6. Do not create additional sibling folders for the same topic unless there is a materially different research question. If a sibling folder is created accidentally and is empty, remove it after protection checks. If it contains artifacts, add a canonical pointer rather than silently leaving duplicate surfaces.

This contract exists because the owner prefers output that is immediately usable and not buried in engine internals.

### Pre-meeting DD source isolation and provenance

For pre-meeting due diligence, investor/vendor/person/company research, and stakeholder prep, do **not** pull in prior internal venture outputs, meeting artifacts, or internal strategy documents by default. Use prior internal material only when:

1. It involves the same stakeholder, company, fund, vendor, or entity being researched.
2. The owner explicitly asks to include a specific internal artifact, thesis, meeting, deck, or context.
3. The output clearly labels the material as internal venture context rather than external evidence.

Common research modes should stay distinct:

- **Pre-meeting DD:** external/company/person evidence first; same-stakeholder internal context only.
- **Investor diligence:** manual named-entity VC/fund/partner prep. A meeting is optional, not required. If a calendar scan is requested, inspect only the accounts in `file config/profile.json` (`allowed_calendar_accounts`), prioritize the next 72 hours, and use a 14-day lookahead. Never inspect accounts listed in `excluded_calendar_accounts`.
- **Physical intelligence / science research:** field developments, papers, labs, datasets, robotics/data science evidence; internal context only on request or when directly relevant.
- **Travel/local search:** maps/web/local-source led; no internal strategic context unless requested.

Outputs must make source provenance obvious. Include a short "Source scope / tool provenance" note when advanced or private tools are used, distinguishing ordinary web sources from Exa, Aviato, LinkedIn, app integrations, calendar/email, and internal workspace retrieval.

### Investor diligence mode

Use `--mode investor-diligence` for your venture's investor/VC prep. This is a focused variation of generic `diligence`; keep generic `diligence` for non-investor vendor, partner, candidate, customer, or unknown-stakeholder investigations.

Default invocation is named-entity first and manual:

```bash
python3 Skills/research-engine/scripts/research_engine.py run --query "Diligence <VC/Fund/Partner> for <your venture> investor prep" --mode investor-diligence --depth standard --topic <slug>
```

Meeting-aware invocation is optional. If the owner asks to prepare for upcoming investor calls, use the connected calendar tools only for the accounts in `file config/profile.json` (`allowed_calendar_accounts`); prioritize meetings inside 72 hours and look up to 14 days ahead. Do not inspect excluded accounts.

Brief sizes are selectable with `--brief-size skim|standard|full-dossier`; default is `standard`.

Required investor-diligence lens:

- Fund/partner snapshot, check size/stage/geography, recent deals, and public thesis.
- How much they actually invest in the venture's domain and adjacent spaces.
- Portfolio map with rationale for each classification: `competitive`, `complementary`, `channel`, `capital`, `future-buyer`, `irrelevant`, or `unknown`.
- Competitive/complementary portcos and conflict risk.
- LinkedIn layer: investor/fund profile signals, key figures, mutuals, and plausible intro paths when connected LinkedIn tools can provide them; otherwise label web-visible LinkedIn limitations.
- X/public discourse layer: what they publicly support, discuss, amplify, or avoid in the venture's domain and toward founders.
- Private email layer, when explicitly used: summarize relevant history only and include subject/date/source account/counterparty for traceability. Do not dump full private email bodies.
- Internal layer: use approved Content Library material and evergreen approved links only (from `file config/profile.json`). Do not use applications, unrelated Research folders, or broad workspace search.

Evergreen internal links are sourced from `file config/profile.json` (`evergreen_internal_sources`).

Explicit resources should usually be provided up front via `--source`. Exa is used for external search. Local workspace scan is forbidden unless `--allow-local-scan` is explicitly passed.

### Product diligence mode

Use `--mode product-diligence` for product, service, or product-category buying/testing decisions. It is a focused decision-research mode for finding credible top candidates, collecting objective and semi-objective reviews, clarifying the owner's preferences, and producing a ranked recommendation with explicit tradeoffs.

Default invocation is category-first:

```bash
python3 Skills/research-engine/scripts/research_engine.py run --query "Find the best on-person AI recorder / meeting transcription product for in-person meetings, walks, and voice notes" --mode product-diligence --depth standard --topic ai-recorder-product-diligence
```

Specific-product invocation:

```bash
python3 Skills/research-engine/scripts/research_engine.py run --query "Diligence Plaud NotePin for in-person meeting capture and voice note workflows" --mode product-diligence --depth standard --topic plaud-notepin-product-diligence
```

Brief sizes are selectable with `--brief-size skim|standard|full-dossier`; default is `standard`.

Required product-diligence lens:

- Initial category scan before ranking.
- Socratic preference discovery for non-one-shot runs: primary job, non-goals, must-not-fail constraints, privacy posture, workflow/export needs, form factor, price/subscription tolerance, and relevant substitution tradeoffs.
- External-review-first evidence: hands-on reviews, customer reviews, forum/community first-hand reports, independent comparisons, product docs, API/support docs, pricing pages, privacy policies, and changelogs.
- Affiliate listicles and vendor marketing are weak evidence unless corroborated.
- Ranking criteria and weights must be explicit, with defaults around reliability, output quality, workflow/export/API fit, use-case/form-factor fit, privacy/control, and cost/lock-in.
- Output disposition for each candidate should be one of `buy`, `trial`, `watch`, `avoid`, or `not-enough-evidence`.
- Persona lenses such as Teacher, Builder, Debugger, and Strategist may be used for explanation and tradeoff analysis, but factual claims must stay source-grounded.

For one-shot product diligence, do not pause for the preference interview. State assumptions, rank with caveats, and surface the unresolved questions that would most change the recommendation.

### Promotion Gate

```bash
python3 Skills/research-engine/scripts/research_engine.py propose-promotion --topic <topic-slug> --target Knowledge/path/to/file.md
python3 Skills/research-engine/scripts/research_engine.py promote --candidate-id <id> --dry-run
python3 Skills/research-engine/scripts/research_engine.py promote --candidate-id <id> --confirm
```

### Manage repos

```bash
python3 Skills/research-engine/scripts/research_engine.py propose --title "Topic" --objective "What this repo is tracking"
python3 Skills/research-engine/scripts/research_engine.py activate --repo-id repo_YYYYMMDD_001
python3 Skills/research-engine/scripts/research_engine.py list
python3 Skills/research-engine/scripts/research_engine.py show --repo-id repo_YYYYMMDD_001
```

### Add and compact evidence

```bash
python3 Skills/research-engine/scripts/research_engine.py append --repo-id repo_YYYYMMDD_001 --source meeting --source-ref "path/or/url" --summary "Finding" --payload-json '{"key":"value"}'
python3 Skills/research-engine/scripts/research_engine.py compact --repo-id repo_YYYYMMDD_001
python3 Skills/research-engine/scripts/research_engine.py compendium
```

### Repair failed appends

```bash
python3 Skills/research-engine/scripts/research_engine.py repair-status
python3 Skills/research-engine/scripts/research_engine.py repair-sweep --dry-run
python3 Skills/research-engine/scripts/research_engine.py repair-sweep
```

## Contract

- Repos live under `Research/repos/<slug>/`.
- Engine state lives under `Research/_engine/`.
- Registry lives at `file Research/repos/registry.json` and `file Research/repos/REGISTRY.md`.
- The global compendium lives at `file Research/repos/COMPENDIUM.md`.
- Topic views are written as `file INDEX.md` in the relevant research folder, not into a parallel wiki tree.
- Appends write JSONL entries to `file INTAKE.jsonl` with deterministic dedupe keys.
- Failed appends are logged to `file Research/repos/.repair/FAILED_APPENDS.jsonl` and can be replayed with `repair-sweep`.
- Every mutating command supports `--dry-run` where relevant.
- Machine callers get one JSON object on stdout. Non-zero exits are reserved for unrecoverable framework errors or malformed command inputs; handled research misses return `ok: false` JSON so callers can continue safely.
- Promoting extracted research into Knowledge is always explicit and gated.

## Meeting Integration

`file Skills/meeting-ingestion/AGENTS.md` references this skill for repairing append failures created by meeting research-repo extraction. `repair-sweep` only retries failed append operations; artifact generation failures require reprocessing the meeting. If `meeting-ingestion` is not installed on this Zo, `repair-sweep` is simply inert — the engine is otherwise unaffected.

## References

- `file Skills/research-engine/references/portability.md` — profile model, soft-dependency degradation table, and the install/acclimatization flow for a new Zo.
- `file Skills/research-engine/references/architecture.md` — settled architecture, layer boundaries, and the wrap-the-router / index-in-place decisions.
- `file Skills/research-engine/references/schemas.md` — Phase 1 primitive schemas (Source, Extract, Claim, Topic, Synthesis, PromotionCandidate).
- `file Skills/research-engine/references/ontology.md` — ontology spine policy: Wikidata/Wikipedia references, personal overlay, and the Knowledge-ontology boundary.
- `Skills/research-engine/assets/examples/` — valid and invalid fixtures used by `validate` and the test suite.
- `file Skills/research-engine/references/investor-diligence.md` — investor/VC diligence mode workflow, source policy, portfolio classification, and dossier template.
- `file Skills/research-engine/references/product-diligence.md` — product/service/category diligence workflow, Socratic preference discovery, source taxonomy, ranking criteria, and dossier template.
- `file Skills/research-engine/references/run-pipeline.md` — Phase 3 run pipeline, depth semantics, Exa/source policy, and output contract.
- `file Skills/research-engine/references/promotion.md` — Phase 4 Knowledge promotion gate policy and commands.

## Development Checks

```bash
python3 -m py_compile Skills/research-engine/scripts/research_engine.py
pytest -q Skills/research-engine/scripts/test_research_engine.py
```

## Install / Acclimatize on a new Zo

Install just this skill from the public Vibe Thinker skills repo:

```bash
slug="research-engine"; dest="Skills"; repo="https://github.com/thevibethinker/vibe-thinker-skills/archive/refs/heads/main.tar.gz"; archive_root="vibe-thinker-skills-main"; mkdir -p "$dest" && curl -L "$repo" | tar -xz -C "$dest" --strip-components=1 "$archive_root/$slug"
```

Then initialize the local profile/state:

```bash
python3 Skills/research-engine/scripts/install.py            # probe + dry-run report
python3 Skills/research-engine/scripts/install.py --apply    # scaffold dirs + seed local profile
$EDITOR Skills/research-engine/config/profile.json           # remap identity
python3 Skills/research-engine/scripts/research_engine.py modes
python3 Skills/research-engine/scripts/research_engine.py validate Skills/research-engine/assets/examples/valid
```

`config/profile.json` is intentionally git-ignored; public installs ship only `config/profile.default.json`.