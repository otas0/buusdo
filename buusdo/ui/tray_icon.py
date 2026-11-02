"""App / tray icons from the bundled logo."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

from buusdo.assets import logo_dock_path, logo_icns_path, logo_path

# Tray / menu-bar critical sizes (logical); Qt picks 2× for Retina when present.
TRAY_SIZES = (16, 32, 64)
APP_SIZES = (16, 24, 32, 48, 64, 128, 256)


def _scaled_square(src: QPixmap, side: int) -> QPixmap:
    return src.scaled(
        side,
        side,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def make_mark_icon(size: int = 64) -> QIcon:
    """Build a multi-resolution mark (16/32/64 plus ``size``) from logo.png."""
    path = logo_path()
    icon = QIcon()
    if path.is_file():
        src = QPixmap(str(path))
        if not src.isNull():
            sides = sorted({*TRAY_SIZES, size})
            for side in sides:
                icon.addPixmap(_scaled_square(src, side))
            return icon
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.black)
    return QIcon(pix)


def app_icon() -> QIcon:
    """Window / Dock / taskbar icon.

    Prefer ``logo.icns`` when Qt can load it (macOS Dock keeps squircle alpha).
    Else squircle-masked ``logo_dock.png``, else ``logo.png``.
    """
    icns = logo_icns_path()
    if icns.is_file():
        native = QIcon(str(icns))
        if not native.isNull() and native.availableSizes():
            return native
    path = logo_dock_path()
    icon = QIcon()
    if path.is_file():
        src = QPixmap(str(path))
        if not src.isNull():
            for side in APP_SIZES:
                icon.addPixmap(_scaled_square(src, side))
            return icon
    return make_mark_icon(64)


def tray_icon() -> QIcon:
    """Explicit tray mark with 16/32/64 for crisp Retina menu-bar icons."""
    return make_mark_icon(64)
