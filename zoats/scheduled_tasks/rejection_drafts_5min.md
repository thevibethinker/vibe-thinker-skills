# Scheduled Task Spec: Rejection Drafts (5‑min, one-at-a-time)

id: zoats_rejection_drafts_5min
label: "💾 ATS Rejection Drafts (5‑min, one-at-a-time)"
purpose: "Generate at most one new rejection email draft per run for candidates with decision in {REJECT, PASS}; drafts only, queued for human approval; never send."

rrule: "FREQ=HOURLY;BYMINUTE=0,5,10,15,20,25,30,35,40,45,50,55"

instruction: |
  Read ZoATS and create at most one new rejection draft. Do not send any emails.
  Steps:
  1) cd "${ZOATS_HOME:-${ZOATS_HOME}}"
  2) python workers/rejection_email/batch.py --all-jobs --limit 1 --dry-run
  Success: 0–1 new draft added; draft queued at jobs/{job}/approvals/reject_pending.json; no errors.
  Error handling: Skip candidates missing required JSON; never send; stop on first error and log.

defaults:
  dry_run: true
  enabled: false

artifacts:
  - jobs/{job_id}/candidates/{candidate_id}/outputs/rejection_email.md
  - jobs/{job_id}/candidates/{candidate_id}/outputs/feedback.json
  - jobs/{job_id}/approvals/reject_pending.json

references:
  - file 'ZoATS/workers/rejection_email/README.md'
  - file 'ZoATS/workers/rejection_email/batch.py'
  - file 'N5/prefs/operations/scheduled-task-protocol.md'

notes:
  - Switch off --dry-run after validating content quality and legal safety
  - Keeps cadence gentle to avoid bulk processing; respects one-at-a-time evaluation
