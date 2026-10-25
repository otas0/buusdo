"""Track recently touched games for tray shortcuts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from buusdo.core.platform_detect import user_config_dir


def _path() -> Path:
    return user_config_dir() / "recent_games.json"


def _item_key(game: dict[str, Any]) -> str:
    return str(game.get("app_id") or game.get("install_path") or game.get("name"))


def push_recent(game: dict[str, Any], *, limit: int = 8) -> None:
    items = list_recent()
    key = _item_key(game)
    items = [i for i in items if _item_key(i) != key]
    payload = dict(game)
    payload.pop("last_uninstalled_at", None)
    items.insert(0, payload)
    _path().parent.mkdir(parents=True, exist_ok=True)
    _path().write_text(json.dumps(items[:limit], indent=2) + "\n", encoding="utf-8")


def list_recent() -> list[dict[str, Any]]:
    path = _path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def mark_uninstalled(game: dict[str, Any] | None = None, *, key: str | None = None) -> bool:
    """Stamp last_uninstalled_at on a recent entry (kept for tray grey-out)."""
    needle = key or (_item_key(game) if game else "")
    if not needle:
        return False
    items = list_recent()
    found = False
    ts = datetime.now(timezone.utc).isoformat()
    for item in items:
        if _item_key(item) == needle:
            item["last_uninstalled_at"] = ts
            found = True
            break
    if not found and game:
        payload = dict(game)
        payload["last_uninstalled_at"] = ts
        items.insert(0, payload)
        found = True
    if not found:
        return False
    _path().parent.mkdir(parents=True, exist_ok=True)
    _path().write_text(json.dumps(items[:8], indent=2) + "\n", encoding="utf-8")
    return True


def remove_recent(game: dict[str, Any] | None = None, *, key: str | None = None) -> bool:
    """Remove a recent entry by app_id / install_path / name. Returns True if removed."""
    needle = key or (_item_key(game) if game else "")
    if not needle:
        return False
    items = list_recent()
    kept = [i for i in items if _item_key(i) != needle]
    if len(kept) == len(items):
        return False
    _path().parent.mkdir(parents=True, exist_ok=True)
    _path().write_text(json.dumps(kept, indent=2) + "\n", encoding="utf-8")
    return True


def is_greyed(item: dict[str, Any]) -> bool:
    return bool(item.get("last_uninstalled_at"))


def clear_uninstalled(game: dict[str, Any] | None = None, *, key: str | None = None) -> bool:
    """Clear last_uninstalled_at after the game is reinstalled / back in library."""
    needle = key or (_item_key(game) if game else "")
    if not needle:
        return False
    items = list_recent()
    found = False
    for item in items:
        if _item_key(item) == needle and "last_uninstalled_at" in item:
            item.pop("last_uninstalled_at", None)
            found = True
            break
    if not found:
        return False
    _path().parent.mkdir(parents=True, exist_ok=True)
    _path().write_text(json.dumps(items[:8], indent=2) + "\n", encoding="utf-8")
    return True
