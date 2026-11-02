"""Stable game-list selection keys (no Qt)."""

from __future__ import annotations

from buusdo.core.backend import EnhancementTarget


def selection_key(target: EnhancementTarget | None) -> tuple[str, str, str] | None:
    """Identify a target across scan/reload (app_id, install_path, name)."""
    if target is None:
        return None
    return (
        str(target.metadata.get("app_id") or ""),
        str(target.install_path),
        target.name,
    )
