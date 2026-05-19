---
name: startup-memo-generator
description: Generate gated, analytics-enabled founder memo pages for investors, customers, and vendors on zo.space. Use when creating or managing memo rooms from Google Docs, Markdown, text, PDFs, data, or images with strict source fidelity, stakeholder access controls, replay analytics, central reusable content blocks, and private admin/CLI operations.
compatibility: Created for Zo Computer
metadata:
  author: va.zo.computer
  version: "0.1.0"
---

# Startup Memo Generator

Build gated, design-forward memo pages on zo.space while preserving source material and tracking stakeholder engagement.

## Required Dependencies

Before using this skill, verify these skills exist on the target Zo:

- `Skills/teach-impeccable/SKILL.md`
- `Skills/frontend-design/SKILL.md`
- `Skills/clarify/SKILL.md`
- `Skills/arrange/SKILL.md`
- `Skills/typeset/SKILL.md`
- `Skills/polish/SKILL.md`
- `Skills/adapt/SKILL.md`
- `Skills/harden/SKILL.md`

Run `teach-impeccable` first for the target company/project so `.impeccable.md` exists and reflects the founder's local brand context.

## Core Rules

- Do not rewrite source wording unless the user explicitly authorizes rewriting.
- Preserve a generation-time source snapshot before rendering a memo.
- Keep private runtime data outside `Skills/`, defaulting to `N5/data/startup-memo-generator/`.
- Use one route per memo: `/investor-memos/<human-slug>-<uuidv7>` or `/customer-memos/<human-slug>-<uuidv7>`.
- Use 4-digit stable PINs per email until reset.
- Use Pulse only for major template/functionality overhauls, not ordinary memo generation.
- Show a configurable analytics disclosure on memo pages.

## Quick Start

```bash
python3 Skills/startup-memo-generator/scripts/memo.py doctor
python3 Skills/startup-memo-generator/scripts/memo.py setup --org "ACME Inc" --gmail-sender "founder@acme.example"
python3 Skills/startup-memo-generator/scripts/memo.py create-memo --title "Seed Memo" --category investor-memos --source /path/to/source.md
python3 Skills/startup-memo-generator/scripts/memo.py add-stakeholder --memo-id <memo-id> --email investor@example.com --name "Investor Name" --role investor
python3 Skills/startup-memo-generator/scripts/memo.py reset-pin --memo-id <memo-id> --email investor@example.com
python3 Skills/startup-memo-generator/scripts/memo.py email-pin --memo-id <memo-id> --email investor@example.com --pin <visible-pin-from-reset>
python3 Skills/startup-memo-generator/scripts/memo.py gate --memo-id <memo-id>
python3 Skills/startup-memo-generator/scripts/memo.py generate-route-bundle --memo-id <memo-id>
```

Use `--dry-run` on write commands to preview changes.

## Workflow

1. **Install check**: run `doctor` and resolve missing dependencies.
2. **Setup**: configure org name, Gmail sender, runtime data path, replay retention, and disclosure text.
3. **Create memo**: snapshot the source, create memo/version metadata, and generate the intended route path.
4. **Manage stakeholders**: add, approve, block, reset PINs, or revoke access.
5. **Email access**: generate the email body with `email-pin`, then send through the target Zo's Gmail integration from the designated sender.
6. **Generate route bundle**: use templates in `assets/zo-space/` as the basis for zo.space page/API routes.
7. **Run gates**: hard-block dead links, broken auth configuration, missing source snapshot, and broken route rendering; warn on PII/PR-sensitive content.
8. **Publish**: create/update zo.space routes only after gates pass.
9. **Review analytics**: inspect local JSONL logs and private admin dashboard.

## Access Modes

- `whitelist-only`: approved stakeholders only.
- `email+pin`: approved stakeholder enters email plus stable PIN.
- `pin-only-with-email-capture`: unknown viewers can enter email and PIN, receive the default version, and appear as `candidate` in admin.

Revoking or blocking a stakeholder must invalidate active sessions for that email.

## Data Model

Read `references/data-model.md` before modifying schemas or storage behavior.

Runtime data should be outside the skill package:

```text
N5/data/startup-memo-generator/
├── config.json
├── memos/
├── sources/
├── analytics/
├── replay/
└── audit.jsonl
```

## Templates

zo.space route templates live in `assets/zo-space/`:

- `memo-page.tsx`
- `admin-page.tsx`
- `api-auth.ts`
- `api-content.ts`
- `api-analytics.ts`

These are templates, not active routes. Adapt them through Zo Space route tools when publishing to a specific Zo.

Generated route bundles include a `manifest.json` with suggested zo.space paths.

## Distribution

The working skill lives in `Skills/startup-memo-generator/`. Use `Skills/skill-export/` for a public-safe export bundle after license-chain verification and sanitization.

Before public publication, verify:

- Impeccable license and attribution obligations.
- Upstream frontend-design provenance.
- No runtime data inside the package.
- No hardcoded private email, org, source, PIN, or analytics data.
