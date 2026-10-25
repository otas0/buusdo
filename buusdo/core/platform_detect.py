"""Host platform detection. Platform branching for backends lives only here
and in ``backends.__init__`` (C3).
"""

from __future__ import annotations

import os
import sys
from enum import Enum
from pathlib import Path


class HostPlatform(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNSUPPORTED = "unsupported"


def detect_host_platform() -> HostPlatform:
    if sys.platform == "win32":
        return HostPlatform.WINDOWS
    if sys.platform.startswith("linux"):
        return HostPlatform.LINUX
    if sys.platform == "darwin":
        return HostPlatform.MACOS
    return HostPlatform.UNSUPPORTED


def user_config_dir(platform: HostPlatform | None = None) -> Path:
    """Per-OS user config root for buusdo (allowed platform branch site)."""
    host = platform if platform is not None else detect_host_platform()
    home = Path.home()
    if host is HostPlatform.WINDOWS:
        base = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        return base / "buusdo"
    if host is HostPlatform.MACOS:
        return home / "Library" / "Application Support" / "buusdo"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "buusdo"
    return home / ".config" / "buusdo"


def steam_roots(platform: HostPlatform | None = None) -> list[Path]:
    """Candidate Steam client install roots for the host platform."""
    host = platform if platform is not None else detect_host_platform()
    home = Path.home()
    candidates: list[Path] = []

    if host is HostPlatform.WINDOWS:
        program_files = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        program_files64 = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        candidates.extend(
            [
                program_files / "Steam",
                program_files64 / "Steam",
                home / "Steam",
            ]
        )
        # Steam registry-less extra: LOCALAPPDATA is uncommon for Steam root.
    elif host is HostPlatform.LINUX:
        candidates.extend(
            [
                home / ".local" / "share" / "Steam",
                home / ".steam" / "steam",
                home / ".steam" / "root",
                home / ".var" / "app" / "com.valvesoftware.Steam" / "data" / "Steam",
                Path("/usr/share/steam"),
            ]
        )
    elif host is HostPlatform.MACOS:
        candidates.extend(
            [
                home / "Library" / "Application Support" / "Steam",
            ]
        )

    env = os.environ.get("STEAM_ROOT") or os.environ.get("STEAM_DIR")
    if env:
        candidates.insert(0, Path(env).expanduser())

    out: list[Path] = []
    seen: set[Path] = set()
    for raw in candidates:
        try:
            path = raw.expanduser().resolve()
        except OSError:
            path = raw.expanduser()
        if path in seen:
            continue
        seen.add(path)
        out.append(path)
    return out
