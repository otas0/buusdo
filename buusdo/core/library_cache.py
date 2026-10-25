"""Incremental Steam library refresh cache."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from buusdo.core.discovery import CancelCb, DiscoveredGame, DiscoveryCancelled, discover_steam_games
from buusdo.core.platform_detect import user_config_dir
from buusdo.core.vdf import parse_vdf


ProgressCb = Callable[[str, float], None]
# progress(stage, value) — stage may be resume|discover|cache_hit|...; value 0..1


def _cache_path() -> Path:
    return user_config_dir() / "library_cache.json"


def _library_paths_from_vdf(vdf_path: Path) -> list[Path]:
    try:
        data = parse_vdf(vdf_path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return []
    folders = data.get("libraryfolders") or data.get("LibraryFolders") or {}
    if not isinstance(folders, dict):
        return []
    out: list[Path] = []
    for key, value in folders.items():
        if str(key).lower() in {"contentstatsid", "time_next_stats_report"}:
            continue
        raw = None
        if isinstance(value, dict):
            raw = value.get("path") or value.get("Path")
        elif isinstance(value, str) and value.strip() and not value.isdigit():
            raw = value
        if isinstance(raw, str) and raw.strip():
            out.append(Path(raw.strip()))
    return out


def _fingerprint(steam_roots: list[Path]) -> dict[str, float]:
    """mtime of libraryfolders.vdf + appmanifests across all library paths."""
    stamps: dict[str, float] = {}
    libraries: list[Path] = []

    for root in steam_roots:
        for rel in ("steamapps/libraryfolders.vdf", "config/libraryfolders.vdf"):
            vdf = root / rel
            if vdf.is_file():
                try:
                    stamps[str(vdf.resolve())] = vdf.stat().st_mtime
                except OSError:
                    stamps[str(vdf)] = vdf.stat().st_mtime
                libraries.extend(_library_paths_from_vdf(vdf))
        if (root / "steamapps").is_dir():
            libraries.append(root)

    seen: set[Path] = set()
    for lib in libraries:
        try:
            resolved = lib.expanduser().resolve()
        except OSError:
            resolved = lib.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        steamapps = resolved / "steamapps"
        if not steamapps.is_dir():
            continue
        try:
            stamps[str(steamapps)] = steamapps.stat().st_mtime
        except OSError:
            pass
        for manifest in steamapps.glob("appmanifest_*.acf"):
            try:
                stamps[str(manifest)] = manifest.stat().st_mtime
            except OSError:
                continue
    return stamps


def _write_cache(
    *,
    fingerprint: dict[str, float],
    games: list[DiscoveredGame],
    partial: bool = False,
    scanned_manifests: dict[str, float] | None = None,
) -> None:
    cache_file = _cache_path()
    payload: dict[str, Any] = {
        "saved_at": time.time(),
        "fingerprint": fingerprint,
        "games": [_game_to_cache(g) for g in games],
        "partial": partial,
    }
    if scanned_manifests is not None:
        payload["scanned_manifests"] = scanned_manifests
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_cached_games(
    steam_roots: list[Path],
    *,
    force: bool = False,
    progress: ProgressCb | None = None,
    should_cancel: CancelCb | None = None,
) -> list[DiscoveredGame]:
    cache_file = _cache_path()
    if should_cancel and should_cancel():
        raise DiscoveryCancelled("scan cancelled")
    if progress:
        progress("fingerprint", 0.1)
    fp = _fingerprint(steam_roots)
    if should_cancel and should_cancel():
        raise DiscoveryCancelled("scan cancelled")

    prior_games: list[DiscoveredGame] = []
    prior_scanned: dict[str, float] = {}
    if not force and cache_file.is_file():
        try:
            raw = json.loads(cache_file.read_text(encoding="utf-8"))
            if raw.get("fingerprint") == fp and not raw.get("partial"):
                if progress:
                    progress("cache_hit", 1.0)
                return [_game_from_cache(item) for item in raw.get("games") or []]
            # Resume from cancelled partial scan when fingerprint still matches.
            if raw.get("partial") and raw.get("fingerprint") == fp:
                prior_games = [_game_from_cache(item) for item in raw.get("games") or []]
                prior_scanned = dict(raw.get("scanned_manifests") or {})
                if progress:
                    total = max(1, len([k for k in fp if "appmanifest_" in str(k)]))
                    scanned_n = len(prior_scanned)
                    progress(
                        f"resume:{scanned_n}/{total}",
                        min(0.35, 0.1 + 0.25 * (scanned_n / total)),
                    )
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            pass

    if progress:
        progress("discover", 0.4)
    try:
        games = discover_steam_games(
            steam_roots,
            should_cancel=should_cancel,
            prior_games=prior_games or None,
            prior_scanned=prior_scanned or None,
        )
    except DiscoveryCancelled as exc:
        # Keep partial fingerprint so the next scan resumes instead of full rescan.
        _write_cache(
            fingerprint=fp,
            games=exc.games,
            partial=True,
            scanned_manifests=exc.scanned_manifests,
        )
        raise

    if should_cancel and should_cancel():
        raise DiscoveryCancelled(
            "scan cancelled",
            games=games,
            scanned_manifests=prior_scanned,
        )
    if progress:
        progress("write_cache", 0.85)
    _write_cache(fingerprint=fp, games=games, partial=False, scanned_manifests=None)
    if progress:
        progress("done", 1.0)
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
