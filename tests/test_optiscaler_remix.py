from pathlib import Path

from buusdo.core import optiscaler, rtx_remix
from buusdo.core.transaction import Transaction


def test_optiscaler_deploy_uninstall(tmp_path: Path) -> None:
    kit = tmp_path / "opti"
    kit.mkdir()
    (kit / "OptiScaler.dll").write_bytes(b"OPTI")
    game = tmp_path / "game"
    game.mkdir()
    with Transaction() as tx:
        optiscaler.deploy(tx, game, kit, target_name="G")
    assert (game / "OptiScaler.dll").is_file()
    assert optiscaler.status(game)["installed"] is True
    with Transaction() as tx:
        optiscaler.uninstall(tx, game)
    assert not (game / "OptiScaler.dll").exists()


def test_rtx_remix_enable_disable(tmp_path: Path) -> None:
    game = tmp_path / "game"
    game.mkdir()
    (game / "NvRemixBridge.exe").write_bytes(b"bridge")
    (game / "d3d9.dll").write_bytes(b"REMIX")
    assert rtx_remix.detect(game)["present"] is True
    with Transaction() as tx:
        rtx_remix.disable(tx, game, target_name="G")
    assert (game / "d3d9.dll.buusdo_disabled").is_file()
    assert not (game / "d3d9.dll").exists()
    with Transaction() as tx:
        rtx_remix.enable(tx, game, target_name="G")
    assert (game / "d3d9.dll").read_bytes() == b"REMIX"
