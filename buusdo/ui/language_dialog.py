"""Language picker popup with search — one language at a time (monolingual UI)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from buusdo.core.i18n import (
    available_locales,
    filter_locales,
    get_locale,
    locale_display_name,
    t,
)


class LanguageDialog(QDialog):
    """Modal language chooser. First-run: reject/close falls back to English."""

    def __init__(self, parent=None, *, first_run: bool = False):
        super().__init__(parent)
        self._first_run = first_run
        self._selected = get_locale() if get_locale() in available_locales() else "en"
        self.setModal(True)
        self.setObjectName("languageDialog")
        self.setAccessibleName(t("lang.pick_title") if not first_run else "Language")
        self.setWindowTitle(t("lang.pick_title") if not first_run else "buusdo")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        hint = QLabel(t("lang.pick_hint") if not first_run else "Language")
        if first_run:
            # Bootstrap chrome: native names only in the list; keep chrome minimal.
            hint.setText("Language")
        hint.setWordWrap(True)
        hint.setObjectName("sectionLabel")
        hint.setAccessibleName(hint.text())
        layout.addWidget(hint)

        self._search = QLineEdit()
        self._search.setObjectName("languageSearch")
        self._search.setAccessibleName(
            t("lang.search_placeholder") if not first_run else "Search"
        )
        self._search.setPlaceholderText(
            t("lang.search_placeholder") if not first_run else "Search"
        )
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._refilter)
        self._search.returnPressed.connect(self._focus_list_or_accept)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setObjectName("languageList")
        self._list.setAccessibleName(t("lang.pick_title") if not first_run else "Languages")
        self._list.setMinimumHeight(260)
        self._list.setMinimumWidth(320)
        self._list.itemDoubleClicked.connect(self._accept_current)
        self._list.itemSelectionChanged.connect(self._sync_selection)
        self._list.itemActivated.connect(self._accept_current)
        layout.addWidget(self._list, stretch=1)

        buttons = QDialogButtonBox()
        self._ok = buttons.addButton(
            t("lang.confirm") if not first_run else "OK",
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self._ok.setObjectName("languageConfirm")
        self._ok.setAccessibleName(t("lang.confirm") if not first_run else "OK")
        self._cancel = None
        if not first_run:
            self._cancel = buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
            self._cancel.setObjectName("languageCancel")
            self._cancel.setAccessibleName("Cancel")
        buttons.accepted.connect(self._accept_current)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Down from search focuses the list; Escape still rejects via QDialog.
        QShortcut(QKeySequence(Qt.Key.Key_Down), self._search, activated=self._focus_list)

        self._refilter("")
        self._search.setFocus(Qt.FocusReason.OtherFocusReason)

    def selected_locale(self) -> str:
        return self._selected

    def _focus_list(self) -> None:
        if self._list.count() == 0:
            return
        if self._list.currentRow() < 0:
            self._list.setCurrentRow(0)
        self._list.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _focus_list_or_accept(self) -> None:
        # Return in search: if a single match, accept; else move focus to list.
        if self._list.count() == 1:
            self._list.setCurrentRow(0)
            self._accept_current()
            return
        self._focus_list()

    def _refilter(self, text: str = "") -> None:
        self._list.clear()
        current = self._selected
        for code in filter_locales(text):
            item = QListWidgetItem(locale_display_name(code))
            item.setData(Qt.ItemDataRole.UserRole, code)
            item.setData(Qt.ItemDataRole.AccessibleTextRole, locale_display_name(code))
            self._list.addItem(item)
            if code == current:
                self._list.setCurrentItem(item)
        if self._list.count() and self._list.currentItem() is None:
            self._list.setCurrentRow(0)

    def _sync_selection(self) -> None:
        item = self._list.currentItem()
        if item is not None:
            code = item.data(Qt.ItemDataRole.UserRole)
            if code:
                self._selected = str(code)

    def _accept_current(self) -> None:
        self._sync_selection()
        if not self._selected:
            self._selected = "en"
        self.accept()

    def reject(self) -> None:
        if self._first_run:
            self._selected = "en"
            self.accept()
            return
        super().reject()


def needs_locale_pick(settings: dict) -> bool:
    loc = settings.get("locale")
    return loc not in available_locales()
