---
name: prompt-to-skill
description: |
  Convert complex prompts into reusable skills. Assess whether a prompt should become a skill,
  then scaffold a cleaner starter structure with stronger defaults and less template slop.
compatibility: Created for Zo Computer
metadata:
  author: thevibethinker
  version: "1.0"
---

# Prompt to Skill

## Overview

This skill helps you decide when a prompt has become complicated enough to deserve its own skill, then gives you a better starter structure to build from.

The goal is not just to create folders. The goal is to turn an overgrown prompt into something another person — or a future version of you — can actually understand, route into, and maintain.

## Quick Start

```bash
# Assess a prompt for conversion eligibility
python3 Skills/prompt-to-skill/scripts/assess.py "Prompts/MyPrompt.prompt.md"

# Scaffold a new skill with stronger default files
python3 Skills/prompt-to-skill/scripts/scaffold.py my-new-skill

# Optionally set the author field in generated frontmatter
python3 Skills/prompt-to-skill/scripts/scaffold.py my-new-skill --author your-handle.zo.computer
```

## When to Use This Skill

Use this skill when a prompt is doing too much and would be clearer as a reusable capability.

Good candidates usually:
- have multiple phases or decision points
- reference scripts, tools, files, or external systems
- require structured outputs or repeatable setup
- need durable docs instead of conversational context
- are likely to be reused, delegated, or shared

## What the Scaffold Generates

The scaffold creates a stronger starter package than a bare placeholder:
- `SKILL.md` with a real structure and a clearer acceptance bar
- `README.md` for maintainer-facing context and first edits
- `scripts/main.py` as a working example CLI entrypoint
- `references/NOTES.md` for deeper implementation details
- `assets/.gitkeep` when static resources are needed later

This is intentionally still a starter. You should replace the generic example behavior with the real workflow before publishing.

## Eligibility Criteria

The assessment script evaluates prompts based on:
- **Length**: 200+ lines suggests rising complexity
- **Script references**: `python3`, `bun`, or `N5/scripts/` usage
- **Phase structure**: multiple steps or workflow stages
- **Schema requirements**: JSON/YAML output specifications
- **Prompt references**: dependencies on other prompts or skills
- **File operations**: repeated file manipulation or transforms
- **Code blocks**: embedded logic that should probably live elsewhere

**Scoring thresholds:**
- **15+**: strong conversion candidate
- **8-14**: convert if reuse/maintenance pain is real
- **Below 8**: probably keep it as a prompt

## Recommended Conversion Process

1. **Assess** the prompt to see whether it has enough complexity to justify a skill.
2. **Decide the boundary**: what belongs in docs, scripts, references, and assets?
3. **Scaffold** the skill with a usable starter structure.
4. **Extract** reusable logic from the prompt into files with clear roles.
5. **Tighten** the docs so routing and prerequisites are obvious.
6. **Test** the quick start and one real example workflow.
7. **Replace or slim** the original prompt so it points to the new skill instead of duplicating it.

## Usage

### Assessment

```bash
# Basic assessment
python3 Skills/prompt-to-skill/scripts/assess.py "Prompts/MyPrompt.prompt.md"

# JSON output for scripting
python3 Skills/prompt-to-skill/scripts/assess.py "Prompts/MyPrompt.prompt.md" --json
```

### Scaffolding

```bash
# Create a new skill in the default Skills/ directory
python3 Skills/prompt-to-skill/scripts/scaffold.py my-skill-name

# Create in a custom base directory
python3 Skills/prompt-to-skill/scripts/scaffold.py my-skill-name --base /path/to/directory

# Set a better author value in generated frontmatter
python3 Skills/prompt-to-skill/scripts/scaffold.py my-skill-name --author your-handle.zo.computer
```

## Quality Bar for the Generated Skill

Before calling the scaffolded result reusable, make sure:
- the description clearly says what the skill does and when to use it
- the quick start actually works
- required secrets, integrations, and runtime assumptions are explicit
- examples contain no private names, paths, or tokens
- the file reads like instructions, not leftover brainstorming

## Implementation Notes

- Skill names must be lowercase with single hyphen separators
- The scaffold is designed to reduce blank-template drift, not eliminate editing entirely
- If a skill does not need code, remove `scripts/` rather than keeping dead starter files
- If a skill grows long, move detailed implementation notes into `references/` rather than bloating `SKILL.md`
