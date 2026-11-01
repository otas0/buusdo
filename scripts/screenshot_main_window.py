#!/usr/bin/env python3
"""Grab an offscreen screenshot of MainWindow for theme review (macOS/Linux)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Prefer offscreen for headless; allow override.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unittest.mock import patch

from buusdo.core.backend import (  # noqa: E402
    EnhancementBackend,
    EnhancementTarget,
    InstallResult,
)
from buusdo.ui.main_window import MainWindow  # noqa: E402
from buusdo.ui.theme import apply_product_theme  # noqa: E402


class _Stub(EnhancementBackend):
    def platform_id(self) -> str:
        return "macos"

    def discover_games(self, *, should_cancel=None, progress=None):
        return []

    def list_capabilities(self, target: EnhancementTarget):
        return []

    def install(self, target, options=None):
        return InstallResult(True, "ok")

    def uninstall(self, target):
        return InstallResult(True, "ok")

    def status(self, target):
        return {}


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    out = Path(args[0] if args else "docs/fixtures/ui_main_window_macos.png")
    out.parent.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication([])
    apply_product_theme(app)
    # Avoid FirstRunWizard.exec() blocking under offscreen.
    with patch("buusdo.ui.main_window.needs_wizard", return_value=False):
        with patch.object(MainWindow, "_setup_tray", lambda self: None):
            win = MainWindow(backend=_Stub())
    win.resize(980, 720)
    win.show()
    for _ in range(20):
        app.processEvents()
    pix = win.grab()
    ok = pix.save(str(out))
    win.close()
    app.processEvents()
    if not ok or not out.is_file():
        print(f"FAIL: could not write {out}", file=sys.stderr)
        return 1
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
