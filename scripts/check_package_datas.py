#!/usr/bin/env python3
"""Gate: wheel / PyInstaller / Nuitka packaging must ship locales + logo_wordmark."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ROOT / "buusdo" / "locales"
WORDMARK = ROOT / "buusdo" / "assets" / "logo_wordmark.png"


def _fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    jsons = sorted(LOCALES.glob("*.json"))
    if len(jsons) < 12:
        _fail(f"expected ≥12 locale JSON files, found {len(jsons)}")
    if not WORDMARK.is_file() or WORDMARK.stat().st_size < 50:
        _fail(f"missing/empty {WORDMARK}")

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if 'locales/*' not in pyproject or "assets/*" not in pyproject:
        _fail("pyproject.toml [tool.setuptools.package-data] must include assets/* and locales/*")

    spec = (ROOT / "packaging" / "pyinstaller_buusdo.spec").read_text(encoding="utf-8")
    if "buusdo/locales" not in spec or "buusdo/assets" not in spec:
        _fail("packaging/pyinstaller_buusdo.spec must datas-include assets + locales")
    if "logo_wordmark" not in spec:
        _fail("pyinstaller spec should mention logo_wordmark.png in a comment or path")

    deploy = (ROOT / "scripts" / "pyside6-deploy.spec").read_text(encoding="utf-8")
    # Nuitka must pull package data (JSON/PNG), not only .py modules.
    if "include-package-data=buusdo" not in deploy and "include-data-dir" not in deploy:
        _fail(
            "scripts/pyside6-deploy.spec nuitka.extra_args must include "
            "--include-package-data=buusdo (or explicit --include-data-dir for locales/assets)"
        )

    print(
        f"OK  package datas: {len(jsons)} locales, {WORDMARK.name}, "
        "pyproject + pyinstaller + nuitka wired"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
