from pathlib import Path

from buusdo.core.backend import EnhancementTarget
from buusdo.core.config_store import export_configs, import_configs, save_game_config
from buusdo.core.graphics_detect import GraphicsApi
from buusdo.core.history import append_event, list_events
from buusdo.core.preflight import PreflightLevel, check_install_preflight


def test_preflight_proxy_warning(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    game = tmp_path / "game"
    game.mkdir()
    (game / "dxgi.dll").write_bytes(b"OLD")
    target = EnhancementTarget(name="G", install_path=game)
    report = check_install_preflight(target, api=GraphicsApi.D3D11)
    assert report.ok
    assert any(i.code == "proxy_conflict" for i in report.issues)


def test_history_and_config_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    # Force config dir under tmp via XDG (Linux path); on macOS user_config_dir
    # ignores XDG — patch user_config_dir instead.
    from buusdo.core import config_store, history, platform_detect

    cfg_root = tmp_path / "cfg"
    monkeypatch.setattr(platform_detect, "user_config_dir", lambda platform=None: cfg_root)
    monkeypatch.setattr(config_store, "user_config_dir", lambda: cfg_root)
    monkeypatch.setattr(history, "user_config_dir", lambda: cfg_root)

    save_game_config("42", {"graphics_api": "vulkan", "executable": "/tmp/g.exe"})
    append_event("install:reshade", target="Demo", success=True, message="ok")
    assert list_events()[0]["target"] == "Demo"

    zpath = tmp_path / "out.zip"
    export_configs(zpath)
    # wipe and reimport
    for p in (cfg_root / "games").glob("*.json"):
        p.unlink()
    result = import_configs(zpath)
    assert any(name.startswith("games/") for name in result["imported"])
