"""Honesty catalog for host hardware (C4)."""

from __future__ import annotations

from buusdo.core.hardware_notes import HARDWARE_NOTES, honesty_capabilities
from buusdo.core.i18n import reload_catalogs, set_locale, t
from buusdo.core.platform_detect import HostPlatform, host_adapter_summary


def test_hardware_notes_five_points() -> None:
    assert len(HARDWARE_NOTES) == 5
    ids = [n.id for n in HARDWARE_NOTES]
    assert ids == [
        "unified_memory",
        "extra_gpu",
        "resizable_bar",
        "vram_spill",
        "soft_raster",
    ]


def test_honesty_capabilities_marked_unavailable() -> None:
    reload_catalogs()
    set_locale("en")
    rows = honesty_capabilities(t=t)
    assert len(rows) == 5
    assert all(not c.available for c in rows)
    assert "Unified memory" in rows[0].title
    assert "not a buusdo trick" in rows[0].description.lower() or "hardware design" in rows[0].description.lower()
    assert "RAM" in rows[2].description or "VRAM" in rows[2].description


def test_host_adapter_summary_never_raises() -> None:
    # May be empty in CI sandboxes; must not throw.
    s = host_adapter_summary()
    assert isinstance(s, str)
    for plat in HostPlatform:
        assert isinstance(host_adapter_summary(plat), str)


def test_hw_i18n_keys_present_zh() -> None:
    reload_catalogs()
    set_locale("zh")
    assert t("hw.section") != "hw.section"
    assert "统一" in t("hw.unified_memory.title") or "内存" in t("hw.unified_memory.body")
