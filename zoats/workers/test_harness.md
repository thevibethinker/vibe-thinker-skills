# Test Harness (Worker)
Status: Draft | Owner: TBA

Purpose
- Provide a minimal smoke test over the end-to-end pipeline.

Inputs
- fixtures/job-sample/*
- fixtures/resumes/*

Outputs
- logs/test_smoke/*.log
- PASS/FAIL summary

Interface
- `python tests/smoke.py --job demo --dry-run`

Tonight Milestones
- Seed demo job and 2–3 resumes; verify outputs exist and are non-empty

Definition of Done (Night 1)
- Smoke test runs to completion with expected files present

Dependencies
- All workers minimal implementations

Risks & Mitigations
- Over-testing → only existence/size checks tonight

Checklist (Night 1)
- [ ] Seed fixtures
- [ ] Run pipeline
- [ ] Check outputs
- [ ] Emit summary

Integration Points
- Orchestrator uses this to validate Night 1

Notes
- Expand later to structured assertions
