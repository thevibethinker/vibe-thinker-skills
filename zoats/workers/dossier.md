# Candidate Dossier Generator (Worker)
Status: Draft | Owner: TBA

Purpose
- Produce human-readable summary for decisioning.

Inputs
- jobs/<job>/candidates/<id>/outputs/scores.json
- jobs/<job>/candidates/<id>/outputs/quick_test.json
- jobs/<job>/candidates/<id>/parsed/text.md
- jobs/<job>/candidates/<id>/parsed/fields.json

Outputs
- jobs/<job>/candidates/<id>/outputs/candidate.md
- jobs/<job>/candidates/<id>/outputs/candidate.json (rollup)

Interface
- `python workers/dossier/main.py --job <job> --candidate <id> --dry-run`

Tonight Milestones
- Concise MD with pass/fail, rationale, and next-questions placeholder

Definition of Done (Night 1)
- candidate.md present, includes key data and rationale

Dependencies
- Scoring Engine

Risks & Mitigations
- Overly long output → keep concise sections and tables

Checklist (Night 1)
- [ ] Load inputs
- [ ] Compose MD summary
- [ ] Emit MD and JSON rollup
- [ ] Verify files exist

Paths
- jobs/<job>/candidates/<id>/outputs/

Integration Points
- Pipeline CLI aggregates a job summary

Notes
- Future: .sheet.json export
