#!/usr/bin/env python3
"""Write buusdo/assets/logo.ico from logo.png for Windows / Inno Setup."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        from PySide6.QtGui import QImage
    except ImportError:
        print("PySide6 required", file=sys.stderr)
        return 1

    src = ROOT / "buusdo" / "assets" / "logo.png"
    out = ROOT / "buusdo" / "assets" / "logo.ico"
    if not src.is_file():
        print(f"missing {src}", file=sys.stderr)
        return 1
    img = QImage(str(src))
    if img.isNull():
        print("failed to load logo.png", file=sys.stderr)
        return 1
    # QImage can save multi-size ICO on Qt platforms that support it.
    ok = img.save(str(out), "ICO")
    if not ok:
        # Fallback: single-size PNG masquerading — still try scaled 256.
        scaled = img.scaled(256, 256)
        ok = scaled.save(str(out), "ICO")
    if not ok or not out.is_file():
        print("failed to write logo.ico", file=sys.stderr)
        return 1
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
