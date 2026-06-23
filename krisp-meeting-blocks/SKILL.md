---
name: krisp-meeting-blocks
description: Portable Krisp transcript ingestion and meeting block pipeline for Zo Computer. Receives Krisp transcript webhooks or manual transcript files, normalizes meetings into repairable folders, optionally triangulates against calendar context, generates summary/metadata/decisions/action-item blocks, supports richer v3-style add-on blocks, archives monthly, and notifies the Zo owner when a meeting is partial or needs review.
compatibility: Created for Zo Computer
metadata:
  author: va.zo.computer
  version: "1.3.0"
  created: 2026-06-23
  last_modified: 2026-06-23
---

# Krisp Meeting Blocks

Portable meeting-transcript pipeline for a Zo Computer that uses Krisp as the capture source.

Use this skill when you want another Zo to set up its own version of V's Krisp-based meeting pipeline without inheriting V-specific calendar, CRM, research-repo, Fathom, Drive, Pocket, or private workspace dependencies.

## What It Builds

A standalone pipeline:

1. **Krisp webhook route** receives `transcript_created` events.
2. **Manual ingestion** imports `.md`, `.txt`, `.json`, or `.jsonl` transcripts without Krisp.
3. **Normalizer** writes source payloads/files and a canonical meeting folder.
4. **Quality gate** decides whether the meeting can be processed, is partial, or needs review.
5. **Optional calendar add-on** asks the target Zo to match likely calendar events when enabled.
6. **Repair surface** writes `ENRICHMENT.yaml` and immutable `transcript.original.md`.
7. **Block generator** writes always-on blocks:
   - `summary.md`
   - `metadata.md`
   - `decisions.md`
   - `action_items.md`
8. **Add-on block layer** can generate richer v3-inspired blocks:
   - `open_questions.md`
   - `key_moments.md`
   - `stakeholder_intelligence.md`
   - `business_context.md`
   - `strategic_intelligence.md`
   - `deliverable_map.md`
   - `relationship_trajectory.md`
   - `plan_of_action.md`
   - `thought_provoking_ideas.md`
   - `decision_rationale.md`
9. **Monthly archive** moves terminal meetings under `Personal/Meetings/YYYY/MM-Month/`.
10. **Notification hook** notifies the Zo owner when a meeting is partial or needs review.

## Install

Copy this folder to the target Zo's workspace:

```bash
mkdir -p /home/workspace/Skills
cp -R krisp-meeting-blocks /home/workspace/Skills/krisp-meeting-blocks
```

Optionally copy `config.example.yaml` to `config.yaml` and customize thresholds/notification behavior. Then run the bootstrap check:

```bash
cd /home/workspace
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py init --dry-run
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py init
```

## Required Zo Setup

### 1. Add Secrets

In [Settings > Advanced](/?t=settings&s=advanced), add:

- `KRISP_WEBHOOK_SECRET` — any strong random token. Krisp/the webhook caller must send it as `Authorization: Bearer <token>`.
- `ZO_CLIENT_IDENTITY_TOKEN` — normally already present inside Zo runtime for `/zo/ask` calls.
- Optional: `MEETING_BLOCK_MODEL_NAME` — override the model used for block generation/calendar matching.

### Runtime Reliability Defaults

The default `config.yaml` includes:

```yaml
zo_ask:
  max_retries: 3
  retry_base_seconds: 2.0
  timeout_seconds: 90
```

These apply to block generation, calendar matching, and Zo-owner notifications. Transient `/zo/ask` failures are retried with bounded exponential backoff; exhausted retries are recorded as partial block failures instead of crashing the pipeline.


### 2. Create the zo.space Route

Create a zo.space API route using `templates/zo-space-krisp-webhook.ts`.

Suggested route path:

```text
/api/krisp-webhook
```

The route writes incoming payloads to:

```text
Personal/Integrations/krisp-meeting-blocks/incoming/
```

Then it spawns:

```bash
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py import <payload-file> --process
```

The route also supports `GET` as a lightweight health check and writes importer output to:

```text
Personal/Integrations/krisp-meeting-blocks/importer.log
Personal/Integrations/krisp-meeting-blocks/importer.err.log
```

Set `KRISP_BLOCKS_CALENDAR=on|off|auto` in the zo.space environment if you want the webhook importer to force a calendar policy.

### 3. Configure Krisp

Point Krisp's transcript webhook to:

```text
https://<your-space>.zo.space/api/krisp-webhook
```

Send the configured bearer token in the `Authorization` header.

## Commands

```bash
# Create folders and config
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py init [--dry-run]

# Import one Krisp payload saved by the zo.space route
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py import /path/to/payload.json [--process] [--calendar auto|on|off] [--dry-run]

# Import a manually supplied transcript
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py manual /path/to/transcript.md --title "Customer Call" --date 2026-06-23 --participants "Alex,V" [--process] [--calendar auto|on|off] [--dry-run]

# Process one meeting folder into blocks and monthly archive
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py process Personal/Meetings/Active/<meeting-folder> [--addons auto|all|none] [--dry-run]

# Reprocess from transcript.original.md + ENRICHMENT.yaml
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py reprocess Personal/Meetings/Active/<meeting-folder> [--addons auto|all|none] [--dry-run]

# Show active/review/archived status
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py status

# Run install/runtime diagnostics
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py doctor
```


