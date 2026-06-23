# Scheduled Task Spec: Resume Parser Queue (5‑min, one-at-a-time)

id: zoats_parser_queue_5min
label: "🧾 ATS Parser Queue (single candidate)"
purpose: "Parse resume for one candidate lacking parsed outputs (text.md, fields.json)."

rrule: "FREQ=HOURLY;BYMINUTE=1,6,11,16,21,26,31,36,41,46,51,56"

instruction: |
  Parse exactly one pending candidate per run for the default job.
  Steps:
  1) cd "${ZOATS_HOME:-${ZOATS_HOME}}"
  2) JOB=$(jq -r .default_job config/settings.json)
  3) CAND=$(ls jobs/$JOB/candidates | while read C; do test -f jobs/$JOB/candidates/$C/raw/* 2>/dev/null && test ! -f jobs/$JOB/candidates/$C/parsed/fields.json && echo $C && break; done)
  4) if [ -n "$CAND" ]; then python workers/parser/main.py --job $JOB --candidate $CAND --dry-run; fi
  Success: 0–1 candidates parsed (dry-run preview).
  Error handling: Skip if none found; never process more than one.

defaults:
  dry_run: true
  enabled: false

artifacts:
  - jobs/{job}/candidates/{candidate}/parsed/text.md
  - jobs/{job}/candidates/{candidate}/parsed/fields.json

references:
  - file 'ZoATS/workers/parser/README.md'
  - file 'ZoATS/workers/parser/main.py'

notes:
  - Switch off dry-run after verifying parser extraction quality.
