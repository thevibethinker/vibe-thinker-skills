# Candidate Intake Processor (Worker)
Status: Draft | Owner: con_6eNkFTCmluuGFa4a

Purpose
- Process candidate applications from `inbox_drop/` staging area; validate, bundle, and move into job-specific candidate directories; initialize a living dossier.

Inputs
- `inbox_drop/*` — accepts resumes and related files: `{pdf,docx,md,txt,eml,json}`
- Optional: `metadata.json` alongside resume with fields: `{name, email, source, applied_date, role_code}` (silent if missing)

Outputs
- `jobs/<job>/candidates/<id>/raw/*` — moved files (not copied)
- `jobs/<job>/candidates/<id>/interactions.md` — initialized candidate dossier (chronological log)

Interface
- `python workers/candidate_intake/main.py --job <job> [--dry-run]`

ID Generation
- Candidate ID slug format: `<roleCode>-<nameSlug>-<yyyymmdd>-<shortid>`
  - `roleCode`: provided via `--job` mapping or metadata
  - `nameSlug`: slugified from metadata or best-effort from filename
  - `yyyymmdd`: from submission date (metadata) or file mtime
  - `shortid`: 6-char base32 to avoid collisions

Tonight Milestones
- Scan `inbox_drop/` and detect application bundles (multi-file)
- Quick-check validation: ensure at least one resume-like file
- Move (not copy) candidate files into `jobs/<job>/candidates/<id>/raw/`
- Create `interactions.md` with initial entry (timestamp, source, files)
- Leave unqualified files in `inbox_drop/` (do not move)

Definition of Done (Night 1)
- For each valid bundle: candidate directory created, files moved, `interactions.md` exists and includes file list and provenance
- Supports `--dry-run` (no filesystem writes; logs planned actions)
- Idempotent for already-moved bundles (detects and skips)

Dependencies
- Records/Storage layout (see workers/records_storage.md)

Bundle Detection
- Group files by basename prefix and temporal proximity (<= 2 minutes)
- EML parsing: extract attachment list; treat the .eml + attachments as a single bundle
- Prefer metadata.json for name/email/source/role_code when present
- Conservative grouping: avoid merging across clearly different names/subjects; fallback to single-file bundles

Risks & Mitigations
- False grouping across candidates → use time window + filename similarity + optional LLM later
- Missing names → derive from resume text later (parser stage); tonight: placeholder `unknown`
- Collisions → add `shortid`

Checklist (Night 1)
- [ ] Scan inbox and identify bundles
- [ ] Heuristic quick-check for resume presence
- [ ] Generate candidate ID
- [ ] Create candidate dir structure
- [ ] Move files (atomic), write interactions.md
- [ ] Dry-run works and logs planned moves

Paths
- `inbox_drop/`
- `jobs/<job>/candidates/<id>/{raw,parsed,outputs}`

Integration Points
- Resume Parser consumes `raw/` files next
- Pipeline Orchestrator CLI calls this first (Night 1)

Notes
- Gmail API Intake will write to `inbox_drop/` later (Week 2); this worker remains source-agnostic
