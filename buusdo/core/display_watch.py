"""Watch a game process and roll back display settings when it exits."""

from __future__ import annotations

import threading
import time
from typing import Callable

import psutil

from buusdo.core.backend import EnhancementTarget


def watch_and_rollback(
    target: EnhancementTarget,
    *,
    rollback: Callable[[], dict],
    poll_s: float = 2.0,
    on_done: Callable[[dict], None] | None = None,
) -> threading.Thread:
    """Start a daemon thread: when matching process disappears after being seen, rollback."""

    def _run() -> None:
        names = set()
        if target.executable:
            names.add(target.executable.name.lower())
            names.add(target.executable.stem.lower())
        for raw in target.metadata.get("executables") or []:
            from pathlib import Path

            p = Path(str(raw))
            names.add(p.name.lower())
            names.add(p.stem.lower())

        seen = False
        while True:
            alive = False
            try:
                for proc in psutil.process_iter(["name"]):
                    pname = (proc.info.get("name") or "").lower()
                    if any(n and n in pname for n in names):
                        alive = True
                        seen = True
                        break
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
