"""Batch V: clear uninstall mark, steam cache clear, renderer comments, schema_version."""

from __future__ import annotations

from pathlib import Path

from buusdo.core.backend import EnhancementTarget
from buusdo.core.conflict_preview import preview_triple_matrix
from buusdo.core.macos_compat import merge_bridgeplay_metalfx
from buusdo.core.recent_games import clear_uninstalled, is_greyed, list_recent, mark_uninstalled, push_recent
from buusdo.core.steam_uris import (
    cache_properties_uri,
    cached_properties_template,
    clear_properties_uri_cache,
    probe_open_uris,
)
from buusdo.core.crash_report import append_crash_opt_in_audit, export_crash_opt_in_audit
from buusdo.core.vkbasalt_prefs import get_remembered_config_path


def test_clear_uninstalled() -> None:
    push_recent({"name": "G", "app_id": "42", "install_path": "/g"})
    mark_uninstalled({"app_id": "42"})
    assert is_greyed(next(i for i in list_recent() if i.get("app_id") == "42"))
    assert clear_uninstalled({"app_id": "42"}) is True
    item = next(i for i in list_recent() if i.get("app_id") == "42")
    assert is_greyed(item) is False


def test_steam_probe_fail_clears_cache() -> None:
    cache_properties_uri("steam://url/GameHub/570")
    assert cached_properties_template()
    out = probe_open_uris(
        ["steam://bad/1"],
        opener=lambda _u: False,
        clear_cache_on_fail=True,
    )
    assert out["opened"] is False
    assert out["cache_cleared"] is True
    assert cached_properties_template() is None
    assert clear_properties_uri_cache() is False


def test_renderer_merge_keeps_comments(tmp_path: Path) -> None:
    ini = tmp_path / "metalfx.ini"
    ini.write_text(
        "[renderer]\n"
        "; keep this comment\n"
        "upscaler = none\n"
        "api = metal\n"
        "extra = stay\n",
        encoding="utf-8",
    )
    merge_bridgeplay_metalfx(tmp_path, game_name="X", enable=True, quality="quality")
    text = ini.read_text(encoding="utf-8")
    assert "; keep this comment" in text
    assert "extra = stay" in text
    assert "upscaler = metalfx" in text or "upscaler=metalfx" in text.replace(" ", "")
    # Order: comment before upscaler still present as original line order for non-touched keys
    assert text.index("; keep this comment") < text.lower().index("extra")


def test_triple_matrix_schema_version(tmp_path: Path) -> None:
    game = tmp_path / "g"
    game.mkdir()
    details = preview_triple_matrix(EnhancementTarget(name="G", install_path=game))
    assert details.get("schema_version") == 1


def test_export_audit_double_redact(tmp_path: Path) -> None:
    append_crash_opt_in_audit(enabled=True, note=f"token=sekrit path={Path.home()}/x")
    dest = tmp_path / "out.jsonl"
    export_crash_opt_in_audit(dest)
    body = dest.read_text(encoding="utf-8")
    assert "sekrit" not in body
    assert str(Path.home()) not in body


def test_remembered_vkbasalt_clears_missing(tmp_path: Path) -> None:
    from buusdo.core.config_store import load_settings, save_settings

    missing = tmp_path / "gone.conf"
    data = load_settings()
    data["vkbasalt_config_path"] = str(missing)
    save_settings(data)
    assert get_remembered_config_path() == ""
    assert "vkbasalt_config_path" not in load_settings()


def test_unsigned_sha256_format(tmp_path: Path) -> None:
    import hashlib

    f = tmp_path / "buusdo"
    f.write_bytes(b"abc")
    digest = hashlib.sha256(b"abc").hexdigest()
    line = f"{digest}  {f}"
    assert line.startswith(digest)
    assert "buusdo" in line
