# Gmail Intake (Worker)
Status: Planned (Week 2) | Owner: TBA

Purpose
- Poll Gmail API for applications and write all relevant artifacts into `inbox_drop/` for downstream processing.

Inputs
- Gmail API (labels/queries), threads, messages with attachments

Outputs
- `inbox_drop/*` — attachments (e.g., resumes), `.eml` raw message files, `metadata.json`

Interface
- `python workers/gmail_intake/main.py --poll --label "Applications" --dry-run`

Milestones (Week 2)
- OAuth and token storage
- Label filters (e.g., Applications), query support
- Thread de-duplication; only download new
- Attachment extraction to `inbox_drop/`
- Write `metadata.json` with inferred fields: `name, email, source, applied_date, role_code`
- Idempotent runs; retries with backoff

Notes
- Source-agnostic: Email Intake should not decide candidacy; it only collects into `inbox_drop/`.
- Candidate Intake Processor consumes from `inbox_drop/` (see workers/candidate_intake.md).
