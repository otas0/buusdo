"""Batch X: prune targets, steam TTL settings, plist comments, migrate CLI."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from buusdo.backends import windows_display as wd
from buusdo.core.macos_compat import _merge_plist_text
from buusdo.core.steam_uris import (
    DEFAULT_STEAM_URI_CACHE_TTL_S,
    cache_properties_uri,
    cached_properties_template,
    set_steam_uri_cache_ttl_s,
    steam_uri_cache_ttl_s,
)


def test_prune_session_targets(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(wd, "user_config_dir", lambda platform=None: tmp_path)
    snap = {
        "captured_at": 1.0,
        "width": 2560,
        "height": 1440,
        "displays": [
            {"device": r"\\.\DISPLAY1", "width": 2560, "height": 1440, "primary": True},
            {"device": r"\\.\DISPLAY2", "width": 1920, "height": 1080, "primary": False},
        ],
        "targets": [
            {"adapterLow": 1, "adapterHigh": 0, "targetId": 0},
            {"adapterLow": 1, "adapterHigh": 0, "targetId": 1},
        ],
    }
    failed = [
        {
            "device": r"\\.\DISPLAY2",
            "width": 1920,
            "height": 1080,
            "adapterLow": 1,
            "adapterHigh": 0,
            "targetId": 1,
        }
    ]
    wd._prune_session_to_failed(snap, failed)
    loaded = json.loads((tmp_path / "display_session.json").read_text(encoding="utf-8"))
    assert len(loaded["displays"]) == 1
    assert loaded["targets"] == [{"adapterLow": 1, "adapterHigh": 0, "targetId": 1}]


def test_steam_ttl_settings_override() -> None:
    assert steam_uri_cache_ttl_s() == DEFAULT_STEAM_URI_CACHE_TTL_S
    set_steam_uri_cache_ttl_s(3600)
    assert steam_uri_cache_ttl_s() == 3600
    cache_properties_uri("steam://url/GameHub/1")
    future = datetime.now(timezone.utc) + timedelta(seconds=3601)
    assert cached_properties_template(now=future) is None


def test_plist_merge_keeps_comment() -> None:
    src = (
        '<?xml version="1.0"?>\n'
        "<plist><dict>\n"
        "\t<!-- keep -->\n"
        "\t<key>other</key>\n"
        "\t<string>x</string>\n"
        "\t<key>metalfx.enabled</key>\n"
        "\t<false/>\n"
        "</dict></plist>\n"
    )
    out = _merge_plist_text(src, enable=True, quality="quality", scale=None)
    assert "<!-- keep -->" in out
    assert "<key>other</key>" in out
    assert out.index("<!-- keep -->") < out.index("<key>other</key>")
    assert "<true/>" in out


def test_migrate_conflict_cli(tmp_path: Path) -> None:
    import importlib.util

    src = Path("docs/fixtures/conflict_export_v1.json")
    dest = tmp_path / "out.json"
    path = Path("scripts/migrate_conflict_export.py")
    spec = importlib.util.spec_from_file_location("migrate_conflict_export", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main([str(src), "-o", str(dest)]) == 0
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert data["schema_version"] == 2
    assert "issue_counts" in data["triple_matrix_summary"]
