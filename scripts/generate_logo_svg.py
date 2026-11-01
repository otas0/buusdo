#!/usr/bin/env python3
"""Trace buusdo/assets/logo.png → tight logo.svg (themeable fills).

Crops empty margin, upscales with nearest-neighbor, then VTracer.
Requires: pillow, vtracer.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PNG = ROOT / "buusdo" / "assets" / "logo.png"
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
    pad = 10
    box = (
        max(0, min(xs) - pad),
        max(0, min(ys) - pad),
        min(im.width, max(xs) + 1 + pad),
        min(im.height, max(ys) + 1 + pad),
    )
    crop = im.crop(box)
    # Integer upscale keeps geometric edges crisp for tracing.
    crop = crop.resize((crop.width * 4, crop.height * 4), Image.Resampling.NEAREST)
    bg = Image.new("RGB", crop.size, (255, 255, 255))
    bg.paste(crop, mask=crop.split()[-1])
    out = Path(tempfile.gettempdir()) / "buusdo-logo-trace.png"
    bg.save(out)
    return out


def _remap_fills(text: str) -> str:
    text = re.sub(
        r'<path d="M0 0 C[\d.]+ 0[^"]+" fill="#FEFEFE"[^/]*/>\s*',
        "",
        text,
        count=1,
    )
    # Drop any full-bleed near-white rects.
    text = re.sub(
        r'<path d="M0 0[^"]{0,80}" fill="#F[EeFf][EeFf][EeFf][EeFf]"[^/]*/>\s*',
        "",
        text,
    )
    for c in ("#010101", "#020202", "#040404", "#000000", "#030303"):
        text = text.replace(f'fill="{c}"', 'fill="#111111"')
    for c in ("#F0F0F0", "#E7E7E7", "#F4F4F4", "#FEFEFE", "#FFFFFF", "#FAFAFA"):
        text = text.replace(f'fill="{c}"', 'fill="#EDEDED"')
    for c in ("#545454", "#555555", "#666666", "#777777", "#888888"):
        text = text.replace(f'fill="{c}"', 'fill="#6B6B6B"')
    return text


def _tighten_viewbox(svg_path: Path) -> None:
    """Set viewBox to content using a high-res raster probe."""
    from PySide6.QtCore import QByteArray
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    raw = svg_path.read_text(encoding="utf-8")
    # Temporary square box for probing.
    if "viewBox" not in raw:
        raw = raw.replace("<svg ", '<svg viewBox="0 0 500 500" ', 1)
    r = QSvgRenderer(QByteArray(raw.encode()))
    if not r.isValid():
        return
    vb = r.viewBoxF()
    w0 = max(1.0, vb.width())
    h0 = max(1.0, vb.height())
    img = QImage(1600, 1600, QImage.Format.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    r.render(p)
    p.end()
    minx, miny, maxx, maxy = 1600, 1600, 0, 0
    for y in range(1600):
        row = False
        for x in range(1600):
            if img.pixelColor(x, y).alpha() > 12:
                minx = min(minx, x)
                maxx = max(maxx, x)
                miny = min(miny, y)
                maxy = max(maxy, y)
                row = True
        if not row and miny < maxy and y > maxy + 20:
            break
    if maxx <= minx:
        return
    # Map pixel → viewBox units
    x = vb.x() + (minx / 1600.0) * w0
    y = vb.y() + (miny / 1600.0) * h0
    w = ((maxx - minx) / 1600.0) * w0
    h = ((maxy - miny) / 1600.0) * h0
    pad = max(w, h) * 0.04
    x = max(vb.x(), x - pad)
    y = max(vb.y(), y - pad)
    w = min(vb.x() + w0 - x, w + 2 * pad)
    h = min(vb.y() + h0 - y, h + 2 * pad)
    vb_attr = f'viewBox="{x:.2f} {y:.2f} {w:.2f} {h:.2f}"'
    text = svg_path.read_text(encoding="utf-8")
    if re.search(r'viewBox="[^"]*"', text):
        text = re.sub(r'viewBox="[^"]*"', vb_attr, text, count=1)
    else:
        text = text.replace("<svg ", f"<svg {vb_attr} ", 1)
    # Prefer CSS size from viewBox aspect; drop fixed 500 square hints.
    text = re.sub(r'\swidth="[^"]*"', "", text, count=1)
    text = re.sub(r'\sheight="[^"]*"', "", text, count=1)
    svg_path.write_text(text, encoding="utf-8")
    _ = app  # keep alive for probe


def main() -> int:
    if not PNG.is_file():
        print(f"FATAL: missing {PNG}", file=sys.stderr)
        return 1
    try:
        import vtracer
    except ImportError:
        print("FATAL: uv pip install vtracer pillow", file=sys.stderr)
        return 1

    src = _crop_content(PNG)
    vtracer.convert_image_to_svg_py(
        str(src),
        str(SVG),
        colormode="color",
        hierarchical="stacked",
        mode="polygon",  # sharper for geometric wordmark
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
        # cropped source size unknown — leave square until tighten
        text = text.replace("<svg ", '<svg viewBox="0 0 1000 1000" ', 1)
    SVG.write_text(text, encoding="utf-8")
    _tighten_viewbox(SVG)
    print(f"OK  {SVG} ({SVG.stat().st_size} bytes)")
    head = SVG.read_text(encoding="utf-8").split(">", 1)[0] + ">"
    print(head[:200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
