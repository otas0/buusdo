"""Per-game JSON persistence in the user config directory."""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

from buusdo.core.platform_detect import user_config_dir
from buusdo.core.schema import ensure_schema, stamp_new

_APP_SETTINGS = "settings.json"


def game_config_path(game_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in game_id)
    return user_config_dir() / "games" / f"{safe}.json"


def load_game_config(game_id: str) -> dict[str, Any]:
    path = game_config_path(game_id)
    if not path.exists():
        return stamp_new()
    data = json.loads(path.read_text(encoding="utf-8"))
    migrated = ensure_schema(data)
    if migrated != data:
        save_game_config(game_id, migrated)
    return migrated


def save_game_config(game_id: str, data: dict[str, Any]) -> Path:
    path = game_config_path(game_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = stamp_new(ensure_schema(dict(data)))
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def update_game_config(game_id: str, **fields: Any) -> dict[str, Any]:
    data = load_game_config(game_id)
    # Prefer nested prefs for known keys (schema v2)
    pref_keys = {"executable", "graphics_api", "steam_id3", "display_profile"}
    prefs = dict(data.get("prefs") or {})
    for key, value in fields.items():
        if key in pref_keys:
            prefs[key] = value
        else:
            data[key] = value
    if prefs:
        data["prefs"] = prefs
    save_game_config(game_id, data)
    return data


def get_game_pref(game_id: str, key: str, default: Any = None) -> Any:
    data = load_game_config(game_id)
    prefs = data.get("prefs") or {}
    if key in prefs:
        return prefs[key]
    return data.get(key, default)


def load_settings() -> dict[str, Any]:
    path = user_config_dir() / _APP_SETTINGS
    if not path.exists():
        return stamp_new()
    data = json.loads(path.read_text(encoding="utf-8"))
    migrated = ensure_schema(data)
    if migrated != data:
        save_settings(migrated)
    return migrated


def save_settings(data: dict[str, Any]) -> Path:
    path = user_config_dir() / _APP_SETTINGS
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = stamp_new(ensure_schema(dict(data)))
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def get_reshade_kit_path() -> Path | None:
    raw = load_settings().get("reshade_kit_path")
    if not raw:
        return None
    return Path(str(raw)).expanduser()


def set_reshade_kit_path(path: Path | str) -> None:
    data = load_settings()
    data["reshade_kit_path"] = str(Path(path).expanduser())
    save_settings(data)


def get_optiscaler_kit_path() -> Path | None:
    raw = load_settings().get("optiscaler_kit_path")
    if not raw:
        return None
    return Path(str(raw)).expanduser()


def set_optiscaler_kit_path(path: Path | str) -> None:
    data = load_settings()
    data["optiscaler_kit_path"] = str(Path(path).expanduser())
    save_settings(data)


def export_configs(dest_zip: Path | str) -> Path:
    """Export settings + per-game JSON into a zip archive."""
    dest = Path(dest_zip).expanduser()
    dest.parent.mkdir(parents=True, exist_ok=True)
    root = user_config_dir()
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        settings = root / _APP_SETTINGS
        if settings.is_file():
            zf.write(settings, arcname=_APP_SETTINGS)
        games = root / "games"
        if games.is_dir():
            for path in games.glob("*.json"):
                zf.write(path, arcname=f"games/{path.name}")
    return dest


def import_configs(src_zip: Path | str, *, merge: bool = True) -> dict[str, Any]:
    """Import configs from a zip. merge=True keeps existing keys not in the archive."""
    src = Path(src_zip).expanduser()
    if not src.is_file():
        raise FileNotFoundError(src)
    root = user_config_dir()
    root.mkdir(parents=True, exist_ok=True)
    imported: list[str] = []
    with zipfile.ZipFile(src, "r") as zf:
        for info in zf.infolist():
            name = info.filename
            if name.endswith("/"):
                continue
            if name != _APP_SETTINGS and not name.startswith("games/"):
                continue
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if merge and name == _APP_SETTINGS and target.is_file():
                existing = json.loads(target.read_text(encoding="utf-8"))
                incoming = json.loads(zf.read(info).decode("utf-8"))
                existing.update(incoming)
                target.write_text(
                    json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
            else:
                with zf.open(info) as src_fh, target.open("wb") as dst_fh:
                    shutil.copyfileobj(src_fh, dst_fh)
            imported.append(name)
    return {"imported": imported, "root": str(root)}
