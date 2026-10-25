"""RTX Remix mod detection and enable/disable — manage existing mods only (C4).

Never claims \"ray tracing enabled\"; only toggles known Remix bridge files.
"""

from __future__ import annotations

import json
from pathlib import Path

from buusdo.core.errors import BuusdoError
from buusdo.core.transaction import Transaction

STATE_FILE = ".buusdo/rtx_remix_state.json"

# Heuristic markers for an already-installed Remix bridge / runtime.
_REMIX_MARKERS = (
    "d3d9.dll",  # often the Remix bridge for classic titles
    "NvRemixBridge.exe",
    "remix",
)


def detect(game_dir: Path) -> dict:
    """Return whether an RTX Remix-style mod layout appears present."""
    hits: list[str] = []
    lower_names = {p.name.lower(): p for p in game_dir.iterdir()} if game_dir.is_dir() else {}
    for name, path in lower_names.items():
        if "remix" in name:
            hits.append(str(path))
        if name in {"nvremixbridge.exe", "d3d9.dll"} and path.is_file():
            # d3d9 alone is weak; require sibling remix cue
            pass
    remix_dirs = [
        str(p)
        for p in game_dir.rglob("*")
        if p.is_dir() and "remix" in p.name.lower()
    ][:10]
    hits.extend(remix_dirs)

    bridge = game_dir / "NvRemixBridge.exe"
    d3d9 = game_dir / "d3d9.dll"
    present = bridge.is_file() or bool(remix_dirs) or any("remix" in h.lower() for h in hits)
    disabled = (game_dir / "d3d9.dll.buusdo_disabled").is_file()
    return {
        "present": present,
        "disabled": disabled,
        "bridge": str(bridge) if bridge.is_file() else None,
        "d3d9": str(d3d9) if d3d9.is_file() else None,
        "hits": hits[:20],
    }


def enable(tx: Transaction, game_dir: Path, *, target_name: str) -> dict:
    info = detect(game_dir)
    if not info["present"] and not (game_dir / "d3d9.dll.buusdo_disabled").is_file():
        raise BuusdoError(
            "未检测到已有的 RTX Remix mod。buusdo 只管理现成 mod，不重建场景。"
        )
    disabled = game_dir / "d3d9.dll.buusdo_disabled"
    active = game_dir / "d3d9.dll"
    if disabled.is_file() and not active.exists():
        data = disabled.read_bytes()
        tx.write_bytes(active, data)
        tx.delete(disabled)

    state_path = game_dir / STATE_FILE
    tx.ensure_dir(state_path.parent)
    state = {
        "target": target_name,
        "enabled": True,
        "copy": "已启用已有 RTX Remix 路径追踪 mod（未宣称「已开启光线追踪」）。",
    }
    tx.write_text(state_path, json.dumps(state, indent=2, ensure_ascii=False) + "\n")
    return state


def disable(tx: Transaction, game_dir: Path, *, target_name: str) -> dict:
    info = detect(game_dir)
    active = game_dir / "d3d9.dll"
    disabled = game_dir / "d3d9.dll.buusdo_disabled"
    if active.is_file() and info["present"]:
        tx.write_bytes(disabled, active.read_bytes())
        tx.delete(active)
    elif not info["present"] and not disabled.is_file():
        raise BuusdoError("未检测到可禁用的 RTX Remix mod。")

    state_path = game_dir / STATE_FILE
    tx.ensure_dir(state_path.parent)
    state = {
        "target": target_name,
        "enabled": False,
        "copy": "已禁用 RTX Remix 路径追踪 mod 桥接文件。",
    }
    tx.write_text(state_path, json.dumps(state, indent=2, ensure_ascii=False) + "\n")
    return state


def status(game_dir: Path) -> dict:
    info = detect(game_dir)
    state_path = game_dir / STATE_FILE
    enabled = None
    if state_path.is_file():
        try:
            enabled = json.loads(state_path.read_text(encoding="utf-8")).get("enabled")
        except (OSError, json.JSONDecodeError):
            enabled = None
    return {**info, "enabled": enabled}
