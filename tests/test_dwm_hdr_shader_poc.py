"""phase3/dwm-hdr only: shader PoC materialization."""

from __future__ import annotations

from pathlib import Path

import pytest

from buusdo.core import dwm_hdr
from buusdo.core.errors import BuusdoError


def test_shader_poc_materializes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BUUSDO_ENABLE_DWM_HDR_PROTOTYPE", "1")
    state = dwm_hdr.install(game_dir=tmp_path, target_name="Demo")
    assert state["live_dwm_patch"] is False
    shader = tmp_path / ".buusdo" / "dwm_hdr_poc" / "sdr_to_hdr_tonemap.hlsl"
    assert shader.is_file()
    text = shader.read_text(encoding="utf-8")
    assert "ToneMapToHdr" in text
    assert "NOT applied to DWM" in text or "PoC" in text
    st = dwm_hdr.status(tmp_path)
    assert st["shader_poc"] is True
    assert st["available"] is False


def test_shader_poc_off_without_flag(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("BUUSDO_ENABLE_DWM_HDR_PROTOTYPE", raising=False)
    with pytest.raises(BuusdoError):
        dwm_hdr.install(game_dir=tmp_path, target_name="X")
