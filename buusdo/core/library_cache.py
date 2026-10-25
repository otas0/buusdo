"""Incremental Steam library refresh cache."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from buusdo.core.discovery import DiscoveredGame, discover_steam_games
from buusdo.core.platform_detect import user_config_dir


def _cache_path() -> Path:
    return user_config_dir() / "library_cache.json"


def _fingerprint(steam_roots: list[Path]) -> dict[str, float]:
    """mtime of libraryfolders.vdf + appmanifests for change detection."""
    stamps: dict[str, float] = {}
    for root in steam_roots:
        for pattern in (
            "steamapps/libraryfolders.vdf",
            "config/libraryfolders.vdf",
            "steamapps/appmanifest_*.acf",
        ):
            for path in root.glob(pattern):
                try:
                    stamps[str(path)] = path.stat().st_mtime
                except OSError:
                    continue
            # Also libraries referenced — discovery already expands; fingerprint manifests under root only.
    return stamps


def load_cached_games(steam_roots: list[Path], *, force: bool = False) -> list[DiscoveredGame]:
    cache_file = _cache_path()
    fp = _fingerprint(steam_roots)
    if not force and cache_file.is_file():
        try:
            raw = json.loads(cache_file.read_text(encoding="utf-8"))
            if raw.get("fingerprint") == fp:
                return [_game_from_cache(item) for item in raw.get("games") or []]
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            pass

    games = discover_steam_games(steam_roots)
    payload = {
        "saved_at": time.time(),
        "fingerprint": fp,
        "games": [_game_to_cache(g) for g in games],
    }
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return games


def invalidate_cache() -> None:
    path = _cache_path()
    if path.exists():
        path.unlink()


def _game_to_cache(g: DiscoveredGame) -> dict[str, Any]:
    return {
        "name": g.name,
        "app_id": g.app_id,
        "install_path": str(g.install_path),
        "library_path": str(g.library_path),
        "executable": str(g.executable) if g.executable else None,
        "proton_prefix": str(g.proton_prefix) if g.proton_prefix else None,
    }


def _game_from_cache(item: dict[str, Any]) -> DiscoveredGame:
    return DiscoveredGame(
        name=item["name"],
        app_id=item["app_id"],
        install_path=Path(item["install_path"]),
        library_path=Path(item["library_path"]),
        executable=Path(item["executable"]) if item.get("executable") else None,
        proton_prefix=Path(item["proton_prefix"]) if item.get("proton_prefix") else None,
    )
