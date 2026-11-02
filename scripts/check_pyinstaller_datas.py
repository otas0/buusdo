#!/usr/bin/env python3
"""Optional: unpack a PyInstaller onefile/onedir dist and verify locales + wordmark.

Usage:
  python scripts/check_pyinstaller_datas.py path/to/buusdo  # onedir
  python scripts/check_pyinstaller_datas.py path/to/buusdo.exe  # extracts with pyi-archive-viewer tips
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path


def _ok(msg: str) -> None:
    print(f"OK  {msg}")


def _fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def check_tree(root: Path) -> None:
    locales = list(root.rglob("locales/*.json"))
    if len(locales) < 12:
        # also accept buusdo/locales layout
        locales = list(root.rglob("**/buusdo/locales/*.json"))
    wordmarks = list(root.rglob("logo_wordmark.png"))
    if len(locales) < 12:
        _fail(f"found {len(locales)} locale JSON under {root} (need ≥12)")
    if not wordmarks:
        _fail(f"logo_wordmark.png missing under {root}")
    _ok(f"{root}: {len(locales)} locales, wordmark={wordmarks[0]}")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip())
        # Still verify source packaging wiring when no dist given.
        from check_package_datas import main as pkg_main

        return pkg_main()
    target = Path(sys.argv[1]).expanduser().resolve()
    if not target.exists():
        _fail(f"missing {target}")
    if target.is_dir():
        check_tree(target)
        return 0
    if target.suffix.lower() == ".whl" or zipfile.is_zipfile(target):
        with zipfile.ZipFile(target) as zf:
            names = zf.namelist()
        locs = [n for n in names if "/locales/" in n and n.endswith(".json")]
        wm = [n for n in names if n.endswith("logo_wordmark.png")]
        if len(locs) < 12:
            _fail(f"wheel/zip locales={len(locs)}")
        if not wm:
            _fail("wheel/zip missing logo_wordmark.png")
        _ok(f"{target.name}: {len(locs)} locales, {wm[0]}")
        return 0
    _fail(
        f"{target} is a binary — extract the onedir build or pass a .whl; "
        "onefile needs PyInstaller extract before this check"
    )
    return 1


if __name__ == "__main__":
    # Allow `python scripts/check_pyinstaller_datas.py` from repo root.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
