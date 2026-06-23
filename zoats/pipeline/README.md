# Pipeline Orchestrator CLI

End-to-end orchestration: intake → parse → score → dossier for all candidates in a job.

## Usage

```bash
# Process existing candidates only
python pipeline/run.py --job <job> [--dry-run]

# Run intake first, then process all
python pipeline/run.py --job <job> --from-inbox [--dry-run]
```

## Flow

1. **Optional: Intake** (if `--from-inbox`)
   - Calls `workers/candidate_intake/main.py`
   - Processes files from `inbox_drop/` into `jobs/<job>/candidates/<id>/`

2. **Discovery**
   - Finds all candidate IDs in `jobs/<job>/candidates/`

3. **Per-Candidate Processing** (continue-on-error)
   - Parser: raw/* → parsed/text.md, parsed/fields.json
   - Scorer: rubric + parsed → outputs/scores.json, outputs/quick_test.json (when implemented)
   - Dossier: all inputs → outputs/candidate.md (when implemented)

4. **Summary**
   - Logs pipeline run results to `jobs/<job>/pipeline_run.json`
   - Returns JSON summary to stdout

## Output Structure

```json
{
  "job": "smoke-test",
  "stages": {
    "intake": {"success": true, "stdout": "..."}
  },
  "candidates_processed": 2,
  "candidate_results": [
    {
      "candidate_id": "alice-johnson-st001-2025-10-22",
      "status": "partial_complete",
      "steps": {
        "parser": {"success": true},
        "scorer": {"success": false, "reason": "not_implemented"},
        "dossier": {"success": false, "reason": "not_implemented"}
      }
    }
  ],
  "summary": {
    "total": 2,
    "complete": 0,
    "partial": 1,
    "failed": 1
  }
}
```

## Status Values

- `complete`: All steps (parser → scorer → dossier) succeeded
- `partial_complete`: Parser succeeded, downstream not implemented or failed
- `parser_failed`: Parser failed, downstream skipped
- `scorer_failed`: Scorer failed, dossier skipped
- `dossier_failed`: Dossier failed
- `error`: Uncaught exception

## Exit Codes

- `0`: Pipeline completed (check summary for per-candidate status)
- `1`: Critical failure (job not found, intake failed if requested)

## Integration

Called by Test Harness (`tests/smoke.py`) for end-to-end validation.
