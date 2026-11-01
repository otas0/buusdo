#!/usr/bin/env python3
"""CI gate: logo.png is logo_path(); logo.ico exists and is <= 96KB."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from buusdo.assets import logo_ico_path, logo_path, logo_svg_path  # noqa: E402

MAX_ICO = 96_000


def main() -> int:
    logo = logo_path()
    if logo.name != "logo.png":
        print(f"FAIL logo_path().name={logo.name!r} (want logo.png)", file=sys.stderr)
        return 1
    if not logo.is_file() or logo.stat().st_size < 50:
        print(f"FAIL missing/empty {logo}", file=sys.stderr)
        return 1
    svg = logo_svg_path()
    if not svg.is_file() or svg.stat().st_size < 50:
        print(f"FAIL missing/empty {svg}", file=sys.stderr)
        return 1
    if "<svg" not in svg.read_text(encoding="utf-8", errors="ignore"):
        print(f"FAIL {svg} is not SVG", file=sys.stderr)
        return 1
    ico = logo_ico_path()
    if not ico.is_file():
        print(f"FAIL missing {ico}", file=sys.stderr)
        return 1
    size = ico.stat().st_size
    if not (50 < size <= MAX_ICO):
        print(f"FAIL logo.ico size {size} (want 50 < n <= {MAX_ICO})", file=sys.stderr)
        return 1
    print(f"OK  logo.png + logo.svg + logo.ico ({size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
