"""Logo is the app / tray / UI icon source."""

from __future__ import annotations

import pytest

from buusdo.assets import logo_ico_path, logo_path


def test_logo_png_exists() -> None:
    assert logo_path().name == "logo.png"
    assert logo_path().is_file()


def test_app_icon_uses_logo() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from buusdo.ui.tray_icon import app_icon, make_mark_icon

    app = QApplication.instance() or QApplication([])
    icon = app_icon()
    assert not icon.isNull()
    sizes = icon.availableSizes()
    assert sizes
    mark = make_mark_icon(32)
    assert not mark.isNull()
    app.processEvents()


def test_generate_logo_ico() -> None:
    pytest.importorskip("PySide6")
    import importlib.util
    from pathlib import Path

    path = Path("scripts/generate_logo_ico.py")
    spec = importlib.util.spec_from_file_location("generate_logo_ico", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
    ico = logo_ico_path()
    assert ico.is_file()
    assert ico.stat().st_size > 50
