"""About dialog — version, license pointer, feedback link."""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFontMetrics
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from buusdo import __version__
from buusdo.companion.honesty import MOBILE_NON_GOALS
from buusdo.core.hardware_notes import HARDWARE_NOTES
from buusdo.core.i18n import t
from buusdo.core.platform_detect import host_adapter_summary
from buusdo.core.urls import (
    DOCS_HARDWARE_URL,
    DOCS_MOBILE_URL,
    DOCS_USER_GUIDE_URL,
    FEEDBACK_URL,
    REPO_URL,
)
from buusdo.ui.logo_widget import make_logo_label

LICENSE_NAME = "See repository LICENSE (MIT)"


def _fit_button_width(btn: QPushButton) -> None:
    """Pin min width using font metrics — monospace + CJK undersizes sizeHint."""
    fm = QFontMetrics(btn.font())
    # Style padding is ~12px each side; add slack so glyphs are not clipped.
    text_w = fm.horizontalAdvance(btn.text())
    btn.setMinimumWidth(text_w + 28)
    btn.setMinimumHeight(max(btn.sizeHint().height(), fm.height() + 14))


def show_about_dialog(parent=None) -> None:
    dlg = QDialog(parent)
    dlg.setObjectName("instrumentDialog")
    dlg.setWindowTitle(t("about.title"))
    dlg.setWindowIcon(parent.windowIcon() if parent is not None else dlg.windowIcon())
    root = QVBoxLayout(dlg)
    root.setContentsMargins(16, 16, 16, 16)
    root.setSpacing(10)

    scroll = QScrollArea(dlg)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    body = QWidget()
    layout = QVBoxLayout(body)
    layout.setContentsMargins(0, 0, 8, 0)
    layout.setSpacing(10)

    mark = make_logo_label(40, body)
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
    layout.addStretch(1)

    scroll.setWidget(body)
    root.addWidget(scroll, 1)

    def _link_btn(label: str, url: str, tip: str = "") -> QPushButton:
        btn = QPushButton(label)
        btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        _fit_button_width(btn)
        if tip:
            btn.setToolTip(tip)
        btn.clicked.connect(lambda _=False, u=url: QDesktopServices.openUrl(QUrl(u)))
        return btn

    # Footer stays outside the scroll area so links stay visible and body text
    # (e.g. HARDWARE_NOTES.md in hw.not_a_boost) is not clipped mid-glyph.
    row1 = QHBoxLayout()
    row1.setSpacing(8)
    feedback = _link_btn(t("about.feedback"), FEEDBACK_URL, FEEDBACK_URL)
    feedback.setObjectName("accentAction")
    _fit_button_width(feedback)
    repo = _link_btn(t("about.repo"), REPO_URL, REPO_URL)
    docs_guide = _link_btn(
        t("about.docs_user_guide"), DOCS_USER_GUIDE_URL, "docs/user-guide/"
    )
    row1.addWidget(feedback)
    row1.addWidget(repo)
    row1.addWidget(docs_guide)
    row1.addStretch(1)
    root.addLayout(row1)

    row2 = QHBoxLayout()
    row2.setSpacing(8)
    docs_mobile = _link_btn(
        t("about.docs_mobile"), DOCS_MOBILE_URL, "docs/MOBILE.md"
    )
    docs_hw = _link_btn(
        t("about.docs_hardware"), DOCS_HARDWARE_URL, "docs/HARDWARE_NOTES.md"
    )
    close = QPushButton(t("about.close"))
    close.setObjectName("primaryAction")
    close.setDefault(True)
    close.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
    _fit_button_width(close)
    close.clicked.connect(dlg.accept)
    row2.addWidget(docs_mobile)
    row2.addWidget(docs_hw)
    row2.addStretch(1)
    row2.addWidget(close)
    root.addLayout(row2)

    dlg.setMinimumWidth(420)
    dlg.setMinimumHeight(420)
    dlg.resize(520, 560)
    dlg.exec()
