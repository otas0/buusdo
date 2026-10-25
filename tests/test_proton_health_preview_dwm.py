import os
from pathlib import Path

from buusdo.core.backend import EnhancementTarget
from buusdo.core.conflict_preview import preview_reshade_deploy
from buusdo.core.graphics_detect import GraphicsApi
from buusdo.core.proton_health import check_proton_prefix
from buusdo.core import dwm_hdr
from buusdo.core.errors import BuusdoError
import pytest


def test_proton_health_missing(tmp_path: Path) -> None:
    target = EnhancementTarget(
        name="G",
        install_path=tmp_path,
        metadata={"runtime": "proton", "proton_prefix": str(tmp_path / "missing")},
    )
    health = check_proton_prefix(target)
    assert health is not None
    assert health.ok is False


def test_conflict_preview_lists_creates(tmp_path: Path) -> None:
    kit = tmp_path / "kit"
    kit.mkdir()
    (kit / "ReShade64.dll").write_bytes(b"R")
    game = tmp_path / "game"
    game.mkdir()
    target = EnhancementTarget(name="G", install_path=game)
    details = preview_reshade_deploy(target, kit, api=GraphicsApi.D3D11)
    assert details["diffs"]
    assert any(d["action"] == "create" for d in details["diffs"])


def test_dwm_hdr_default_off(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("BUUSDO_ENABLE_DWM_HDR_PROTOTYPE", raising=False)
    assert dwm_hdr.is_available() is False
    with pytest.raises(BuusdoError):
        dwm_hdr.install(game_dir=tmp_path, target_name="G")


def test_dwm_hdr_prototype_flag(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BUUSDO_ENABLE_DWM_HDR_PROTOTYPE", "1")
    assert dwm_hdr.prototype_enabled() is True
    assert dwm_hdr.is_available() is False  # product flag still false
    state = dwm_hdr.install(game_dir=tmp_path, target_name="G")
    assert state["prototype"] is True
    assert (tmp_path / ".buusdo" / "dwm_hdr_prototype.json").is_file()
