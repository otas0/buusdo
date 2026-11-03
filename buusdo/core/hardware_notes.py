"""Honest host-hardware doctrine (C4). No fake 'RAM as GPU' features."""

from __future__ import annotations

from dataclasses import dataclass

from buusdo.core.backend import Capability


@dataclass(frozen=True)
class HardwareNote:
    """Stable id + i18n keys for one honesty bullet."""

    id: str
    title_key: str
    body_key: str


# Order matches docs/HARDWARE_NOTES.md.
HARDWARE_NOTES: tuple[HardwareNote, ...] = (
    HardwareNote(
        "unified_memory",
        "hw.unified_memory.title",
        "hw.unified_memory.body",
    ),
    HardwareNote(
        "extra_gpu",
        "hw.extra_gpu.title",
        "hw.extra_gpu.body",
    ),
    HardwareNote(
        "resizable_bar",
        "hw.resizable_bar.title",
        "hw.resizable_bar.body",
    ),
    HardwareNote(
        "vram_spill",
        "hw.vram_spill.title",
        "hw.vram_spill.body",
    ),
    HardwareNote(
        "soft_raster",
        "hw.soft_raster.title",
        "hw.soft_raster.body",
    ),
)


def honesty_capabilities(*, t) -> list[Capability]:
    """Capabilities-list rows: informational only (available=False = not a boost)."""
    rows: list[Capability] = []
    for note in HARDWARE_NOTES:
        rows.append(
            Capability(
                id=f"hw.{note.id}",
                title=t(note.title_key),
                description=t(note.body_key),
                available=False,
                notes=t("hw.not_a_boost"),
            )
        )
    return rows
