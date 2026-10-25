#!/usr/bin/env python3
"""Windows multi-monitor SET_ADVANCED_COLOR_STATE verification helper.

Usage (on a real Windows host with HDR displays):
  python scripts/verify_ccd_hdr.py
  python scripts/verify_ccd_hdr.py --apply on
  python scripts/verify_ccd_hdr.py --apply off
  python scripts/verify_ccd_hdr.py --record docs/fixtures/ccd_dual_monitor_sample.json
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        choices=("on", "off"),
        default=None,
        help="Actually toggle HDR (omit for dry-run)",
    )
    parser.add_argument(
        "--record",
        type=Path,
        default=None,
        help="Write adapterId/targetId (+ modes) JSON record for dual-monitor verification logs",
    )
    args = parser.parse_args(argv)
    targets = list_advanced_color_targets()
    modes = list_display_modes()
    summary = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
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
    }
    print(json.dumps(summary, indent=2))
    if args.apply is None:
        result = verify_set_advanced_color_state(enable=True, dry_run=True)
    else:
        result = verify_set_advanced_color_state(
            enable=args.apply == "on", dry_run=False
        )
    print(json.dumps(result, indent=2))
    if args.record:
        args.record.parent.mkdir(parents=True, exist_ok=True)
        payload = {**summary, "verify": result, "apply": args.apply}
        args.record.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"recorded: {args.record}", file=sys.stderr)
    return 0 if result.get("ok") or result.get("reason") == "not_windows" else 1


if __name__ == "__main__":
    sys.exit(main())
