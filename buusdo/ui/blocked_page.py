"""Non-bypassable anti-cheat / unsafe-target block page (C1)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QListWidget, QVBoxLayout, QWidget

from buusdo.core.errors import UnsafeTargetError
from buusdo.ui.theme import COLOR_BLOCK


class BlockedPage(QWidget):
    """Shown when UnsafeTargetError is raised. No continue-anyway control."""

    def __init__(self, error: UnsafeTargetError, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("blockedPage")
        layout = QVBoxLayout(self)

        title = QLabel("已阻断 — 检测到不安全目标")
        title.setObjectName("blockTitle")
        title.setAccessibleName("安全阻断标题")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet(f"color: {COLOR_BLOCK};")
        layout.addWidget(title)

        summary = QLabel(
            f"目标「{error.target_name}」无法应用增强。\n"
            f"原因：{error.reason}\n\n"
            "存在反作弊或无法确认安全时一律拒绝，不可继续。"
            "（本页无「继续」按钮，此为强制门禁。）"
        )
        summary.setWordWrap(True)
        summary.setAccessibleName("阻断说明")
        layout.addWidget(summary)

        if error.evidence:
            evidence_label = QLabel("证据：")
            evidence_label.setAccessibleName("证据列表标题")
            layout.addWidget(evidence_label)
            evidence_list = QListWidget()
            evidence_list.setAccessibleName("反作弊证据列表")
            for item in error.evidence:
                evidence_list.addItem(item)
            layout.addWidget(evidence_list)

        layout.addStretch(1)
