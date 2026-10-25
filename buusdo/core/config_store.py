"""Per-game JSON persistence in the user config directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from buusdo.core.platform_detect import user_config_dir


def game_config_path(game_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in game_id)
    return user_config_dir() / "games" / f"{safe}.json"


def load_game_config(game_id: str) -> dict[str, Any]:
    path = game_config_path(game_id)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_game_config(game_id: str, data: dict[str, Any]) -> Path:
    path = game_config_path(game_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
