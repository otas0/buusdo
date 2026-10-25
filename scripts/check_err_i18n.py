#!/usr/bin/env python3
"""CI gate: err.* keys must exist and match between zh and en (dual with pytest)."""

from __future__ import annotations

import sys

from buusdo.core.i18n import _STRINGS


def main() -> int:
    zh = {k for k in _STRINGS["zh"] if k.startswith("err.")}
    en = {k for k in _STRINGS["en"] if k.startswith("err.")}
    missing_en = sorted(zh - en)
    missing_zh = sorted(en - zh)
    empty = [
        k
        for k in sorted(zh & en)
        if not str(_STRINGS["zh"][k]).strip() or not str(_STRINGS["en"][k]).strip()
    ]
    ok = True
    if missing_en:
        print("err.* missing in en:", ", ".join(missing_en), file=sys.stderr)
        ok = False
    if missing_zh:
        print("err.* missing in zh:", ", ".join(missing_zh), file=sys.stderr)
        ok = False
    if empty:
        print("err.* empty string:", ", ".join(empty), file=sys.stderr)
        ok = False
    if not zh:
        print("no err.* keys found", file=sys.stderr)
        ok = False
    if ok:
        print(f"err.* i18n OK ({len(zh)} keys)")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
