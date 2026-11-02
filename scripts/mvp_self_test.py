#!/usr/bin/env python3
"""MVP developer self-test — no third-party acceptance; local gates only."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ok(msg: str) -> None:
    print(f"OK  {msg}")


def _fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)


def _run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


def test_docs() -> bool:
    for rel in ("docs/MVP.md", "docs/E2E_CHECKLIST.md", "docs/PROJECT.md"):
        if not (ROOT / rel).is_file():
            _fail(f"missing {rel}")
            return False
    mvp = (ROOT / "docs/MVP.md").read_text(encoding="utf-8")
    if "Windows" not in mvp or "Linux" not in mvp or "macOS" not in mvp:
        _fail("MVP.md must name Windows, Linux, and macOS as supported targets")
        return False
    if "Windows-first" in mvp:
        _fail("MVP.md must not say Windows-first — platforms are Win/Linux/macOS")
        return False
    _ok("docs present")
    return True


def test_brand_mark() -> bool:
    mark = ROOT / "buusdo" / "assets" / "brand_mark.png"
    if not mark.is_file() or mark.stat().st_size < 50:
        _fail("brand_mark.png missing/empty")
        return False
    _ok("brand_mark.png")
    return True


def test_logo_assets() -> bool:
    sys.path.insert(0, str(ROOT))
    from buusdo.assets import logo_ico_path, logo_path, logo_wordmark_path

    logo = logo_path()
    if logo.name != "logo.png" or not logo.is_file() or logo.stat().st_size < 50:
        _fail("logo_path() must resolve to existing logo.png")
        return False
    wm = logo_wordmark_path()
    if wm.name != "logo_wordmark.png" or not wm.is_file() or wm.stat().st_size < 50:
        _fail("logo_wordmark.png missing — run scripts/generate_logo_wordmark.py")
        return False
    ico = logo_ico_path()
    if not ico.is_file() or ico.stat().st_size < 50:
        _fail("logo.ico missing — run scripts/generate_logo_ico.py")
        return False
    if ico.stat().st_size > 96_000:
        _fail(f"logo.ico too large ({ico.stat().st_size})")
        return False
    _ok("logo.png + logo_wordmark.png + logo.ico")
    return True


def test_anticheat_block() -> bool:
    sys.path.insert(0, str(ROOT))
    from buusdo.core.anticheat_guard import check
    from buusdo.core.backend import EnhancementTarget
    from buusdo.core.errors import UnsafeTargetError
    from buusdo.core.platform_detect import HostPlatform

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        eac = root / "EasyAntiCheat"
        eac.mkdir()
        (eac / "EasyAntiCheat_EOS_Setup.exe").write_text("x", encoding="utf-8")
        target = EnhancementTarget(name="ACGame", install_path=root)
        try:
            check(target, HostPlatform.WINDOWS)
        except UnsafeTargetError as exc:
            if "continue" in str(exc).lower():
                _fail("UnsafeTargetError must not invite continue")
                return False
            _ok("anticheat blocks UnsafeTargetError")
            return True
        _fail("expected UnsafeTargetError")
        return False


def test_transaction_roundtrip() -> bool:
    sys.path.insert(0, str(ROOT))
    from buusdo.core.transaction import Transaction

    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "x.bin"
        f.write_bytes(b"orig")
        try:
            with Transaction() as tx:
                tx.write_bytes(f, b"changed")
                raise RuntimeError("force rollback")
        except RuntimeError:
            pass
        if f.read_bytes() != b"orig":
            _fail("transaction did not restore bytes")
            return False
        _ok("transaction restore")
        return True


def test_c3_lint() -> bool:
    rc = _run([sys.executable, str(ROOT / "scripts" / "check_no_platform_branch.py")])
    if rc != 0:
        _fail("C3 platform-branch lint")
        return False
    _ok("C3 lint")
    return True


def test_offline_poc() -> bool:
    rc = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_dwm_hdr_poc_local.py"),
            "--json",
        ]
    )
    if rc != 0:
        _fail("verify_dwm_hdr_poc_local")
        return False
    _ok("offline dwm-hdr PoC verify")
    return True


def test_pytest_core() -> bool:
    # Keep this subset Qt-free so the gate stays headless-fast.
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/test_anticheat_guard.py",
        "tests/test_transaction.py",
        "tests/test_batch_mvp_features.py",
        "--tb=line",
    ]
    rc = _run(cmd)
    if rc != 0:
        _fail("core pytest subset")
        return False
    _ok("core pytest subset")
    return True


def test_scan_worker_thread_gate() -> bool:
    # Queued QObject-slot wiring; prevents DirectConnection UI segfaults.
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/test_scan_worker_thread.py",
        "--tb=line",
    ]
    rc = _run(cmd)
    if rc != 0:
        _fail("scan worker thread gate")
        return False
    _ok("scan worker thread gate")
    return True


def test_logo_dark_contrast_gate() -> bool:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/test_logo_dark_contrast.py",
        "--tb=line",
    ]
    rc = _run(cmd)
    if rc != 0:
        _fail("logo dark contrast gate")
        return False
    _ok("logo dark contrast gate")
    return True


def test_i18n_locale_gate() -> bool:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/test_i18n_locales.py",
        "tests/test_locale_quality.py",
        "--tb=line",
    ]
    rc = _run(cmd)
    if rc != 0:
        _fail("i18n locale gate")
        return False
    _ok("i18n locale gate")
    return True


def test_package_datas_gate() -> bool:
    rc = _run([sys.executable, str(ROOT / "scripts" / "check_package_datas.py")])
    if rc != 0:
        _fail("package datas gate")
        return False
    _ok("package datas gate")
    return True


def test_issue_template() -> bool:
    path = ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.md"
    if not path.is_file():
        _fail("missing bug_report issue template")
        return False
    _ok("issue template")
    return True


def test_github_release_gate() -> bool:
    rc = _run([sys.executable, str(ROOT / "scripts" / "smoke_github_release_gate.py")])
    if rc != 0:
        _fail("github release structural gate")
        return False
    _ok("github release structural gate")
    return True


def main() -> int:
    print("buusdo MVP self-test")
    checks = [
        test_docs,
        test_brand_mark,
        test_logo_assets,
        test_anticheat_block,
        test_transaction_roundtrip,
        test_c3_lint,
        test_offline_poc,
        test_issue_template,
        test_github_release_gate,
        test_pytest_core,
        test_scan_worker_thread_gate,
        test_logo_dark_contrast_gate,
        test_i18n_locale_gate,
        test_package_datas_gate,
    ]
    failed = 0
    for fn in checks:
        try:
            if not fn():
                failed += 1
        except Exception as exc:  # noqa: BLE001 — surface any gate crash
            _fail(f"{fn.__name__}: {exc}")
            failed += 1
    if failed:
        print(f"\nMVP self-test FAILED ({failed} gate(s))", file=sys.stderr)
        return 1
    print("\nMVP self-test OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
