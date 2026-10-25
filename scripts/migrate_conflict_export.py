#!/usr/bin/env python3
"""Upgrade conflict-export JSON files to the current schema_version.

Supports a single file or a directory of JSON files (optionally recursive).
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Any

from buusdo.core.conflict_preview import (
    CONFLICT_EXPORT_SCHEMA_VERSION,
    migrate_conflict_export,
)


def _json_lines(payload: dict[str, Any]) -> list[str]:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True).splitlines(
        keepends=True
    )


def _print_dry_run_diff(src: Path, before: dict[str, Any], after: dict[str, Any]) -> None:
    """Human-readable unified diff of sorted JSON (dry-run only)."""
    left = _json_lines(before)
    right = _json_lines(after)
    if left == right:
        print(f"{src}: no JSON changes")
        return
    diff = difflib.unified_diff(
        left,
        right,
        fromfile=f"{src} (before)",
        tofile=f"{src} (after migrate → v{CONFLICT_EXPORT_SCHEMA_VERSION})",
    )
    sys.stdout.writelines(diff)


def _iter_inputs(path: Path, *, recursive: bool, pattern: str) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []
    globber = path.rglob if recursive else path.glob
    return sorted(p for p in globber(pattern) if p.is_file())


def _migrate_one(
    src: Path,
    *,
    dest: Path | None,
    in_place: bool,
    dry_run: bool,
) -> int:
    raw = json.loads(src.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        print(f"{src}: expected a JSON object", file=sys.stderr)
        return 2
    before = int(raw.get("schema_version") or 1)
    migrated = migrate_conflict_export(raw)
    after = int(migrated.get("schema_version") or before)
    if dry_run:
        changed = before != after or raw != migrated
        print(
            f"{src}: {'WOULD migrate' if changed else 'ok'} "
            f"{before} -> {after} (current={CONFLICT_EXPORT_SCHEMA_VERSION})"
        )
        _print_dry_run_diff(src, raw, migrated)
        return 0
    out = dest
    if out is None:
        if in_place:
            out = src
        else:
            print(json.dumps(migrated, indent=2, ensure_ascii=False))
            print(
                f"# {src}: migrated {before} -> {migrated.get('schema_version')} "
                f"(current={CONFLICT_EXPORT_SCHEMA_VERSION})",
                file=sys.stderr,
            )
            return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(migrated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} ({before} -> {migrated.get('schema_version')})")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "path",
        type=Path,
        help="Input conflict-export JSON file, or a directory of JSON files",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write migrated JSON here (file→file, or directory→directory when input is a dir)",
    )
    p.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite each input file",
    )
    p.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="When path is a directory, recurse into subfolders",
    )
    p.add_argument(
        "--glob",
        default="*.json",
        help="Filename glob when path is a directory (default: *.json)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing files",
    )
    args = p.parse_args(argv)

    inputs = _iter_inputs(args.path, recursive=args.recursive, pattern=args.glob)
    if not inputs:
        print(f"no inputs matched under {args.path}", file=sys.stderr)
        return 2

    if args.path.is_file():
        return _migrate_one(
            args.path, dest=args.output, in_place=args.in_place, dry_run=args.dry_run
        )

    # Directory batch
    if args.output is not None and args.output.exists() and not args.output.is_dir():
        print("--output must be a directory when migrating a directory", file=sys.stderr)
        return 2
    rc = 0
    for src in inputs:
        if args.dry_run:
            dest: Path | None = None
            in_place = False
        elif args.in_place:
            dest = src
            in_place = True
        elif args.output is not None:
            dest = args.output / src.relative_to(args.path)
            in_place = True
        else:
            dest = None
            in_place = False
        step = _migrate_one(src, dest=dest, in_place=in_place, dry_run=args.dry_run)
        if step != 0:
            rc = step
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
