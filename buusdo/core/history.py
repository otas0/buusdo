"""Append-only operation history for installs / rollbacks."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from buusdo.core.platform_detect import user_config_dir


def _history_path() -> Path:
    return user_config_dir() / "history.jsonl"


def append_event(
    action: str,
    *,
    target: str,
    success: bool,
    message: str = "",
    details: dict[str, Any] | None = None,
    message_key: str = "",
    message_params: dict[str, Any] | None = None,
) -> None:
    """Append a history row.

    Prefer ``message_key`` (+ optional ``message_params``) so the UI can
    ``t()`` at display time. ``message`` remains as a legacy/fallback snapshot.
    """
    path = _history_path()
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "target": target,
        "success": success,
        "message": message,
        "details": details or {},
    }
    if message_key:
        event["message_key"] = message_key
        if message_params:
            event["message_params"] = dict(message_params)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        # History must never block install/uninstall paths.
        return


def list_events(limit: int = 100) -> list[dict[str, Any]]:
    path = _history_path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    events: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(events))


def clear_history() -> None:
    path = _history_path()
    if path.exists():
        path.unlink()
