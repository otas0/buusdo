#!/usr/bin/env python3
"""Windows multi-monitor SET_ADVANCED_COLOR_STATE verification helper.

Usage (on a real Windows host with HDR displays):
  python scripts/verify_ccd_hdr.py              # dry-run enumerate + plan
  python scripts/verify_ccd_hdr.py --apply on   # enable advanced color
  python scripts/verify_ccd_hdr.py --apply off  # disable advanced color
"""

from __future__ import annotations

import argparse
import json
import sys

from buusdo.backends.windows_display import (
    list_advanced_color_targets,
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
    args = parser.parse_args(argv)
    targets = list_advanced_color_targets()
    print(json.dumps({"targets": targets, "count": len(targets)}, indent=2))
    if args.apply is None:
        result = verify_set_advanced_color_state(enable=True, dry_run=True)
    else:
        result = verify_set_advanced_color_state(
            enable=args.apply == "on", dry_run=False
        )
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") or result.get("reason") == "not_windows" else 1


if __name__ == "__main__":
    sys.exit(main())
