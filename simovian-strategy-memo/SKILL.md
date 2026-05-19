---
name: simovian-strategy-memo
description: Maintain the Simovian strategic memo through deliberate, auditable evidence commits; use when adding source memos, checking memo state, applying approved memo changes, tracing claims, or generating positioning.
compatibility: Created for Zo Computer
metadata:
  author: va.zo.computer
  canonical_memo: Research/general/pi-venture-intel/CURRENT_MEMO.md
  source_library: Knowledge/content-library/memos/simovian-strategy-ingest
created: 2026-05-17
last_edited: 2026-05-17
version: 0.2
provenance: con_sbLZWP2YUSq9Yq1k
---

# Simovian Strategy Memo

This skill keeps Simovian strategy updates deliberate and traceable. It treats the current memo as the canonical rolling understanding, while every proposed change starts as a candidate backed by copied source evidence.

## Canonical Paths

- Memo: `Research/general/pi-venture-intel/CURRENT_MEMO.md`
- Positioning output: `Research/general/pi-venture-intel/POSITIONING.md`
- Memo state: `Research/general/pi-venture-intel/.strategy-memo/`
- Source copies: `Knowledge/content-library/memos/simovian-strategy-ingest/`
- Ingestion ledger: `Research/general/pi-venture-intel/.strategy-memo/indexes/source_ingest.jsonl`

## Commands

```bash
python3 Skills/simovian-strategy-memo/scripts/simovian_strategy_memo.py status --json
python3 Skills/simovian-strategy-memo/scripts/simovian_strategy_memo.py ingest-source --source <memo.md> --intent "<why this matters>" --pathway <slug> --json
python3 Skills/simovian-strategy-memo/scripts/simovian_strategy_memo.py commit --source <memo.md> --intent "<memo update intent>" --pathway <slug> --json
python3 Skills/simovian-strategy-memo/scripts/simovian_strategy_memo.py apply --candidate-id <id> --approve "APPROVE <id>" --json
python3 Skills/simovian-strategy-memo/scripts/simovian_strategy_memo.py generate-positioning --json
```

## Operating Rules

1. Do not auto-update the memo from arbitrary documents.
2. Ingest source material first so there is a durable copy and ledger entry.
3. Create a candidate from the ingested source.
4. Review the candidate patch, contradiction report, and downstream report.
5. Apply only with the exact approval phrase.
6. Generate positioning explicitly as a derived artifact, never as a side effect of memo updates.
