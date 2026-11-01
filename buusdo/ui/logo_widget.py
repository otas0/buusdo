"""Wordmark logo for UI chrome — prefer crisp PNG (SVG kept as asset)."""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QGuiApplication, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy

from buusdo.assets import logo_path, logo_svg_path
from buusdo.ui import theme as theme_mod

try:
    from PySide6.QtCore import QByteArray, QRectF
    from PySide6.QtSvg import QSvgRenderer

    _HAS_SVG = True
except ImportError:  # pragma: no cover
    _HAS_SVG = False


def _content_bbox(img: QImage) -> tuple[int, int, int, int] | None:
    """Return (x, y, w, h) of non-near-white opaque pixels."""
    w, h = img.width(), img.height()
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            c = img.pixelColor(x, y)
            if c.alpha() < 20:
                continue
            # Treat near-white as background
            if c.red() > 245 and c.green() > 245 and c.blue() > 245:
                continue
            minx = min(minx, x)
            miny = min(miny, y)
            maxx = max(maxx, x)
            maxy = max(maxy, y)
    if maxx < minx:
        return None
    pad = 2
    x0 = max(0, minx - pad)
    y0 = max(0, miny - pad)
    x1 = min(w - 1, maxx + pad)
    y1 = min(h - 1, maxy + pad)
    return x0, y0, x1 - x0 + 1, y1 - y0 + 1


def _recolor_ink(img: QImage, ink: str) -> QImage:
    """Map dark ink pixels to theme ink; keep transparency (drop white bg)."""
    from PySide6.QtGui import QColor

    out = QImage(img.size(), QImage.Format.Format_ARGB32_Premultiplied)
    out.fill(Qt.GlobalColor.transparent)
    target = QColor(ink)
    for y in range(img.height()):
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            if c.alpha() < 20:
                continue
            if c.red() > 245 and c.green() > 245 and c.blue() > 245:
                continue
            # Mid grays (logo accent parallelogram) → muted blend toward ink
            lum = (c.red() + c.green() + c.blue()) / 3
            if lum > 40:
                # Keep as slightly lighter ink (accent)
                a = QColor(target)
                a.setAlpha(180)
                out.setPixelColor(x, y, a)
            else:
                out.setPixelColor(x, y, target)
    return out


def _pixmap_from_png(height: int, *, ink: str) -> QPixmap:
    path = logo_path()
    if not path.is_file():
        return QPixmap()
    src = QImage(str(path))
    if src.isNull():
        return QPixmap()
    bbox = _content_bbox(src)
    if bbox:
        x, y, w, h = bbox
        src = src.copy(x, y, w, h)
    src = _recolor_ink(src, ink)

    dpr = 1.0
    screen = QGuiApplication.primaryScreen()
    if screen is not None:
        dpr = max(1.0, float(screen.devicePixelRatio()))
    logical_w = max(1, int(round(height * (src.width() / max(1, src.height())))))
    pixel_w = max(1, int(round(logical_w * dpr)))
    pixel_h = max(1, int(round(height * dpr)))
    scaled = src.scaled(
        pixel_w,
        pixel_h,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    pix = QPixmap.fromImage(scaled)
    pix.setDevicePixelRatio(dpr)
    return pix


def _pixmap_from_svg(height: int, *, ink: str, paper: str, accent: str) -> QPixmap:
    if not _HAS_SVG:
        return QPixmap()
    path = logo_svg_path()
    if not path.is_file():
        return QPixmap()
    raw = (
        path.read_text(encoding="utf-8")
        .replace("#111111", ink)
        .replace("#EDEDED", paper)
        .replace("#6B6B6B", accent)
    )
    renderer = QSvgRenderer(QByteArray(raw.encode()))
    if not renderer.isValid():
        return QPixmap()
    vb = renderer.viewBoxF()
    if vb.width() <= 0 or vb.height() <= 0:
        vb = QRectF(0, 0, 500, 120)
    dpr = 1.0
    screen = QGuiApplication.primaryScreen()
    if screen is not None:
        dpr = max(1.0, float(screen.devicePixelRatio()))
    logical_w = max(1, int(round(height * (vb.width() / vb.height()))))
    pixel_h = max(1, int(round(height * dpr)))
    pixel_w = max(1, int(round(logical_w * dpr)))
    pix = QPixmap(QSize(pixel_w, pixel_h))
    pix.setDevicePixelRatio(dpr)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer.render(painter)
    painter.end()
    return pix


def logo_pixmap(
    height: int = 22,
    *,
    ink: str | None = None,
    paper: str | None = None,
    accent: str | None = None,
) -> QPixmap:
    """Rasterize wordmark at *logical* height (device-pixel sharp). Prefers PNG."""
    ink = ink or theme_mod.COLOR_INK
    paper = paper or theme_mod.COLOR_BG
    accent = accent or theme_mod.COLOR_MUTED
    pix = _pixmap_from_png(height, ink=ink)
    if pix.isNull():
        pix = _pixmap_from_svg(height, ink=ink, paper=paper, accent=accent)
    return pix


def make_logo_label(height: int = 22, parent=None) -> QLabel:
    label = QLabel(parent)
    label.setObjectName("brandMark")
    label.setAccessibleName("buusdo logo")
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    label.setScaledContents(False)
    pix = logo_pixmap(height)
    if not pix.isNull():
        label.setPixmap(pix)
        label.setFixedHeight(height + 2)
        label.setFixedWidth(int(pix.width() / max(1.0, pix.devicePixelRatio())) + 2)
    label.setProperty("logoHeight", height)
    return label


def refresh_logo_label(label: QLabel, height: int | None = None) -> None:
    h = height if height is not None else int(label.property("logoHeight") or 22)
    label.setProperty("logoHeight", h)
    pix = logo_pixmap(h)
    if pix.isNull():
        return
    label.setPixmap(pix)
    label.setFixedHeight(h + 2)
    label.setFixedWidth(int(pix.width() / max(1.0, pix.devicePixelRatio())) + 2)
