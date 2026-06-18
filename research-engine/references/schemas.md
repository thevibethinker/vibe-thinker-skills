---
created: 2026-06-15
last_edited: 2026-06-15
version: 1.0
provenance: con_zAgcy3AP0A6vzikR
---

# Research Engine — Primitive Schemas (v1)

The Research Engine has six durable primitives. All are append-only JSONL records except `Topic` (registry rows) and `Synthesis` (rendered into `INDEX.md`). Every record carries provenance so any synthesized claim can be traced back to a raw source.

Trust flows one direction only:

```text
Source → Extract → Claim → Synthesis → PromotionCandidate → (gated) Knowledge
```

`Topic` is the ontology/wiki node that the other primitives attach to.

---

## 1. Source

A raw thing that was consulted. Immutable reference — never edited after creation.

| Field | Type | Required | Notes |
|---|---|---|---|
| `kind` | string | yes | Always `"source"`. |
| `source_id` | string | yes | Stable ID, e.g. `src_<sha1[:12]>`. |
| `type` | enum | yes | `url` \| `pdf` \| `meeting` \| `note` \| `email` \| `paper` \| `dataset` \| `other`. |
| `uri` | string | yes | URL or workspace-relative path. |
| `title` | string | no | Human label. |
| `retrieved_at` | string (ISO 8601) | yes | When it was consulted. |
| `provenance` | string | yes | Conversation/agent/run ID that recorded it. |
| `hash` | string | no | Content hash when available, for dedupe. |

```json
{
  "kind": "source",
  "source_id": "src_a1b2c3d4e5f6",
  "type": "paper",
  "uri": "https://arxiv.org/abs/2406.00001",
  "title": "Scaling Laws for Agentic Retrieval",
  "retrieved_at": "2026-06-15T08:00:00Z",
  "provenance": "con_zAgcy3AP0A6vzikR",
  "hash": "9f2c..."
}
```

---

## 2. Extract

An atomic observation pulled verbatim (or near-verbatim) from one source. Append-only.

| Field | Type | Required | Notes |
|---|---|---|---|
| `kind` | string | yes | Always `"extract"`. |
| `extract_id` | string | yes | `ext_<sha1[:12]>`. |
| `source_id` | string | yes | Must reference an existing `Source`. |
| `text` | string | yes | The observation. |
| `locator` | string | no | Page, timestamp, section, line. |
| `quote` | string | no | Exact quote if `text` is paraphrased. |
| `recorded_at` | string (ISO 8601) | yes | |
| `provenance` | string | yes | |

```json
{
  "kind": "extract",
  "extract_id": "ext_1122334455aa",
  "source_id": "src_a1b2c3d4e5f6",
  "text": "Retrieval depth past 8 hops yielded diminishing accuracy gains.",
  "locator": "p.7, fig.3",
  "quote": "Beyond eight hops, accuracy improvements fell below 1%.",
  "recorded_at": "2026-06-15T08:05:00Z",
  "provenance": "con_zAgcy3AP0A6vzikR"
}
```

---

## 3. Claim

A normalized proposition supported by one or more extracts. Append-only; supersession is a new record referencing the old `claim_id`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `kind` | string | yes | Always `"claim"`. |
| `claim_id` | string | yes | `clm_<sha1[:12]>`. |
| `claim` | string | yes | The proposition. |
| `supporting_extracts` | array[string] | yes | Extract IDs (≥1). |
| `confidence` | enum | yes | `low` \| `medium` \| `high`. |
| `status` | enum | yes | `open` \| `corroborated` \| `contested` \| `superseded`. |
| `supersedes` | string | no | Prior `claim_id` this replaces. |
| `recorded_at` | string (ISO 8601) | yes | |
| `provenance` | string | yes | |

```json
{
  "kind": "claim",
  "claim_id": "clm_aabbccddeeff",
  "claim": "Agentic retrieval gains plateau past ~8 hops.",
  "supporting_extracts": ["ext_1122334455aa"],
  "confidence": "medium",
  "status": "open",
  "recorded_at": "2026-06-15T08:10:00Z",
  "provenance": "con_zAgcy3AP0A6vzikR"
}
```

