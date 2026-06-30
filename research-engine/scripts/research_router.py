#!/usr/bin/env python3
"""Portable Research Router for standalone Research Engine installs.

Routes a research topic to a deterministic workspace path under Research/.
The script is intentionally stdlib-only and does not require N5 core files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def workspace_root() -> Path:
    """Return the active Zo workspace root."""
    return Path(os.environ.get("ZO_WORKSPACE", "/home/workspace")).resolve()


def research_root() -> Path:
    """Return the active Research root."""
    return Path(os.environ.get("RESEARCH_ROUTER_ROOT", str(workspace_root() / "Research"))).resolve()


def today() -> str:
    """Return the current UTC date for frontmatter."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def slugify(value: str, *, fallback: str = "research") -> str:
    """Convert text to a filesystem-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (slug or fallback)[:80].strip("-") or fallback


def first_readme_paragraph(path: Path) -> str:
    """Extract the first non-heading paragraph after optional frontmatter."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    in_frontmatter = False
    seen_frontmatter_start = False
    for line in lines:
        stripped = line.strip()
        if stripped == "---" and not seen_frontmatter_start:
            in_frontmatter = True
            seen_frontmatter_start = True
            continue
        if stripped == "---" and in_frontmatter:
            in_frontmatter = False
            continue
        if in_frontmatter or not stripped or stripped.startswith("#"):
            continue
        return stripped
    return ""


def existing_categories(root: Path) -> list[dict[str, str]]:
    """List existing Research category folders."""
    categories: list[dict[str, str]] = []
    if not root.exists():
        return categories
    for item in sorted(root.iterdir(), key=lambda p: p.name):
        if not item.is_dir() or item.name.startswith(".") or item.name in {"_engine", "repos"}:
            continue
        readme = item / "README.md"
        description = first_readme_paragraph(readme) if readme.exists() else ""
        categories.append({
            "slug": item.name,
            "path": str(item),
            "description": description or f"Research related to {item.name.replace('-', ' ')}",
        })
    return categories


def classify(topic: str, categories: list[dict[str, str]]) -> dict[str, Any]:
    """Classify topic using deterministic keyword fallback."""
    topic_lower = topic.lower()
    mappings = {
        "market-intel": ["competitor", "market", "analysis", "due diligence", "diligence", "company", "startup", "industry", "investor", "fund"],
        "people": ["person", "founder", "candidate", "executive", "profile", "bio", "linkedin"],
        "consumer-tech": ["glasses", "ring", "device", "gadget", "hardware", "phone", "watch", "earbuds", "headphones", "smart"],
        "productivity": ["workflow", "productivity", "tool", "app", "software", "automation"],
        "health": ["health", "supplement", "nutrition", "fitness", "medical", "wellness"],
    }
    existing = {c["slug"] for c in categories}
    for category, keywords in mappings.items():
        if any(keyword in topic_lower for keyword in keywords):
            return {
                "matches_existing": category in existing,
                "category_slug": category,
                "category_description": f"Research related to {category.replace('-', ' ')}",
                "reasoning": f"Matched deterministic keywords for {category}",
            }
    if categories:
        return {
            "matches_existing": True,
            "category_slug": categories[0]["slug"],
            "category_description": categories[0]["description"],
            "reasoning": "No keyword match; used first existing category as conservative fallback",
        }
    return {
        "matches_existing": False,
        "category_slug": "general",
        "category_description": "General research and investigations",
        "reasoning": "No existing category or keyword match found",
    }


def write_readme(path: Path, title: str, description: str) -> None:
    """Create a README.md with required frontmatter if missing."""
    readme = path / "README.md"
    if readme.exists():
        return
    date = today()
    content = "\n".join([
        "---",
        f"created: {date}",
        f"last_edited: {date}",
        "version: 1.0",
        "provenance: research-engine-router",
        "---",
        "",
        f"# {title}",
        "",
        description,
        "",
    ])
    readme.write_text(content, encoding="utf-8")


def route_research(topic: str, *, create: bool = False, custom_slug: str | None = None) -> dict[str, Any]:
    """Route a topic to a canonical Research category/item path."""
    root = research_root()
    categories = existing_categories(root)
    classification = classify(topic, categories)
    category_slug = slugify(str(classification["category_slug"]), fallback="general")
    category_path = root / category_slug
    item_slug = slugify(custom_slug or topic, fallback="research-item")
    item_path = category_path / item_slug
    result: dict[str, Any] = {
        "topic": topic,
        "category": category_slug,
        "category_path": str(category_path),
        "item_slug": item_slug,
        "item_path": str(item_path),
        "is_new_category": not bool(classification.get("matches_existing")),
        "reasoning": classification.get("reasoning", ""),
        "router": "Skills/research-engine/scripts/research_router.py",
    }
    if create:
        if not category_path.exists():
            category_path.mkdir(parents=True, exist_ok=True)
            write_readme(
                category_path,
                category_slug.replace("-", " ").title(),
                str(classification.get("category_description") or f"Research related to {category_slug.replace('-', ' ')}"),
            )
            result["created_category"] = True
        if not item_path.exists():
            item_path.mkdir(parents=True, exist_ok=True)
            result["created_item"] = True
    return result


def emit_text(result: dict[str, Any]) -> None:
    """Print a human-friendly routing result."""
    print(f"Category: {result['category']}")
    print(f"Item path: {result['item_path']}")
    if result.get("is_new_category"):
        print(f"Note: New category (reason: {result['reasoning']})")
    if result.get("created_category"):
        print("Created category directory")
    if result.get("created_item"):
        print("Created item directory")


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Route research artifacts to canonical paths")
    parser.add_argument("topic", help="Research topic or description")
    parser.add_argument("--create", action="store_true", help="Create directories if they do not exist")
    parser.add_argument("--slug", help="Custom slug for the research item")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args(argv)
    try:
        result = route_research(args.topic, create=args.create, custom_slug=args.slug)
    except OSError as exc:
        print(f"research_router error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        emit_text(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
