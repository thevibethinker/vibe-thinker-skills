# Records/Storage (Worker)
Status: Draft | Owner: TBA

Purpose
- Provide portable on-disk layout and utility helpers.

Structure
- ZoATS/
  - jobs/<job>/{job-description.md,rubric.json,deal_breakers.json,candidates/<id>/{raw,parsed,outputs}}
  - inbox_drop/
  - logs/
  - config/{settings.json}

Outputs
- Created directories
- config/settings.json (minimal)

Interface
- `python workers/storage/main.py --init --dry-run`

Tonight Milestones
- Create directory skeleton and write settings.json

Definition of Done (Night 1)
- All directories exist; settings.json created with defaults

Dependencies
- None

Risks & Mitigations
- Path drift → centralize path helpers

Checklist (Night 1)
- [ ] Create dirs
- [ ] Write settings.json
- [ ] Verify existence

Integration Points
- All workers rely on this layout

Notes
- Keep names stable for portability
