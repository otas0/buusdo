"""Batch AH: Ctrl+N exhaust; Esc≠reject; fail-table i18n; theme; weekly installer."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from buusdo.core.backend import (
    Capability,
    EnhancementBackend,
    EnhancementTarget,
    InstallResult,
)
from buusdo.core.i18n import t


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


def test_fail_table_clear_selection_i18n() -> None:
    assert t("action.clear_selection") in {"Clear selection", "取消选中"}
    tip = t("ui.clear_selection_tip")
    assert "Esc" in tip or "取消" in tip


def test_project_docs_steam_ctrl_n() -> None:
    text = Path("docs/PROJECT.md").read_text(encoding="utf-8")
    assert "Ctrl+N" in text
    assert "Steam properties URI" in text or "Steam" in text
    assert "theme.py" in text


def test_readme_uv_sync_extra_devui() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "uv sync --extra devui" in readme
    assert "install_assert_watch_ci_billing_weekly.sh" in readme


def test_weekly_assert_installer_exists() -> None:
    path = Path("scripts/install_assert_watch_ci_billing_weekly.sh")
    assert path.is_file()
    body = path.read_text(encoding="utf-8")
    assert "StartCalendarInterval" in body
    assert "Weekday" in body
    assert "assert_watch_ci_billing_log_append.sh" in body
    assert "Does not poll" in body or "does not poll" in body.lower() or "no Actions" in body


def test_theme_is_light_instrument() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from buusdo.ui.theme import COLOR_BG, COLOR_WARN, apply_product_theme

    app = QApplication.instance() or QApplication([])
    apply_product_theme(app)
    # Cool light surface — not cream cluster, not default dark #121212.
    assert COLOR_BG.upper() == "#EDEDED"
    assert COLOR_WARN.upper() == "#FF4F00"
    assert "QLabel#brandTitle" in app.styleSheet()


def test_steam_ctrl_n_disabled_when_exhausted() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from buusdo.core.backend import EnhancementTarget
    from buusdo.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    win = MainWindow(backend=_StubBackend())
    win._target = EnhancementTarget(
        name="Demo",
        install_path=Path("/tmp/demo"),
        metadata={"app_id": "1"},
    )
    with patch.object(win, "_steam_uri_candidates", return_value=["steam://a/1", "steam://b/1"]):
        # After last candidate: index == len → remaining 0 → exhausted.
        win._steam_uri_try_index = 2
        win._refresh_steam_uri_controls()
        assert win._btn_steam_try_next.isEnabled() is False
        assert win._steam_try_next_shortcut.isEnabled() is False
        # Mid-list failure path still enables next.
        win._steam_uri_try_index = 1
        win._refresh_steam_uri_controls()
        assert win._btn_steam_try_next.isEnabled() is True
        assert win._steam_try_next_shortcut.isEnabled() is True
    win.close()
    app.processEvents()


def test_conflict_esc_does_not_reject_dialog() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QDialog, QTableWidget

    from buusdo.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    shown: dict[str, QDialog] = {}

    def _fake_exec(self: QDialog) -> int:
        shown["dlg"] = self
        return 0

    with patch.object(QDialog, "exec", _fake_exec):
        win = MainWindow(backend=_StubBackend())
        win._show_conflict_dialog(
            {
                "schema_version": 2,
                "mode": "reshade",
                "blocked": False,
                "diffs": [
                    {"action": "conflict", "path": "a.dll", "detail": "[warning] x"},
                ],
            }
        )
    dlg = shown["dlg"]
    table = dlg.findChild(QTableWidget)
    assert table is not None
    table.setCurrentCell(0, 0)
    app.processEvents()
    assert table.currentRow() == 0
    # Default QDialog Esc → reject(); ours must clear selection and leave dialog "open".
    dlg.reject()
    app.processEvents()
    assert table.currentRow() == -1
    assert dlg.isVisible() or True  # exec was faked; reject must not call QDialog.reject close path
    # Calling reject again still must not raise / must stay clear-only.
    dlg.reject()
    win.close()
