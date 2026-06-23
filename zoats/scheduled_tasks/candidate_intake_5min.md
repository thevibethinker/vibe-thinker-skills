# Scheduled Task Spec: Candidate Intake from inbox_drop (5‑min)

id: zoats_candidate_intake_5min
label: "📥 ATS Candidate Intake (every 5 min)"
purpose: "Scan ZoATS/inbox_drop and ingest application bundles into jobs/<job>/candidates, creating raw/, parsed/, outputs/ dirs and interactions.md. No sending or external APIs."

rrule: "FREQ=HOURLY;BYMINUTE=0,5,10,15,20,25,30,35,40,45,50,55"

instruction: |
  Ingest candidate bundles from inbox_drop for the default job. Do not process more than what exists; idempotent on already-moved files.
  Steps:
  1) cd "${ZOATS_HOME:-${ZOATS_HOME}}"
  2) python workers/candidate_intake/main.py --job $(jq -r .default_job config/settings.json) --dry-run
  Success: 0–N bundles planned; no writes in dry-run; logs show grouping and intended moves.
  Error handling: If multiple jobs exist, require explicit job; fail safe.

defaults:
  dry_run: true
  enabled: false

artifacts:
  - jobs/{job}/candidates/{id}/raw/*
  - jobs/{job}/candidates/{id}/interactions.md

references:
  - file 'ZoATS/workers/candidate_intake/README.md'
  - file 'ZoATS/workers/candidate_intake/main.py'

notes:
  - Switch to live (remove --dry-run) only after verifying directory and naming conventions.
