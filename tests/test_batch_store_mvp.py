"""GitHub-release MVP: unsigned Inno path, About copy, freeze docs."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from buusdo.core.i18n import t


def test_store_mvp_skips_signing() -> None:
    text = Path("docs/STORE_MVP.md").read_text(encoding="utf-8")
    assert "Skipped" in text or "skipped" in text.lower()
    assert "Inno" in text
    assert "GitHub" in text
    assert "Authenticode" in text


def test_inno_iss_unsigned() -> None:
    iss = Path("packaging/inno/buusdo.iss").read_text(encoding="utf-8")
    assert not any(
        ln.strip().lower().startswith("signtool") and not ln.strip().startswith(";")
        for ln in iss.splitlines()
    )
    assert "buusdo-setup-" in iss
    assert "payload" in iss


def test_release_template_non_goals() -> None:
    text = Path(".github/RELEASE_TEMPLATE.md").read_text(encoding="utf-8")
    assert "unsigned" in text.lower()
    assert "DWM HDR" in text
    assert "Windows" in text


def test_about_i18n() -> None:
    assert "GitHub" in t("about.channel")
    assert "{version}" in t("about.version") or "Version" in t("about.version") or "版本" in t(
        "about.version"
    )


def test_smoke_github_gate_script() -> None:
    path = Path("scripts/smoke_github_release_gate.py")
    spec = importlib.util.spec_from_file_location("smoke_github_release_gate", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
