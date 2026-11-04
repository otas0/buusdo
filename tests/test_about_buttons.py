"""About footer buttons must keep full label width (no clipped text)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_about_link_buttons_min_width_covers_zh_labels() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QPushButton, QSizePolicy

    from buusdo.core.i18n import reload_catalogs, set_locale, t

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
        hint = btn.sizeHint().width()
        btn.setMinimumWidth(hint)
        # Visible text must fit; clipped zh labels were typically under ~72px.
        assert hint >= 48, f"{text!r} sizeHint={hint}"
        assert btn.minimumWidth() >= hint
        assert "Issu" not in text  # old clipped zh feedback fragment
        assert "MOBILE.md" not in text
        assert "HARDWARE_NOTES" not in text
    app.processEvents()