---

## 4. Topic

A wiki/ontology node. Lives in the engine registry, maps to one router-chosen folder where its `INDEX.md` is rendered.

| Field | Type | Required | Notes |
|---|---|---|---|
| `kind` | string | yes | Always `"topic"`. |
| `topic_id` | string | yes | `top_<slug>`. |
| `slug` | string | yes | Filesystem-safe. |
| `title` | string | yes | |
| `folder` | string | yes | Workspace-relative router-chosen home (e.g. `Research/<category>/<item>`). |
| `ontology_refs` | array[object] | no | `{ "node_id", "wikidata_qid?", "wikipedia_title?", "personal?" }`. |
| `aliases` | array[string] | no | |
| `created_at` | string (ISO 8601) | yes | |
| `provenance` | string | yes | |

```json
{
  "kind": "topic",
  "topic_id": "top_agentic-retrieval",
  "slug": "agentic-retrieval",
  "title": "Agentic Retrieval",
  "folder": "Research/ai-systems/agentic-retrieval",
  "ontology_refs": [
    { "node_id": "node_agentic_retrieval", "wikidata_qid": "Q117", "personal": false }
  ],
  "aliases": ["multi-hop retrieval"],
  "created_at": "2026-06-15T08:00:00Z",
  "provenance": "con_zAgcy3AP0A6vzikR"
}
```

---

## 5. Synthesis

A rendered, post-processed view written into a topic's `INDEX.md`. Recorded as a metadata record so renders are auditable.

| Field | Type | Required | Notes |
|---|---|---|---|
| `kind` | string | yes | Always `"synthesis"`. |
| `topic_id` | string | yes | |
| `mode` | enum | yes | One of the mode registry IDs. |
| `generated_at` | string (ISO 8601) | yes | |
| `inputs` | object | yes | `{ "claim_ids": [...], "source_ids": [...] }`. |
| `provenance` | string | yes | |

```json
{
  "kind": "synthesis",
  "topic_id": "top_agentic-retrieval",
  "mode": "literature-review",
  "generated_at": "2026-06-15T08:20:00Z",
  "inputs": { "claim_ids": ["clm_aabbccddeeff"], "source_ids": ["src_a1b2c3d4e5f6"] },
  "provenance": "con_zAgcy3AP0A6vzikR"
}
```

---

## 6. PromotionCandidate

A proposed delta into `Knowledge/`. Review-gated; only a confirmed `promote` may act on it.

| Field | Type | Required | Notes |
|---|---|---|---|
| `kind` | string | yes | Always `"promotion_candidate"`. |
| `candidate_id` | string | yes | `pc_<sha1[:12]>`. |
| `topic_id` | string | yes | |
| `target` | string | yes | Explicit `Knowledge/...` path. |
| `claim_ids` | array[string] | yes | Claims being promoted (≥1). |
| `rationale` | string | yes | Why this belongs in Knowledge. |
| `review_status` | enum | yes | `proposed` \| `approved` \| `rejected` \| `promoted`. |
| `created_at` | string (ISO 8601) | yes | |
| `provenance` | string | yes | |

```json
{
  "kind": "promotion_candidate",
  "candidate_id": "pc_998877665544",
  "topic_id": "top_agentic-retrieval",
  "target": "Knowledge/ai-systems/agentic-retrieval-limits.md",
  "claim_ids": ["clm_aabbccddeeff"],
  "rationale": "Corroborated across 3 sources; stable enough to be a durable belief.",
  "review_status": "proposed",
  "created_at": "2026-06-15T08:30:00Z",
  "provenance": "con_zAgcy3AP0A6vzikR"
}
```

---

## Validation

`research_engine.py validate --kind <kind> --file <path>` (or `--json '<obj>'`) checks a record against these schemas. Valid records return `{"ok": true}`; malformed records return `{"ok": false, "errors": [...]}` with a non-zero exit only on framework error, never on a handled validation miss.