## Manual Ingestion

Manual ingestion is first-class. Use it for pasted transcripts, exported notes, historical backfill, or non-Krisp sources that can be represented as text. Supported inputs:

- `.md` / `.txt` — raw transcript text
- `.json` — object with `text`/`transcript`/`raw_content`, optional `title`, `date`, `participants`, `duration_seconds`
- `.jsonl` — one utterance per line with `speaker` and `text` fields

Manual imports produce the same meeting folder contract as Krisp imports: immutable `transcript.original.md`, editable `transcript.md`, `ENRICHMENT.yaml`, `manifest.json`, block outputs, review/partial notifications, and monthly archive.

## Optional Calendar Add-on

Calendar triangulation is opt-in and non-blocking. Enable it with either:

```yaml
calendar:
  enabled: true
  window_hours: 8
  min_confidence: 0.6
```

or pass `--calendar on`. The skill asks the current Zo to inspect the owner's calendar context and return a compact match object. If calendar access is unavailable or the match is low-confidence, the meeting still imports/processes; the manifest records `calendar_match.status` and warnings instead of failing the pipeline.

## Storage Contract

```text
Personal/
  Integrations/
    krisp-meeting-blocks/
      incoming/             # raw webhook payloads from zo.space route
      processed/            # copied processed payloads
      rejected/             # too short / invalid payloads
      notifications.jsonl   # local notification ledger
      dedup_ledger.jsonl    # idempotency ledger (dedupes re-deliveries)
      webhook.log           # zo.space route request log
      importer.log          # background importer stdout
      importer.err.log      # background importer stderr
  Meetings/
    Active/                 # in-flight folders
    Needs-Review/           # optional review lane for blocked imports
    Rejected/               # rejected meetings
    YYYY/
      MM-Month/             # monthly archive target
        <meeting-folder>/
```

Each meeting folder contains:

```text
manifest.json
transcript.original.md      # immutable source transcript
transcript.md               # working/repaired transcript
transcript.jsonl            # structured utterances when available
ENRICHMENT.yaml             # editable repair surface
summary.md
metadata.md
decisions.md
action_items.md
```

Add-on blocks are generated as separate markdown files when enabled.

## Quality / Review Semantics

A meeting becomes **needs review** when:

- no usable transcript exists
- transcript is under the configured minimum length
- Krisp only supplies generic speakers and no title/participant/date context
- `ENRICHMENT.yaml` is malformed
- an archive move would collide with an existing folder

A meeting becomes **partial** when:

- the transcript appears incomplete relative to duration
- one or more generated blocks fall back after a generation failure
- add-on block generation fails but core blocks exist

Partial and needs-review meetings are not silently buried. The script writes a notification event to `notifications.jsonl` and attempts a local Zo notification relay when configured.

## Notifications

Default behavior is portable and auditable:

- Always writes a local JSONL notification ledger.
- If `notify_mode: zo_ask`, asks the current Zo to notify its owner using its configured channels.
- If `notify_command` is configured, runs that local command with the event JSON on stdin.
- The command is intentionally target-Zo-specific. Examples:
  - a Telegram relay script
  - a local email helper
  - a Zo API notification endpoint

The skill never hardcodes V's Telegram handle, phone, email, or private notification routes.


## Block Specs

Block specs live in `block_specs/*.yaml`. The always-on set is intentionally small and portable. Rich v3-style blocks are declared as add-ons and can be generated with `--addons auto` or `--addons all`.

## Design Principles

- Inputs are immutable: raw payloads and `transcript.original.md` are never overwritten.
- Processing is a pipeline: import → enrich → gate → blocks → archive.
- State is visible: manifest status, quality flags, block completion, and notifications are recorded.
- Monthly archive is the default terminal structure.
- Portable first: no dependency on V's CRM, research repos, or private N5 scripts. Calendar is optional and delegated to the target Zo's own connected calendar.

## Reliability & Idempotency

This pipeline is hardened against the three most common failure modes for a handed-off meeting system:

**1. Duplicate delivery is deduped.** Every import/process records an entry in `dedup_ledger.jsonl` keyed by a stable `dedup_key`:
- Krisp re-deliveries key on `event_id`, then `meeting_id`.
- Manual/text sources key on a SHA-256 content hash.
A second delivery of the same logical meeting returns `status: existing` (reason `dedup_ledger_match`) instead of creating a duplicate folder. If the original was already archived, the ledger resolves the archived path rather than treating it as new.

**2. The calendar add-on never blocks block generation.** Calendar triangulation is best-effort enrichment only. A `no_match`, `error`, `unavailable`, or low-confidence result annotates `manifest.calendar_match` and may mark the meeting `partial`, but the always-on blocks are still generated and the meeting still archives monthly. Calendar access being unavailable can never strand a meeting in `Active/`.

**3. Partial and needs-review meetings always notify.** Whenever a meeting is classified `needs_review` or `partial` (short/invalid transcript, generic-speaker-without-context, calendar miss, or any block falling back), the pipeline both appends an event to `notifications.jsonl` and mirrors that event into `manifest.notifications[]`, so the signal survives archival and is auditable in the meeting folder itself.
