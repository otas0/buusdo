"""Coverage for CCD verify, exact watch, session heal, cancel, Bridgeplay merge, crash opt-in."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest import mock

import pytest

from buusdo.backends.windows_display import (
    heal_display_session,
    list_advanced_color_targets,
    verify_set_advanced_color_state,
)
from buusdo.core.backend import EnhancementTarget
from buusdo.core.crash_report import (
    _build_sentry_envelope,
    _upload,
    capture_exception,
    set_crash_upload_opt_in,
)
from buusdo.core.discovery import DiscoveryCancelled, discover_steam_games
from buusdo.core.display_watch import process_matches_target
from buusdo.core.macos_compat import discover_bridgeplay_config_files, merge_bridgeplay_metalfx
from buusdo.core.steam_launch import write_proton_launch_note
from buusdo.core.transaction import Transaction
from buusdo.core.i18n import set_locale, t


def test_ccd_verify_non_windows() -> None:
    assert list_advanced_color_targets() == []
    result = verify_set_advanced_color_state(enable=True, dry_run=True)
    assert result["reason"] == "not_windows"


def test_display_session_heal_corrupt_and_expired(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "buusdo.backends.windows_display.user_config_dir", lambda platform=None: tmp_path
    )
    path = tmp_path / "display_session.json"
    path.write_text("{not-json", encoding="utf-8")
    assert heal_display_session()["action"] == "deleted_corrupt"
    assert not path.exists()

    path.write_text(
        json.dumps({"width": 1920, "height": 1080, "captured_at": time.time() - 999999}),
        encoding="utf-8",
    )
    assert heal_display_session()["action"] == "deleted_expired"

    path.write_text(
        json.dumps({"width": 1920, "height": 1080, "captured_at": time.time()}),
        encoding="utf-8",
    )
    assert heal_display_session()["action"] == "kept"


def test_exact_exe_match(tmp_path: Path) -> None:
    exe = tmp_path / "Game.exe"
    exe.write_bytes(b"MZ")
    target = EnhancementTarget(name="G", install_path=tmp_path, executable=exe)

    class _Proc:
        def exe(self):
            return str(exe.resolve())

    assert process_matches_target(_Proc(), target) is True

    class _Other:
        def exe(self):
            return str(tmp_path / "other.exe")

    assert process_matches_target(_Other(), target) is False


def test_discover_cancel(tmp_path: Path) -> None:
    steam = tmp_path / "Steam"
    apps = steam / "steamapps"
    apps.mkdir(parents=True)
    (apps / "appmanifest_1.acf").write_text(
        '"AppState"\n{\n"appid" "1"\n"name" "A"\n"installdir" "A"\n}\n',
        encoding="utf-8",
    )
    (apps / "common" / "A").mkdir(parents=True)

    calls = {"n": 0}

    def cancel() -> bool:
        calls["n"] += 1
        return calls["n"] > 1

    with pytest.raises(DiscoveryCancelled):
        discover_steam_games([steam], should_cancel=cancel)


def test_bridgeplay_merge_existing_ini(tmp_path: Path) -> None:
    ini = tmp_path / "metalfx.ini"
    ini.write_text("[Other]\nx=1\n", encoding="utf-8")
    found = discover_bridgeplay_config_files(tmp_path)
    assert found["ini"] == ini
    result = merge_bridgeplay_metalfx(tmp_path, game_name="Demo", enable=True, quality="quality")
    assert str(ini) in result["merged"]
    text = ini.read_text(encoding="utf-8")
    assert "MetalFX" in text
    assert "quality" in text


def test_crash_opt_in_and_envelope(monkeypatch) -> None:
    set_crash_upload_opt_in(True)
    monkeypatch.setenv("BUUSDO_CRASH_REPORTS", "1")
    monkeypatch.setenv("BUUSDO_CRASH_UPLOAD", "1")
    monkeypatch.setenv("BUUSDO_CRASH_DSN", "https://key@example.test/1")
    body = _build_sentry_envelope({"ts": "t", "type": "E", "message": "m", "traceback": "x", "context": {}})
    assert b"application/json" in body or b'"type":"event"' in body
    assert b"buusdo" in body

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with mock.patch("urllib.request.urlopen", return_value=_Resp()):
        path = capture_exception(RuntimeError("boom"), context={"token": "sekrit"})
        assert path is not None
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("upload") is True
        assert "sekrit" not in path.read_text(encoding="utf-8")

    set_crash_upload_opt_in(False)
    assert _upload({"message": "x"}).get("reason") == "opt_in_required"


def test_proton_launch_note(tmp_path: Path) -> None:
    local = tmp_path / "localconfig.vdf"
    local.write_text(
        '"UserLocalConfigStore"\n{\n\t"Software"\n\t{\n\t\t"Valve"\n\t\t{\n\t\t\t'
        '"Steam"\n\t\t\t{\n\t\t\t\t"apps"\n\t\t\t\t{\n\t\t\t\t\t"570"\n\t\t\t\t\t{\n'
        '\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n}\n',
        encoding="utf-8",
    )
    with Transaction() as tx:
        result = write_proton_launch_note(tx, local, "570", note="launch once")
    text = local.read_text(encoding="utf-8")
    assert "buusdo_note" in text
    assert "launch once" in text
    assert result["app_id"] == "570"


def test_install_messages_i18n() -> None:
    set_locale("en")
    assert "Uninstalled" in t("msg.uninstall_win")
    set_locale("zh")
    assert "卸载" in t("msg.uninstall_win")
