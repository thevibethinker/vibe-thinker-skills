# Onboarding & Activation (Worker)
Status: Draft | Owner: TBA

Purpose
- Last-mile setup on a brand-new Zo: ask questions, request actions, and generate the initial configuration and job scaffold.

Inputs
- User answers (CLI prompts or flags)
- ZoATS/ path

Outputs
- config/settings.json (populated)
- jobs/<job>/{job-description.md,rubric.json (template),founder-notes.md}
- hiring_pov.md (initial POV file)
- connectivity status report (Gmail optional)

Interface
- `python workers/onboarding/main.py --job <job> [--connect-gmail] [--seed-demo] --dry-run`

Tonight Milestones (Post-Night-1)
- Not in Night 1 scope; part of soft roadmap

Definition of Done
- Wizard completes without errors and writes all expected files; verifies environment

Dependencies
- Records/Storage worker

Risks & Mitigations
- Over-scoping; keep the MVP to file generation and validation first

Checklist
- [ ] Prompt for job name and basics
- [ ] Write settings.json and job scaffold
- [ ] Optionally connect Gmail
- [ ] Verify environment (deps)

Paths
- config/, jobs/<job>/

Integration Points
- Seeds rubric generator; prepares inputs for email intake

Notes
- Aligns with governance in docs/ETHICS_AND_PRINCIPLES.md
