from pathlib import Path

from buusdo.core.macos_compat import discover_compat_layers, metalfx_options_payload


def test_metalfx_payload_not_dlss() -> None:
    payload = metalfx_options_payload()
    blob = str(payload).lower()
    assert "metalfx" in blob
    assert "dlss" not in blob
    assert payload["enhancement"] == "metalfx_compat"


def test_discover_compat_layers(tmp_path: Path) -> None:
    gptk = tmp_path / "Library" / "Application Support" / "Game Porting Toolkit"
    gptk.mkdir(parents=True)
    layers = discover_compat_layers(home=tmp_path)
    assert any(l.id == "gptk" for l in layers)
