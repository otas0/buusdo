"""Apply companion bind preference from settings (no UI; C3-safe)."""

from __future__ import annotations

from typing import Protocol

from buusdo.core.config_store import get_companion_loopback_only


class _LoopbackBindable(Protocol):
    def set_loopback_only(self, enabled: bool) -> None: ...


def apply_companion_bind_preference(transport: _LoopbackBindable) -> None:
    """Honor ``companion_loopback_only`` from settings.json before start."""
    if get_companion_loopback_only():
        transport.set_loopback_only(True)
