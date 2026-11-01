#!/usr/bin/env python3
"""Pre-tag gate: frozen release visual checklist screenshots must exist."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs" / "fixtures" / "release_visual_checklist"
REQUIRED = ("main_window.png", "about_dialog.png", "tray_icon_sizes.png", "README.md")


def main() -> int:
    if not DIR.is_dir():
        print(f"FAIL missing {DIR.relative_to(ROOT)}", file=sys.stderr)
        print("Run: python scripts/screenshot_release_checklist.py", file=sys.stderr)
        return 1
    failed = 0
    for name in REQUIRED:
        path = DIR / name
        if not path.is_file() or path.stat().st_size < 50:
            print(f"FAIL missing/empty {path.relative_to(ROOT)}", file=sys.stderr)
            failed += 1
        else:
            print(f"OK  {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")
    if failed:
        print("Re-run scripts/screenshot_release_checklist.py after UI chrome changes.", file=sys.stderr)
        return 1
    print("OK  release visual checklist frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
