"""Wordmark logo for UI chrome — prefer crisp PNG (SVG kept as asset)."""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QGuiApplication, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy

from buusdo.assets import logo_svg_path, logo_wordmark_path
from buusdo.ui import theme as theme_mod

try:
    from PySide6.QtCore import QByteArray, QRectF
    from PySide6.QtSvg import QSvgRenderer

    _HAS_SVG = True
except ImportError:  # pragma: no cover
    _HAS_SVG = False


def _is_paper(c) -> bool:
    """True only for near-pure white / empty — keep soft AA fringe as ink."""
    if c.alpha() < 8:
        return True
    # Strict: light gray AA (e.g. 248) is logo fringe, not paper.
    return c.red() >= 252 and c.green() >= 252 and c.blue() >= 252


def _content_bbox(img: QImage) -> tuple[int, int, int, int] | None:
    """Return (x, y, w, h) of non-paper opaque pixels."""
    w, h = img.width(), img.height()
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            c = img.pixelColor(x, y)
            if _is_paper(c):
                continue
            minx = min(minx, x)
            miny = min(miny, y)
            maxx = max(maxx, x)
            maxy = max(maxy, y)
    if maxx < minx:
        return None
    # Generous right pad — final "o" AA was still kissing the crop edge.
    pad_l, pad_t, pad_r, pad_b = 6, 6, 28, 6
    x0 = max(0, minx - pad_l)
    y0 = max(0, miny - pad_t)
    x1 = min(w - 1, maxx + pad_r)
    y1 = min(h - 1, maxy + pad_b)
    return x0, y0, x1 - x0 + 1, y1 - y0 + 1


def _recolor_ink(img: QImage, ink: str) -> QImage:
    """Map ink (+ AA fringe) to theme ink; drop paper; preserve edge coverage."""
    from PySide6.QtGui import QColor

    out = QImage(img.size(), QImage.Format.Format_ARGB32_Premultiplied)
    out.fill(Qt.GlobalColor.transparent)
    target = QColor(ink)
    for y in range(img.height()):
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            if _is_paper(c):
                continue
            lum = (c.red() + c.green() + c.blue()) / 3.0
            # Coverage from luminance: black→1, near-paper fringe→small alpha.
            coverage = max(0.0, min(1.0, (252.0 - lum) / 252.0))
            if coverage < 0.02:
                continue
            a = QColor(target)
            # Accent parallelograms (mid gray) stay slightly softer.
            if 40 < lum < 160:
                a.setAlpha(int(180 * coverage))
            else:
                a.setAlpha(int(255 * coverage))
            out.setPixelColor(x, y, a)
    return out


def _pixmap_from_png(height: int, *, ink: str) -> QPixmap:
    path = logo_wordmark_path()
    if not path.is_file():
        return QPixmap()
    src = QImage(str(path))
    if src.isNull():
        return QPixmap()
    # Wordmark is already a tight horizontal crop; only re-bbox square fallbacks.
    if src.width() <= src.height() * 2:
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
    # Small transparent pad so the final "o" never kisses the pixmap edge.
    pad_r = max(3, int(round(pixel_h * 0.12)))
    pad_y = max(1, int(round(pixel_h * 0.06)))
    pad_l = max(1, int(round(pixel_h * 0.04)))
    padded = QImage(
        scaled.width() + pad_l + pad_r,
        scaled.height() + 2 * pad_y,
        QImage.Format.Format_ARGB32_Premultiplied,
    )
    padded.fill(Qt.GlobalColor.transparent)
    painter = QPainter(padded)
    painter.drawImage(pad_l, pad_y, scaled)
    painter.end()
    pix = QPixmap.fromImage(padded)
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
    height: int = 40,
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


def make_logo_label(height: int = 40, parent=None) -> QLabel:
    label = QLabel(parent)
    label.setObjectName("brandMark")
    label.setAccessibleName("buusdo logo")
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    label.setScaledContents(False)
    pix = logo_pixmap(height)
    if not pix.isNull():
        label.setPixmap(pix)
        label.setFixedHeight(height + 4)
        # ceil width so Retina rounding never clips the right edge
        logical_w = int((pix.width() + pix.devicePixelRatio() - 0.001) / max(1.0, pix.devicePixelRatio()))
        label.setFixedWidth(logical_w + 6)
    label.setProperty("logoHeight", height)
    return label


def refresh_logo_label(label: QLabel, height: int | None = None) -> None:
    h = height if height is not None else int(label.property("logoHeight") or 40)
    label.setProperty("logoHeight", h)
    pix = logo_pixmap(h)
    if pix.isNull():
        return
    label.setPixmap(pix)
    label.setFixedHeight(h + 4)
    logical_w = int((pix.width() + pix.devicePixelRatio() - 0.001) / max(1.0, pix.devicePixelRatio()))
    label.setFixedWidth(logical_w + 6)
