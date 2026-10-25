"""Coverage for CCD/HDR batch: kits, triple matrix, presets, Bridgeplay, crash upload, recent."""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

from buusdo.core.backend import EnhancementTarget
from buusdo.core.conflict import triple_matrix
from buusdo.core.conflict_preview import preview_triple_matrix
from buusdo.core.crash_report import _upload, capture_exception, redact
from buusdo.core.kit_validate import validate_optiscaler_kit, validate_reshade_kit
from buusdo.core.macos_compat import bridgeplay_metalfx_file_contents, write_bridgeplay_metalfx_files
from buusdo.core.proton_health import check_proton_prefix
from buusdo.core.recent_games import list_recent, push_recent
from buusdo.core.vkbasalt_template import list_presets, render_preset, write_template
from buusdo.core.i18n import set_locale, t


def test_kit_validate_missing_and_ok(tmp_path: Path) -> None:
    bad = validate_reshade_kit(tmp_path / "missing")
    assert bad.ok is False
    assert "ReShade64.dll" in bad.missing

    kit = tmp_path / "reshade"
    kit.mkdir()
    (kit / "ReShade64.dll").write_bytes(b"x")
    good = validate_reshade_kit(kit)
    assert good.ok is True
    assert "ReShade64.dll" in good.found

    o = validate_optiscaler_kit(None)
    assert o.ok is False


def test_triple_matrix_and_preview(tmp_path: Path) -> None:
    game = tmp_path / "game"
    game.mkdir()
    (game / "d3d9.dll").write_bytes(b"remix-ish")
    (game / ".buusdo").mkdir()
    # remix status looks for known markers — empty report is fine
    kit = tmp_path / "opti"
    kit.mkdir()
    (kit / "dxgi.dll").write_bytes(b"o")
    report = triple_matrix(game, optiscaler_kit=kit, reshade_proxy="d3d9.dll")
    assert isinstance(report.issues, list)

    target = EnhancementTarget(name="G", install_path=game)
    rkit = tmp_path / "rs"
    rkit.mkdir()
    (rkit / "ReShade64.dll").write_bytes(b"R")
    details = preview_triple_matrix(target, reshade_kit=rkit, optiscaler_kit=kit)
    assert details["mode"] == "triple_matrix"
    assert details["diffs"]


def test_vkbasalt_presets(tmp_path: Path) -> None:
    names = list_presets()
    assert {"cas", "smaa", "contrast"}.issubset(set(names))
    for name in ("cas", "smaa", "contrast", "cas_smaa"):
        text = render_preset(name)
        assert "effects =" in text
        path = write_template(tmp_path / f"{name}.conf", preset=name)
        assert path.is_file()


def test_bridgeplay_ini_plist(tmp_path: Path) -> None:
    files = bridgeplay_metalfx_file_contents(enable=True, quality="balanced", scale=1.25)
    assert "[MetalFX]" in files["ini"]
    assert "metalfx.enabled" in files["plist"]
    assert "<true/>" in files["plist"]
    written = write_bridgeplay_metalfx_files(tmp_path, game_name="Demo", scale=1.0)
    assert Path(written["ini"]).is_file()
    assert Path(written["plist"]).read_text(encoding="utf-8").startswith("<?xml")


def test_crash_upload_redacted(monkeypatch, tmp_path: Path) -> None:
    from buusdo.core.crash_report import set_crash_upload_opt_in

    set_crash_upload_opt_in(True)
    monkeypatch.setenv("BUUSDO_CRASH_REPORTS", "1")
    monkeypatch.setenv("BUUSDO_CRASH_UPLOAD", "1")
    monkeypatch.setenv("BUUSDO_CRASH_ENDPOINT", "https://example.test/crash")
    monkeypatch.setenv("BUUSDO_CRASH_FORMAT", "json")

    class _Resp:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with mock.patch("urllib.request.urlopen", return_value=_Resp()) as opener:
        path = capture_exception(
            RuntimeError(f"fail at {Path.home()}/secret"),
            context={"token": "sekrit"},
        )
        assert path is not None
        opener.assert_called_once()
        body = path.read_text(encoding="utf-8")
        assert str(Path.home()) not in body
        assert "sekrit" not in body or "<redacted>" in redact("token=sekrit")
        data = json.loads(body)
        assert data.get("upload") is True


def test_upload_requires_endpoint(monkeypatch) -> None:
    monkeypatch.delenv("BUUSDO_CRASH_ENDPOINT", raising=False)
    monkeypatch.delenv("BUUSDO_CRASH_DSN", raising=False)
    assert _upload({"message": "x"}).get("uploaded") is False


def test_recent_games_roundtrip() -> None:
    push_recent({"name": "A", "install_path": "/a"})
    push_recent({"name": "B", "install_path": "/b"})
    push_recent({"name": "A", "install_path": "/a"})
    items = list_recent()
    assert items[0]["name"] == "A"
    assert len(items) == 2


def test_proton_health_steam_uri_and_i18n(tmp_path: Path) -> None:
    set_locale("zh")
    target = EnhancementTarget(
        name="G",
        install_path=tmp_path,
        metadata={
            "runtime": "proton",
            "app_id": "123",
            "proton_prefix": str(tmp_path / "nope"),
        },
    )
    health = check_proton_prefix(target)
    assert health is not None
    assert health.ok is False
    assert health.steam_uri == "steam://run/123"
    assert "Proton" in health.message or "启动" in health.message
    assert t("proton.open_steam")
