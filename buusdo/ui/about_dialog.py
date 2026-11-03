"""About dialog — version, license pointer, feedback link."""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from buusdo import __version__
from buusdo.companion.honesty import MOBILE_NON_GOALS
from buusdo.core.hardware_notes import HARDWARE_NOTES
from buusdo.core.i18n import t
from buusdo.core.platform_detect import host_adapter_summary
from buusdo.core.urls import DOCS_HARDWARE_URL, DOCS_MOBILE_URL, FEEDBACK_URL, REPO_URL
from buusdo.ui.logo_widget import make_logo_label

LICENSE_NAME = "See repository LICENSE (MIT)"


def show_about_dialog(parent=None) -> None:
    dlg = QDialog(parent)
    dlg.setObjectName("instrumentDialog")
    dlg.setWindowTitle(t("about.title"))
    dlg.setWindowIcon(parent.windowIcon() if parent is not None else dlg.windowIcon())
    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(10)

    mark = make_logo_label(22, dlg)
    mark.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    layout.addWidget(mark, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    layout.addWidget(QLabel(t("about.version", version=__version__)))
    layout.addWidget(QLabel(t("about.channel")))
    layout.addWidget(QLabel(t("about.license", license=LICENSE_NAME)))
    support = QLabel(t("about.support_os"))
    support.setWordWrap(True)
    support.setObjectName("brandSubtitle")
    layout.addWidget(support)
    note = QLabel(t("about.non_goals"))
    note.setWordWrap(True)
    note.setObjectName("brandSubtitle")
    layout.addWidget(note)

    mobile_hdr = QLabel(t("companion.about_section"))
    mobile_hdr.setObjectName("sectionLabel")
    layout.addWidget(mobile_hdr)
    mobile_intro = QLabel(t("companion.about_intro"))
    mobile_intro.setWordWrap(True)
    mobile_intro.setObjectName("brandSubtitle")
    layout.addWidget(mobile_intro)
    for ng in MOBILE_NON_GOALS:
        line = QLabel(f"• {t(ng.title_key)} — {t(ng.body_key)}")
        line.setWordWrap(True)
        line.setObjectName("brandSubtitle")
        layout.addWidget(line)

    hw_hdr = QLabel(t("hw.section"))
    hw_hdr.setObjectName("sectionLabel")
    layout.addWidget(hw_hdr)
    adapters = host_adapter_summary()
    if adapters:
        adapt = QLabel(t("hw.adapters", summary=adapters))
        adapt.setWordWrap(True)
        adapt.setObjectName("brandSubtitle")
        adapt.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(adapt)
    for hn in HARDWARE_NOTES:
        line = QLabel(f"• {t(hn.title_key)} — {t(hn.body_key)}")
        line.setWordWrap(True)
        line.setObjectName("brandSubtitle")
        layout.addWidget(line)
    hw_foot = QLabel(t("hw.not_a_boost"))
    hw_foot.setWordWrap(True)
    hw_foot.setObjectName("brandSubtitle")
    layout.addWidget(hw_foot)

    row = QHBoxLayout()
    feedback = QPushButton(t("about.feedback"))
    feedback.setObjectName("accentAction")
    feedback.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))
    repo = QPushButton(t("about.repo"))
    repo.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(REPO_URL)))
    docs_mobile = QPushButton(t("about.docs_mobile"))
    docs_mobile.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DOCS_MOBILE_URL)))
    docs_hw = QPushButton(t("about.docs_hardware"))
    docs_hw.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DOCS_HARDWARE_URL)))
    close = QPushButton(t("about.close"))
    close.setObjectName("primaryAction")
    close.setDefault(True)
    close.clicked.connect(dlg.accept)
    row.addWidget(feedback)
    row.addWidget(repo)
    row.addWidget(docs_mobile)
    row.addWidget(docs_hw)
    row.addWidget(close)
    layout.addLayout(row)
    # Narrow windows: long DE/RU platform copy must wrap, not stretch the dialog.
    dlg.setMinimumWidth(360)
    dlg.resize(480, 620)
    dlg.exec()
