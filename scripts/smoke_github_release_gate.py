#!/usr/bin/env python3
"""Structural gate for GitHub-release MVP (no Authenticode). Runs on any OS."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    required = [
        ROOT / "docs" / "STORE_MVP.md",
        ROOT / "packaging" / "inno" / "buusdo.iss",
        ROOT / "scripts" / "package_windows_inno.sh",
        ROOT / "scripts" / "smoke_windows_install.ps1",
        ROOT / "scripts" / "generate_logo_ico.py",
        ROOT / "scripts" / "pyside6-deploy.spec.json",
        ROOT / ".github" / "RELEASE_TEMPLATE.md",
        ROOT / "buusdo" / "ui" / "about_dialog.py",
        ROOT / "buusdo" / "assets" / "logo.png",
        ROOT / "buusdo" / "assets" / "logo.ico",
    ]
    failed = 0
    for path in required:
        if not path.is_file():
            print(f"FAIL missing {path.relative_to(ROOT)}", file=sys.stderr)
            failed += 1
        else:
            print(f"OK  {path.relative_to(ROOT)}")

    store = (ROOT / "docs" / "STORE_MVP.md").read_text(encoding="utf-8")
    for needle in ("Skipped", "Inno Setup", "GitHub", "v1.0.0"):
        if needle not in store:
            print(f"FAIL STORE_MVP.md missing {needle!r}", file=sys.stderr)
            failed += 1
    if "Authenticode" in store and "Skipped" not in store:
        print("FAIL signing should be marked skipped", file=sys.stderr)
        failed += 1

    iss = (ROOT / "packaging" / "inno" / "buusdo.iss").read_text(encoding="utf-8")
    # Allow comments mentioning SignTool; forbid active SignTool= directives.
    active_sign = [
        ln for ln in iss.splitlines()
        if ln.strip().lower().startswith("signtool") and not ln.strip().startswith(";")
    ]
    if active_sign:
        print("FAIL iss must not require SignTool", file=sys.stderr)
        failed += 1
    else:
        print("OK  iss unsigned")
    if "logo.ico" not in iss:
        print("FAIL iss must reference logo.ico SetupIconFile", file=sys.stderr)
        failed += 1
    else:
        print("OK  iss SetupIconFile logo.ico")

    deploy_spec = (ROOT / "scripts" / "pyside6-deploy.spec.json").read_text(encoding="utf-8")
    if "logo.ico" not in deploy_spec:
        print("FAIL pyside6-deploy.spec.json must set icon=logo.ico", file=sys.stderr)
        failed += 1
    else:
        print("OK  deploy icon logo.ico")

    ico_size = (ROOT / "buusdo" / "assets" / "logo.ico").stat().st_size
    if not (50 < ico_size <= 96_000):
        print(f"FAIL logo.ico size {ico_size}", file=sys.stderr)
        failed += 1
    else:
        print(f"OK  logo.ico {ico_size} bytes")

    if failed:
        print(f"gate FAILED ({failed})", file=sys.stderr)
        return 1
    print("GitHub release structural gate OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
