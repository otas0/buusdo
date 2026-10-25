from buusdo.core.macos_compat import BRIDGEPLAY_METALFX_KEYS, metalfx_options_payload


def test_bridgeplay_keys_are_metalfx_only() -> None:
    payload = metalfx_options_payload(layer_id="bridgeplay", quality="quality", scale=1.5)
    keys = payload["bridgeplay_keys"]
    assert keys["renderer.upscaler"] == "metalfx"
    assert "metalfx.enabled" in keys
    blob = str(payload).lower()
    assert "dlss" not in blob
    assert "metalfx" in BRIDGEPLAY_METALFX_KEYS or "metalfx.enabled" in BRIDGEPLAY_METALFX_KEYS
