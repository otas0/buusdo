#!/usr/bin/env python3
"""Fail if core/ or ui/ contain forbidden platform branching (C3)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = [ROOT / "buusdo" / "core", ROOT / "buusdo" / "ui"]
ALLOW_FILES = {"platform_detect.py"}

FORBIDDEN = [
    re.compile(r"""if\s+platform\s*=="""),
    re.compile(r"""if\s+.*==\s*["']windows["']"""),
    re.compile(r"""if\s+.*==\s*["']linux["']"""),
    re.compile(r"""if\s+.*==\s*["']macos["']"""),
    re.compile(r"""sys\.platform"""),
    re.compile(r"""win32"""),
    re.compile(r"""["']darwin["']"""),
]


def main() -> int:
    violations: list[str] = []
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if path.name in ALLOW_FILES:
                continue
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), start=1):
                if line.lstrip().startswith("#"):
                    continue
                for pat in FORBIDDEN:
                    if pat.search(line):
                        violations.append(f"{path.relative_to(ROOT)}:{i}: {line.strip()}")
                        break
    if violations:
        print("C3 violations (platform branching in core/ui):")
        for v in violations:
            print(f"  {v}")
        return 1
    print("C3 check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
