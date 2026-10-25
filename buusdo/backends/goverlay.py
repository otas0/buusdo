"""Linux Goverlay launcher detection (no Vulkan layer implementation)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def find_goverlay() -> Path | None:
    which = shutil.which("goverlay")
    if which:
        return Path(which)
    desktop_candidates = [
        Path("/usr/share/applications/goverlay.desktop"),
        Path("/usr/local/share/applications/goverlay.desktop"),
        Path.home() / ".local/share/applications/goverlay.desktop",
    ]
    for desk in desktop_candidates:
        if desk.is_file():
            exe = _exec_from_desktop(desk)
            if exe:
                return exe
    return None


def _exec_from_desktop(path: Path) -> Path | None:
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("Exec="):
                cmd = line.split("=", 1)[1].strip().split()[0]
                resolved = shutil.which(cmd) or cmd
                p = Path(resolved)
                return p if p.exists() else None
    except OSError:
        return None
    return None


def launch_goverlay() -> dict:
    path = find_goverlay()
    if path is None:
        return {"launched": False, "reason": "goverlay_not_found"}
    env = os.environ.copy()
    subprocess.Popen(  # noqa: S603 — intentional user-facing launcher
        [str(path)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return {"launched": True, "path": str(path)}
