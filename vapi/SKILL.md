---
name: vapi
description: Voice AI integration with Vapi. Enables inbound/outbound phone calls with AI voice agents that can check calendars and book appointments. Webhook server handles dynamic assistant config, call history, and post-call recaps.
compatibility: Created for Zo Computer
created: 2026-02-12
last_edited: 2026-02-12
version: 1.0
provenance: con_QTABCDASvBcVRxAC
metadata:
  author: thevibethinker
  upstream: https://github.com/zocomputer/skills/pull/8
  upstream_author: nloui
---
# Vapi Voice Integration

AI-powered voice assistant that handles phone calls, checks calendar availability, and books appointments.

## Setup

### Environment Variables

Set in [Settings → Advanced](/?t=settings&s=advanced):

| Variable | Required | Value |
|----------|----------|-------|
| `VAPI_API_KEY` | ✅ | Vapi private API key |
| `VAPI_OWNER_PHONE` | Recommended | Owner phone number for trusted-caller flows |
| `VAPI_OWNER_NAME` | Recommended | Name of the person the assistant represents |
| `VAPI_ASSISTANT_NAME` | Recommended | Assistant display name used in calls |
| `VAPI_OWNER_CONTEXT` | Recommended | Short context string, e.g. `Founder of Acme` |
| `VAPI_CALENDAR_ID` | For booking | Google Calendar ID to check and book against |
| `VAPI_WORK_CALENDAR_ID` | Optional | Secondary calendar for availability checks |
| `VAPI_TIMEZONE` | Default: `America/New_York` | Scheduling timezone |
| `VAPI_VOICE_ID` | Optional | ElevenLabs voice ID or equivalent provider voice |
| `VAPI_VOICE_MODEL` | Optional | Voice model name |
| `VAPI_LLM_MODEL` | Optional | LLM for voice responses |
| `VAPI_SECURITY_PIN` | Optional | DTMF PIN for protected caller flows |
| `VAPI_WEBHOOK_SECRET` | Strongly recommended | Shared secret for webhook validation |
| `VAPI_WEBHOOK_PORT` | Default: `4242` | Local webhook port |
| `VAPI_DB_PATH` | Optional | DuckDB path for call records |
| `GOOGLE_TOKEN_PATH` | For booking | Path to a Google OAuth token JSON file |

### Required Services and Accounts

- A Vapi account, phone number, and webhook configuration
- Bun and DuckDB available in the runtime
- Google Calendar OAuth credentials if you want booking support
- Zo API access if you want post-call recap delivery via Zo primitives

### Deployment Shape

Bring your own phone number, webhook URL, and service registration. The bundled scripts are examples; review them before production use and replace any example identities, prompts, or defaults with your own.

## Usage

### Inbound Calls
People call the configured phone line → the webhook dynamically generates assistant config → the AI handles the call → a recap can be delivered through Zo or another channel you configure.

### Outbound Calls
```bash
bun Skills/vapi/scripts/vapi.ts call +15551234567
bun Skills/vapi/scripts/vapi.ts call +15551234567 --purpose "Following up on the deck"
bun Skills/vapi/scripts/vapi.ts call +15551234567 --context "Meeting about Q4 planning"
```

### Manage Assistants
```bash
bun Skills/vapi/scripts/vapi.ts assistant list
bun Skills/vapi/scripts/vapi.ts assistant create
```

### Call History
```bash
bun Skills/vapi/scripts/vapi.ts calls
duckdb Datasets/vapi-calls/data.duckdb -c "SELECT * FROM calls ORDER BY started_at DESC LIMIT 10"
```

## Architecture

- **webhook.ts** — Bun HTTP server handling Vapi webhooks (assistant-request, tool-calls, end-of-call-report)
- **vapi.ts** — CLI for managing assistants, phone numbers, and making outbound calls
- Call data stored in DuckDB (default path configurable via `VAPI_DB_PATH`)
- Calendar integration via Google Calendar API (direct OAuth token file)
- Post-call recaps can be sent via Zo API → email/SMS, or adapted to your own notification path

## Portability Notes

- The repo still includes opinionated example prompts, asset copy, and runtime defaults that should be reviewed before public reuse.
- Treat this skill as a portable starting point, not a drop-in production deployment without customization.
