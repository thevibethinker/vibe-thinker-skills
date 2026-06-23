# Scheduled Task Spec: MAYBE Clarification Drafts (5‑min, one-at-a-time)

id: zoats_maybe_clarification_drafts_5min
label: "✉️ ATS MAYBE Clarification Drafts (single)"
purpose: "Generate at most one clarification_email.md draft per run for candidates with decision == MAYBE; queue to approvals."

rrule: "FREQ=HOURLY;BYMINUTE=3,8,13,18,23,28,33,38,43,48,53,58"

instruction: |
  Generate at most one MAYBE clarification draft per cycle.
  Steps:
  1) cd "${ZOATS_HOME:-${ZOATS_HOME}}"
  2) python workers/maybe_email/batch.py --all-jobs --dry-run
  Success: 0–N drafts previewed; may queue manifests in dry-run.
  Error handling: Skip candidates without gestalt_evaluation.json; never send emails.

defaults:
  dry_run: true
  enabled: false

artifacts:
  - jobs/{job_id}/candidates/{candidate_id}/outputs/clarification_email.md
  - jobs/{job_id}/approvals/maybe_pending.json

references:
  - file 'ZoATS/workers/maybe_email/README.md'
  - file 'ZoATS/workers/maybe_email/batch.py'
  - file 'ZoATS/workers/maybe_email/APPROVALS.md'

notes:
  - Add explicit --limit in future to hard-cap to 1 when implemented.
