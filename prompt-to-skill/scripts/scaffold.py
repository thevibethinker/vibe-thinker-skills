#!/usr/bin/env python3
"""Scaffold a new skill directory structure with stronger defaults."""

import argparse
import re
from pathlib import Path

DEFAULT_COMPATIBILITY = "Created for Zo Computer"

SKILL_TEMPLATE = '''---
name: {name}
description: |
  {description}
compatibility: {compatibility}
metadata:
  author: {author}
---

# {title}

## What this skill is for

Use this skill when {use_case}.

## What it should contain

A strong skill usually includes:
- a clear decision rule for when to use it
- a short quick-start path that works immediately
- scripts only when automation actually helps
- references for deeper details instead of bloating the main file
- assets only when templates or static resources are genuinely useful

## Quick Start

```bash
python3 Skills/{name}/scripts/main.py --help
```

## Recommended build order

1. Tighten the one-sentence description so someone can route into the skill correctly.
2. Replace the example CLI in `scripts/main.py` with the real entrypoint or remove `scripts/` if the skill is documentation-only.
3. Add one concrete example command or workflow.
4. Move long implementation details into `references/`.
5. Delete any sections that do not help someone use or maintain the skill.

## Minimal acceptance bar

Before publishing or reusing this skill, make sure:
- the description says what it does and when to use it
- the quick start is real
- required accounts, secrets, or integrations are stated explicitly
- examples do not contain private names, paths, or tokens
- the file reads like instructions, not a scratchpad
'''

README_TEMPLATE = '''# {title}

Short version: {description}

## Included files

- `SKILL.md` — main routing and usage instructions
- `scripts/` — automation entrypoints if needed
- `references/` — deeper implementation notes
- `assets/` — templates or static resources

## First improvements to make

1. sharpen the description in `SKILL.md`
2. replace the example CLI in `scripts/main.py`
3. add one real usage example
4. delete anything you do not need
'''

MAIN_SCRIPT_TEMPLATE = '''#!/usr/bin/env python3
"""Example entrypoint for the {name} skill."""

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Starter CLI for the {name} skill. Replace or extend this with real behavior."
    )
    parser.add_argument(
        "--example",
        default="hello",
        help="Example argument to show CLI wiring"
    )
    args = parser.parse_args()

    print("{title} skill starter")
    print(f"example={{args.example}}")
    print("Next step: replace this script with the real skill workflow or remove scripts/ if unnecessary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

REFERENCES_TEMPLATE = '''# Implementation Notes

Use this file for details that would clutter `SKILL.md`, such as:
- API notes
- data contracts
- prompt structure details
- edge cases and failure modes
- setup steps that only maintainers need
'''


def slug_to_title(name: str) -> str:
    return name.replace('-', ' ').title()


def validate_name(name: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name))


def write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n")


def scaffold_skill(name: str, base_path: str = "Skills", author: str = "your-handle.zo.computer") -> bool:
    skill_dir = Path(base_path) / name
    if skill_dir.exists():
        print(f"Error: {skill_dir} already exists")
        return False

    title = slug_to_title(name)
    description = f"Describe what {title} does, what problem it solves, and when someone should reach for it."
    use_case = f"you need {title.lower()} behavior and the workflow is repeatable enough to package"

    (skill_dir / "scripts").mkdir(parents=True)
    (skill_dir / "references").mkdir()
    (skill_dir / "assets").mkdir()

    write_text(
        skill_dir / "SKILL.md",
        SKILL_TEMPLATE.format(
            name=name,
            title=title,
            description=description,
            compatibility=DEFAULT_COMPATIBILITY,
            author=author,
            use_case=use_case,
        ),
    )
    write_text(
        skill_dir / "README.md",
        README_TEMPLATE.format(title=title, description=description),
    )
    write_text(skill_dir / "scripts" / "main.py", MAIN_SCRIPT_TEMPLATE.format(name=name, title=title))
    write_text(skill_dir / "references" / "NOTES.md", REFERENCES_TEMPLATE)
    (skill_dir / "assets" / ".gitkeep").touch()

    print(f"✓ Created {skill_dir}/")
    print("  - SKILL.md")
    print("  - README.md")
    print("  - scripts/main.py")
    print("  - references/NOTES.md")
    print("  - assets/.gitkeep")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new skill with stronger default files")
    parser.add_argument("name", help="Skill name in slug format, e.g. my-skill")
    parser.add_argument("--base", default="Skills", help="Base directory")
    parser.add_argument(
        "--author",
        default="your-handle.zo.computer",
        help="Author metadata to place in SKILL.md"
    )
    args = parser.parse_args()

    if not validate_name(args.name):
        print("Error: name must use lowercase letters/numbers separated by single hyphens")
        return 1

    return 0 if scaffold_skill(args.name, args.base, args.author) else 1


if __name__ == "__main__":
    raise SystemExit(main())
