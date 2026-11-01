"""App / tray icons from the bundled logo."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

from buusdo.assets import logo_path


def make_mark_icon(size: int = 64) -> QIcon:
    """Build a QIcon from logo.png (multi-size when used via app_icon())."""
    path = logo_path()
    if path.is_file():
        pix = QPixmap(str(path))
        if not pix.isNull():
            scaled = pix.scaled(
                size,
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            return QIcon(scaled)
    # Minimal fallback if assets missing.
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.black)
    return QIcon(pix)


def app_icon() -> QIcon:
    """Window / taskbar / tray icon with several resolutions from logo.png."""
    path = logo_path()
    icon = QIcon()
    if path.is_file():
        src = QPixmap(str(path))
        if not src.isNull():
            for side in (16, 24, 32, 48, 64, 128, 256):
                icon.addPixmap(
                    src.scaled(
                        side,
                        side,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            return icon
    return make_mark_icon(64)
