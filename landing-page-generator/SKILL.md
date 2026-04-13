---
name: landing-page-generator
description: Create self-contained landing-page specs and outputs with bundled design foundations, anti-slop guardrails, reusable templates, and target file-structure guidance. Portable across repos with no dependency on N5 or other skills.
compatibility: Created for Zo Computer
metadata:
  author: thevibethinker
created: 2026-04-13
last_edited: 2026-04-13
version: 1.0
provenance: con_HfUUximXBPXjU7iq
---

# Landing Page Generator

This is the standalone version of the landing-page skill. It is intentionally self-contained:

- no dependency on `frontend-design`
- no dependency on `teach-impeccable`
- no dependency on `N5/` paths, workspace memory, or private repo structure
- all operating references live inside this skill directory

Use this when you want a portable landing-page bundle that can be dropped into another repo and still work as a complete playbook.

## Bundled Skill Surface

Use only these local files when running the skill:

- `references/design-foundations.md` for design standards
- `references/anti-patterns.md` for anti-slop checks
- `references/target-file-structures.md` for target-specific output shapes
- `templates/_TEMPLATE.yaml` for new template authoring
- `templates/minimal-saas.yaml` and `templates/warm-consulting.yaml` for reusable starting points

If you need something that is not covered by the files above, add it to this skill instead of routing to another skill.

## What This Skill Produces

The skill can generate:

- a landing-page plan
- a content and section outline
- one or more visual directions
- final code or markup for a selected target
- reusable YAML templates captured from successful outputs

Supported targets:

- standalone HTML
- React + Tailwind
- Next.js App Router
- Zo.space page routes

See `references/target-file-structures.md` for the exact expected shape of each target.

## Inputs It Accepts

### Vibes Only

Example:

> "A confident landing page for an AI recruiting platform."

Behavior:

- extract likely audience, outcome, and tone
- ask clarifying questions if the brief is too underspecified
- if answers are unavailable, proceed with explicit assumptions

### Guided Brief

Example:

> "Healthcare workflow product, clinic managers, calm but authoritative, CTA is Book a demo."

Behavior:

- treat the brief as primary truth
- fill only the missing structural gaps
- optimize hierarchy, proof, and section flow

### Template-Led

Example:

> "Use warm-consulting with a forest accent for a GTM advisory shop."

Behavior:

- load `templates/<name>.yaml`
- preserve its layout and tone logic
- override only the fields requested by the user

## Required Clarification Pass

Before generating, capture or infer these six items:

1. who the page is for
2. what the offer is
3. what action the page should drive
4. what proof exists
5. what tone the page should convey
6. what output target to generate

If two or more are missing, ask a short clarification round first. If the user wants speed over back-and-forth, proceed with assumptions and label them clearly.

## Core Workflow

### 1. Normalize the brief

Convert the request into this internal shape:

- audience
- offer
- primary CTA
- supporting proof
- tone
- constraints
- target
- template, if any

### 2. Pick a design direction

Read `references/design-foundations.md` and commit to one clear aesthetic point of view. Do not drift into generic SaaS defaults.

Good direction labels:

- warm expert
- technical precision
- editorial authority
- premium minimal
- bold challenger

### 3. Check the anti-slop list

Read `references/anti-patterns.md` before producing output. If the draft starts to look like a generic AI landing page, change course before continuing.

### 4. Select page structure

Use either:

- the structure embedded in the chosen template, or
- a custom sequence driven by the brief

Do not force every page into hero -> feature grid -> testimonials -> CTA if the offer needs a different narrative.

### 5. Generate the target output

Match the output to the target described in `references/target-file-structures.md`.

### 6. Run the quality gate

Before calling the page complete, verify:

- the offer is obvious above the fold
- the CTA is specific
- the proof feels concrete
- the hierarchy is readable on mobile
- the aesthetic feels intentional, not templated
- the code or markup matches the target structure

## Multi-Variant Mode

When the request asks for variants, generate distinct directions rather than superficial recolors.

Vary at least two of:

- layout composition
- typography character
- proof presentation
- palette treatment
- section ordering

For each variant, label:

- concept name
- emotional tone
- why it fits the brief

## Template Rules

When using a bundled template:

1. load the YAML
2. treat `sections`, `palette`, `typography`, and `style_notes` as the governing frame
3. let user-provided content override template filler
4. preserve the template's visual logic unless explicitly asked to change it

When capturing a new template:

1. copy `templates/_TEMPLATE.yaml`
2. fill every required field
3. document source and intended use
4. include style notes detailed enough that another agent can recreate the feel

## Output Contract

Every run should return, explicitly or implicitly:

- assumptions used
- selected design direction
- chosen section sequence
- target output
- any template used or created

If delivering code, make sure the code is directly usable in the declared target structure.

## Recommended Response Shape

For planning requests:

1. assumptions
2. design direction
3. section outline
4. target file structure

For build requests:

1. assumptions
2. short rationale
3. final code or markup
4. any setup notes specific to the target

## Examples

### Simple

> "Create a landing page for a recruiting copilot for founders."

### Template-driven

> "Use minimal-saas for a developer analytics tool. Output React + Tailwind."

### Variant request

> "Generate 3 directions for a fractional CMO landing page: one editorial, one warm, one technical."

## Non-Goals

This skill does not assume:

- a specific workspace layout
- an orchestration system
- a private memory layer
- another skill being installed

If you find yourself about to say "also load another skill," stop and move that missing guidance into this package instead.
