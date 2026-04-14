---
created: 2026-04-14
last_edited: 2026-04-14
version: 1.0
provenance: con_RgWWKAwbg46pECpk
---

# Portable Skill Quality-Bar Audit

## Summary

- Audited the retained standalone skill set in `/tmp/vibe-thinker-skills-work`.
- Applied safe, non-breaking doc/frontmatter fixes to 13 skills plus the repo `README.md`.
- Main issues found: stale metadata, slug/frontmatter mismatches, private placeholders in public docs, hardcoded conversation paths, outdated tool references, and a few skills whose runtime shape is still tightly coupled to a specific Zo workspace.

## Repo-Level Notes

- Updated `README.md` to set a clearer public portability bar: each skill should declare prerequisites, message-sending behavior, and runtime assumptions.
- Verification target S1 is clean at the doc layer for the retained skills: no `Careerspan`, `Simovian`, `zo-skills`, `vibe-thinker-zo-skills`, or `<YOUR_...>` placeholders remain in retained `SKILL.md` / `README.md` files.

## Skill Status

| Skill | Disposition | Safe fixes applied | Remaining flags |
|---|---|---|---|
| `booking-metadata-calendar` | doc-fixed | Added explicit note that persistence assumes `N5/data/booking_metadata/`. | Script still hardcodes an N5-style storage layout; making persistence path configurable would require code changes. |
| `branded-pdf` | doc-fixed | Added explicit `reportlab` prerequisite and install command. | No major portability blocker after docs fix. |
| `calendar-intelligence` | portable-with-prereqs + flagged | No doc edit needed. | Strong Zo coupling remains: depends on connected calendar/email integrations, optional LinkedIn local connection, `create_agent`, and a companion `zo-linkedin` skill path outside this repo. |
| `claude-code-window-primer` | portable-with-prereqs | No doc edit needed. | Depends on Zo API identity, a Claude Code subscription, and the specific model/window behavior remaining valid. |
| `debono-thinking-hats` | doc-fixed | Replaced stale `zo-skills` author metadata. | No major portability blocker. |
| `frontend` | portable | No doc edit needed. | Broad design skill; no direct portability blocker found in the skill doc. |
| `frontend-design` | doc-fixed | Replaced stale `n5os-ode` author metadata. | No major portability blocker. |
| `frontend-design-anthropic` | doc-fixed | Fixed imported metadata wording and corrected the skill `name` to match the folder slug. | No major portability blocker after frontmatter fix. |
| `gamma` | doc-fixed | Added Gamma account/API/credits prerequisites and corrected secret-placement guidance. | Paid API dependency remains, but it is now explicit rather than implicit. |
| `meme-factory` | doc-fixed | Added missing `compatibility` field. | No major portability blocker. |
| `prompt-to-skill` | doc-fixed + flagged | Added missing frontmatter metadata and clarified that scaffold output intentionally contains `TODO` markers. | The generated template assets and scaffold script still emit TODO-laden starter files; improving publish-readiness needs a broader scaffold redesign. |
| `rapid-context-extractor` | doc-fixed + flagged | Replaced hardcoded conversation path example; removed V-specific semantic-memory wording; clarified ingestion helper is optional. | Advanced mode still assumes optional N5 semantic memory and content-ingest helpers for the full experience. |
| `remotion` | portable-with-prereqs + flagged | No doc edit needed. | Runtime assumes Zo-style `Sites/` placement plus Node/Bun package installation; making it repo-layout-agnostic would require code changes. |
| `systematic-debugging` | portable | No doc edit needed. | No major portability blocker found in the skill doc. |
| `text-commute-info` | doc-fixed | Added missing `compatibility`, corrected browser flow (`open_webpage` + `view_webpage`), replaced outdated `create_scheduled_task` guidance with `create_agent`, and made SMS sending explicitly consent-based. | Still depends on browser access to Google Maps and explicit authorization for texting. |
| `text-to-diagram` | doc-fixed | Removed V-specific framing and `<YOUR_GITHUB>` placeholder aesthetic language. | No major portability blocker after doc cleanup. |
| `zo-create-site` | doc-fixed | Corrected the skill `name` to match the folder slug, added missing `compatibility`, and fixed the file-reference example. | Zo-specific by design, but the scope is explicit and acceptable. |

## Flagged Follow-Up Work

### 1. `prompt-to-skill` now has stronger defaults, but can go further

The skill itself is understandable, but its generated outputs still start with TODO-heavy templates. That is acceptable for a maintainer-facing starter, but it misses the stricter portable-skill quality bar for “newcomer can scaffold and immediately understand what remains.”

Recommendation: make the scaffold emit higher-signal placeholder text and better default metadata instead of raw TODO markers.

### 2. `booking-metadata-calendar` and `remotion` are still layout-coupled

Both skills are installable, but they assume a particular Zo workspace structure:

- `booking-metadata-calendar` persists into `N5/data/...`
- `remotion` scaffolds into `Sites/...`

That is fine if the repo stays Zo-first, but if the bar becomes “portable across arbitrary workspace layouts,” these need configurable paths.

### 3. `calendar-intelligence` is portable only inside a fairly complete Zo environment

The skill is well-structured, but it assumes a rich host environment:

- Connected calendar and email integrations
- Optional LinkedIn local connection
- A companion `zo-linkedin` skill path that is not part of this repo
- Agent creation and review loops inside Zo

Recommendation: either ship the missing companion dependency with the repo, or explicitly document this as a Zo-environment skill rather than a generally portable install.

### 4. `rapid-context-extractor` has optional-but-real platform coupling

The core packet-prep flow is portable. The richer experience still assumes optional N5 memory and ingestion helpers. That is acceptable if documented as an enhancement layer, not a baseline guarantee.

Recommendation: consider explicitly labeling the semantic-memory and ingestion steps as “Zo-enhanced mode” in a future pass.

## Bottom Line

The retained set is in materially better shape after this pass. Most skills now meet a reasonable “portable with explicit prerequisites” bar. The main remaining improvement opportunities are `calendar-intelligence`, `prompt-to-skill`, `booking-metadata-calendar`, `remotion`, and the enhanced modes of `rapid-context-extractor`.
