"""During scan, language/theme chrome is disabled; idle restores it."""

from __future__ import annotations

import pytest


def test_scan_chrome_disables_lang_and_theme(qapp=None) -> None:  # noqa: ANN001
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QPushButton

    from buusdo.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    # Avoid constructing the full window (Steam scan, tray, etc.): exercise the
    # helper the same way MainWindow wires it.
    class Stub:
        def __init__(self) -> None:
            self._theme_btn = QPushButton("theme")
            self._lang_btn = QPushButton("lang")
            self._lang = None

        _set_scan_chrome_enabled = MainWindow._set_scan_chrome_enabled

    stub = Stub()
    stub._set_scan_chrome_enabled(False)
    assert not stub._theme_btn.isEnabled()
    assert not stub._lang_btn.isEnabled()
    stub._set_scan_chrome_enabled(True)
    assert stub._theme_btn.isEnabled()
    assert stub._lang_btn.isEnabled()
    app.processEvents()
