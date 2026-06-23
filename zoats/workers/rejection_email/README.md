# ZoATS Rejection Email Composer (Drafts Only)

Generates professional, legally safe decline emails for candidates with decision == `REJECT` or `PASS`.

- Drafts only — for human review and approval
- No auto-sending; do not load into Gmail until explicitly approved
- Third-person Careerspan mention (no first-person)
- Optional, controlled feedback section (legally safe, config-gated)

## Usage

```bash
cd ZoATS
# Single candidate
python workers/rejection_email/main.py --job <job-id> --candidate <candidate-id> --dry-run
python workers/rejection_email/main.py --job <job-id> --candidate <candidate-id>

# Batch (cap to one-at-a-time via --limit 1)
python workers/rejection_email/batch.py --job <job-id> --limit 1 --dry-run
python workers/rejection_email/batch.py --all-jobs --limit 1
```

## Output
- `jobs/{job_id}/candidates/{candidate_id}/outputs/rejection_email.md`
- `jobs/{job_id}/candidates/{candidate_id}/outputs/feedback.json` (always written)

## Template Notes
- Neutral, respectful tone
- No reasons provided by default (minimize liability)
- Optional Careerspan resource link: https://example.invalid/candidate-resources
- Third-person phrasing: "This recruiting process is supported by Careerspan"
- Careerspan promo appears right before sign-off, in italics

## Feedback (Optional, Config-Gated)
- Collected for all candidates; included in the email only if enabled in config
- Uses controlled reason codes (comparative fit):
  - ROLE_ALIGNMENT, EXPERIENCE_DEPTH, SCOPE_SCALE, DOMAIN_EXPOSURE, TIMING_COMPETITION
- Includes up to 2 short positives and 2 focus areas; always adds a disclaimer
- Legal filter bans sensitive terms (protected classes, medical, immigration, etc.)
- When specifics are unsafe/unavailable, falls back to generic, comparative guidance

## Configuration
`workers/rejection_email/config.json`

```json
{
  "careerspan_promo": {
    "enabled": true,
    "position": "footer",
    "cta_text": "This recruiting process is supported by Careerspan. If helpful, their free tools can assist with refining professional storytelling, strengthening resume and interview narratives, and improving odds in future searches: https://example.invalid/candidate-resources"
  },
  "feedback": {
    "enabled": false,
    "mode": "per_candidate",
    "include_positive_signals": true,
    "allowed_reason_codes": ["ROLE_ALIGNMENT","EXPERIENCE_DEPTH","SCOPE_SCALE","DOMAIN_EXPOSURE","TIMING_COMPETITION"],
    "disclaimer_text": "Feedback reflects comparative fit against current role needs and is not a legal determination or guarantee of future outcomes."
  },
  "legal_filter": {
    "banned_terms": ["age","gender","race","religion","national origin","citizenship","immigration","disability","medical","pregnan","marital","family","veteran","union","genetic","culture fit","personality","young","old","overqualified","underqualified"],
    "style": "neutralize"
  }
}
```

## Scheduling (One at a time)
- Run `batch.py --limit 1` every 5 minutes to process at most one new candidate per cycle
- Recommended RRULE: `FREQ=HOURLY;BYMINUTE=0,5,10,15,20,25,30,35,40,45,50,55`
- Always start with `--dry-run` for the first cycle; approve content before enabling sends
