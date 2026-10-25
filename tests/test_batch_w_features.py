"""Batch W: session prune, steam TTL, conflict v2, MetalFX comments, HDR retry."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import ctypes
import pytest

from buusdo.backends import windows_display as wd
from buusdo.core.backend import EnhancementTarget
from buusdo.core.conflict_preview import (
    CONFLICT_EXPORT_SCHEMA_VERSION,
    migrate_conflict_export,
    preview_triple_matrix,
)
from buusdo.core.macos_compat import merge_bridgeplay_metalfx
from buusdo.core.steam_uris import (
    STEAM_URI_CACHE_TTL_S,
    cache_properties_uri,
    cached_properties_template,
)


def test_prune_session_keeps_failed_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(wd, "user_config_dir", lambda platform=None: tmp_path)
    snap = {
        "captured_at": 1.0,
        "width": 2560,
        "height": 1440,
        "displays": [
            {"device": r"\\.\DISPLAY1", "width": 2560, "height": 1440, "primary": True},
            {"device": r"\\.\DISPLAY2", "width": 1920, "height": 1080, "primary": False},
        ],
    }
    failed = [{"device": r"\\.\DISPLAY2", "width": 1920, "height": 1080}]
    wd._prune_session_to_failed(snap, failed)
    loaded = json.loads((tmp_path / "display_session.json").read_text(encoding="utf-8"))
    assert len(loaded["displays"]) == 1
    assert loaded["displays"][0]["device"] == r"\\.\DISPLAY2"
    assert loaded["width"] == 1920


def test_steam_uri_ttl_expires() -> None:
    cache_properties_uri("steam://url/GameHub/570")
    assert cached_properties_template() is not None
    future = datetime.now(timezone.utc) + timedelta(seconds=STEAM_URI_CACHE_TTL_S + 10)
    assert cached_properties_template(now=future) is None


def test_conflict_schema_v2_and_migrate() -> None:
    v1 = json.loads(Path("docs/fixtures/conflict_export_v1.json").read_text(encoding="utf-8"))
    migrated = migrate_conflict_export(v1)
    assert migrated["schema_version"] == CONFLICT_EXPORT_SCHEMA_VERSION
    assert "issue_counts" in migrated["triple_matrix_summary"]
    v2 = json.loads(Path("docs/fixtures/conflict_export_v2.json").read_text(encoding="utf-8"))
    assert migrate_conflict_export(v2)["schema_version"] == 2
    details = preview_triple_matrix(
        EnhancementTarget(name="G", install_path=Path("."))
    )
    assert details["schema_version"] == 2


def test_metalfx_section_keeps_comments(tmp_path: Path) -> None:
    ini = tmp_path / "metalfx.ini"
    ini.write_text(
        "[MetalFX]\n"
        "; preserve me\n"
        "enabled = false\n"
        "custom = keep\n",
        encoding="utf-8",
    )
    merge_bridgeplay_metalfx(tmp_path, game_name="X", enable=True, quality="balanced")
    text = ini.read_text(encoding="utf-8")
    assert "; preserve me" in text
    assert "custom = keep" in text
    assert "enabled = true" in text or "enabled=true" in text.replace(" ", "")


def test_retry_hdr_target_mock(monkeypatch) -> None:
    calls: list = []

    class FakeUser32:
        def DisplayConfigSetDeviceInfo(self, req_ref):
            calls.append(req_ref)
            return 0

    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(user32=FakeUser32()), raising=False)
    out = wd.retry_hdr_target(
        adapter_low=12345, adapter_high=0, target_id=1, enable=True, dry_run=False
    )
    assert out["ok"] is True
    assert out["action"] == "SET_ADVANCED_COLOR_STATE"
    assert out["targetId"] == 1
    assert calls

    dry = wd.retry_hdr_target(
        adapter_low=1, adapter_high=0, target_id=0, enable=False, dry_run=True
    )
    assert dry["ok"] is True
    assert dry["action"] == "hdr_retry_dry_run"


def test_compile_packs_hlsl_zip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util

    path = Path("scripts/compile_dwm_hdr_poc.py")
    spec = importlib.util.spec_from_file_location("compile_dwm_hdr_poc", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = tmp_path / "poc"
    monkeypatch.setattr(mod, "_find_compiler", lambda: None)
    rc = mod.main(["--out", str(out)])
    assert rc == 0
    man = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert man["status"] == "skipped_no_compiler"
    assert (out / "hlsl_sources.zip").is_file()
    assert man.get("hlsl_sha256")
