---
created: 2026-05-19
last_edited: 2026-05-19
version: 0.1
provenance: con_qLD69udM5Wj85dfo
---

# Data Model

Runtime data belongs outside `Skills/`, defaulting to `N5/data/startup-memo-generator/`.

> Examples below use `ACME Inc` / `founder@acme.example` as illustrative placeholders. Replace with the installing founder's values via `setup`.

## Config

`config.json`

```json
{
  "org_name": "ACME Inc",
  "gmail_sender": "founder@acme.example",
  "data_root": "N5/data/startup-memo-generator",
  "default_replay_retention_days": 90,
  "analytics_disclosure": "Please be aware that this page's analytics are being collected and used by ACME Inc.",
  "default_locale": "en-US"
}
```

## Memo

`memos/<memo-id>/memo.json`

```json
{
  "id": "uuidv7",
  "title": "Seed Memo",
  "category": "investor-memos",
  "route_path": "/investor-memos/seed-memo-<uuidv7>",
  "auth_mode": "email+pin",
  "default_version_id": "uuidv7",
  "versions": [],
  "stakeholders": [],
  "created_at": "RFC3339",
  "updated_at": "RFC3339"
}
```

## Version

Versions reference source snapshots and central content blocks. Refreshing a source creates a new version.

```json
{
  "id": "uuidv7",
  "label": "A",
  "source_snapshot_id": "uuidv7",
  "content_block_ids": ["uuidv7"],
  "created_at": "RFC3339"
}
```

## Content Block

Central blocks live under `blocks/<block-id>.json`.

```json
{
  "id": "uuidv7",
  "label": "Market Timing",
  "body": "Exact source text...",
  "source_snapshot_id": "uuidv7",
  "updated_at": "RFC3339"
}
```

Memos compose blocks by reference. Stakeholder overrides do not mutate the central block.

## Stakeholder

```json
{
  "email": "investor@example.com",
  "name": "Investor Name",
  "org": "Fund",
  "role": "investor",
  "status": "approved",
  "locale": "en-US",
  "version_id": "uuidv7",
  "pin_hash": "sha256",
  "pin_updated_at": "RFC3339",
  "session_revoked_at": "RFC3339 or null",
  "custom_fields": {}
}
```

Statuses:

- `approved`
- `candidate`
- `blocked`
- `revoked`

## Audit Log

`audit.jsonl` is append-only JSONL.

Every line includes:

- `ts`
- `actor`
- `action`
- `entity_type`
- `entity_id`
- `details`

## Analytics

Raw events are stored as JSONL under `analytics/<memo-id>.jsonl`.

Required event names:

- `page_view`
- `return_visit`
- `visible_time`
- `read_depth`
- `section_dwell`
- `click`
- `download`
- `version_exposure`
- `auth_attempt`
- `candidate_capture`

## Replay

Replay events are stored under `replay/<memo-id>/<session-id>.jsonl` and retained for 90 days by default.
