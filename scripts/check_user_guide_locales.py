#!/usr/bin/env python3
"""Fail if a UI locale lacks docs/user-guide/<code>.md (or pt-BR.md style)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ROOT / "buusdo" / "locales"
USER_GUIDE = ROOT / "docs" / "user-guide"


def main() -> int:
    if not LOCALES.is_dir() or not USER_GUIDE.is_dir():
        print(f"FAIL: missing {LOCALES} or {USER_GUIDE}", file=sys.stderr)
        return 2
    codes = sorted(p.stem for p in LOCALES.glob("*.json"))
    missing = [c for c in codes if not (USER_GUIDE / f"{c}.md").is_file()]
    if missing:
        print(
            "FAIL: UI locales without docs/user-guide/<code>.md:",
            ", ".join(missing),
            file=sys.stderr,
        )
        return 1
    print(f"OK: {len(codes)} locale(s) each have docs/user-guide/<code>.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
