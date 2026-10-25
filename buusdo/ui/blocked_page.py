"""Non-bypassable anti-cheat / unsafe-target block page (C1)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QListWidget, QVBoxLayout, QWidget

from buusdo.core.errors import UnsafeTargetError


class BlockedPage(QWidget):
    """Shown when UnsafeTargetError is raised. No continue-anyway control."""

    def __init__(self, error: UnsafeTargetError, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        title = QLabel("已阻断 — 检测到不安全目标")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        summary = QLabel(
            f"目标「{error.target_name}」无法应用增强。\n"
            f"原因：{error.reason}\n\n"
            "存在反作弊或无法确认安全时一律拒绝，不可继续。"
        )
        summary.setWordWrap(True)
        layout.addWidget(summary)

        if error.evidence:
            layout.addWidget(QLabel("证据："))
            evidence_list = QListWidget()
            for item in error.evidence:
                evidence_list.addItem(item)
            layout.addWidget(evidence_list)

        layout.addStretch(1)
