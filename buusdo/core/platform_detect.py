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


def host_adapter_summary(platform: HostPlatform | None = None) -> str:
    """Best-effort, read-only one-line GPU/adapter hint (C3 branch site).

    Empty string when unknown. Never claims acceleration or 'RAM as GPU'.
    """
    host = platform if platform is not None else detect_host_platform()
    try:
        if host is HostPlatform.MACOS:
            return _macos_adapter_summary()
        if host is HostPlatform.LINUX:
            return _linux_adapter_summary()
        if host is HostPlatform.WINDOWS:
            return _windows_adapter_summary()
    except OSError:
        return ""
    return ""


def _macos_adapter_summary() -> str:
    import platform as py_platform
    import subprocess

    machine = (py_platform.machine() or "").lower()
    chips: list[str] = []
    try:
        out = subprocess.run(
            ["system_profiler", "SPDisplaysDataType", "-detailLevel", "mini"],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
        for line in (out.stdout or "").splitlines():
            s = line.strip()
            if s.startswith("Chipset Model:"):
                chips.append(s.split(":", 1)[1].strip())
    except (OSError, subprocess.TimeoutExpired):
        chips = []
    if machine in {"arm64", "aarch64"}:
        label = ", ".join(chips) if chips else "Apple Silicon"
        return f"{label} (unified memory — hardware design, not a buusdo trick)"
    if chips:
        return ", ".join(chips)
    return ""


def _linux_adapter_summary() -> str:
    drm = Path("/sys/class/drm")
    if not drm.is_dir():
        return ""
    names: list[str] = []
    for card in sorted(drm.glob("card[0-9]")):
        # Prefer vendor/device uevent; fall back to card name.
        uevent = card / "device" / "uevent"
        label = card.name
        if uevent.is_file():
            try:
                text = uevent.read_text(encoding="utf-8", errors="replace")
            except OSError:
                text = ""
            for line in text.splitlines():
                if line.startswith("DRIVER="):
                    label = f"{card.name} ({line.split('=', 1)[1]})"
                    break
        names.append(label)
        if len(names) >= 3:
            break
    if not names:
        return ""
    return "; ".join(names) + " — device pick/encode only when OS/game allows; not a general boost"


def _windows_adapter_summary() -> str:
    import subprocess

    # PowerShell CIM is widely available; keep it short and non-fatal.
    ps = (
        "Get-CimInstance Win32_VideoController | "
        "Select-Object -ExpandProperty Name"
    )
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    names = [ln.strip() for ln in (out.stdout or "").splitlines() if ln.strip()]
    if not names:
        return ""
    shown = "; ".join(names[:3])
    extra = " (+more)" if len(names) > 3 else ""
    return (
        f"{shown}{extra} — extra GPU may help displays/encode/device pick; "
        "not a universal FPS switch"
    )
