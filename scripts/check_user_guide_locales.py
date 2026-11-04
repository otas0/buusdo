#!/usr/bin/env python3
"""Fail if a UI locale lacks docs/user-guide/<code>.md, or a guide is still a stub."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ROOT / "buusdo" / "locales"
USER_GUIDE = ROOT / "docs" / "user-guide"
# Marker from scripts/generate_user_guides.py stub_body(); must not ship.
STUB_BANNER = "> **Stub:**"


def main() -> int:
    if not LOCALES.is_dir() or not USER_GUIDE.is_dir():
        print(f"FAIL: missing {LOCALES} or {USER_GUIDE}", file=sys.stderr)
        return 2
    codes = sorted(p.stem for p in LOCALES.glob("*.json"))
    missing = [c for c in codes if not (USER_GUIDE / f"{c}.md").is_file()]
    stubs: list[str] = []
    for code in codes:
        path = USER_GUIDE / f"{code}.md"
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"FAIL: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        if STUB_BANNER in text:
            stubs.append(code)
    if missing:
        print(
            "FAIL: UI locales without docs/user-guide/<code>.md:",
            ", ".join(missing),
            file=sys.stderr,
        )
        print(
            "Hook: add BODIES/LOCALE_NAMES in scripts/generate_user_guides.py, "
            "then run: python scripts/generate_user_guides.py",
            file=sys.stderr,
        )
        return 1
    if stubs:
        print(
            "FAIL: user-guide still has generator stub banner "
            f"({STUB_BANNER!r}) for: ",
            ", ".join(stubs),
            file=sys.stderr,
        )
        print(
            "Replace stub BODIES[code] with a real translation, regenerate, "
            "and re-run this check.",
            file=sys.stderr,
        )
        return 1
    print(
        f"OK: {len(codes)} locale(s) each have docs/user-guide/<code>.md "
        f"(no stub banners)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
