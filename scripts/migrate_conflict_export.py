#!/usr/bin/env python3
"""Upgrade conflict-export JSON files to the current schema_version."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from buusdo.core.conflict_preview import (
    CONFLICT_EXPORT_SCHEMA_VERSION,
    migrate_conflict_export,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", type=Path, help="Input conflict-export JSON")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write migrated JSON here (default: overwrite input with --in-place)",
    )
    p.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the input file",
    )
    args = p.parse_args(argv)
    raw = json.loads(args.path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        print("expected a JSON object", file=sys.stderr)
        return 2
    before = int(raw.get("schema_version") or 1)
    migrated = migrate_conflict_export(raw)
    dest = args.output
    if dest is None:
        if args.in_place:
            dest = args.path
        else:
            print(json.dumps(migrated, indent=2, ensure_ascii=False))
            print(
                f"# migrated {before} -> {migrated.get('schema_version')} "
                f"(current={CONFLICT_EXPORT_SCHEMA_VERSION})",
                file=sys.stderr,
            )
            return 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(migrated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {dest} ({before} -> {migrated.get('schema_version')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
