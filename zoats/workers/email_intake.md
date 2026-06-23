# Email Intake Worker (Deprecated)
Status: Deprecated in favor of Candidate Intake Processor | Owner: con_6eNkFTCmluuGFa4a

This worker has been superseded by the Candidate Intake Processor and a separate Gmail API Intake worker.

- Candidate Intake Processor: `file 'ZoATS/workers/candidate_intake.md'`
- Gmail API Intake (Week 2): `file 'ZoATS/workers/gmail_intake.md'`

Rationale
- Separate concerns for reliability and portability: Gmail API polling writes to a universal staging area `inbox_drop/`, while the Candidate Intake Processor handles validation, bundling, and moving files into job-specific candidate directories.

Action
- Use `python workers/candidate_intake/main.py --job <job> [--dry-run]` to process files in `inbox_drop/`.
