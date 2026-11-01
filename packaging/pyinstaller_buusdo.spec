# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onefile fallback when pyside6-deploy/Nuitka is unavailable.
# Usage: pyinstaller packaging/pyinstaller_buusdo.spec
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent.parent  # noqa: F821 — PyInstaller injects SPECPATH
ICO = ROOT / "buusdo" / "assets" / "logo.ico"

a = Analysis(  # noqa: F821
    [str(ROOT / "buusdo" / "app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(ROOT / "buusdo" / "assets"), "buusdo/assets")],
    hiddenimports=["buusdo"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="buusdo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICO) if ICO.is_file() else None,
)
