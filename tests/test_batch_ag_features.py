"""Batch AG: PySide6 pin notes; LaunchAgent exit-after-ts; conflict Esc; Steam Ctrl+N."""

from __future__ import annotations

import importlib.util
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


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pyside6_essentials_pinned_in_pyproject() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'PySide6-Essentials==6.12.0' in text
    lock = Path("uv.lock").read_text(encoding="utf-8")
    assert "pyside6-essentials" in lock
    assert 'specifier = "==6.12.0"' in lock or "6.12.0" in lock


def test_exit_follows_latest_timestamp() -> None:
    mod = _load(
        "watch_ci_billing_log_assert",
        Path("scripts/watch_ci_billing_log_assert.py"),
    )
    ok, _ = mod.exit_follows_latest_timestamp(
        "---- 2026-10-25T12:00:00Z watch_ci_billing ----\n"
        "ok\n"
        "---- exit 1 ----\n"
    )
    assert ok is True
    bad, reason = mod.exit_follows_latest_timestamp(
        "---- 2026-10-25T12:00:00Z watch_ci_billing ----\n"
        "ok\n"
        "---- 2026-10-25T13:00:00Z watch_ci_billing ----\n"
        "still running\n"
    )
    assert bad is False
    assert "exit" in reason
    # Stale exit before a newer timestamp must not count.
    stale, _ = mod.exit_follows_latest_timestamp(
        "---- 2026-10-25T12:00:00Z watch_ci_billing ----\n"
        "---- exit 0 ----\n"
        "---- 2026-10-25T13:00:00Z watch_ci_billing ----\n"
        "no exit yet\n"
    )
    assert stale is False


def test_appended_chunk_requires_growth() -> None:
    mod = _load(
        "watch_ci_billing_log_assert",
        Path("scripts/watch_ci_billing_log_assert.py"),
    )
    text = "---- 2026-10-25T12:00:00Z watch_ci_billing ----\n---- exit 0 ----\n"
    ok, _ = mod.appended_chunk_ok(text, before_nbytes=0)
    assert ok is True
    no_grow, reason = mod.appended_chunk_ok(text, before_nbytes=len(text.encode()))
    assert no_grow is False
    assert "grow" in reason


def test_steam_try_next_shortcut_copy() -> None:
    assert "Ctrl+N" in t("settings.steam_uri_try_next_shortcut")


def test_readme_devui_and_cron() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert 'uv pip install -e ".[devui]"' in readme
    assert "assert_watch_ci_billing_log_append.sh" in readme
    assert "Ctrl+N" in readme
    assert "LaunchAgent only" in readme or "LaunchAgent-only" in readme or (
        "LaunchAgent only" in Path("docs/CI_ARTIFACTS.md").read_text(encoding="utf-8")
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


def test_conflict_esc_clears_selection() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeySequence, QShortcut
    from PySide6.QtWidgets import QApplication, QDialog, QPushButton, QTableWidget

    from buusdo.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    shown: dict[str, QDialog] = {}

    def _fake_exec(self: QDialog) -> int:  # noqa: ANN001
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
                    {"action": "create", "path": "b.ini", "detail": "new"},
                ],
            }
        )
    dlg = shown["dlg"]
    table = dlg.findChild(QTableWidget)
    assert table is not None
    assert table.selectionMode() == QTableWidget.SelectionMode.ExtendedSelection
    esc_shortcuts = [
        s
        for s in dlg.findChildren(QShortcut)
        if s.key() == QKeySequence(Qt.Key.Key_Escape)
        or s.key().toString() in ("Esc", "Escape")
    ]
    assert esc_shortcuts, "conflict dialog must wire Esc → clear_row_selections"
    clear_btns = [
        b for b in dlg.findChildren(QPushButton) if b.text() in ("Clear selection", "取消选中")
    ]
    assert clear_btns
    table.setCurrentCell(0, 0)
    table.selectRow(0)
    app.processEvents()
    assert table.currentRow() == 0
    esc_shortcuts[0].activated.emit()
    app.processEvents()
    assert table.currentRow() == -1
    assert table.selectedItems() == []
    table.setCurrentCell(1, 0)
    clear_btns[0].click()
    app.processEvents()
    assert table.currentRow() == -1
    win.close()


def test_steam_try_next_shortcut_tracks_button() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from buusdo.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    win = MainWindow(backend=_StubBackend())
    assert win._steam_try_next_shortcut.isEnabled() is False
    win._btn_steam_try_next.setEnabled(True)
    win._steam_try_next_shortcut.setEnabled(True)
    assert "N" in win._steam_try_next_shortcut.key().toString()
    # Refresh with no game keeps both disabled.
    win._refresh_steam_uri_controls()
    assert win._btn_steam_try_next.isEnabled() is False
    assert win._steam_try_next_shortcut.isEnabled() is False
    win.close()
    app.processEvents()
