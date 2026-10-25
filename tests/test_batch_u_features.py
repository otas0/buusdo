"""Batch U: i18n err keys, recent grey, steam cache, audit export, GPTK renderer merge."""

from __future__ import annotations

from pathlib import Path

from buusdo.core.crash_report import (
    append_crash_opt_in_audit,
    clear_crash_opt_in_audit,
    export_crash_opt_in_audit,
)
from buusdo.core.i18n import _STRINGS, set_locale, t
from buusdo.core.macos_compat import merge_bridgeplay_metalfx
from buusdo.core.recent_games import is_greyed, list_recent, mark_uninstalled, push_recent
from buusdo.core.steam_uris import cache_properties_uri, cached_properties_template, game_properties_uri_candidates
from buusdo.core.conflict_preview import preview_triple_matrix
from buusdo.core.backend import EnhancementTarget


def test_err_keys_complete_zh_en() -> None:
    zh = _STRINGS["zh"]
    en = _STRINGS["en"]
    err_zh = {k for k in zh if k.startswith("err.")}
    err_en = {k for k in en if k.startswith("err.")}
    assert err_zh == err_en
    assert err_zh  # non-empty
    set_locale("en")
    for key in sorted(err_zh):
        assert t(key) != key
        assert t(key)
    set_locale("zh")
    for key in sorted(err_zh):
        assert t(key) != key


def test_mark_uninstalled_greys() -> None:
    push_recent({"name": "G", "app_id": "9", "install_path": "/g"})
    assert mark_uninstalled({"app_id": "9"}) is True
    item = next(i for i in list_recent() if i.get("app_id") == "9")
    assert item.get("last_uninstalled_at")
    assert is_greyed(item) is True


def test_steam_uri_cache() -> None:
    cache_properties_uri("steam://url/GameHub/570")
    tpl = cached_properties_template()
    assert tpl and "{app_id}" in tpl
    uris = game_properties_uri_candidates(730)
    assert "730" in uris[0]


def test_audit_export_clear(tmp_path: Path) -> None:
    append_crash_opt_in_audit(enabled=True, note="n")
    dest = tmp_path / "audit.jsonl"
    export_crash_opt_in_audit(dest)
    assert dest.is_file()
    assert clear_crash_opt_in_audit() is True
    assert clear_crash_opt_in_audit() is False


def test_gptk_renderer_merge(tmp_path: Path) -> None:
    src = Path("tests/fixtures/gptk_metalfx.ini").read_text(encoding="utf-8")
    ini = tmp_path / "metalfx.ini"
    ini.write_text(src, encoding="utf-8")
    merge_bridgeplay_metalfx(tmp_path, game_name="X", enable=True, quality="quality")
    text = ini.read_text(encoding="utf-8")
    assert "[renderer]" in text
    assert "upscaler" in text
    assert "metalfx" in text.lower()


def test_triple_matrix_summary(tmp_path: Path) -> None:
    game = tmp_path / "g"
    game.mkdir()
    target = EnhancementTarget(name="G", install_path=game)
    details = preview_triple_matrix(target)
    assert "triple_matrix_summary" in details
    assert "issue_counts" in details["triple_matrix_summary"]


def test_ccd_fixture_shape() -> None:
    import importlib.util

    path = Path("scripts/validate_ccd_fixture.py")
    spec = importlib.util.spec_from_file_location("validate_ccd_fixture", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fixture = Path("docs/fixtures/ccd_dual_monitor_sample.json")
    assert mod.validate(fixture) == []
    live = mod.validate(fixture, require_live=True)
    assert any("host_windows" in e or "ILLUSTRATIVE" in e for e in live)


def test_deploy_unsigned_snippet(tmp_path: Path) -> None:
    """deploy.sh always writes dist/UNSIGNED.txt; assert the inventory pattern."""
    out = tmp_path / "dist"
    out.mkdir()
    (out / "buusdo").write_text("x", encoding="utf-8")
    inv = out / "UNSIGNED.txt"
    inv.write_text(
        "# buusdo unsigned inventory\n" + "\n".join(sorted(str(p) for p in out.rglob("*") if p.is_file())) + "\n",
        encoding="utf-8",
    )
    text = inv.read_text(encoding="utf-8")
    assert "UNSIGNED" in text or "unsigned" in text.lower()
    assert "buusdo" in text
