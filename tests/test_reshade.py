from pathlib import Path

import pytest

from buusdo.backends.linux import LinuxBackend
from buusdo.backends.windows import WindowsBackend
from buusdo.core.backend import EnhancementTarget
from buusdo.core.errors import BuusdoError, UnsafeTargetError
from buusdo.core.graphics_detect import GraphicsApi
from buusdo.core.reshade import plan_deploy, resolve_kit, status
from buusdo.core.transaction import Transaction
from buusdo.core import reshade


def _make_kit(root: Path) -> Path:
    kit = root / "reshade_kit"
    kit.mkdir(parents=True)
    (kit / "ReShade64.dll").write_bytes(b"RESHADE64")
    (kit / "ReShade32.dll").write_bytes(b"RESHADE32")
    (kit / "ReShade.ini").write_text("[GENERAL]\n", encoding="utf-8")
    return kit


def test_deploy_and_uninstall_restores_overwrite(tmp_path: Path) -> None:
    kit = _make_kit(tmp_path)
    game = tmp_path / "game"
    game.mkdir()
    original = game / "dxgi.dll"
    original.write_bytes(b"ORIGINAL_DXGI")

    plan = plan_deploy(game, resolve_kit(kit), api=GraphicsApi.D3D11)
    with Transaction() as tx:
        reshade.deploy(tx, plan, target_name="Demo")

    assert (game / "dxgi.dll").read_bytes() == b"RESHADE64"
    assert status(game)["installed"] is True

    with Transaction() as tx:
        result = reshade.uninstall(tx, game)

    assert original.read_bytes() == b"ORIGINAL_DXGI"
    assert str(original) in result["restored"]
    assert status(game)["installed"] is False


def test_windows_backend_requires_kit(tmp_path: Path) -> None:
    backend = WindowsBackend()
    target = EnhancementTarget(name="G", install_path=tmp_path)
    with pytest.raises(BuusdoError, match="ReShade"):
        backend.install(target, options={})


def test_windows_backend_blocks_anticheat(tmp_path: Path) -> None:
    game = tmp_path / "game"
    game.mkdir()
    (game / "EasyAntiCheat").mkdir()
    kit = _make_kit(tmp_path / "kits")
    backend = WindowsBackend()
    target = EnhancementTarget(name="Risky", install_path=game)
    with pytest.raises(UnsafeTargetError):
        backend.install(target, options={"reshade_kit": str(kit)})


def test_linux_proton_reshade_deploy(tmp_path: Path) -> None:
    kit = _make_kit(tmp_path)
    game = tmp_path / "common" / "WinGame"
    game.mkdir(parents=True)
    (game / "game.exe").write_bytes(b"MZ")
    prefix = tmp_path / "compatdata" / "9" / "pfx"
    prefix.mkdir(parents=True)

    backend = LinuxBackend()
    target = EnhancementTarget(
        name="WinGame",
        install_path=game,
        executable=game / "game.exe",
        metadata={"runtime": "proton", "proton_prefix": str(prefix), "app_id": "9"},
    )
    result = backend.install(target, options={"reshade_kit": str(kit), "api": "d3d11"})
    assert result.success
    assert (game / "dxgi.dll").is_file()
    assert (game / ".buusdo" / "proton.json").is_file()
