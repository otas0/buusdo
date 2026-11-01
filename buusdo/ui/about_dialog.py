"""About dialog — version, license pointer, feedback link."""

from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from buusdo import __version__
from buusdo.core.i18n import t

FEEDBACK_URL = "https://github.com/otas0/buusdo/issues"
REPO_URL = "https://github.com/otas0/buusdo"
LICENSE_NAME = "See repository LICENSE (MIT)"


def show_about_dialog(parent=None) -> None:
    dlg = QDialog(parent)
    dlg.setObjectName("instrumentDialog")
    dlg.setWindowTitle(t("about.title"))
    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(10)

    title = QLabel("buusdo")
    title.setObjectName("brandTitle")
    layout.addWidget(title)

    layout.addWidget(QLabel(t("about.version", version=__version__)))
    layout.addWidget(QLabel(t("about.channel")))
    layout.addWidget(QLabel(t("about.license", license=LICENSE_NAME)))
    layout.addWidget(QLabel(t("about.support_os")))
    note = QLabel(t("about.non_goals"))
    note.setWordWrap(True)
    note.setObjectName("brandSubtitle")
    layout.addWidget(note)

    row = QHBoxLayout()
    feedback = QPushButton(t("about.feedback"))
    feedback.setObjectName("accentAction")
    feedback.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))
    repo = QPushButton(t("about.repo"))
    repo.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(REPO_URL)))
    close = QPushButton(t("about.close"))
    close.setObjectName("primaryAction")
    close.setDefault(True)
    close.clicked.connect(dlg.accept)
    row.addWidget(feedback)
    row.addWidget(repo)
    row.addWidget(close)
    layout.addLayout(row)
    dlg.resize(420, 280)
    dlg.exec()
