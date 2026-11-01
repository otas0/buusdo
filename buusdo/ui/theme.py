"""Product UI theme — instrument-panel clarity (Nothing × teenage engineering cues).

Light cool surface (not cream), ink type, single orange accent, monospace labels,
hairline borders, flat fills — no glow, no purple, no multi-layer shadows.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

# Colorblind-safe-ish: blue (ok) / orange (warn+accent) / vermillion (block)
COLOR_OK = "#1F6F8B"
COLOR_WARN = "#FF4F00"  # TE-adjacent orange — also primary accent
COLOR_BLOCK = "#C73E1D"
COLOR_MUTED = "#6B6B6B"
COLOR_BG = "#EDEDED"  # cool light gray (avoid cream #F4F1EA cluster)
COLOR_SURFACE = "#FAFAFA"
COLOR_INK = "#111111"
COLOR_LINE = "#111111"
COLOR_BTN = "#111111"
COLOR_BTN_TEXT = "#FAFAFA"
COLOR_BTN_SECONDARY = "#E4E4E4"

# Keep legacy aliases used by badge helpers / blocked page
COLOR_TEXT = COLOR_INK


def _mono_family() -> str:
    # Prefer readable monospace stacks present on macOS / Windows / Linux.
    return "Menlo, Courier New, monospace"


def apply_dark_theme(app: QApplication) -> None:
    """Historically named; applies the light instrument theme."""
    apply_product_theme(app)


def apply_product_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    font = QFont()
    # Prefer fonts that exist on stock macOS/Windows/Linux (avoid missing-family lag).
    font.setFamilies(["Helvetica Neue", "Arial"])
    font.setPointSize(11)
    app.setFont(font)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(COLOR_BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLOR_INK))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLOR_SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#E6E6E6"))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLOR_INK))
    palette.setColor(QPalette.ColorRole.Button, QColor(COLOR_BTN_SECONDARY))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLOR_INK))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLOR_WARN))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLOR_SURFACE))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(COLOR_INK))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(COLOR_MUTED))
    palette.setColor(QPalette.ColorRole.Light, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Mid, QColor("#C8C8C8"))
    palette.setColor(QPalette.ColorRole.Dark, QColor("#333333"))
    app.setPalette(palette)

    mono = _mono_family()
    app.setStyleSheet(
        f"""
        QWidget {{
            background: {COLOR_BG};
            color: {COLOR_INK};
        }}
        QMainWindow, QDialog {{
            background: {COLOR_BG};
        }}
        QLabel#brandMark {{
            margin-right: 4px;
        }}
        QLabel#brandTitle {{
            font-family: {mono};
            font-size: 26px;
            font-weight: 700;
            letter-spacing: 3px;
            color: {COLOR_INK};
            text-transform: lowercase;
        }}
        QLabel#brandSubtitle {{
            font-family: {mono};
            font-size: 10px;
            color: {COLOR_MUTED};
            letter-spacing: 1.5px;
        }}
        QDialog#instrumentDialog {{
            background: {COLOR_BG};
        }}
        QLabel#sectionLabel, QLabel#backendChip {{
            font-family: {mono};
            font-size: 10px;
            letter-spacing: 1.5px;
            color: {COLOR_MUTED};
            text-transform: uppercase;
        }}
        QLabel#backendChip {{
            border: 1px solid {COLOR_LINE};
            padding: 4px 8px;
            background: {COLOR_SURFACE};
        }}
        QLabel#blockTitle {{
            color: {COLOR_BLOCK};
            font-weight: 700;
            font-family: {mono};
        }}
        QLabel#badgeOk {{ color: {COLOR_OK}; font-weight: 600; }}
        QLabel#badgeWarn {{ color: {COLOR_WARN}; font-weight: 600; }}
        QPushButton {{
            font-family: {mono};
            font-size: 11px;
            padding: 7px 12px;
            border: 1px solid {COLOR_LINE};
            border-radius: 2px;
            background: {COLOR_BTN_SECONDARY};
            color: {COLOR_INK};
        }}
        QPushButton:hover {{
            background: #DADADA;
        }}
        QPushButton:pressed {{
            background: #CFCFCF;
        }}
        QPushButton:disabled {{
            color: #9A9A9A;
            border-color: #BDBDBD;
            background: #EFEFEF;
        }}
        QPushButton:default, QPushButton#primaryAction {{
            background: {COLOR_BTN};
            color: {COLOR_BTN_TEXT};
            border: 1px solid {COLOR_BTN};
        }}
        QPushButton:default:hover, QPushButton#primaryAction:hover {{
            background: #2A2A2A;
        }}
        QPushButton#accentAction {{
            background: {COLOR_WARN};
            color: #FFFFFF;
            border: 1px solid {COLOR_WARN};
        }}
        QLineEdit, QSpinBox, QComboBox, QTextEdit {{
            font-family: {mono};
            font-size: 12px;
            padding: 6px 8px;
            border: 1px solid {COLOR_LINE};
            border-radius: 0px;
            background: {COLOR_SURFACE};
            selection-background-color: {COLOR_WARN};
            selection-color: #FFFFFF;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 22px;
        }}
        QListWidget, QTableWidget {{
            font-family: {mono};
            font-size: 12px;
            border: 1px solid {COLOR_LINE};
            border-radius: 0px;
            background: {COLOR_SURFACE};
            outline: none;
            gridline-color: #D0D0D0;
        }}
        QListWidget::item {{
            padding: 8px 10px;
            border-bottom: 1px solid #E2E2E2;
        }}
        QListWidget::item:selected, QTableWidget::item:selected {{
            background: {COLOR_WARN};
            color: #FFFFFF;
        }}
        QHeaderView::section {{
            font-family: {mono};
            font-size: 10px;
            letter-spacing: 1px;
            text-transform: uppercase;
            background: {COLOR_BG};
            color: {COLOR_MUTED};
            border: none;
            border-bottom: 1px solid {COLOR_LINE};
            border-right: 1px solid #D0D0D0;
            padding: 6px 8px;
        }}
        QProgressBar {{
            border: 1px solid {COLOR_LINE};
            border-radius: 0px;
            background: {COLOR_SURFACE};
            text-align: center;
            font-family: {mono};
            font-size: 10px;
            height: 16px;
        }}
        QProgressBar::chunk {{
            background: {COLOR_WARN};
        }}
        QCheckBox, QRadioButton {{
            font-family: {mono};
            spacing: 8px;
        }}
        QToolTip {{
            font-family: {mono};
            background: {COLOR_INK};
            color: {COLOR_SURFACE};
            border: none;
            padding: 6px 8px;
        }}
        QStatusBar {{
            font-family: {mono};
            font-size: 11px;
            border-top: 1px solid {COLOR_LINE};
        }}
        QScrollBar:vertical {{
            background: {COLOR_BG};
            width: 10px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: #B5B5B5;
            min-height: 24px;
            border-radius: 0px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
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
