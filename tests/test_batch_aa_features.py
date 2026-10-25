"""Batch AA: steam cache status, migrate dry-run JSON diff, session target counts."""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

from buusdo.backends import windows_display as wd
from buusdo.core.steam_uris import (
    cache_properties_uri,
    clear_properties_uri_cache,
    steam_uri_cache_status,
)


def test_steam_uri_cache_status() -> None:
    clear_properties_uri_cache()
    off = steam_uri_cache_status()
    assert off["cached"] is False
    assert off["template"] is None
    cache_properties_uri("steam://url/GameHub/570")
    on = steam_uri_cache_status()
    assert on["cached"] is True
    assert "{app_id}" in str(on["template"])
    clear_properties_uri_cache()
    assert steam_uri_cache_status()["cached"] is False


def test_display_session_status_includes_targets(tmp_path: Path, monkeypatch) -> None:
    import time

    monkeypatch.setattr(wd, "user_config_dir", lambda platform=None: tmp_path)
    snap = {
        "captured_at": time.time(),
        "width": 1920,
        "height": 1080,
        "displays": [{"device": r"\\.\DISPLAY1", "width": 1920, "height": 1080, "primary": True}],
        "targets": [{"adapterLow": 1, "adapterHigh": 0, "targetId": 0}],
    }
    (tmp_path / "display_session.json").write_text(json.dumps(snap), encoding="utf-8")
    st = wd.display_session_status()
    assert st["present"] is True
    assert st["displays"] == 1
    assert st["targets"] == 1
    assert wd.drop_session_ccd_target(adapter_low=1, adapter_high=0, target_id=0) is True
    assert wd.display_session_status().get("present") is False


def test_migrate_dry_run_prints_json_diff(tmp_path: Path, capsys) -> None:
    src = tmp_path / "export_v1.json"
    src.write_text(
        json.dumps({"schema_version": 1, "mode": "reshade", "blocked": False, "diffs": []}),
        encoding="utf-8",
    )
    path = Path("scripts/migrate_conflict_export.py")
    spec = importlib.util.spec_from_file_location("migrate_conflict_export", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main([str(src), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "WOULD migrate" in out
    assert "schema_version" in out
    assert "+++" in out or "---" in out
    # Unchanged file → no diff body beyond header line
    shutil.copy(src, tmp_path / "already.json")
    # Migrate once for real so second dry-run is ok
    assert mod.main([str(src), "--in-place"]) == 0
    assert mod.main([str(src), "--dry-run"]) == 0
    out2 = capsys.readouterr().out
    assert "ok " in out2
    assert "no JSON changes" in out2
