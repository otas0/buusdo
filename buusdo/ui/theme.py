"""Dark theme + colorblind-friendly accents (no sole reliance on green/red)."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

# Colorblind-safe-ish pair: blue (ok) / orange (warn) / magenta (block)
COLOR_OK = "#2E86AB"  # blue
COLOR_WARN = "#E2A03F"  # orange
COLOR_BLOCK = "#C73E1D"  # vermillion
COLOR_MUTED = "#A0A0A0"
COLOR_BG = "#121212"
COLOR_SURFACE = "#1E1E1E"
COLOR_TEXT = "#F2F2F2"


def apply_dark_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(COLOR_BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLOR_TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLOR_SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#252525"))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLOR_TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(COLOR_SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLOR_TEXT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLOR_OK))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLOR_SURFACE))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(COLOR_TEXT))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(COLOR_MUTED))
    app.setPalette(palette)
    app.setStyleSheet(
        f"""
        QListWidget::item {{ padding: 4px; }}
        QPushButton {{ padding: 6px 10px; }}
        QLabel#brandSubtitle {{ color: {COLOR_MUTED}; }}
        QLabel#blockTitle {{ color: {COLOR_BLOCK}; font-weight: 700; }}
        QLabel#badgeOk {{ color: {COLOR_OK}; font-weight: 600; }}
        QLabel#badgeWarn {{ color: {COLOR_WARN}; font-weight: 600; }}
        """
    )


def badge_color(kind: str) -> QColor:
    if kind in {"deployed", "ok"}:
        return QColor(COLOR_OK)
    if kind in {"warn", "vkbasalt", "remix"}:
        return QColor(COLOR_WARN)
    if kind in {"block", "unsafe"}:
        return QColor(COLOR_BLOCK)
    return QColor(COLOR_MUTED)
