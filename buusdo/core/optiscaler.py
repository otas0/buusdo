"""OptiScaler / neural upscaling addon scheduling (decoupled from ReShade base).

Honest copy: this schedules neural image enhancement, not path tracing.
"""

from __future__ import annotations

import json
from pathlib import Path

from buusdo.core.errors import BuusdoError
from buusdo.core.transaction import Transaction

STATE_FILE = ".buusdo/optiscaler_state.json"

# Common OptiScaler / DLSS-substitute filenames users place in a kit folder.
_KIT_MARKERS = (
    "OptiScaler.dll",
    "optiscaler.dll",
    "nvngx.dll",
    "libxess.dll",
)


def resolve_kit(kit_path: Path | str) -> Path:
    from buusdo.core.i18n import t

    root = Path(kit_path).expanduser()
    if not root.is_dir():
        raise BuusdoError(t("err.optiscaler_kit_missing", path=root))
    if not any((root / name).is_file() for name in _KIT_MARKERS):
        raise BuusdoError(
            t("err.optiscaler_kit_dlls", path=root, markers=", ".join(_KIT_MARKERS))
        )
    return root


def deploy(tx: Transaction, game_dir: Path, kit: Path, *, target_name: str) -> dict:
    """Copy OptiScaler kit files next to the game; independent of ReShade state."""
    deployed: list[str] = []
    for src in kit.iterdir():
        if not src.is_file():
            continue
        if src.suffix.lower() not in {".dll", ".ini", ".json", ".txt"}:
            continue
        dest = game_dir / src.name
        tx.copy_file(src, dest)
        deployed.append(str(dest))

    state_path = game_dir / STATE_FILE
    tx.ensure_dir(state_path.parent)
    state = {
        "target": target_name,
        "kind": "neural_upscaling",
        "label": "神经画质增强（OptiScaler / DLSS 附加组件调度）",
        "deployed": deployed,
        "note": "与路径追踪（RTX Remix）是不同能力；此处不宣称已开启光线追踪。",
    }
    tx.write_text(state_path, json.dumps(state, indent=2, ensure_ascii=False) + "\n")
    return state


def uninstall(tx: Transaction, game_dir: Path) -> dict:
    state_path = game_dir / STATE_FILE
    if not state_path.is_file():
        return {"removed": False}
    state = json.loads(state_path.read_text(encoding="utf-8"))
    removed: list[str] = []
    for path_str in state.get("deployed") or []:
        path = Path(path_str)
        if path.is_file():
            tx.delete(path)
            removed.append(path_str)
    tx.delete(state_path)
    return {"removed": True, "deleted": removed}


def status(game_dir: Path) -> dict:
    state_path = game_dir / STATE_FILE
    if not state_path.is_file():
        return {"installed": False}
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"installed": False, "corrupt_state": True}
    return {"installed": True, "state": state}
