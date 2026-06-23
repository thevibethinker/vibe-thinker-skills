# MAYBE Email Approvals

This worker queues draft emails for approval; it does not send.

## Manifest
- `jobs/{job_id}/approvals/maybe_pending.json`
  - `candidate_id`: string
  - `email_path`: string (absolute or workspace-relative)
  - `status`: "pending" | "approved" | "sent"
  - `created_at`: ISO8601Z

## Review Workflow
1. Run batch to queue drafts:
   - All jobs: `python workers/maybe_email/batch.py --all-jobs --dry-run`
   - Single job: `python workers/maybe_email/batch.py --job <job-id>`
2. Reviewer opens each `email_path`, edits if needed
3. Mark approved in manifest (manual edit for now)
4. Only after explicit approval → hand-off to sending tool (not included)

## Safety
- Do not pre-load drafts into Gmail until approval
- Drafts live in candidate outputs folders
- Manifest is append-only; de-duplication by `candidate_id`
