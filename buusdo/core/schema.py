"""Config schema versioning and migrations."""

from __future__ import annotations

from typing import Any, Callable

CURRENT_SCHEMA_VERSION = 2

Migrator = Callable[[dict[str, Any]], dict[str, Any]]


def _migrate_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
    # v1 had flat keys; v2 nests preferences under "prefs".
    if "prefs" not in data:
        prefs = {}
        for key in ("executable", "graphics_api", "steam_id3", "display_profile"):
            if key in data:
                prefs[key] = data.pop(key)
        if prefs:
            data["prefs"] = prefs
    data["schema_version"] = 2
    return data


_MIGRATIONS: dict[int, Migrator] = {
    1: _migrate_v1_to_v2,
}


def ensure_schema(data: dict[str, Any]) -> dict[str, Any]:
    """Upgrade game/settings dict in-place-ish to CURRENT_SCHEMA_VERSION."""
    version = int(data.get("schema_version") or 1)
    while version < CURRENT_SCHEMA_VERSION:
        migrator = _MIGRATIONS.get(version)
        if migrator is None:
            break
        data = migrator(data)
        version = int(data.get("schema_version") or version + 1)
    data.setdefault("schema_version", CURRENT_SCHEMA_VERSION)
    return data


def stamp_new(data: dict[str, Any] | None = None) -> dict[str, Any]:
    out = dict(data or {})
    out["schema_version"] = CURRENT_SCHEMA_VERSION
    return out
