"""Track recently touched games for tray shortcuts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from buusdo.core.platform_detect import user_config_dir


def _path() -> Path:
    return user_config_dir() / "recent_games.json"


def push_recent(game: dict[str, Any], *, limit: int = 8) -> None:
    items = list_recent()
    key = _item_key(game)
    items = [i for i in items if _item_key(i) != key]
    items.insert(0, game)
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


def _item_key(game: dict[str, Any]) -> str:
    return str(game.get("app_id") or game.get("install_path") or game.get("name"))


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
