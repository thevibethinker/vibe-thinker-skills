---
name: calendar-intelligence
description: |
  Calendar intelligence with distinct install, scan, and personalization phases.
  Scans connected calendars for trends and patterns, recommends automations,
  and includes an EOD roundup that cross-references calendar attendees with
  recent emails and LinkedIn profiles. Designed for any Zo Computer.
compatibility: Created for Zo Computer
metadata:
  author: va.zo.computer
  version: "1.0.0"
  created: 2026-04-13
allowed-tools: Bash Read
---

# Calendar Intelligence

Transform raw calendar data into actionable patterns and automated workflows.
Works with Google Calendar or Microsoft Outlook. Includes LinkedIn-powered
attendee due diligence.

**Three-phase lifecycle:**
1. **Install** — detect integrations, select calendars, write config
2. **Scan & Analyze** — pull events, detect patterns, generate report
3. **Personalize** — recommend automations, user approves, activate agents

## Prerequisites

The installing user must have the following connected in their Zo before running:

| Integration | Required | Purpose |
|-------------|----------|---------|
| Google Calendar OR Microsoft Outlook | ✅ | Calendar event source |
| Gmail OR Microsoft Outlook (email) | ✅ | Email cross-referencing in EOD roundup |
| LinkedIn (local connection) | ⭐ Recommended | Attendee due diligence via `lk.py` |

See `references/integrations.md` for setup instructions.

---

## Phase 1: Install

**Goal:** Create `data/config.yaml` with the user's integrations and preferences.

### Interactive Setup (Zo guides the user)

1. **Detect available integrations.** Check which calendar/email/LinkedIn integrations the user has connected.
2. **Ask the user** which calendars to scan (if they have multiple).
3. **Collect preferences:** timezone, work hours, work days, EOD time, delivery method.
4. **Run install:**

```bash
python3 Skills/calendar-intelligence/scripts/install.py init \
  --cal-provider google_calendar \
  --cal-email "user@email.com" \
  --calendars "primary:My Calendar" \
  --mail-provider gmail \
  --mail-email "user@email.com" \
  --linkedin available \
  --timezone "America/New_York" \
  --eod-time "21:00" \
  --delivery email \
  --work-start "09:00" \
  --work-end "18:00" \
  --work-days "1,2,3,4,5"
```

5. **Validate:**

```bash
python3 Skills/calendar-intelligence/scripts/install.py validate
```

### Config Management

```bash
python3 Skills/calendar-intelligence/scripts/install.py status       # Show current config
python3 Skills/calendar-intelligence/scripts/install.py update ...   # Modify fields
python3 Skills/calendar-intelligence/scripts/install.py validate     # Check completeness
```

---

## Phase 2: Scan & Analyze

**Goal:** Pull calendar events, normalize them, and run pattern analysis.

### Step 2a: Fetch Calendar Events

Use Zo's calendar integration tools to fetch events for the scan window
(default: 4 weeks). Save the raw response to a temp file.

**For Google Calendar:**
```
use_app_google_calendar("google_calendar-list-events", {
  "calendarId": "<calendar-id>",
  "timeMin": "<4 weeks ago ISO>",
  "timeMax": "<now ISO>",
  "maxResults": 500,
  "singleEvents": true,
  "orderBy": "startTime"
}, email="<user-email>")
```

Save the response JSON to a temp file, then ingest:

```bash
python3 Skills/calendar-intelligence/scripts/scan.py ingest \
  --raw /path/to/raw_response.json \
  --calendar-id "primary"
```

Repeat for each calendar in the config. The script merges events into a single scan file.

### Step 2b: Run Analysis

```bash
python3 Skills/calendar-intelligence/scripts/analyze.py run
```

This generates `data/analysis_YYYY-MM-DD.md` with:
- 8 pattern analyses (meeting density, buffer gaps, recurring load, collaborator frequency, time clustering, deep work windows, context switching, meeting length distribution)
- Threshold classifications (light/moderate/heavy/etc.)
- Actionable insights per pattern

**Quick check:**
```bash
python3 Skills/calendar-intelligence/scripts/analyze.py quick
```

---

## Phase 3: Personalize

**Goal:** Recommend automations based on the user's patterns, let them approve and activate.

### Step 3a: Generate Recommendations

```bash
python3 Skills/calendar-intelligence/scripts/recommend.py generate
```

This reads the analysis report and automation templates, and produces
`data/recommendations_YYYY-MM-DD.yaml` with matched recommendations.

### Step 3b: Review with User

Present each recommendation and ask for approval:

```bash
python3 Skills/calendar-intelligence/scripts/recommend.py list
```

### Step 3c: Activate Approved Automations

For each approved recommendation:

```bash
python3 Skills/calendar-intelligence/scripts/recommend.py activate --id <recommendation-id>
```

