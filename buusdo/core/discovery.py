"""Steam library discovery — platform-agnostic given root paths (C3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from buusdo.core.backend import EnhancementTarget
from buusdo.core.errors import BuusdoError
from buusdo.core.vdf import parse_vdf

CancelCb = Callable[[], bool]


class DiscoveryCancelled(BuusdoError):
    """Raised when a caller aborts discover_steam_games mid-scan."""


@dataclass(frozen=True)
class DiscoveredGame:
    name: str
    app_id: str
    install_path: Path
    library_path: Path
    executable: Path | None = None
    proton_prefix: Path | None = None
    launch_options: dict[str, Any] = field(default_factory=dict)

    def to_target(self) -> EnhancementTarget:
        candidates = list_executable_candidates(self.install_path)
        meta: dict[str, Any] = {
            "source": "steam",
            "app_id": self.app_id,
            "library_path": str(self.library_path),
            "executables": [str(p) for p in candidates],
        }
        if self.proton_prefix is not None:
            meta["proton_prefix"] = str(self.proton_prefix)
            meta["runtime"] = "proton"
        return EnhancementTarget(
            name=self.name,
            install_path=self.install_path,
            executable=self.executable or (candidates[0] if candidates else None),
            metadata=meta,
        )


def discover_steam_games(
    steam_roots: list[Path],
    *,
    should_cancel: CancelCb | None = None,
) -> list[DiscoveredGame]:
    """Scan Steam library folders under the given client roots."""
    games: list[DiscoveredGame] = []
    seen: set[str] = set()
    for root in steam_roots:
        if should_cancel and should_cancel():
            raise DiscoveryCancelled("scan cancelled")
        if not root.exists():
            continue
        for library in _library_paths(root):
            if should_cancel and should_cancel():
                raise DiscoveryCancelled("scan cancelled")
            steamapps = library / "steamapps"
            if not steamapps.is_dir():
                continue
            for manifest in sorted(steamapps.glob("appmanifest_*.acf")):
                if should_cancel and should_cancel():
                    raise DiscoveryCancelled("scan cancelled")
                game = _game_from_manifest(manifest, library)
                if game is None:
                    continue
                key = game.app_id
                if key in seen:
                    continue
                seen.add(key)
                games.append(game)
    games.sort(key=lambda g: g.name.lower())
    return games


def _library_paths(steam_root: Path) -> list[Path]:
    paths: list[Path] = []
    # Default library is the client root itself.
    if (steam_root / "steamapps").is_dir():
        paths.append(steam_root)

    vdf_path = steam_root / "steamapps" / "libraryfolders.vdf"
    if not vdf_path.exists():
        # Older layout
        alt = steam_root / "config" / "libraryfolders.vdf"
        vdf_path = alt if alt.exists() else vdf_path

    if not vdf_path.exists():
        return _unique_existing(paths)

    try:
        data = parse_vdf(vdf_path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return _unique_existing(paths)

    folders = data.get("libraryfolders") or data.get("LibraryFolders") or {}
    if not isinstance(folders, dict):
        return _unique_existing(paths)

    for key, value in folders.items():
        if key.lower() in {"contentstatsid", "time_next_stats_report"}:
            continue
        lib_path: Path | None = None
        if isinstance(value, dict):
            raw = value.get("path") or value.get("Path")
            if isinstance(raw, str) and raw.strip():
                lib_path = Path(raw.strip())
        elif isinstance(value, str) and value.strip() and not value.isdigit():
            # Very old format: "1" "D:\\SteamLibrary"
            lib_path = Path(value.strip())
        if lib_path is not None:
            paths.append(lib_path)

    return _unique_existing(paths)


def _unique_existing(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for p in paths:
        try:
            resolved = p.expanduser().resolve()
        except OSError:
            resolved = p.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            out.append(resolved)
    return out


def _game_from_manifest(manifest: Path, library: Path) -> DiscoveredGame | None:
    try:
        data = parse_vdf(manifest.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return None
    state = data.get("AppState") or data.get("appstate") or {}
    if not isinstance(state, dict):
        return None
    app_id = str(state.get("appid") or state.get("appID") or "").strip()
    name = str(state.get("name") or "").strip()
    installdir = str(state.get("installdir") or "").strip()
    if not app_id or not name or not installdir:
        return None

    install_path = library / "steamapps" / "common" / installdir
    if not install_path.exists():
        return None

    proton_prefix = library / "steamapps" / "compatdata" / app_id / "pfx"
    proton = proton_prefix if proton_prefix.is_dir() else None
    executable = _guess_executable(install_path)

    return DiscoveredGame(
        name=name,
        app_id=app_id,
        install_path=install_path,
        library_path=library,
        executable=executable,
        proton_prefix=proton,
    )


def list_executable_candidates(install_path: Path) -> list[Path]:
    """Shallow scan for likely game binaries (multi-EXE support)."""
    suffixes = {".exe", ".x86_64", ".bin"}
    skip_parts = ("crash", "redistributable", "easyanticheat", "battleye", "uninstall")
    exes: list[Path] = []

    def consider(path: Path) -> None:
        if not path.is_file() or path.suffix.lower() not in suffixes:
            return
        lower = str(path).lower()
        if any(s in lower for s in skip_parts):
            return
        exes.append(path)

    try:
        for child in install_path.iterdir():
            consider(child)
            if child.is_dir() and child.name.lower() not in {"_commonredist", "redist", "support"}:
                try:
                    for nested in child.iterdir():
                        consider(nested)
                except OSError:
                    continue
    except OSError:
        return []

    folder = install_path.name.lower().replace(" ", "")

    def score(p: Path) -> tuple[int, int, str]:
        depth = len(p.relative_to(install_path).parts)
        stem = p.stem.lower().replace(" ", "")
        name_hit = 0 if folder and folder[:4] in stem else 1
        return (name_hit, depth, p.name.lower())

    exes.sort(key=score)
    return exes


def _guess_executable(install_path: Path) -> Path | None:
    candidates = list_executable_candidates(install_path)
    return candidates[0] if candidates else None
