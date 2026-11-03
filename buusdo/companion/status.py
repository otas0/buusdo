"""Read-only status snapshot for paired mobile clients."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from buusdo import __version__
from buusdo.companion.protocol import PROTOCOL_VERSION


@dataclass(frozen=True)
class StatusSnapshot:
    """JSON-friendly desktop status; no secrets, no install payloads."""

    protocol_version: int
    app_version: str
    host_label: str
    paired: bool
    recent_game_names: tuple[str, ...] = ()
    last_history_summary: str = ""
    notes: tuple[str, ...] = ()
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["recent_game_names"] = list(self.recent_game_names)
        d["notes"] = list(self.notes)
        return d


def build_status_snapshot(
    *,
    host_label: str,
    paired: bool,
    recent_game_names: list[str] | None = None,
    last_history_summary: str = "",
    extras: dict[str, Any] | None = None,
) -> StatusSnapshot:
    """Assemble a status payload. Caller supplies already-sanitized fields."""
    names = tuple((recent_game_names or [])[:20])
    return StatusSnapshot(
        protocol_version=PROTOCOL_VERSION,
        app_version=__version__,
        host_label=host_label or "desktop",
        paired=bool(paired),
        recent_game_names=names,
        last_history_summary=str(last_history_summary or "")[:500],
        notes=(
            "Companion is read-mostly; install/inject stays on the desktop.",
            "Hardware tricks are not product features — see HARDWARE_NOTES.md.",
        ),
        extras=dict(extras or {}),
    )
