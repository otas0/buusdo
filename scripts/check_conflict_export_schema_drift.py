#!/usr/bin/env python3
"""Fail if fixture conflict exports drift from migrate_conflict_export expectations.

Uses ``--dry-run --diff-keys-only`` JSON Lines:
- ``conflict_export_v1.json`` must produce at least one non-noop op (upgrade path).
- ``conflict_export_v2.json`` must be a noop (already current schema).

When ``GITHUB_STEP_SUMMARY`` is set (Actions), append a markdown summary of the JSONL.
"""

from __future__ import annotations

import importlib.util
import json
import os
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


def _write_step_summary(*, v1_changes: list[dict], v2_rows: list[dict], ok: bool) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    lines = [
        "## Conflict-export schema drift",
        "",
        f"- Result: **{'OK' if ok else 'FAIL'}**",
        f"- `{V1.name}`: {len(v1_changes)} key op(s)",
        f"- `{V2.name}`: {', '.join(sorted({str(r.get('op')) for r in v2_rows})) or 'none'}",
        "",
        "### JSONL (v1 upgrades)",
        "",
        "```json",
    ]
    for row in v1_changes[:20]:
        lines.append(json.dumps(row, ensure_ascii=False))
    if len(v1_changes) > 20:
        lines.append(f"... ({len(v1_changes) - 20} more)")
    lines.extend(["```", "", "### JSONL (v2)", "", "```json"])
    for row in v2_rows[:5]:
        lines.append(json.dumps(row, ensure_ascii=False))
    lines.append("```")
    lines.append("")
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> int:
    mod = _load_migrate()
    v1_rows = _jsonl_ops(mod, V1)
    v2_rows = _jsonl_ops(mod, V2)

    v1_changes = [r for r in v1_rows if r.get("op") != "noop"]
    ok = True
    if not v1_changes:
        print(f"FAIL: {V1.name} produced no schema upgrades (expected key changes)", file=sys.stderr)
        ok = False
    elif not any(r.get("key") == "schema_version" for r in v1_changes):
        print(f"FAIL: {V1.name} JSONL missing schema_version change: {v1_changes}", file=sys.stderr)
        ok = False

    if not v2_rows or any(r.get("op") != "noop" for r in v2_rows):
        print(f"FAIL: {V2.name} should be noop JSONL, got {v2_rows}", file=sys.stderr)
        ok = False

    _write_step_summary(v1_changes=v1_changes, v2_rows=v2_rows, ok=ok)
    if not ok:
        return 1
    print(f"OK: {V1.name} upgrades ({len(v1_changes)} key ops); {V2.name} noop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
