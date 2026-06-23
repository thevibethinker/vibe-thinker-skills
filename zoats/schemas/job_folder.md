# Job Folder Contract

Every job in ZoATS lives in `jobs/<job-id>/`. The zo.space job board reads from these folders.

## Required Files

| File | Purpose | Created by |
|------|---------|-----------|
| `job-description.md` | Full job description (rendered on job board) | Operator |
| `rubric.json` | Scoring criteria for candidates | Operator |
| `deal_breakers.json` | Hard disqualifiers | Operator |
| `metadata.json` | Structured data for job board listing | Operator or auto-generated |

## metadata.json Schema

```json
{
  "title": "string (REQUIRED)",
  "company": "string (REQUIRED)",
  "location": "string",
  "type": "full-time | part-time | contract",
  "posted_date": "YYYY-MM-DD",
  "status": "open | on_hold | filled | closed",
  "description_summary": "string (1-2 sentence summary for listing cards)"
}
```

## Auto-Created Directories

| Directory | Purpose |
|-----------|---------|
| `candidates/` | Per-candidate folders created by intake worker |
| `approvals/` | Approval workflow records |
| `send_queue/` | Outbound email queue |

## Status Values

- `open` — accepting applications, shown on job board
- `on_hold` — hidden from job board, pipeline paused
- `filled` — role has been filled
- `closed` — archived, no new applications
