from pathlib import Path

from buusdo.core.backend import EnhancementTarget
from buusdo.core.conflict import check_install_conflicts, check_optiscaler_reshade
from buusdo.core.library_cache import invalidate_cache, load_cached_games
from buusdo.core.schema import CURRENT_SCHEMA_VERSION, ensure_schema
from buusdo.core.transaction import Transaction
from buusdo.core import optiscaler, reshade
from buusdo.core.graphics_detect import GraphicsApi
from buusdo.core.reshade import plan_deploy, resolve_kit


def test_schema_migrates_v1_prefs() -> None:
    data = ensure_schema({"executable": "/g.exe", "graphics_api": "d3d11"})
    assert data["schema_version"] == CURRENT_SCHEMA_VERSION
    assert data["prefs"]["graphics_api"] == "d3d11"


def test_optiscaler_reshade_collision_blocks(tmp_path: Path) -> None:
    game = tmp_path / "game"
    game.mkdir()
    kit_r = tmp_path / "rk"
    kit_r.mkdir()
    (kit_r / "ReShade64.dll").write_bytes(b"R")
    with Transaction() as tx:
        reshade.deploy(
            tx,
            plan_deploy(game, resolve_kit(kit_r), api=GraphicsApi.D3D11),
            target_name="G",
        )
    kit_o = tmp_path / "ok"
    kit_o.mkdir()
    (kit_o / "dxgi.dll").write_bytes(b"O")
    report = check_optiscaler_reshade(game, kit_o)
    assert report.blocked


def test_remix_blocks_d3d9_reshade(tmp_path: Path) -> None:
    game = tmp_path / "game"
    game.mkdir()
    (game / "NvRemixBridge.exe").write_bytes(b"b")
    (game / "d3d9.dll").write_bytes(b"r")
    target = EnhancementTarget(name="G", install_path=game)
    report = check_install_conflicts(target, mode="reshade", reshade_proxy="d3d9.dll")
    assert report.blocked


def test_library_cache_roundtrip(tmp_path: Path, monkeypatch) -> None:
    steam = tmp_path / "Steam"
    lib = tmp_path / "Lib"
    game = lib / "steamapps" / "common" / "X"
    game.mkdir(parents=True)
    (game / "x.exe").write_bytes(b"MZ")
    (steam / "steamapps").mkdir(parents=True)
    (steam / "steamapps" / "libraryfolders.vdf").write_text(
        f'"libraryfolders" {{ "0" {{ "path" "{lib.as_posix()}" }} }}',
        encoding="utf-8",
    )
    (lib / "steamapps" / "appmanifest_1.acf").write_text(
        '"AppState" { "appid" "1" "name" "X" "installdir" "X" }',
        encoding="utf-8",
    )
    from buusdo.core import library_cache

    monkeypatch.setattr(library_cache, "user_config_dir", lambda: tmp_path / "cfg")
    invalidate_cache()
    g1 = load_cached_games([steam])
    assert len(g1) == 1
    g2 = load_cached_games([steam])
    assert g2[0].app_id == "1"
