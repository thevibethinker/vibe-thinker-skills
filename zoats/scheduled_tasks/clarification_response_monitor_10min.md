# Scheduled Task Spec: Clarification Response Monitor (10‑min)

id: zoats_clarification_response_monitor_10min
label: "📬 ATS Clarification Response Monitor"
purpose: "Check Gmail for candidate replies to clarification emails; save responses; queue re-evaluation tasks."

rrule: "FREQ=HOURLY;BYMINUTE=0,10,20,30,40,50"

instruction: |
  Monitor clarification responses for the default job. Requires Gmail connection.
  Steps:
  1) cd "${ZOATS_HOME:-${ZOATS_HOME}}"
  2) python workers/clarification/track_responses.py --job $(jq -r .default_job config/settings.json) --dry-run
  Success: Logs show pending approvals and any detected responses; writes nothing in dry-run.
  Error handling: If Gmail tools unavailable, log and continue.

defaults:
  dry_run: true
  enabled: false

artifacts:
  - jobs/{job}/candidates/{candidate}/outputs/clarification_response.json
  - jobs/{job}/approvals/*.json (status updates)
  - jobs/{job}/reevaluation_queue/*.json

references:
  - file 'ZoATS/workers/clarification/track_responses.py'
  - file 'ZoATS/workers/clarification/APPROVALS.md'

notes:
  - Only enable after Gmail is configured.
