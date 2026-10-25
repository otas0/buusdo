"""Generate a simplified parallelogram tray icon inspired by the buusdo logo mark."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QPolygon


def make_mark_icon(size: int = 64) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Two overlapping parallelograms (logo "uu" mark), black + dark grey.
    def para(ox: int, oy: int, color: QColor) -> None:
        w, h, skew = int(size * 0.42), int(size * 0.55), int(size * 0.18)
        pts = QPolygon(
            [
                QPoint(ox + skew, oy),
                QPoint(ox + skew + w, oy),
                QPoint(ox + w, oy + h),
                QPoint(ox, oy + h),
            ]
        )
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(pts)

    margin = int(size * 0.12)
    para(margin, margin + 4, QColor("#000000"))
    para(margin + int(size * 0.16), margin, QColor("#4A4A4A"))
    painter.end()
    return QIcon(pix)
