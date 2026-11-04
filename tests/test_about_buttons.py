"""About footer buttons and body must not clip CJK / long paths."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_about_link_buttons_min_width_covers_zh_labels() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtGui import QFontMetrics
    from PySide6.QtWidgets import QApplication, QPushButton, QSizePolicy

    from buusdo.core.i18n import reload_catalogs, set_locale, t
    from buusdo.ui.about_dialog import _fit_button_width

    app = QApplication.instance() or QApplication([])
    reload_catalogs()
    set_locale("zh")
    labels = [
        t("about.feedback"),
        t("about.repo"),
        t("about.docs_user_guide"),
        t("about.docs_mobile"),
        t("about.docs_hardware"),
        t("about.close"),
    ]
    for text in labels:
        btn = QPushButton(text)
        btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        _fit_button_width(btn)
        fm = QFontMetrics(btn.font())
        assert btn.minimumWidth() >= fm.horizontalAdvance(text) + 24
        assert "Issu" not in text
        assert "MOBILE.md" not in text
        assert "HARDWARE_NOTES" not in text
    app.processEvents()


def test_about_dialog_scrolls_hw_foot_fully() -> None:
    """hw.not_a_boost ends with HARDWARE_NOTES.md — must live in a scroll area."""
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QDialog, QLabel, QScrollArea

    from buusdo.core.i18n import reload_catalogs, set_locale, t
    from buusdo.ui import about_dialog as about_mod

    app = QApplication.instance() or QApplication([])
    reload_catalogs()
    set_locale("zh")

    # Avoid blocking on exec(); build the dialog the same way, then inspect.
    original_exec = QDialog.exec

    captured: list[QDialog] = []

    def _capture(self: QDialog) -> int:  # noqa: ANN001
        captured.append(self)
        return 0

    QDialog.exec = _capture  # type: ignore[method-assign]
    try:
        about_mod.show_about_dialog(None)
    finally:
        QDialog.exec = original_exec  # type: ignore[method-assign]

    assert captured, "dialog was not built"
    dlg = captured[0]
    scrolls = dlg.findChildren(QScrollArea)
    assert scrolls, "About body must use QScrollArea so footer text is not clipped"
    labels = [
        lab
        for lab in scrolls[0].findChildren(QLabel)
        if "HARDWARE_NOTES.md" in lab.text()
    ]
    assert labels, f"expected hw.not_a_boost text, got {[t('hw.not_a_boost')]!r}"
    foot = labels[0]
    assert foot.wordWrap()
    # Full string present (not truncated mid-path in the widget text).
    assert foot.text() == t("hw.not_a_boost")
    assert foot.text().endswith("HARDWARE_NOTES.md。")
    app.processEvents()
    dlg.close()
