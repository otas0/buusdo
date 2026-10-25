from pathlib import Path

from buusdo.core.graphics_detect import GraphicsApi
from buusdo.core.reshade import plan_deploy, resolve_kit, status
from buusdo.core.transaction import Transaction
from buusdo.core import reshade


def _make_kit(root: Path) -> Path:
    kit = root / "kit"
    kit.mkdir()
    (kit / "ReShade64.dll").write_bytes(b"VK64")
    return kit


def test_vulkan_layer_deploy(tmp_path: Path) -> None:
    kit = resolve_kit(_make_kit(tmp_path))
    game = tmp_path / "game"
    game.mkdir()
    plan = plan_deploy(game, kit, api=GraphicsApi.VULKAN)
    assert plan.mode == "vulkan_layer"
    assert plan.proxy_dll_name is None
    with Transaction() as tx:
        state = reshade.deploy(tx, plan, target_name="VkGame")
    assert (game / "ReShade64.dll").is_file()
    assert (game / "ReShade64.json").is_file()
    assert "VK_LAYER" in (game / "ReShade64.json").read_text()
    assert status(game)["installed"] is True
    assert "steam_launch_hint" in state["deployed"]
