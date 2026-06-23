# Scheduled Task Spec: Gestalt Scoring Queue (5‑min, one-at-a-time)

id: zoats_scoring_queue_5min
label: "🧠 ATS Scoring Queue (single candidate)"
purpose: "Run gestalt evaluation for one candidate that has parsed text but no gestalt_evaluation.json; then generate dossier."

rrule: "FREQ=HOURLY;BYMINUTE=2,7,12,17,22,27,32,37,42,47,52,57"

instruction: |
  Score exactly one pending candidate per run; then generate dossier. Do not send any emails.
  Steps:
  1) cd "${ZOATS_HOME:-${ZOATS_HOME}}"
  2) JOB=$(jq -r .default_job config/settings.json)
  3) CAND=$(ls jobs/$JOB/candidates | while read C; do test -f jobs/$JOB/candidates/$C/parsed/text.md && test ! -f jobs/$JOB/candidates/$C/outputs/gestalt_evaluation.json && echo $C && break; done)
  4) if [ -n "$CAND" ]; then python workers/scoring/main_gestalt.py --job $JOB --candidate $CAND --dry-run; fi
  5) if [ -n "$CAND" ]; then python workers/dossier/main.py --job $JOB --candidate $CAND --dry-run; fi
  Success: 0–1 candidates evaluated; dossier preview only.
  Error handling: Skip if none found; exit cleanly on missing rubric.

defaults:
  dry_run: true
  enabled: false

artifacts:
  - jobs/{job}/candidates/{candidate}/outputs/gestalt_evaluation.json
  - jobs/{job}/candidates/{candidate}/outputs/dossier.md

references:
  - file 'ZoATS/workers/scoring/main_gestalt.py'
  - file 'ZoATS/workers/dossier/main.py'
  - file 'ZoATS/pipeline/README.md'

notes:
  - Keep one-at-a-time cadence to avoid cross-candidate coupling.
