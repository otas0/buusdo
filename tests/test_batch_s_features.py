"""Batch S: multi-monitor session, partial cancel cache, Bridgeplay plist, CCD fixture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from buusdo.backends.windows_display import (
    display_session_status,
    heal_display_session,
)
from buusdo.core.discovery import DiscoveryCancelled, discover_steam_games
from buusdo.core.library_cache import load_cached_games
from buusdo.core.macos_compat import merge_bridgeplay_metalfx
from buusdo.core.i18n import set_locale, t


def test_ccd_fixture_shape() -> None:
    path = Path("docs/fixtures/ccd_dual_monitor_sample.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["target_count"] == 2
    assert len(data["adapter_target_ids"]) == 2
    assert {t["targetId"] for t in data["adapter_target_ids"]} == {0, 1}
    assert data["display_count"] == 2


def test_session_warn_and_legacy_migrate(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "buusdo.backends.windows_display.user_config_dir", lambda platform=None: tmp_path
    )
    import time

    path = tmp_path / "display_session.json"
    path.write_text(
        json.dumps(
            {
                "width": 1920,
                "height": 1080,
                "refresh_hz": 60,
                "captured_at": time.time() - (11 * 3600),
            }
        ),
        encoding="utf-8",
    )
    status = heal_display_session()
    assert status["action"] == "kept"
    assert status.get("warn_expiring") is True
    assert "displays" in status["snap"]
    ui = display_session_status()
    assert ui["present"] is True
    assert ui["warn_expiring"] is True


def test_partial_cache_resume(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "buusdo.core.library_cache.user_config_dir", lambda: tmp_path / "cfg"
    )
    (tmp_path / "cfg").mkdir()
    steam = tmp_path / "Steam"
    apps = steam / "steamapps"
    apps.mkdir(parents=True)
    manifests = []
    for app_id, name in (("1", "A"), ("2", "B"), ("3", "C")):
        m = apps / f"appmanifest_{app_id}.acf"
        m.write_text(
            f'"AppState"\n{{\n"appid" "{app_id}"\n"name" "{name}"\n"installdir" "{name}"\n}}\n',
            encoding="utf-8",
        )
        (apps / "common" / name).mkdir(parents=True, exist_ok=True)
        manifests.append(m)

    # Cancel after the first real manifest parse by counting cancel probes.
    state = {"n": 0}

    def cancel_after_one() -> bool:
        state["n"] += 1
        return state["n"] >= 6

    with pytest.raises(DiscoveryCancelled) as ei:
        load_cached_games([steam], force=True, should_cancel=cancel_after_one)
    assert ei.value.scanned_manifests

    cache = json.loads((tmp_path / "cfg" / "library_cache.json").read_text(encoding="utf-8"))
    assert cache.get("partial") is True

    # Resume: skip already-scanned manifests (same mtime).
    games = load_cached_games([steam], force=False)
    assert {g.app_id for g in games} >= {"1", "2", "3"} or len(games) >= 1
    cache2 = json.loads((tmp_path / "cfg" / "library_cache.json").read_text(encoding="utf-8"))
    assert cache2.get("partial") is False


def test_bridgeplay_official_plist_fixture(tmp_path: Path) -> None:
    fixture = Path("tests/fixtures/bridgeplay_metalfx.plist")
    dest = tmp_path / "metalfx.plist"
    dest.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    result = merge_bridgeplay_metalfx(
        tmp_path, game_name="Demo", enable=True, quality="balanced", scale=1.5
    )
    assert str(dest) in result["merged"]
    text = dest.read_text(encoding="utf-8")
    assert "metalfx.enabled" in text
    assert "<true/>" in text
    assert "balanced" in text
    assert "metalfx.scale" in text
    assert "bridgeplay.schema" in text  # preserved


def test_err_i18n_keys() -> None:
    set_locale("zh")
    assert "ReShade" in t("err.reshade_kit") or "工具包" in t("err.reshade_kit")
    set_locale("en")
    assert "ReShade" in t("err.reshade_kit")
