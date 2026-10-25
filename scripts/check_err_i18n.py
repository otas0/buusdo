#!/usr/bin/env python3
"""CI gate: err.* / cap.* / action.* keys must match between zh and en (dual with pytest)."""

from __future__ import annotations

import sys

from buusdo.core.i18n import _STRINGS

_PREFIXES = ("err.", "cap.", "action.")


def _check_prefix(prefix: str) -> list[str]:
    zh = {k for k in _STRINGS["zh"] if k.startswith(prefix)}
    en = {k for k in _STRINGS["en"] if k.startswith(prefix)}
    errors: list[str] = []
    missing_en = sorted(zh - en)
    missing_zh = sorted(en - zh)
    empty = [
        k
        for k in sorted(zh & en)
        if not str(_STRINGS["zh"][k]).strip() or not str(_STRINGS["en"][k]).strip()
    ]
    if missing_en:
        errors.append(f"{prefix}* missing in en: {', '.join(missing_en)}")
    if missing_zh:
        errors.append(f"{prefix}* missing in zh: {', '.join(missing_zh)}")
    if empty:
        errors.append(f"{prefix}* empty string: {', '.join(empty)}")
    if not zh:
        errors.append(f"no {prefix}* keys found")
    else:
        print(f"{prefix}* i18n OK ({len(zh)} keys)")
    return errors


def main() -> int:
    errors: list[str] = []
    for prefix in _PREFIXES:
        errors.extend(_check_prefix(prefix))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
