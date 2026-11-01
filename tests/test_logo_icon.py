"""Logo is the app / tray / UI icon source."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from buusdo.assets import logo_ico_path, logo_path


def test_logo_png_exists() -> None:
    assert logo_path().name == "logo.png"
    assert logo_path().is_file()


def test_logo_ico_exists_and_capped() -> None:
    ico = logo_ico_path()
    assert ico.is_file(), "commit logo.ico or run scripts/generate_logo_ico.py"
    size = ico.stat().st_size
    assert 50 < size <= 96_000, size


def test_app_and_tray_icons_multi_size() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from buusdo.ui.tray_icon import app_icon, make_mark_icon, tray_icon

    app = QApplication.instance() or QApplication([])
    icon = app_icon()
    assert not icon.isNull()
    assert icon.availableSizes()
    tray = tray_icon()
    assert not tray.isNull()
    sides = {s.width() for s in tray.availableSizes()}
    assert {16, 32, 64}.issubset(sides) or len(sides) >= 1
    mark = make_mark_icon(32)
    assert not mark.isNull()
    app.processEvents()


def test_generate_logo_ico_compact() -> None:
    pytest.importorskip("PySide6")
    path = Path("scripts/generate_logo_ico.py")
    spec = importlib.util.spec_from_file_location("generate_logo_ico", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
    ico = logo_ico_path()
    assert ico.is_file()
    assert ico.stat().st_size <= 96_000


def test_deploy_spec_sets_icon() -> None:
    import json

    data = json.loads(Path("scripts/pyside6-deploy.spec.json").read_text(encoding="utf-8"))
    assert data.get("icon") == "buusdo/assets/logo.ico"
    assert Path("packaging/pyinstaller_buusdo.spec").is_file()
