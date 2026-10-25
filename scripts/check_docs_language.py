#!/usr/bin/env python3
"""Fail if Han characters appear under docs/ (English-default documentation).

Also scans repo-root README.md and AGENTS.md when present.

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
ROOT_MARKDOWN = (ROOT / "README.md", ROOT / "AGENTS.md")
HAN = re.compile(r"[\u4e00-\u9fff]")
TEXT_SUFFIXES = {".md", ".txt", ".rst", ".yml", ".yaml", ".toml", ".json"}


def _scan_file(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    for i, line in enumerate(text.splitlines(), 1):
        if HAN.search(line):
            rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
            return f"{rel}:{i}: {line.strip()[:120]}"
    return None


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
        hit = _scan_file(path)
        if hit:
            hits.append(hit)
    for path in ROOT_MARKDOWN:
        if path.is_file():
            hit = _scan_file(path)
            if hit:
                hits.append(hit)
    if hits:
        print(
            "FAIL: Han characters found under docs/ (or README.md / AGENTS.md):",
            file=sys.stderr,
        )
        for h in hits:
            print(f"  {h}", file=sys.stderr)
        print(
            "Translate or move localized notes out of docs/. See AGENTS.md.",
            file=sys.stderr,
        )
        return 1
    print(
        f"OK: no Han characters under {DOCS.relative_to(ROOT)}/ "
        f"(+ README.md / AGENTS.md when present)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
