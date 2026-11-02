#!/usr/bin/env python3
"""Build buusdo/assets/logo.icns (+ logo_dock.png) from logo.png.

Bakes a macOS Big Sur–style continuous rounded-rect alpha so Dock/Finder tiles
match other apps (transparent outside the squircle). Qt ``setWindowIcon`` uses
``logo_dock.png`` so the runtime Dock tile is not a hard opaque square.

Uses PySide6 for masking, then ``sips`` + ``iconutil`` on Darwin. On other
hosts, exits 0 with a skip message so CI elsewhere is not blocked.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "buusdo" / "assets" / "logo.png"
OUT_ICNS = ROOT / "buusdo" / "assets" / "logo.icns"
OUT_DOCK = ROOT / "buusdo" / "assets" / "logo_dock.png"
_BUILD = ROOT / "build"
_ICONSET_DIR = _BUILD / "logo.iconset"

# Apple HIG app-icon corner radius ≈ 22.37% of the icon side.
_CORNER_RATIO = 0.2237
_DOCK_SIDE = 1024


def _iconset_map() -> list[tuple[int, str]]:
    """iconutil slot names. Build @2x via concat so tooling cannot mangle names."""
    retina = "@" + "2x.png"
    return [
        (16, "icon_16x16.png"),
        (32, "icon_16x16" + retina),
        (32, "icon_32x32.png"),
        (64, "icon_32x32" + retina),
        (128, "icon_128x128.png"),
        (256, "icon_128x128" + retina),
        (256, "icon_256x256.png"),
        (512, "icon_256x256" + retina),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512" + retina),
    ]


def _masked_square(src_path: Path, side: int):
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QImage, QPainter, QPainterPath

    src = QImage(str(src_path))
    if src.isNull():
        raise RuntimeError(f"failed to load {src_path}")
    scaled = src.scaled(
        side,
        side,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    out = QImage(side, side, QImage.Format.Format_ARGB32)
    out.fill(0)
    path = QPainterPath()
    r = side * _CORNER_RATIO
    path.addRoundedRect(QRectF(0, 0, side, side), r, r)
    painter = QPainter(out)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    painter.setClipPath(path)
    painter.drawImage(0, 0, scaled)
    painter.end()
    return out


def _save_png(img, path: Path) -> None:
    if not img.save(str(path), "PNG"):
        raise RuntimeError(f"PNG save failed: {path}")


def _sips_resize(src: Path, side: int, dest: Path) -> None:
    """Resize via sips into a plain .png path (never *@2x.png — sips breaks those)."""
    stage = dest.with_name(f".stage_{side}_{dest.stem.replace('.', '_')}.png")
    subprocess.check_call(
        ["sips", "-z", str(side), str(side), str(src), "--out", str(stage)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.check_call(
        [
            "sips",
            "-s",
            "dpiWidth",
            "72",
            "-s",
            "dpiHeight",
            "72",
            str(stage),
            "--out",
            str(stage),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    dest.write_bytes(stage.read_bytes())
    stage.unlink(missing_ok=True)


def main() -> int:
    if not SRC.is_file():
        print(f"missing {SRC}", file=sys.stderr)
        return 1
    if sys.platform != "darwin":
        print("skip: logo.icns generation requires macOS (sips + iconutil)")
        return 0
    if not shutil.which("sips") or not shutil.which("iconutil"):
        print("sips/iconutil missing", file=sys.stderr)
        return 1
    try:
        from PySide6.QtGui import QGuiApplication
    except ImportError:
        print("PySide6 required to mask logo.icns", file=sys.stderr)
        return 1

    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication([])

    _BUILD.mkdir(parents=True, exist_ok=True)

    try:
        _save_png(_masked_square(SRC, _DOCK_SIDE), OUT_DOCK)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    if _ICONSET_DIR.exists():
        shutil.rmtree(_ICONSET_DIR)
    _ICONSET_DIR.mkdir(parents=True)
    for side, name in _iconset_map():
        dest = _ICONSET_DIR / name
        try:
            _sips_resize(OUT_DOCK, side, dest)
        except (RuntimeError, subprocess.CalledProcessError) as exc:
            print(exc, file=sys.stderr)
            return 1
        if not dest.is_file():
            print(f"sips write failed for {name}", file=sys.stderr)
            return 1
    names = sorted(p.name for p in _ICONSET_DIR.iterdir())
    expected = sorted(n for _, n in _iconset_map())
    if names != expected:
        print(f"iconset names mismatch: {names!r}", file=sys.stderr)
        return 1
    tmp_icns = _BUILD / "logo.icns"
    rc = subprocess.call(
        ["iconutil", "-c", "icns", str(_ICONSET_DIR), "-o", str(tmp_icns)]
    )
    if rc != 0 or not tmp_icns.is_file():
        print(
            "iconutil failed (often sandboxed agents). "
            f"logo_dock.png updated; keep existing {OUT_ICNS.name} if present.",
            file=sys.stderr,
        )
        # Leave _ICONSET_DIR for inspection.
        if OUT_DOCK.is_file() and OUT_ICNS.is_file():
            print(f"wrote {OUT_DOCK} ({OUT_DOCK.stat().st_size} bytes)")
            print(f"kept {OUT_ICNS} ({OUT_ICNS.stat().st_size} bytes)")
            return 0
        return 1
    OUT_ICNS.write_bytes(tmp_icns.read_bytes())
    tmp_icns.unlink(missing_ok=True)
    shutil.rmtree(_ICONSET_DIR, ignore_errors=True)

    print(f"wrote {OUT_DOCK} ({OUT_DOCK.stat().st_size} bytes)")
    print(f"wrote {OUT_ICNS} ({OUT_ICNS.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
