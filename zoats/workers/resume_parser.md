# Resume Parser (Worker)
Status: Complete | Owner: con_nfCwRFobhfzNQgM4

Purpose
- Extract text and basic fields from candidate resumes (PDF/DOCX/MD).

Inputs
- jobs/<job>/candidates/<id>/raw/*.{pdf,docx,md}

Outputs
- jobs/<job>/candidates/<id>/parsed/text.md
- jobs/<job>/candidates/<id>/parsed/fields.json

Interface
- `python workers/parser/main.py --job <job> --candidate <id> --dry-run`

Tonight Milestones
- PDF text via pdfminer.six or pypdf
- DOCX via python-docx
- MD passthrough

Definition of Done (Night 1)
- text.md present and non-empty
- fields.json includes name, email (best-effort), years exp (heuristic)

Dependencies
- Intake output

Risks & Mitigations
- Tricky PDFs → fallback to basic text extraction and log warnings

Checklist (Night 1)
- [x] Detect file type
- [x] Extract text
- [x] Heuristic field extraction
- [x] Verify outputs exist

Paths
- jobs/<job>/candidates/<id>/{raw,parsed}

Integration Points
- Scoring Engine consumes parsed text/fields

Notes
- OCR deferred
