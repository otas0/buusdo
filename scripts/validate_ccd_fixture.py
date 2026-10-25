#!/usr/bin/env python3
"""Validate CCD dual-monitor fixture shape (and optionally require live host_windows)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def validate(path: Path, *, require_live: bool = False) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("adapter_target_ids", "targets", "target_count", "display_count"):
        if key not in data:
            errors.append(f"missing {key}")
    ids = data.get("adapter_target_ids") or []
    if len(ids) < 2:
        errors.append("need >=2 adapter_target_ids for dual-monitor")
    for i, row in enumerate(ids):
        for field in ("adapterLow", "adapterHigh", "targetId"):
            if field not in row:
                errors.append(f"adapter_target_ids[{i}] missing {field}")
    if require_live and not data.get("host_windows"):
        errors.append("host_windows is not true — re-run verify_ccd_hdr.py on Windows")
    if require_live and data.get("note", "").startswith("ILLUSTRATIVE"):
        errors.append("fixture still marked ILLUSTRATIVE")
    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fixture", type=Path, nargs="?", default=Path("docs/fixtures/ccd_dual_monitor_sample.json"))
    p.add_argument("--require-live", action="store_true")
    args = p.parse_args(argv)
    errs = validate(args.fixture, require_live=args.require_live)
    if errs:
        print("\n".join(errs), file=sys.stderr)
        return 1
    print("ok:", args.fixture)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
