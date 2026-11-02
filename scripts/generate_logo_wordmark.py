#!/usr/bin/env python3
"""Export horizontal logo_wordmark.png from logo.png (tight crop + right pad).

UI chrome should load this file instead of cropping the 500×500 app mark.
Requires: pillow (or PySide6 fallback).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PNG = ROOT / "buusdo" / "assets" / "logo.png"
OUT = ROOT / "buusdo" / "assets" / "logo_wordmark.png"


def _export_pillow() -> None:
    from PIL import Image

    im = Image.open(PNG).convert("RGBA")
    px = im.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a < 20:
                continue
            if r >= 252 and g >= 252 and b >= 252:
                continue
            xs.append(x)
            ys.append(y)
    if not xs:
        raise SystemExit(f"FATAL: no ink in {PNG}")
    pad_l, pad_t, pad_r, pad_b = 12, 12, 36, 12
    box = (
        max(0, min(xs) - pad_l),
        max(0, min(ys) - pad_t),
        min(im.width, max(xs) + 1 + pad_r),
        min(im.height, max(ys) + 1 + pad_b),
    )
    crop = im.crop(box)
    # Transparent paper: drop near-white background for UI recolor.
    out_px = crop.load()
    for y in range(crop.height):
        for x in range(crop.width):
            r, g, b, a = out_px[x, y]
            if r >= 252 and g >= 252 and b >= 252:
                out_px[x, y] = (255, 255, 255, 0)
    # Upscale 2× for Retina-friendly source
    crop = crop.resize((crop.width * 2, crop.height * 2), Image.Resampling.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    crop.save(OUT, optimize=True)
    print(f"OK  {OUT} ({OUT.stat().st_size} bytes) {crop.size[0]}x{crop.size[1]}")


def _export_qt() -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QImage
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    img = QImage(str(PNG))
    if img.isNull():
        raise SystemExit(f"FATAL: cannot read {PNG}")
    w, h = img.width(), img.height()
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            c = img.pixelColor(x, y)
            if c.alpha() < 20:
                continue
            if c.red() >= 252 and c.green() >= 252 and c.blue() >= 252:
                continue
            minx = min(minx, x)
            miny = min(miny, y)
            maxx = max(maxx, x)
            maxy = max(maxy, y)
    if maxx < minx:
        raise SystemExit(f"FATAL: no ink in {PNG}")
    pad_l, pad_t, pad_r, pad_b = 12, 12, 36, 12
    x0 = max(0, minx - pad_l)
    y0 = max(0, miny - pad_t)
    x1 = min(w - 1, maxx + pad_r)
    y1 = min(h - 1, maxy + pad_b)
    crop = img.copy(x0, y0, x1 - x0 + 1, y1 - y0 + 1)
    for y in range(crop.height()):
        for x in range(crop.width()):
            c = crop.pixelColor(x, y)
            if c.red() >= 252 and c.green() >= 252 and c.blue() >= 252:
                crop.setPixelColor(x, y, QColor(0, 0, 0, 0))
    scaled = crop.scaled(
        crop.width() * 2,
        crop.height() * 2,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    scaled.save(str(OUT))
    print(f"OK  {OUT} ({OUT.stat().st_size} bytes) {scaled.width()}x{scaled.height()}")
    _ = app


def main() -> int:
    if not PNG.is_file():
        print(f"FATAL: missing {PNG}", file=sys.stderr)
        return 1
    try:
        _export_pillow()
    except ImportError:
        _export_qt()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
