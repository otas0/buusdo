#!/usr/bin/env python3
"""Trace wordmark → tight logo.svg (themeable fills).

Prefers logo_wordmark.png (run generate_logo_wordmark.py first); else crops logo.png.
Requires: pillow, vtracer.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PNG = ROOT / "buusdo" / "assets" / "logo.png"
WORDMARK = ROOT / "buusdo" / "assets" / "logo_wordmark.png"
SVG = ROOT / "buusdo" / "assets" / "logo.svg"


def _crop_content(png: Path) -> Path:
    from PIL import Image

    im = Image.open(png).convert("RGBA")
    px = im.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a < 200:
                continue
            if r > 245 and g > 245 and b > 245:
                continue
            xs.append(x)
            ys.append(y)
    if not xs:
        raise SystemExit(f"FATAL: no ink in {png}")
    pad_l, pad_t, pad_r, pad_b = 10, 10, 28, 10
    box = (
        max(0, min(xs) - pad_l),
        max(0, min(ys) - pad_t),
        min(im.width, max(xs) + 1 + pad_r),
        min(im.height, max(ys) + 1 + pad_b),
    )
    crop = im.crop(box)
    # Wordmark sources are already upscaled — keep total scale modest for SVG size.
    scale = 2 if crop.width >= 600 else 3
    crop = crop.resize((crop.width * scale, crop.height * scale), Image.Resampling.NEAREST)
    bg = Image.new("RGB", crop.size, (255, 255, 255))
    bg.paste(crop, mask=crop.split()[-1])
    out = Path(tempfile.gettempdir()) / "buusdo-logo-trace.png"
    bg.save(out)
    return out


def _remap_fills(text: str) -> str:
    # Drop full-bleed background rects (any light fill spanning the canvas).
    text = re.sub(
        r'<path d="M0,?0[^"]{0,120}" fill="#(?:F[EeFf][EeFf][EeFf][EeFf]|EDEDED)"[^/]*/>\s*',
        "",
        text,
    )
    text = re.sub(
        r'<path d="M0,?0 L\d+,0 L\d+,\d+ L0,\d+ Z\s*" fill="#EDEDED"[^/]*/>\s*',
        "",
        text,
    )
    for c in ("#010101", "#020202", "#040404", "#000000", "#030303"):
        text = text.replace(f'fill="{c}"', 'fill="#111111"')
    for c in ("#F0F0F0", "#E7E7E7", "#F4F4F4", "#FEFEFE", "#FFFFFF", "#FAFAFA"):
        text = text.replace(f'fill="{c}"', 'fill="#EDEDED"')
    for c in ("#545454", "#555555", "#666666", "#777777", "#888888", "#535353"):
        text = text.replace(f'fill="{c}"', 'fill="#6B6B6B"')
    return text


def _tighten_viewbox(svg_path: Path) -> None:
    """Set viewBox to ink content (ignore paper), using the SVG's own viewBox."""
    from PySide6.QtCore import QByteArray
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    raw = svg_path.read_text(encoding="utf-8")
    if "viewBox" not in raw:
        raw = raw.replace("<svg ", '<svg viewBox="0 0 1400 400" ', 1)
        svg_path.write_text(raw, encoding="utf-8")
    r = QSvgRenderer(QByteArray(raw.encode()))
    if not r.isValid():
        return
    vb = r.viewBoxF()
    W = max(1, int(vb.width()) or r.defaultSize().width() or 1)
    H = max(1, int(vb.height()) or r.defaultSize().height() or 1)
    scale = 2
    img = QImage(W * scale, H * scale, QImage.Format.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    r.render(p)
    p.end()
    minx, miny, maxx, maxy = W * scale, H * scale, -1, -1
    for y in range(H * scale):
        for x in range(W * scale):
            c = img.pixelColor(x, y)
            if c.alpha() < 12:
                continue
            if c.red() > 230 and c.green() > 230 and c.blue() > 230:
                continue
            minx = min(minx, x)
            maxx = max(maxx, x)
            miny = min(miny, y)
            maxy = max(maxy, y)
    if maxx <= minx:
        return
    sx = vb.width() / (W * scale)
    sy = vb.height() / (H * scale)
    pad = 8.0
    x = vb.x() + minx * sx - pad
    y = vb.y() + miny * sy - pad
    w = (maxx - minx) * sx + 2 * pad
    h = (maxy - miny) * sy + 2 * pad
    vb_attr = f'viewBox="{x:.2f} {y:.2f} {w:.2f} {h:.2f}"'
    text = svg_path.read_text(encoding="utf-8")
    text = re.sub(r'viewBox="[^"]*"', vb_attr, text, count=1)
    text = re.sub(r'\swidth="[^"]*"', "", text, count=1)
    text = re.sub(r'\sheight="[^"]*"', "", text, count=1)
    svg_path.write_text(text, encoding="utf-8")
    _ = app


def main() -> int:
    # Refresh wordmark raster first when possible.
    try:
        import importlib.util

        wm_path = ROOT / "scripts" / "generate_logo_wordmark.py"
        spec = importlib.util.spec_from_file_location("generate_logo_wordmark", wm_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.main()
    except Exception as exc:  # noqa: BLE001
        print(f"WARN wordmark export skipped: {exc}", file=sys.stderr)

    src_png = WORDMARK if WORDMARK.is_file() else PNG
    if not src_png.is_file():
        print(f"FATAL: missing {src_png}", file=sys.stderr)
        return 1
    try:
        import vtracer
    except ImportError:
        print("FATAL: uv pip install vtracer pillow", file=sys.stderr)
        return 1

    src = _crop_content(src_png)
    vtracer.convert_image_to_svg_py(
        str(src),
        str(SVG),
        colormode="color",
        hierarchical="stacked",
        mode="polygon",
        filter_speckle=2,
        color_precision=8,
        layer_difference=8,
        corner_threshold=30,
        length_threshold=2.0,
        max_iterations=10,
        path_precision=2,
    )
    text = _remap_fills(SVG.read_text(encoding="utf-8"))
    text = text.replace(
        "<!-- Generator: visioncortex VTracer",
        "<!-- buusdo wordmark (cropped+traced); theme tokens #111/#EDEDED/#6B6B6B — Generator: visioncortex VTracer",
    )
    if "viewBox" not in text:
        text = text.replace("<svg ", '<svg viewBox="0 0 2000 600" ', 1)
    SVG.write_text(text, encoding="utf-8")
    _tighten_viewbox(SVG)
    print(f"OK  {SVG} ({SVG.stat().st_size} bytes) from {src_png.name}")
    head = SVG.read_text(encoding="utf-8").split(">", 1)[0] + ">"
    print(head[:220])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
