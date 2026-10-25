#!/usr/bin/env python3
"""Fail if fixture conflict exports drift from migrate_conflict_export expectations.

Uses ``--dry-run --diff-keys-only`` JSON Lines:
- ``conflict_export_v1.json`` must produce at least one non-noop op (upgrade path).
- ``conflict_export_v2.json`` must be a noop (already current schema).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATE = ROOT / "scripts" / "migrate_conflict_export.py"
V1 = ROOT / "docs" / "fixtures" / "conflict_export_v1.json"
V2 = ROOT / "docs" / "fixtures" / "conflict_export_v2.json"


def _load_migrate():
    spec = importlib.util.spec_from_file_location("migrate_conflict_export", MIGRATE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MIGRATE}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _jsonl_ops(mod, path: Path) -> list[dict]:
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main([str(path), "--dry-run", "--diff-keys-only"])
    if rc != 0:
        raise RuntimeError(f"migrate failed for {path} rc={rc}")
    rows: list[dict] = []
    for line in buf.getvalue().splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        rows.append(json.loads(line))
    return rows


def main() -> int:
    mod = _load_migrate()
    v1_rows = _jsonl_ops(mod, V1)
    v2_rows = _jsonl_ops(mod, V2)

    v1_changes = [r for r in v1_rows if r.get("op") != "noop"]
    if not v1_changes:
        print(f"FAIL: {V1.name} produced no schema upgrades (expected key changes)", file=sys.stderr)
        return 1
    if not any(r.get("key") == "schema_version" for r in v1_changes):
        print(f"FAIL: {V1.name} JSONL missing schema_version change: {v1_changes}", file=sys.stderr)
        return 1

    if not v2_rows or any(r.get("op") != "noop" for r in v2_rows):
        print(f"FAIL: {V2.name} should be noop JSONL, got {v2_rows}", file=sys.stderr)
        return 1

    print(f"OK: {V1.name} upgrades ({len(v1_changes)} key ops); {V2.name} noop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
