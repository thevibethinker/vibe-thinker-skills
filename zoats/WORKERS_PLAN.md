# ZoATS — Night 1 Workers and Integrated Plans

Status: Draft (orchestrator thread)

---

## Workers Overview

1. Rubric Generator (Worker) — con_Sq70IglhvzX4GJE3 — see workers/rubric.md
2. Candidate Intake Processor (Worker) — con_6eNkFTCmluuGFa4a — see workers/candidate_intake.md
3. Resume Parser (Worker) — see workers/resume_parser.md
4. Scoring Engine (Worker) — see workers/scoring_engine.md
5. Candidate Dossier Generator (Worker) — see workers/dossier.md
6. Pipeline Orchestrator CLI (Glue Worker) — see workers/pipeline_cli.md
7. Records/Storage (Worker) — see workers/records_storage.md
8. Test Harness (Worker) — see workers/test_harness.md
9. Onboarding & Activation (Worker) — see workers/onboarding_activation.md

**Future (Week 2):**
10. Gmail API Intake (Worker) — see workers/gmail_intake.md

---

## 1) Rubric Generator (Worker) — con_Sq70IglhvzX4GJE3
- See: workers/rubric.md
- Purpose: Convert JD + founder reflections into a structured rubric.json with criteria, weights, scoring bands; optionally Socratic flow.
- Inputs: job-description.md (text), founder notes (text/voice→text), optional team notes.
- Outputs: rubric.json, rubric.md (human-readable), deal_breakers.json.
- Interface: `python workers/rubric/main.py --jd jobs/<job>/job-description.md --out jobs/<job>/rubric.json [--interactive | --non-interactive --founder-notes <file>] --dry-run`
- Tonight Milestones:
  - MVP: Non-interactive mode from JD text → rubric.json + rubric.md
  - Interactive Socratic prompts (basic) as optional flag
- Dependencies: none (reads local files)
- Risks: Over-fitting rubric; interactive scope creep → keep minimal bands: Must/Should/Nice, weights sum=100.

## 2) Candidate Intake Processor (Worker) — con_6eNkFTCmluuGFa4a

- Purpose: Process candidate applications from inbox_drop/ staging area; validate, organize, move to candidate directories
- Inputs: inbox_drop/*.{pdf,docx,md,json,eml}
- Outputs: jobs/<job>/candidates/<id>/raw/* (moved files), interactions.md (candidate dossier)
- Interface: `python workers/candidate_intake/main.py --job <job> --dry-run`
- Tonight Milestones: Scan inbox_drop/, generate candidate IDs, quick-check validation, move files, create interactions.md, handle multi-file bundles
- Dependencies: Records/Storage layout
- Risks: Filename collisions → UUID-based IDs; bundle detection accuracy → conservative grouping

**Architecture Note:** Replaces "Email Intake Worker". Gmail API polling moved to separate worker (Week 2). This worker is source-agnostic and processes any files in inbox_drop/.

**Flow:** inbox_drop/ → Candidate Intake Processor → jobs/<job>/candidates/<id>/

## 10) Gmail API Intake (Worker) — DEFERRED TO WEEK 2

- Purpose: Poll Gmail API for applications, download to inbox_drop/ staging area
- Inputs: Gmail API (labels, filters)
- Outputs: inbox_drop/*.{pdf,docx,eml,json}
- Interface: `python workers/gmail_intake/main.py --poll --label "Applications" --dry-run`
- Week 2 Milestones: Gmail auth, label filtering, attachment download, thread de-dup, write to inbox_drop/
- Dependencies: Gmail API setup, Candidate Intake Processor (consumer)

**Architecture Note:** Feeds the intake pipeline; does NOT process candidates. inbox_drop/ is universal staging area for all intake sources (Gmail, web forms, Dropbox, etc.).

**Flow:** Gmail API → Gmail Intake Worker → inbox_drop/ → Candidate Intake Processor

## 3) Resume Parser (Worker)
- See: workers/resume_parser.md
- Purpose: Extract text + basic fields from PDF/DOCX/MD.
- Inputs: candidates/*/raw/*.{pdf,docx,md}
- Outputs: candidates/*/parsed/text.md, parsed/fields.json
- Interface: `python workers/parser/main.py --job <job> --candidate <id> --dry-run`
- Tonight Milestones: PDF via pdfminer.six or pypdf; DOCX via python-docx; MD passthrough.
- Dependencies: Intake output.
- Risks: Edge-case PDFs. Fallback to plaintext OCR deferred.

