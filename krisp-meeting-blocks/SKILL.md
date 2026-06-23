---
name: krisp-meeting-blocks
description: Portable Krisp transcript ingestion and meeting block pipeline for Zo Computer. Receives Krisp transcript webhooks, normalizes meetings into repairable folders, generates summary/metadata/decisions/action-item blocks, supports richer v3-style add-on blocks, archives monthly, and notifies the Zo owner when a meeting is partial or needs review.
compatibility: Created for Zo Computer
metadata:
  author: va.zo.computer
  version: "1.0.0"
  created: 2026-06-23
  last_modified: 2026-06-23
---

# Krisp Meeting Blocks

Portable meeting-transcript pipeline for a Zo Computer that uses Krisp as the capture source.

Use this skill when you want another Zo to set up its own version of V's Krisp-based meeting pipeline without inheriting V-specific calendar, CRM, research-repo, Fathom, Drive, Pocket, or private workspace dependencies.

## What It Builds

A standalone pipeline:

1. **Krisp webhook route** receives `transcript_created` events.
2. **Normalizer** writes source payloads and a canonical meeting folder.
3. **Quality gate** decides whether the meeting can be processed, is partial, or needs review.
4. **Repair surface** writes `ENRICHMENT.yaml` and immutable `transcript.original.md`.
5. **Block generator** writes always-on blocks:
   - `summary.md`
   - `metadata.md`
   - `decisions.md`
   - `action_items.md`
6. **Add-on block layer** can generate richer v3-inspired blocks:
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
7. **Monthly archive** moves terminal meetings under `Personal/Meetings/YYYY/MM-Month/`.
8. **Notification hook** notifies the Zo owner when a meeting is partial or needs review.

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
- Optional: `MEETING_BLOCK_MODEL_NAME` — override the model used for block generation.

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
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py import /path/to/payload.json [--process] [--dry-run]

# Process one meeting folder into blocks and monthly archive
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py process Personal/Meetings/Active/<meeting-folder> [--addons auto|all|none] [--dry-run]

# Reprocess from transcript.original.md + ENRICHMENT.yaml
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py reprocess Personal/Meetings/Active/<meeting-folder> [--addons auto|all|none] [--dry-run]

# Show active/review/archived status
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py status
```

## Storage Contract

```text
Personal/
  Integrations/
    krisp-meeting-blocks/
      incoming/             # raw webhook payloads from zo.space route
      processed/            # copied processed payloads
      rejected/             # too short / invalid payloads
      notifications.jsonl   # local notification ledger
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
- Portable first: no dependency on V's CRM, calendar, research repos, or private N5 scripts.
