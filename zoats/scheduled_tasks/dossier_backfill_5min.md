# Scheduled Task Spec: Dossier Backfill (5‑min, one-at-a-time)

id: zoats_dossier_backfill_5min
label: "📄 ATS Dossier Backfill (single)"
purpose: "Generate dossier for one candidate that has gestalt_evaluation.json but no dossier.md."

rrule: "FREQ=HOURLY;BYMINUTE=6,16,26,36,46,56"

instruction: |
  Backfill exactly one dossier per run.
  Steps:
  1) cd "${ZOATS_HOME:-${ZOATS_HOME}}"
  2) JOB=$(jq -r .default_job config/settings.json)
  3) CAND=$(ls jobs/$JOB/candidates | while read C; do test -f jobs/$JOB/candidates/$C/outputs/gestalt_evaluation.json && test ! -f jobs/$JOB/candidates/$C/outputs/dossier.md && echo $C && break; done)
  4) if [ -n "$CAND" ]; then python workers/dossier/main.py --job $JOB --candidate $CAND --dry-run; fi
  Success: 0–1 dossiers previewed.
  Error handling: Skip if none; continue next cycle.

defaults:
  dry_run: true
  enabled: false

artifacts:
  - jobs/{job}/candidates/{candidate}/outputs/dossier.md
  - jobs/{job}/candidates/{candidate}/outputs/dossier.json

references:
  - file 'ZoATS/workers/dossier/main.py'