## 4) Scoring Engine (Worker)
- See: workers/scoring_engine.md
- Purpose: Apply rubric to parsed text; compute scores, flags, quick-test gate.
- Inputs: rubric.json, deal_breakers.json, parsed/text.md, fields.json
- Outputs: scores.json (per-criterion), quick_test.json (pass/flag/fail)
- Interface: `python workers/scoring/main.py --job <job> --candidate <id> --dry-run`
- Tonight Milestones: Deterministic heuristics for deal-breakers; simple keyword/semantic-lite checks; pluggable later.
- Dependencies: Rubric, Parser.
- Risks: Precision; document assumptions in output.

## 5) Candidate Dossier Generator (Worker)
- See: workers/dossier.md
- Purpose: Produce human-readable candidate.md (+ optional .sheet.json later).
- Inputs: scores.json, quick_test.json, parsed/text.md, fields.json
- Outputs: candidate.md, candidate.json (rollup)
- Interface: `python workers/dossier/main.py --job <job> --candidate <id> --dry-run`
- Tonight Milestones: Markdown dossier with rationale, pass/fail, next questions placeholder.
- Dependencies: Scoring.
- Risks: Formatting scope creep → keep concise.

## 6) Pipeline Orchestrator CLI (Glue Worker)
- See: workers/pipeline_cli.md
- Purpose: End-to-end: intake → parse → score → dossier for all candidates in a job.
- Inputs: jobs/<job>/… and ./inbox_drop
- Outputs: Updated candidate directories and summary index jobs/<job>/finalists.md (manual selection tonight)
- Interface: `python pipeline/run.py --job <job> [--from ./inbox_drop] --dry-run`
- Tonight Milestones: Linear pipeline, logs, idempotent re-run.
- Dependencies: All above workers.
- Risks: Error handling; add fail-fast per candidate, continue others.

## 7) Records/Storage (Worker)
- See: workers/records_storage.md
- Purpose: Define portable on-disk layout and utilities.
- Structure:
  - ZoATS/
    - jobs/<job>/{job-description.md,rubric.json,deal_breakers.json,candidates/<id>/{raw,parsed,outputs}}
    - inbox_drop/
    - logs/
    - config/{settings.json}
- Tonight Milestones: Create dirs, write settings.json with minimal config.
- Dependencies: none.
- Risks: Path assumptions across workers.

## 8) Test Harness (Worker)
- See: workers/test_harness.md
- Purpose: Seed sample job + 2-3 sample resumes; run pipeline and verify outputs exist and non-empty.
- Inputs: fixtures/job-sample, fixtures/resumes
- Outputs: test report under logs/
- Interface: `python tests/smoke.py --job demo --dry-run`
- Tonight Milestones: Smoke test: 1 pass, 1 fail, 1 borderline.
- Dependencies: All workers minimal.
- Risks: Over-testing tonight; keep to existence checks.

## 9) Onboarding & Activation (Worker)
- See: workers/onboarding_activation.md
- Purpose: Guided last-mile setup on a new Zo instance; generate initial POV and job scaffold.
- Status: Post-Night-1 (soft roadmap)

---

## Integration Plan (Night 1)

- Start with Records/Storage to scaffold folders
- Implement Rubric Generator (non-interactive)
- Add Intake (file-drop) → Parser → Scoring → Dossier
- Wire Pipeline CLI and run Test Harness on demo job
- Manual selection to produce jobs/<job>/finalists.md

## Check-in Cadence

- Orchestrator checks every 45 min (manually tonight). Use N5 commands where helpful: assign-task, check-worker, review-worker-changes, approve-worker, test-integration (see file 'N5/config/commands.jsonl').

## Notes

- Keep dependencies minimal (pdfminer.six, python-docx). Avoid heavy OCR tonight.
- All scripts must support --dry-run and verify outputs.
