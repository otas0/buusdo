"""Watch a game process and roll back display settings when it exits."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

import psutil

from buusdo.core.backend import EnhancementTarget


def _exact_exe_paths(target: EnhancementTarget) -> set[Path]:
    paths: set[Path] = set()
    if target.executable:
        paths.add(Path(target.executable).expanduser())
    for raw in target.metadata.get("executables") or []:
        paths.add(Path(str(raw)).expanduser())
    resolved: set[Path] = set()
    for p in paths:
        try:
            resolved.add(p.resolve())
        except OSError:
            resolved.add(p)
    return resolved


def process_matches_target(proc: psutil.Process, target: EnhancementTarget) -> bool:
    """True only when the process exe path exactly matches a known game executable."""
    wanted = _exact_exe_paths(target)
    if not wanted:
        return False
    try:
        exe = proc.exe()
    except (psutil.Error, OSError):
        return False
    if not exe:
        return False
    try:
        current = Path(exe).resolve()
    except OSError:
        current = Path(exe)
    return current in wanted


def watch_and_rollback(
    target: EnhancementTarget,
    *,
    rollback: Callable[[], dict],
    poll_s: float = 2.0,
    on_done: Callable[[dict], None] | None = None,
) -> threading.Thread:
    """Start a daemon thread: when matching process disappears after being seen, rollback."""

    def _run() -> None:
        seen = False
        while True:
            alive = False
            try:
                for proc in psutil.process_iter(["pid"]):
                    try:
                        if process_matches_target(proc, target):
                            alive = True
                            seen = True
                            break
                    except (psutil.Error, OSError):
                        continue
            except (psutil.Error, OSError):
                pass
            if seen and not alive:
                result = rollback()
                if on_done:
                    on_done(result)
                return
            time.sleep(poll_s)

    thread = threading.Thread(target=_run, name="buusdo-display-watch", daemon=True)
    thread.start()
    return thread
