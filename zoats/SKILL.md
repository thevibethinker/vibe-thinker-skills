---
name: zoats
description: Safe, archived Skill wrapper for the former standalone ZoATS applicant-tracking-system repo. Use when inspecting, packaging, validating, or exporting ZoATS as a reusable Zo skill scaffold; do not install live routes or run candidate/employer workflows on V's Zo without explicit approval.
compatibility: Created for Zo Computer
metadata:
  author: va.zo.computer
  source_repo: https://github.com/thevibethinker/ZoATS
  source_commit: c71739429bfb5439db259b3a9d4967da37f923ba
  migration_status: pending-repo-deletion-verification
---

# ZoATS Skill

ZoATS is preserved here as a reusable Skill package migrated from the former dedicated private repo `thevibethinker/ZoATS`.

## Current Status

- The dedicated GitHub repo is **not deleted**.
- This Skill is a local, sanitized migration target for verification.
- ZoATS should **not** be run as a live ATS on V's Zo by default.
- Live zo.space routes from the old scaffold were removed separately before this migration.

## Safety Rules

1. Do not provision `/careers`, `/api/zoats/*`, or other public routes unless V explicitly asks.
2. Do not send emails, process real candidates, or write external state unless V explicitly authorizes that action.
3. Treat `jobs/` contents as fixtures/examples only. Real hiring data does not belong in the skill source tree.
4. Keep runtime settings out of source. Use `config/settings.example.json` as the template; local runtime config should be generated outside committed source.
5. Before exporting publicly, run a redaction scan and remove any private employer/candidate examples.

## Useful Commands

```bash
# Inspect package shape
python3 Skills/zoats/scripts/verify_skill_package.py

# Run unit tests without live external effects
pytest Skills/zoats/tests

# Inspect original repo migration metadata
cat Skills/zoats/references/migration/source-manifest.json
```

## Important Paths

- `references/original-repo-readme.md` — original repo README preserved as reference.
- `references/migration/source-manifest.json` — source repo, commit, exclusions, deletion status.
- `scripts/` — installation/provisioning helpers. Use cautiously; some helpers can create zo.space routes.
- `space-routes/` — template route sources, retained for packaging/export only.
- `tests/` — package/test harness.

## Deletion Gate

Only delete or archive the dedicated GitHub repo after verifying:

- `Skills/zoats/SKILL.md` exists and parses as a valid skill.
- The copied tree includes the expected source, docs, schemas, workers, tests, and route templates.
- Private/runtime files were excluded.
- Tests or import checks pass to the level expected for a preserved package.
- V explicitly approves the repo deletion/archive step.
