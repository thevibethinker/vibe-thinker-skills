#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "assets" / "root"
SYSTEM_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "assets" / "system"


def iter_templates():
    for path in sorted(ROOT_TEMPLATE_DIR.glob("*.md")):
        yield path, path.name
    for path in sorted(SYSTEM_TEMPLATE_DIR.glob("*.md")):
        yield path, str(Path("system") / path.name)


def copy_template(src: Path, dest: Path, force: bool, dry_run: bool) -> str:
    existed_before = dest.exists()
    if existed_before and not force:
        return f"SKIP      {dest} (exists)"
    action = "OVERWRITE" if existed_before else "WRITE"
    if dry_run:
        return f"{action:<9} {dest}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    done = "OVERWROTE" if existed_before else "WROTE"
    return f"{done:<9} {dest}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a synchronized workspace-doc starter structure.")
    parser.add_argument("--target", required=True, help="Target workspace directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        print(f"ERROR target does not exist: {target}", file=sys.stderr)
        return 1
    if not target.is_dir():
        print(f"ERROR target is not a directory: {target}", file=sys.stderr)
        return 1

    results: list[str] = []
    for src, rel_dest in iter_templates():
        dest = target / rel_dest
        results.append(copy_template(src, dest, force=args.force, dry_run=args.dry_run))

    print(f"Target: {target}")
    print(f"Mode: {'dry-run' if args.dry_run else 'write'}")
    print()
    for line in results:
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
