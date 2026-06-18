---
created: 2026-06-15
last_edited: 2026-06-15
version: 1.0
provenance: con_KbScuvu4sQ33UyDe
---
# Research Engine — Promotion Gate

Research output is not Knowledge. Promotion is the only path from Research Engine claims into `Knowledge/`.

## Contract

- Research runs write sources, extracts, claims, synthesis, and `INDEX.md` views under Research-owned locations.
- `propose-promotion` creates a candidate under `Research/_engine/promotions/candidates/` and appends to the topic `PROMOTION_QUEUE.jsonl`.
- `promote --dry-run` renders a diff preview only.
- `promote --candidate-id <id>` without `--confirm` refuses to write.
- `promote --candidate-id <id> --confirm` writes or appends a Markdown section under an explicit `Knowledge/*.md` target and logs to `Research/_engine/promotions/PROMOTION_LOG.jsonl`.
- Candidates must have claim provenance and confidence. Promotion refuses malformed candidates.

## Commands

```bash
python3 Skills/research-engine/scripts/research_engine.py propose-promotion \
  --topic <topic-slug> \
  --target Knowledge/path/to/file.md

python3 Skills/research-engine/scripts/research_engine.py promote --candidate-id <id> --dry-run
python3 Skills/research-engine/scripts/research_engine.py promote --candidate-id <id>
python3 Skills/research-engine/scripts/research_engine.py promote --candidate-id <id> --confirm
```

## Test-only override

`RESEARCH_ENGINE_KNOWLEDGE_ROOT` exists only so tests can verify confirmed promotion without mutating real `Knowledge/`. Production use should leave it unset.
