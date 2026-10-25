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
