"""LanguageDialog accessibility names and keyboard navigation."""

from __future__ import annotations

import os

import pytest

# Prefer offscreen for CI / headless macOS agent runs.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture()
def qapp():
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def test_language_dialog_accessible_names(qapp) -> None:
    from PySide6.QtCore import Qt

    from buusdo.core.i18n import reload_catalogs, set_locale
    from buusdo.ui.language_dialog import LanguageDialog

    reload_catalogs()
    set_locale("en")
    dlg = LanguageDialog(first_run=False)
    assert dlg.accessibleName()
    assert dlg._search.accessibleName()
    assert dlg._list.accessibleName()
    assert dlg._ok.accessibleName()
    assert dlg.objectName() == "languageDialog"
    assert dlg._search.objectName() == "languageSearch"
    assert dlg._list.objectName() == "languageList"
    assert dlg._ok.objectName() == "languageConfirm"
    assert dlg._list.count() > 0
    item = dlg._list.item(0)
    assert item.data(Qt.ItemDataRole.AccessibleTextRole)
    dlg.close()


def test_language_dialog_keyboard_filter_and_down(qapp) -> None:
    from PySide6.QtCore import Qt

    from buusdo.core.i18n import reload_catalogs, set_locale
    from buusdo.ui.language_dialog import LanguageDialog

    reload_catalogs()
    set_locale("en")
    dlg = LanguageDialog(first_run=False)
    # Drive filter via the same textChanged path the search box uses (no IME).
    dlg._search.setText("japan")
    qapp.processEvents()
    codes = [
        dlg._list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(dlg._list.count())
    ]
    assert "ja" in codes

    dlg._search.setText("portug")
    qapp.processEvents()
    codes = [
        dlg._list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(dlg._list.count())
    ]
    assert "pt" in codes and "pt-BR" in codes

    # Single match → Return accepts via _focus_list_or_accept
    dlg._search.setText("日本語")
    qapp.processEvents()
    assert dlg._list.count() == 1
    dlg._focus_list_or_accept()
    assert dlg.result() == 1  # Accepted
    assert dlg.selected_locale() == "ja"


def test_language_dialog_down_focuses_list(qapp) -> None:
    from buusdo.core.i18n import reload_catalogs, set_locale
    from buusdo.ui.language_dialog import LanguageDialog

    reload_catalogs()
    set_locale("en")
    dlg = LanguageDialog(first_run=False)
    dlg._search.setText("")
    dlg._focus_list()
    assert dlg._list.currentRow() >= 0
    dlg.close()


def test_first_run_escape_defaults_to_english(qapp) -> None:
    from buusdo.core.i18n import reload_catalogs, set_locale
    from buusdo.ui.language_dialog import LanguageDialog, needs_locale_pick

    reload_catalogs()
    set_locale("en")
    assert needs_locale_pick({}) is True
    assert needs_locale_pick({"locale": None}) is True
    assert needs_locale_pick({"locale": "zh-Hant"}) is False
    dlg = LanguageDialog(first_run=True)
    dlg.reject()  # first-run maps reject → accept English
    qapp.processEvents()
    assert dlg.result() == 1
    assert dlg.selected_locale() == "en"
