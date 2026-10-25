#!/usr/bin/env python3
"""Windows multi-monitor SET_ADVANCED_COLOR_STATE verification helper.

On a dual-monitor Windows host, record real adapterId/targetId into the fixture:

  python scripts/verify_ccd_hdr.py --apply on --record docs/fixtures/ccd_dual_monitor_sample.json
  python scripts/verify_ccd_hdr.py --apply off --record docs/fixtures/ccd_dual_monitor_sample.json
  python scripts/verify_ccd_hdr.py --record docs/fixtures/ccd_dual_monitor_sample.json --overwrite-fixture

Without Windows hardware this writes a dry-run envelope; --require-multi fails if <2 targets.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from buusdo.backends.windows_display import (
    list_advanced_color_targets,
    list_display_modes,
    verify_set_advanced_color_state,
)


def _build_record(*, apply: str | None, result: dict) -> dict:
    targets = list_advanced_color_targets()
    modes = list_display_modes()
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "host_windows": bool(targets or modes),
        "note": "Recorded by scripts/verify_ccd_hdr.py — replace sample IDs with real dual-monitor values.",
        "targets": targets,
        "target_count": len(targets),
        "displays": modes,
        "display_count": len(modes),
        "adapter_target_ids": [
            {
                "adapterLow": t.get("adapterLow"),
                "adapterHigh": t.get("adapterHigh"),
                "targetId": t.get("targetId"),
                "advancedColorEnabled": t.get("advancedColorEnabled"),
                "advancedColorSupported": t.get("advancedColorSupported"),
            }
            for t in targets
        ],
        "verify": result,
        "apply": apply,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", choices=("on", "off"), default=None)
    parser.add_argument("--record", type=Path, default=None)
    parser.add_argument(
        "--overwrite-fixture",
        action="store_true",
        help="Allow overwriting docs/fixtures/ccd_dual_monitor_sample.json with live data",
    )
    parser.add_argument(
        "--require-multi",
        action="store_true",
        help="Exit non-zero unless at least 2 CCD targets are present",
    )
    args = parser.parse_args(argv)

    if args.apply is None:
        result = verify_set_advanced_color_state(enable=True, dry_run=True)
    else:
        result = verify_set_advanced_color_state(
            enable=args.apply == "on", dry_run=False
        )
    payload = _build_record(apply=args.apply, result=result)
    print(json.dumps(payload, indent=2))

    if args.require_multi and payload["target_count"] < 2:
        print("require-multi: need >=2 CCD targets", file=sys.stderr)
        return 2

    if args.record:
        fixture = Path("docs/fixtures/ccd_dual_monitor_sample.json")
        if (
            args.record.resolve() == fixture.resolve()
            and fixture.is_file()
            and not args.overwrite_fixture
            and not payload.get("host_windows")
        ):
            print(
                "Refusing to overwrite fixture without live Windows data; "
                "pass --overwrite-fixture after a real dual-monitor --record run.",
                file=sys.stderr,
            )
            return 3
        args.record.parent.mkdir(parents=True, exist_ok=True)
        args.record.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"recorded: {args.record}", file=sys.stderr)

    return 0 if result.get("ok") or result.get("reason") == "not_windows" else 1


if __name__ == "__main__":
    sys.exit(main())
