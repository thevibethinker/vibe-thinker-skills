---
created: 2026-06-15
last_edited: 2026-06-15
version: 1.0
provenance: con_zAgcy3AP0A6vzikR
---

# Research Engine — Architecture (v1)

Canonical plan: `file 'N5/builds/research-engine-ontology-v1/PLAN.md'`. This doc is the durable, skill-local summary of the boundaries the implementation must honor.

## Purpose

The Research Engine is Zo's single front door for research. One skill command initiates any research workflow (literature review, market research, diligence, knowledge-scan, explainer, strategy). It organizes findings through an ontology/wiki layer and never writes to `Knowledge/` without an explicit, gated promotion step.

## The five-layer trust model

```text
Sources → Extracts → Claims/Topic views → Promotion Candidates → Knowledge
 (raw)     (atomic)   (synthesized, in place)   (gated)          (pure)
```

- **Sources / Extracts / Claims** are append-only and live under the topic's router-chosen folder.
- **Topic views** (`INDEX.md`) are rendered in place — the engine owns and overwrites these.
- **Promotion candidates** are proposals only.
- **Knowledge** is reached solely through `promote --confirm`.

## Boundary rules (non-negotiable)

1. **The engine wraps the router; it does not replace it.** `Skills/research-engine/scripts/research_router.py` stays the placement brain (LLM classification into the existing ~30 categories / 116 folders). The engine calls the router to decide *where* a topic lives, then manages state *there*.
2. **No parallel namespace.** There is no `Research/wiki/`, `Research/repos/` (as topic home), or `Research/runs/` as a topic's home. Topic views render into the existing router-chosen folder. The engine keeps only its *own* operational state under `Research/_engine/`.
3. **Ontology references Knowledge; it never duplicates or writes it.** `Research/_engine/ontology/` maps topics to nodes and, where useful, to `Knowledge/semantic-memory/ontology/` node IDs by reference. Research runs never write under `Knowledge/`.
4. **Knowledge is pure.** Only `promote --confirm` mutates `Knowledge/`, only to an explicit target path, and only with logged provenance. Every other command is tested to leave `Knowledge/` untouched.
5. **The engine owns `INDEX.md` per topic.** It renders/overwrites the topic view; humans and other tools should treat `INDEX.md` as generated.
6. **Pulse patterns are borrowed, not embedded.** Waves/workers/deposits/recovery may inform run orchestration, but research state is the engine's own data model, not a Pulse build. Pulse is handled separately.

## Engine operational state

```text
Research/_engine/
├── registry.json            # topics + their router-chosen folders
├── ontology/
│   ├── registry.json        # local ontology nodes
│   ├── personal_overlay.jsonl  # owner-specific concepts (from profile overlay_extra_nodes)
│   ├── mappings.jsonl       # topic/folder → ontology node (lazy, per-topic)
│   └── cache/wikidata.jsonl # cached external refs, fetched on demand only
├── runs/<run-id>/           # per-run plan, deposits, synthesis state
└── promotions/
    └── PROMOTION_LOG.jsonl  # audit log of Knowledge promotions
```

Per topic, in the **router-chosen folder** (not under `_engine/`):

```text
Research/<category>/<topic>/
├── INDEX.md         # engine-rendered topic view (generated)
├── EVIDENCE.jsonl   # Sources + Extracts (append-only)
└── CLAIMS.jsonl     # Claims (append-only)
```

## Modes are data, not code

Research modes live as drop-in files (a mode registry) so V can expand research range without code changes. Each mode declares: protocol, source preferences, evidence standards, required output sections, confidence rules. v1 ships: `literature-review`, `market-research`, `diligence`, `knowledge-scan`, `explainer`, `strategy-research`.

## Offline-first

Normal runs must work without live web/Wikipedia/Wikidata access. External ontology refs are cached locally and fetched on demand only; absence of a public ref is never an error.
