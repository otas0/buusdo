"""Batch Z: drop CCD target after HDR retry; steam clear cache; dry-run migrate."""

from __future__ import annotations

import json
from pathlib import Path

from buusdo.backends import windows_display as wd
from buusdo.core.steam_uris import cache_properties_uri, cached_properties_template, clear_properties_uri_cache


def test_drop_session_ccd_target(tmp_path: Path, monkeypatch) -> None:
    import time

    monkeypatch.setattr(wd, "user_config_dir", lambda platform=None: tmp_path)
    snap = {
        "captured_at": time.time(),
        "width": 2560,
        "height": 1440,
        "displays": [
            {
                "device": r"\\.\DISPLAY1",
                "width": 2560,
                "height": 1440,
                "primary": True,
                "adapterLow": 1,
                "adapterHigh": 0,
                "targetId": 0,
            },
            {
                "device": r"\\.\DISPLAY2",
                "width": 1920,
                "height": 1080,
                "primary": False,
                "adapterLow": 1,
                "adapterHigh": 0,
                "targetId": 1,
            },
        ],
        "targets": [
            {"adapterLow": 1, "adapterHigh": 0, "targetId": 0},
            {"adapterLow": 1, "adapterHigh": 0, "targetId": 1},
        ],
    }
    (tmp_path / "display_session.json").write_text(json.dumps(snap), encoding="utf-8")
    assert wd.drop_session_ccd_target(adapter_low=1, adapter_high=0, target_id=1) is True
    loaded = json.loads((tmp_path / "display_session.json").read_text(encoding="utf-8"))
    assert loaded["targets"] == [{"adapterLow": 1, "adapterHigh": 0, "targetId": 0}]
    assert len(loaded["displays"]) == 1


def test_clear_steam_uri_cache() -> None:
    cache_properties_uri("steam://url/GameHub/1")
    assert cached_properties_template()
    assert clear_properties_uri_cache() is True
    assert cached_properties_template() is None
