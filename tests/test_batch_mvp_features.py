"""MVP freeze docs, packaging script, experimental copy."""

from __future__ import annotations

from pathlib import Path

from buusdo.core.i18n import t


def test_mvp_doc_freeze() -> None:
    text = Path("docs/MVP.md").read_text(encoding="utf-8")
    assert "Windows" in text
    assert "experimental" in text.lower() or "Out of scope" in text
    assert "workflow_dispatch" in text
    assert "mvp_self_test" in text


def test_e2e_is_self_test() -> None:
    text = Path("docs/E2E_CHECKLIST.md").read_text(encoding="utf-8")
    assert "self-test" in text.lower()
    assert "sign-off" in text.lower() or "third-party" in text.lower()
    assert "dark theme" not in text.lower()


def test_package_mvp_script() -> None:
    path = Path("scripts/package_mvp.sh")
    assert path.is_file()
    body = path.read_text(encoding="utf-8")
    assert "SHA256SUMS" in body
    assert "INSTALL.txt" in body
    assert "build" in body


def test_experimental_i18n() -> None:
    assert t("cap.experimental") in {"experimental", "实验性"}


def test_readme_end_user_install() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "End-user install" in readme
    assert "mvp_self_test" in readme
    assert "experimental" in readme.lower()
