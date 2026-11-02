"""Dark-theme wordmark AA→ink must stay readable on dark paper."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_dark_theme_wordmark_contrast() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtGui import QColor, QImage, QPainter
    from PySide6.QtWidgets import QApplication

    from buusdo.ui.logo_widget import logo_pixmap

    app = QApplication.instance() or QApplication([])
    ink = "#E8E8E8"
    paper = "#1A1A1A"
    pix = logo_pixmap(44, ink=ink, paper=paper, accent="#9A9A9A")
    assert not pix.isNull()
    img = pix.toImage()
    canvas = QImage(img.width(), img.height(), QImage.Format.Format_RGB32)
    canvas.fill(QColor(paper))
    painter = QPainter(canvas)
    painter.drawImage(0, 0, img)
    painter.end()

    paper_lum = sum(int(paper[i : i + 2], 16) for i in (1, 3, 5)) / 3
    ink_samples: list[float] = []
    for y in range(0, canvas.height(), 2):
        for x in range(0, canvas.width(), 2):
            c = canvas.pixelColor(x, y)
            lum = (c.red() + c.green() + c.blue()) / 3.0
            if lum > paper_lum + 25:
                ink_samples.append(lum)
    assert len(ink_samples) > 30, "expected visible ink on dark paper"
    mean = sum(ink_samples) / len(ink_samples)
    assert mean - paper_lum >= 80, f"dark contrast too low: mean={mean:.1f} paper={paper_lum:.1f}"

    preview = Path("/tmp/buusdo_wordmark_dark_preview.png")
    canvas.save(str(preview))
    app.processEvents()
