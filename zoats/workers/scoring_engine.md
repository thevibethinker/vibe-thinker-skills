# Scoring Engine (Worker)
Status: Draft | Owner: TBA

Purpose
- Apply rubric to parsed resume; compute per-criterion scores and quick-test gate.

Inputs
- jobs/<job>/rubric.json
- jobs/<job>/deal_breakers.json
- jobs/<job>/candidates/<id>/parsed/text.md
- jobs/<job>/candidates/<id>/parsed/fields.json

Outputs
- jobs/<job>/candidates/<id>/outputs/scores.json
- jobs/<job>/candidates/<id>/outputs/quick_test.json

Interface
- `python workers/scoring/main.py --job <job> --candidate <id> --dry-run`

Tonight Milestones
- Deterministic rules for deal-breakers
- Simple keyword/phrase matching per criterion

Definition of Done (Night 1)
- quick_test.json shows pass/flag/fail with reasons
- scores.json includes per-criterion scores and total

Dependencies
- Rubric Generator, Resume Parser

Risks & Mitigations
- False positives/negatives → keep transparent rationale in output

Checklist (Night 1)
- [ ] Load rubric and inputs
- [ ] Compute deal-breaker gate
- [ ] Score criteria heuristically
- [ ] Write outputs and verify

Paths
- jobs/<job>/

Integration Points
- Dossier uses these outputs

Notes
- Later: pluggable scoring modules
