"""Themed SVG wordmark helpers (logo.svg from logo.png)."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, Qt, QSize
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QLabel

from buusdo.assets import logo_svg_path
from buusdo.ui import theme as theme_mod


def _themed_svg_bytes(*, ink: str, paper: str, accent: str) -> bytes:
    path = logo_svg_path()
    raw = path.read_text(encoding="utf-8") if path.is_file() else ""
    if not raw:
        return b""
    # Tokens written by scripts/generate_logo_svg.py
    out = (
        raw.replace("#111111", ink)
        .replace("#EDEDED", paper)
        .replace("#6B6B6B", accent)
    )
    return out.encode("utf-8")


def logo_pixmap(
    height: int = 56,
    *,
    ink: str | None = None,
    paper: str | None = None,
    accent: str | None = None,
) -> QPixmap:
    """Rasterize logo.svg at *height* using current (or override) theme colors."""
    ink = ink or theme_mod.COLOR_INK
    paper = paper or theme_mod.COLOR_BG
    accent = accent or theme_mod.COLOR_MUTED
    data = _themed_svg_bytes(ink=ink, paper=paper, accent=accent)
    if not data:
        return QPixmap()
    renderer = QSvgRenderer(QByteArray(data))
    if not renderer.isValid():
        return QPixmap()
    vb = renderer.viewBoxF()
    if vb.width() <= 0 or vb.height() <= 0:
        vb = QRectF(0, 0, 500, 500)
    width = max(1, int(round(height * (vb.width() / vb.height()))))
    pix = QPixmap(QSize(width, height))
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return pix


def make_logo_label(height: int = 56, parent=None) -> QLabel:
    label = QLabel(parent)
    label.setObjectName("brandMark")
    label.setAccessibleName("buusdo logo")
    pix = logo_pixmap(height)
    if not pix.isNull():
        label.setPixmap(pix)
    return label


def refresh_logo_label(label: QLabel, height: int = 56) -> None:
    pix = logo_pixmap(height)
    if not pix.isNull():
        label.setPixmap(pix)
