"""Narrow About dialog: DE/RU support_os must wrap rather than force a huge width."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_about_support_os_wraps_de_ru() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QLabel

    from buusdo.core.i18n import reload_catalogs, set_locale, t

    app = QApplication.instance() or QApplication([])
    reload_catalogs()
    for code in ("de", "ru", "en"):
        set_locale(code)
        lab = QLabel(t("about.support_os"))
        lab.setWordWrap(True)
        lab.setFixedWidth(360)
        lab.adjustSize()
        # Wrapped multi-line at 360px; single-line height is typically ~16–24.
        # Wrapped multi-line; single-line chrome is typically ~16–24px.
        assert lab.height() >= 32, f"{code} height={lab.height()} text={lab.text()!r}"
        # Must not require an absurd width when wrap is on.
        lab2 = QLabel(t("about.support_os"))
        lab2.setWordWrap(True)
        lab2.adjustSize()
        assert lab2.sizeHint().width() <= 520 or lab.height() >= 36
    app.processEvents()
