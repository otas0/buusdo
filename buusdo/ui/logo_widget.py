"""Themed SVG wordmark helpers (logo.svg from logo.png)."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, Qt, QSize
from PySide6.QtGui import QGuiApplication, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QLabel, QSizePolicy

from buusdo.assets import logo_svg_path
from buusdo.ui import theme as theme_mod


def _themed_svg_bytes(*, ink: str, paper: str, accent: str) -> bytes:
    path = logo_svg_path()
    raw = path.read_text(encoding="utf-8") if path.is_file() else ""
    if not raw:
        return b""
    out = (
        raw.replace("#111111", ink)
        .replace("#EDEDED", paper)
        .replace("#6B6B6B", accent)
    )
    return out.encode("utf-8")


def logo_pixmap(
    height: int = 36,
    *,
    ink: str | None = None,
    paper: str | None = None,
    accent: str | None = None,
) -> QPixmap:
    """Rasterize logo.svg at *logical* height, at device pixel ratio (sharp on Retina)."""
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
        vb = QRectF(0, 0, 500, 120)
    dpr = 1.0
    screen = QGuiApplication.primaryScreen()
    if screen is not None:
        dpr = float(screen.devicePixelRatio())
    dpr = max(1.0, dpr)
    logical_w = max(1, int(round(height * (vb.width() / vb.height()))))
    pixel_h = max(1, int(round(height * dpr)))
    pixel_w = max(1, int(round(logical_w * dpr)))
    pix = QPixmap(QSize(pixel_w, pixel_h))
    pix.setDevicePixelRatio(dpr)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()
    return pix


def make_logo_label(height: int = 36, parent=None) -> QLabel:
    label = QLabel(parent)
    label.setObjectName("brandMark")
    label.setAccessibleName("buusdo logo")
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    pix = logo_pixmap(height)
    if not pix.isNull():
        label.setPixmap(pix)
    label.setProperty("logoHeight", height)
    return label


def refresh_logo_label(label: QLabel, height: int | None = None) -> None:
    h = height if height is not None else int(label.property("logoHeight") or 36)
    label.setProperty("logoHeight", h)
    pix = logo_pixmap(h)
    if not pix.isNull():
        label.setPixmap(pix)
