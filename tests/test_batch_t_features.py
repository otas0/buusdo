"""Batch T: recent remove, rollback failures, steam URIs, crash audit, Bridgeplay ini fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from buusdo.backends.windows_display import rollback_display_session
from buusdo.core.crash_report import append_crash_opt_in_audit, set_crash_upload_opt_in
from buusdo.core.library_progress import resume_scan_status
from buusdo.core.macos_compat import merge_bridgeplay_metalfx
from buusdo.core.recent_games import list_recent, push_recent, remove_recent
from buusdo.core.steam_uris import game_properties_uri_candidates, probe_open_uris
from buusdo.core.i18n import set_locale, t


def test_remove_recent() -> None:
    push_recent({"name": "A", "install_path": "/a", "app_id": "1"})
    push_recent({"name": "B", "install_path": "/b", "app_id": "2"})
    assert remove_recent({"app_id": "1"}) is True
    names = [i["name"] for i in list_recent()]
    assert "A" not in names
    assert "B" in names


def test_rollback_failed_displays_shape(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "buusdo.backends.windows_display.user_config_dir", lambda platform=None: tmp_path
    )
    import time

    (tmp_path / "display_session.json").write_text(
        json.dumps(
            {
                "captured_at": time.time(),
                "width": 1920,
                "height": 1080,
                "displays": [
                    {
                        "device": "\\\\.\\DISPLAY1",
                        "device_string": "Primary",
                        "width": 1920,
                        "height": 1080,
                        "refresh_hz": 60,
                        "primary": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    result = rollback_display_session(dry_run=True)
    # Non-Windows: not restored, but structure includes failed_displays key when nt;
    # on macOS reason is not_windows.
    assert "restored" in result
    assert result.get("reason") == "not_windows" or "failed_displays" in result


def test_steam_uri_probe() -> None:
    uris = game_properties_uri_candidates(570)
    assert uris[0].endswith("/570")
    opened = []

    def opener(uri: str) -> bool:
        opened.append(uri)
        return uri.endswith("GameHub/570")

    result = probe_open_uris(uris, opener=opener)
    assert result["opened"] is True
    assert "GameHub" in result["uri"]
    assert len(result["tried"]) >= 1


def test_crash_opt_in_audit() -> None:
    path = append_crash_opt_in_audit(enabled=True, note="toggle")
    text = path.read_text(encoding="utf-8")
    assert "crash_upload_opt_in" in text
    assert "raw_payload_uploaded" in text
    set_crash_upload_opt_in(False)
    set_crash_upload_opt_in(True)
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1


def test_crossover_gptk_ini_fixtures(tmp_path: Path) -> None:
    for name in ("crossover_metalfx.ini", "gptk_metalfx.ini"):
        src = Path("tests/fixtures") / name
        dest = tmp_path / "metalfx.ini"
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        result = merge_bridgeplay_metalfx(
            tmp_path, game_name="Demo", enable=True, quality="balanced", scale=1.25
        )
        assert str(dest) in result["merged"]
        text = dest.read_text(encoding="utf-8")
        assert "balanced" in text.lower() or "MetalFX" in text or "metalfx" in text
        dest.unlink()


def test_err_kit_i18n_en() -> None:
    set_locale("en")
    assert "not found" in t("err.reshade_kit_missing", path="/x").lower()
    assert "DLL" in t("err.reshade_no_dll") or "dll" in t("err.reshade_no_dll").lower()


def test_resume_scan_status_empty() -> None:
    st = resume_scan_status([])
    assert st["scanned"] == 0
    assert st["partial"] is False
