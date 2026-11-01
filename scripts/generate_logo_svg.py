#!/usr/bin/env python3
"""Trace buusdo/assets/logo.png → logo.svg (themeable fills). Requires pillow + vtracer."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PNG = ROOT / "buusdo" / "assets" / "logo.png"
SVG = ROOT / "buusdo" / "assets" / "logo.svg"


def main() -> int:
    if not PNG.is_file():
        print(f"FATAL: missing {PNG}", file=sys.stderr)
        return 1
    try:
        import vtracer
    except ImportError:
        print("FATAL: pip/uv install vtracer", file=sys.stderr)
        return 1

    vtracer.convert_image_to_svg_py(
        str(PNG),
        str(SVG),
        colormode="color",
        hierarchical="stacked",
        mode="spline",
        filter_speckle=4,
        color_precision=6,
        layer_difference=16,
        corner_threshold=60,
        length_threshold=4.0,
        max_iterations=10,
        path_precision=3,
    )
    text = SVG.read_text(encoding="utf-8")
    text = re.sub(
        r'<path d="M0 0 C165 0[^"]+" fill="#FEFEFE"[^/]*/>\s*',
        "",
        text,
        count=1,
    )
    for c in ("#010101", "#020202", "#040404"):
        text = text.replace(f'fill="{c}"', 'fill="#111111"')
    for c in ("#F0F0F0", "#E7E7E7", "#F4F4F4", "#FEFEFE"):
        text = text.replace(f'fill="{c}"', 'fill="#EDEDED"')
    text = text.replace('fill="#545454"', 'fill="#6B6B6B"')
    if "viewBox" not in text:
        text = text.replace("<svg ", '<svg viewBox="0 0 500 500" ', 1)
    text = text.replace(
        "<!-- Generator: visioncortex VTracer 0.6.12 -->",
        "<!-- buusdo wordmark (from logo.png via VTracer); fills remapped for light/dark -->",
    )
    SVG.write_text(text, encoding="utf-8")
    print(f"OK  {SVG} ({SVG.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
