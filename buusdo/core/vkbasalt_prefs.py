"""Persist last-used vkBasalt config path (validate file still exists)."""

from __future__ import annotations

from pathlib import Path

from buusdo.core.config_store import load_settings, save_settings


def get_remembered_config_path() -> str:
    raw = str(load_settings().get("vkbasalt_config_path") or "")
    if not raw:
        return ""
    path = Path(raw).expanduser()
    if path.is_file():
        return str(path)
    data = load_settings()
    if "vkbasalt_config_path" in data:
        data.pop("vkbasalt_config_path", None)
        save_settings(data)
    return ""


def set_remembered_config_path(path: str) -> None:
    expanded = str(Path(path).expanduser())
    data = load_settings()
    if not Path(expanded).is_file():
        data.pop("vkbasalt_config_path", None)
        save_settings(data)
        return
    data["vkbasalt_config_path"] = expanded
    save_settings(data)
