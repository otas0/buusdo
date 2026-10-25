#!/usr/bin/env python3
"""Fail if Han characters appear under docs/ (English-default documentation).

UI i18n catalogs and product strings live under buusdo/core/i18n.py and are out of scope.
Override with BUUSDO_ALLOW_DOCS_HAN=1 only for intentional exceptions (not for CI).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
HAN = re.compile(r"[\u4e00-\u9fff]")
TEXT_SUFFIXES = {".md", ".txt", ".rst", ".yml", ".yaml", ".toml", ".json"}


def main() -> int:
    if os.environ.get("BUUSDO_ALLOW_DOCS_HAN") == "1":
        print("OK: BUUSDO_ALLOW_DOCS_HAN=1 — skipping Han scan")
        return 0
    if not DOCS.is_dir():
        print(f"FAIL: missing {DOCS}", file=sys.stderr)
        return 2
    hits: list[str] = []
    for path in sorted(DOCS.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if HAN.search(line):
                rel = path.relative_to(ROOT)
                hits.append(f"{rel}:{i}: {line.strip()[:120]}")
                break  # one hit per file is enough for the report header
    if hits:
        print("FAIL: Han characters found under docs/ (English is the default):", file=sys.stderr)
        for h in hits:
            print(f"  {h}", file=sys.stderr)
        print(
            "Translate or move localized notes out of docs/. See AGENTS.md.",
            file=sys.stderr,
        )
        return 1
    print(f"OK: no Han characters under {DOCS.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
