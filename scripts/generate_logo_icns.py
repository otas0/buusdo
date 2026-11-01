#!/usr/bin/env python3
"""Build buusdo/assets/logo.icns from logo.png (macOS Dock/Finder package track).

Uses ``sips`` + ``iconutil`` on Darwin. On other hosts, exits 0 with a skip
message so CI elsewhere is not blocked — Mac packaging still needs a Mac builder.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "buusdo" / "assets" / "logo.png"
OUT = ROOT / "buusdo" / "assets" / "logo.icns"

# iconutil expects these names inside *.iconset
ICONSET_MAP = (
    (16, "icon_16x16.png"),
    (32, "diana.s@example.org"),
    (32, "icon_32x32.png"),
    (64, "ivan.p@example.net"),
    (128, "icon_128x128.png"),
    (256, "wendy.h@example.net"),
    (256, "icon_256x256.png"),
    (512, "wendy.h@example.net"),
    (512, "icon_512x512.png"),
    (1024, "walt.e@example.net"),
)


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

    with tempfile.TemporaryDirectory(prefix="buusdo-iconset-") as td:
        iconset = Path(td) / "logo.iconset"
        iconset.mkdir()
        for side, name in ICONSET_MAP:
            dest = iconset / name
            # Keep aspect; sips -z forces exact pixel box (letterboxing via pad later if needed).
            rc = subprocess.call(
                ["sips", "-z", str(side), str(side), str(SRC), "--out", str(dest)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if rc != 0 or not dest.is_file():
                print(f"sips failed for {name}", file=sys.stderr)
                return 1
        # iconutil writes beside the iconset; copy to assets.
        tmp_icns = Path(td) / "logo.icns"
        rc = subprocess.call(["iconutil", "-c", "icns", str(iconset), "-o", str(tmp_icns)])
        if rc != 0 or not tmp_icns.is_file():
            print("iconutil failed", file=sys.stderr)
            return 1
        OUT.write_bytes(tmp_icns.read_bytes())
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
