# ZoATS Soft Product Roadmap (Post-Night-1)

Status: Living document; updated by orchestrator.

## Themes
- Reliability & Scale
- Better Signals (AI Fluency, semantics)
- Founder Experience (onboarding/activation)
- Governance & Fairness
- Portability & Deployability

## 1) Onboarding & Activation
- Guided setup wizard (CLI) to connect Gmail, select job(s), seed founder notes, generate initial Hiring POV file
- Environment checks (python deps, tesseract optional, permissions)
- Create skeleton: jobs/<job>/, default rubric template, sample fixtures
- Last-mile actions: set config, paths, command shortcuts, schedule status checks

## 2) Governance / Ethics
- Ethics & Principles file (see docs/ETHICS_AND_PRINCIPLES.md) that governs system behavior
- Candidate-time policy; recommendations to compensate for paid tasks
- Data handling: PII, retention, audit trail, redaction
- Fairness checks in scoring; bias audits

## 3) Email Intake (Gmail)
- Gmail API integration with label filters, thread de-dup, attachment extraction
- Metadata extraction from email body/signatures; auto-tag job
- Error handling, retries, idempotency
- **Architecture:** Split into Gmail API Intake (polls Gmail → inbox_drop/) and Candidate Intake Processor (inbox_drop/ → candidates/)

## 3.5) Candidate Dossier Evolution
- Living `interactions.md` file per candidate that grows over time
- Track chronological interactions: emails, video calls, interview notes
- Status changes and decision points with timestamps
- Integration with email intake and future video/meeting intelligence
- Becomes comprehensive candidate history and decision audit trail


## 4) Resume Parser Enhancements
- OCR fallback (tesseract) for image-only PDFs; language detection
- Structured section detection (Experience/Education/Skills)
- Improved contact info extraction, links (LinkedIn/GitHub)
- Parsing quality metrics; caching and dedupe

## 5) Rubric Generator Enhancements
- Role templates & library; versioning and diff
- Interactive Socratic flow with save/resume
- Add "loop_length" attribute where relevant and an "ai_fluency" criterion
- Import/export rubric JSON; provenance trail

## 6) Scoring Engine Enhancements
- Embedding/semantic similarity checks (configurable)
- LLM-assisted scoring with deterministic guardrails and traces
- Calibration workflows; weight tuning; explainability
- Fairness constraints; threshold tuning; cohort analysis

## 7) Dossier & Output
- Export to PDF and .sheet.json; shareable links
- Email/send to founder; feedback capture loop

## 8) Pipeline & Ops
- Concurrency, checkpoints, resume-on-failure
- Detailed logging, metrics, simple UI later
- Config profiles per environment; cloud storage mapping

## 9) Records/Storage
- Encryption at rest (optional), redaction utilities
- Retention policies and archival commands

## 10) Testing & QA
- Golden files, regression tests, synthetic data generator
- Performance budgets and alerts

## 11) Candidate Dossier Evolution (interactions.md)
- Living record of all candidate interactions in `jobs/<job>/candidates/<id>/interactions.md`
- Initial content: Email metadata, timestamp, attachments list
- Future appends: Email correspondence tracking, video call notes and recordings, interview feedback, status changes and decision points
- Becomes the comprehensive "candidate dossier" that grows throughout the hiring process
- Format: Markdown with chronological entries
- Integration: Dossier Generator reads/appends to this file

---

Appendix: Sources of planned items
- Night-1 plans in WORKERS_PLAN.md
- Orchestrator thread con_R3Mk2LoKx4AEGtYy (active), planning thread con_E5iuQnmFOeZcOUDX (archived), and rubric worker con_Sq70IglhvzX4GJE3
