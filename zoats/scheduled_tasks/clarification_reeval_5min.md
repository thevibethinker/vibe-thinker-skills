# Scheduled Task Spec: Clarification Re-evaluation Queue (5‑min)

id: zoats_clarification_reeval_5min
label: "🔁 ATS Clarification Re-evaluation (single)"
purpose: "Process at most one reevaluation_queue task per run; re-score with appended clarification answers; update evaluation + comparison."

rrule: "FREQ=HOURLY;BYMINUTE=4,9,14,19,24,29,34,39,44,49,54,59"

instruction: |
  Process a single pending re-evaluation task.
  Steps:
  1) cd "${ZOATS_HOME:-${ZOATS_HOME}}"
  2) JOB=$(jq -r .default_job config/settings.json)
  3) TASK=$(ls jobs/$JOB/reevaluation_queue 2>/dev/null | head -n1)
  4) if [ -n "$TASK" ]; then CAND=$(echo "$TASK" | sed 's/_reeval\.json$//'); python workers/clarification/reevaluate.py --job $JOB --candidate $CAND --dry-run; fi
  Success: 0–1 re-evals previewed; comparison printed in logs.
  Error handling: Skip if files missing; leave task file present until real run.

defaults:
  dry_run: true
  enabled: false

artifacts:
  - jobs/{job}/candidates/{candidate}/outputs/gestalt_evaluation.json (updated)
  - jobs/{job}/candidates/{candidate}/outputs/reevaluation_comparison.json

references:
  - file 'ZoATS/workers/clarification/reevaluate.py'