This outputs `create_agent` parameters as JSON. Use them to create the scheduled agent:

```python
create_agent(
    rrule=<rrule from output>,
    instruction=<instruction from output>,
    delivery_method=<delivery from output>
)
```

---

## EOD Roundup

The EOD Roundup is the flagship automation. When triggered (nightly), Zo should:

### 1. Fetch Tomorrow's Events

Use the calendar integration to get all events for the next business day.
Normalize them into the scan format (or use a fresh scan).

### 2. Check Attendee Cache

```bash
python3 Skills/calendar-intelligence/scripts/eod_roundup.py cache-check \
  --attendees "email1@example.com,email2@example.com"
```

### 3. LinkedIn Due Diligence (for uncached/expired attendees)

For each attendee needing refresh, use the LinkedIn integration:

```bash
python3 Skills/zo-linkedin/scripts/lk.py search "<attendee name>"
python3 Skills/zo-linkedin/scripts/lk.py profile "<linkedin-public-id>"
```

Save the profile data and update the cache:

```bash
python3 Skills/calendar-intelligence/scripts/eod_roundup.py cache-update \
  --email "attendee@example.com" \
  --profile-json /path/to/profile.json
```

### 4. Email Cross-Reference

Use Zo's email integration to search for recent threads with each attendee:

**For Gmail:**
```
use_app_gmail("gmail-search-email", {
  "q": "from:<attendee-email> OR to:<attendee-email>",
  "maxResults": 10
}, email="<user-email>")
```

Compile the email intel into a JSON file with this structure:
```json
{
  "attendees": {
    "email@example.com": {
      "last_contact": "2026-04-12",
      "thread_count": 3,
      "recent_threads": [
        {
          "subject": "Thread subject",
          "date": "2026-04-12",
          "direction": "inbound",
          "snippet": "Preview text"
        }
      ]
    }
  }
}
```

### 5. Compile the Digest

```bash
python3 Skills/calendar-intelligence/scripts/eod_roundup.py compile \
  --events /path/to/tomorrow_events.json \
  --email-intel /path/to/email_intel.json \
  --linkedin-intel /path/to/linkedin_intel.json
```

### 6. Deliver

Send the compiled digest via the user's preferred delivery method
(email, SMS, or Telegram).

---

## Available Automation Templates

| ID | Name | Trigger | Default Schedule |
|----|------|---------|-----------------|
| `eod-roundup` | EOD Roundup | Always | Sun-Thu evenings |
| `morning-brief` | Morning Brief | Meeting density ≥ moderate | Weekday mornings |
| `buffer-guardian` | Buffer Guardian | Back-to-back > 3/week | Twice daily |
| `focus-defender` | Focus Time Defender | Deep work ≤ constrained | Weekly Sunday |
| `recurring-audit` | Recurring Meeting Audit | Recurring load ≥ moderate | Friday afternoons |
| `weekly-trends` | Weekly Calendar Trends | Meeting density ≥ moderate | Friday evenings |

---

## Script Reference

| Script | Subcommands | Purpose |
|--------|-------------|---------|
| `install.py` | `init`, `status`, `update`, `validate` | Config lifecycle |
| `scan.py` | `ingest`, `summary`, `cleanup` | Event data management |
| `analyze.py` | `run`, `quick` | Pattern analysis |
| `recommend.py` | `generate`, `list`, `activate` | Automation recommendations |
| `eod_roundup.py` | `compile`, `cache-check`, `cache-update` | EOD digest |

All scripts support `--help` for full usage documentation.

---

## Data Files

| File | Purpose | Created By |
|------|---------|-----------|
| `data/config.yaml` | User configuration | `install.py init` |
| `data/scan_YYYY-MM-DD.json` | Normalized calendar events | `scan.py ingest` |
| `data/analysis_YYYY-MM-DD.md` | Pattern analysis report | `analyze.py run` |
| `data/recommendations_YYYY-MM-DD.yaml` | Automation recommendations | `recommend.py generate` |
| `data/roundup_YYYY-MM-DD.md` | EOD digest | `eod_roundup.py compile` |
| `data/attendee_cache.json` | LinkedIn profile cache (7-day TTL) | `eod_roundup.py cache-update` |

---

## Adapting This Skill

This skill is designed to be portable. To adapt for a different Zo:

1. **Install:** Run Phase 1 with the new user's integrations
2. **Scan:** The analysis adapts to whatever calendar data it finds
3. **Personalize:** Recommendations are driven by the user's actual patterns
4. **Extend:** Add new templates to `assets/automation_templates.yaml`
5. **Customize patterns:** Edit thresholds in `assets/pattern_library.yaml`

The `data/` directory is gitignored — each installation gets its own data.
