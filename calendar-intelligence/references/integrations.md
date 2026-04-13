---
created: 2026-04-13
last_edited: 2026-04-13
version: 1.0
provenance: calendar-intelligence-skill
---

# Integration Setup Guide

## For Skill Users

This skill requires integrations to be connected before installation.
Set these up in your Zo Computer's [Settings > Integrations](/?t=settings&s=integrations).

### Calendar (Required — pick one)

**Google Calendar:**
1. Go to Settings > Integrations > Connections
2. Connect Google Calendar with the account that has your calendars
3. Grant read access (the skill only reads events during scan; write access
   is needed only if you activate the Focus Defender automation)

**Microsoft Outlook:**
1. Go to Settings > Integrations > Connections
2. Connect Microsoft Outlook with your work/personal account
3. The skill uses the same read access patterns

### Email (Required — pick one)

**Gmail:**
1. Connect Gmail in Settings > Integrations
2. The skill searches for recent threads with calendar attendees
3. Read access only — the skill never sends emails

**Microsoft Outlook:**
1. Connect Microsoft Outlook (email) in Settings > Integrations
2. Same search functionality as Gmail

### LinkedIn (Recommended)

The LinkedIn integration enables attendee due diligence in the EOD Roundup.
Without it, the roundup still works but won't include professional background.

**Setup:**
1. Go to Settings > Integrations > Local Connections
2. Configure the LinkedIn integration (`zo-linkedin` skill)
3. Follow the cookie-based auth setup in the LinkedIn skill docs
4. Verify with: `python3 Skills/zo-linkedin/scripts/lk.py whoami`

## Data Contracts

### Raw Calendar Response (input to scan.py)

Google Calendar `list-events` response with an `items` array:

```json
{
  "items": [
    {
      "id": "event-id",
      "summary": "Meeting Title",
      "start": {"dateTime": "2026-04-14T10:00:00-04:00"},
      "end": {"dateTime": "2026-04-14T11:00:00-04:00"},
      "attendees": [
        {"email": "person@example.com", "displayName": "Name", "responseStatus": "accepted"}
      ],
      "recurringEventId": "optional-recurring-id",
      "location": "optional",
      "description": "optional",
      "status": "confirmed"
    }
  ]
}
```

### Normalized Event (output of scan.py)

```json
{
  "id": "event-id",
  "summary": "Meeting Title",
  "start": "2026-04-14T10:00:00-04:00",
  "end": "2026-04-14T11:00:00-04:00",
  "duration_minutes": 60,
  "attendees": [
    {"email": "person@example.com", "name": "Name", "response": "accepted"}
  ],
  "is_recurring": false,
  "recurring_event_id": null,
  "calendar_id": "primary",
  "location": "",
  "description": "",
  "status": "confirmed",
  "is_all_day": false
}
```

### Email Intel (input to eod_roundup.py)

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
          "direction": "inbound|outbound",
          "snippet": "Preview text (first 80 chars)"
        }
      ]
    }
  }
}
```

### LinkedIn Intel (input to eod_roundup.py)

```json
{
  "profiles": {
    "email@example.com": {
      "name": "Full Name",
      "headline": "Title at Company",
      "location": "City, State",
      "summary": "Bio text",
      "experience": [
        {"title": "Role", "company": "Company", "duration": "3 years"}
      ]
    }
  }
}
```
