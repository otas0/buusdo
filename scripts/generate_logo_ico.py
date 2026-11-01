#!/usr/bin/env python3
"""Write a compact multi-size buusdo/assets/logo.ico from logo.png.

Sizes: 16, 32, 48, 256 (PNG-compressed ICO entries). Caps size so the wheel
does not ship a huge single-frame dump from QImage.save(..., \"ICO\").
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIZES = (16, 32, 48, 256)
MAX_BYTES = 96_000


def _qimage_png_bytes(img) -> bytes:
    from PySide6.QtCore import QBuffer, QIODevice

    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    if not img.save(buf, "PNG"):
        raise RuntimeError("PNG encode failed")
    return bytes(buf.data())


def _write_ico(path: Path, png_by_size: dict[int, bytes]) -> None:
    count = len(png_by_size)
    offset = 6 + 16 * count
    entries = b""
    blobs = b""
    for size in sorted(png_by_size):
        data = png_by_size[size]
        w = 0 if size >= 256 else size
        h = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offset)
        blobs += data
        offset += len(data)
    path.write_bytes(struct.pack("<HHH", 0, 1, count) + entries + blobs)


def main() -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QImage, QPainter
    except ImportError:
        print("PySide6 required", file=sys.stderr)
        return 1

    src = ROOT / "buusdo" / "assets" / "logo.png"
    out = ROOT / "buusdo" / "assets" / "logo.ico"
    if not src.is_file():
        print(f"missing {src}", file=sys.stderr)
        return 1
    img = QImage(str(src))
    if img.isNull():
        print("failed to load logo.png", file=sys.stderr)
        return 1

    png_by_size: dict[int, bytes] = {}
    for side in SIZES:
        scaled = img.scaled(
            side,
            side,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        square = QImage(side, side, QImage.Format.Format_ARGB32_Premultiplied)
        square.fill(0)
        painter = QPainter(square)
        painter.drawImage((side - scaled.width()) // 2, (side - scaled.height()) // 2, scaled)
        painter.end()
        try:
            png_by_size[side] = _qimage_png_bytes(square)
        except RuntimeError as exc:
            print(exc, file=sys.stderr)
            return 1

    _write_ico(out, png_by_size)
    size = out.stat().st_size
    if size > MAX_BYTES:
        print(f"logo.ico too large ({size} > {MAX_BYTES})", file=sys.stderr)
        return 1
    if size < 50:
        print("logo.ico empty/tiny", file=sys.stderr)
        return 1
    print(f"wrote {out} ({size} bytes; sizes={list(SIZES)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
