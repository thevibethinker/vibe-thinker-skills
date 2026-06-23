# Pipeline Orchestrator CLI (Glue Worker)
Status: Complete | Owner: con_6eNkFTCmluuGFa4a

Purpose
- Run end-to-end pipeline for a job: intake → parse → score → dossier.

Inputs
- inbox_drop/ (if --from-inbox)
- jobs/<job>/

Outputs
- Updated candidates/*/outputs/
- jobs/<job>/pipeline_run.json (execution log)

Interface
- `python pipeline/run.py --job <job> [--from-inbox] [--dry-run]`

Tonight Milestones
- Linear pipeline with logging and idempotent re-run per candidate

Definition of Done (Night 1)
- [x] Discovers candidates from jobs/<job>/candidates/
- [x] Runs intake (optional --from-inbox flag)
- [x] Runs parser → scorer → dossier per candidate with continue-on-error
- [x] Writes pipeline_run.json with summary
- [x] Supports --dry-run

Dependencies
- All workers

Risks & Mitigations
- Failure mid-pipeline → per-candidate isolation and continue-on-error

Checklist (Night 1)
- [ ] Discover candidates
- [ ] Run workers in order
- [ ] Summarize results
- [ ] Verify outputs

Paths
- pipeline/run.py

Integration Points
- Test Harness calls this for smoke

Notes
- Future: resume from checkpoints
