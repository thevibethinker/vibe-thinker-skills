---
created: 2026-06-15
last_edited: 2026-06-15
version: 1.0
provenance: con_zAgcy3AP0A6vzikR
---
# Research Engine — Ontology Spine

The ontology is an **organizing spine**, not a source of truth. It answers "where does this topic belong and what is it related to," never "what is true." Truth lives in claims (with confidence + provenance); purity lives in Knowledge.

## Layers

1. **Local node registry** — `Research/_engine/ontology/registry.json`. Canonical ontology nodes the engine has confirmed.
2. **Personal overlay** — `Research/_engine/ontology/personal_overlay.jsonl`. Owner-specific concepts that public ontologies represent poorly, seeded from the profile's `overlay_extra_nodes` (the neutral default seeds none). Append-only, idempotent seed via `overlay-seed`.
3. **Mappings** — `Research/_engine/ontology/mappings.jsonl`. topic/folder → node associations (lazy, per-topic).
4. **External cache** — `Research/_engine/ontology/cache/wikidata.jsonl`. Cached Wikidata/Wikipedia references, fetched on demand only. Normal operation never requires the network.
5. **Knowledge ontology** — `Knowledge/semantic-memory/ontology/`. Referenced by path/ID only. **Never written by research runs.**

## Node model

```json
{
  "node_id": "node_<slug>",
  "label": "Human Label",
  "aliases": ["alt name", "abbrev"],
  "kind": "concept|entity|domain|method|market|person|org|technology",
  "wikidata_qid": "Q12345 or null",
  "wikipedia_title": "Page Title or null",
  "parent_ids": [],
  "related_ids": [],
  "personal": true,
  "notes": ""
}
```

`wikidata_qid` and `wikipedia_title` are **optional** and used as navigation hints + stable IDs only. Absence is normal and never blocks mapping.

## Mapping policy

- **Local-first.** `map-ontology --topic "X"` scores registry + overlay nodes deterministically (exact label/alias match = 1.0; token overlap otherwise). No network call.
- **Unknown topics** return `matched: false`. With `--suggest`, a candidate node is proposed but **not persisted** unless `--create-node` is passed (and not `--dry-run`). This prevents ontology sprawl from one-off queries.
- **External refs** (Wikidata/Wikipedia) are a later enrichment step writing only to the cache; they are never required for a topic to be mapped or for a run to proceed.

## Why not mirror Wikipedia

We use Wikidata QIDs as stable identifiers and Wikipedia titles/categories as readable navigation hints. We deliberately do **not** adopt Wikipedia's article model, neutrality policy, or notability rules — V's research is often subjective, strategic, and personal. The ontology says where things belong; it does not constrain how claims are synthesized.

## Commands

```bash
python3 Skills/research-engine/scripts/research_engine.py overlay-seed
python3 Skills/research-engine/scripts/research_engine.py map-ontology --topic "<owner concept>"
python3 Skills/research-engine/scripts/research_engine.py map-ontology --topic "New Topic" --suggest
python3 Skills/research-engine/scripts/research_engine.py map-ontology --topic "New Topic" --suggest --create-node
```
