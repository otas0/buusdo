"""Repeated language switches must not leave mixed-language chrome."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from buusdo.core.backend import (
    Capability,
    EnhancementBackend,
    EnhancementTarget,
    InstallResult,
)


class _StubBackend(EnhancementBackend):
    def platform_id(self) -> str:
        return "macos"

    def discover_games(self, *, should_cancel=None, progress=None) -> list[EnhancementTarget]:
        return []

    def list_capabilities(self, target: EnhancementTarget) -> list[Capability]:
        return []

    def install(self, target: EnhancementTarget, options: dict[str, Any] | None = None) -> InstallResult:
        return InstallResult(True, "ok")

    def uninstall(self, target: EnhancementTarget) -> InstallResult:
        return InstallResult(True, "ok")

    def status(self, target: EnhancementTarget) -> dict[str, Any]:
        return {}


@pytest.fixture()
def qapp():
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def test_apply_locale_updates_secondary_chrome(qapp, monkeypatch: pytest.MonkeyPatch) -> None:
    from buusdo.core.i18n import reload_catalogs, set_locale, t
    from buusdo.ui.main_window import MainWindow

    reload_catalogs()
    set_locale("en")
    monkeypatch.setattr(
        "buusdo.ui.main_window.QTimer.singleShot", lambda *_a, **_k: None
    )

    win = MainWindow(backend=_StubBackend())
    for code in ("ja", "pt-BR", "zh-Hant", "de", "ja"):
        set_locale(code)
        win._apply_locale_to_chrome()
        assert win._btn_scan.text() == t("action.scan")
        assert win._btn_steam.text() == t("proton.open_steam")
        assert win._caps_lbl.text() == t("label.capabilities")
        assert win._steam_user_lbl.text() == t("label.steam_user")
        assert win._crash_opt.text() == t("action.crash_opt_in")
        assert win._btn_clear_session.text() == t("action.clear_display_session")
        if code != "en":
            assert win._btn_scan.text() != "Scan Steam library"
            assert win._caps_lbl.text() != "Capabilities"
    win.close()


def test_force_scan_restores_selection() -> None:
    games = [
        EnhancementTarget(
            name=f"G{i}",
            install_path=Path(f"/games/{i}"),
            executable=Path(f"/games/{i}/x.exe"),
            metadata={"app_id": str(100 + i)},
        )
        for i in range(4)
    ]
    from buusdo.ui.main_window import MainWindow

    key = MainWindow._selection_key(games[2])
    assert key == ("102", "/games/2", "G2")
    restored = [EnhancementTarget.from_payload(g.to_payload()) for g in games]
    match = next(i for i, g in enumerate(restored) if MainWindow._selection_key(g) == key)
    assert match == 2
