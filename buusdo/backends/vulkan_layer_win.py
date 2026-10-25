"""Windows-only Vulkan explicit layer path / registry writeback (C2 via Transaction)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from buusdo.core.errors import BuusdoError
from buusdo.core.transaction import Transaction

_STATE = ".buusdo/vulkan_layer_win.json"


def write_vk_layer_path_env_file(
    tx: Transaction,
    game_dir: Path,
    layer_dir: Path,
    layer_name: str,
) -> dict:
    """Persist a per-game env snippet for VK_LAYER_PATH / VK_INSTANCE_LAYERS.

    Full HKCU Vulkan ExplicitLayers registry write is optional and best-effort.
    """
    state_path = game_dir / _STATE
    env_snippet = (
        f"set VK_LAYER_PATH={layer_dir}\n"
        f"set VK_INSTANCE_LAYERS={layer_name}\n"
    )
    bat = game_dir / ".buusdo" / "enable_reshade_vulkan.bat"
    tx.ensure_dir(bat.parent)
    tx.write_text(bat, env_snippet + "rem Launch the game after setting these, or use Steam launch options.\n")

    registry_result = _try_registry_explicit_layer(tx, layer_dir, layer_name)

    state = {
        "layer_dir": str(layer_dir),
        "layer_name": layer_name,
        "bat": str(bat),
        "registry": registry_result,
        "steam_launch_hint": (
            f'VK_LAYER_PATH="{layer_dir}" VK_INSTANCE_LAYERS={layer_name} %command%'
        ),
    }
    tx.write_text(state_path, json.dumps(state, indent=2) + "\n")
    return state


def remove_vk_layer_writeback(tx: Transaction, game_dir: Path) -> dict:
    state_path = game_dir / _STATE
    removed: list[str] = []
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = {}
        bat = state.get("bat")
        if bat and Path(bat).is_file():
            tx.delete(Path(bat))
            removed.append(bat)
        reg = state.get("registry") or {}
        if reg.get("written") and reg.get("value_name"):
            _try_registry_delete(reg["value_name"])
        tx.delete(state_path)
        removed.append(str(state_path))
    return {"removed": removed}


def _try_registry_explicit_layer(tx: Transaction, layer_dir: Path, layer_name: str) -> dict:
    """Best-effort HKCU ExplicitLayers pointer. No-op off Windows."""
    _ = tx  # registry ops are recorded in state for uninstall; not file-backed
    if os.name != "nt":
        return {"written": False, "reason": "not_windows"}
    try:
        import winreg  # type: ignore
    except ImportError:
        return {"written": False, "reason": "winreg_missing"}

    # Point to the layer JSON if present
    json_candidates = list(layer_dir.glob("ReShade*.json"))
    if not json_candidates:
        return {"written": False, "reason": "no_layer_json"}
    json_path = str(json_candidates[0])
    value_name = f"buusdo_{layer_name}"
    try:
        key_path = r"Software\Khronos\Vulkan\ExplicitLayers"
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, 0)
        # Khronos also uses path as value name with DWORD 0 in some layouts.
        winreg.SetValueEx(key, json_path, 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
    except OSError as exc:
        raise BuusdoError(f"Vulkan registry write failed: {exc}") from exc
    return {"written": True, "value_name": value_name, "json_path": json_path}


def _try_registry_delete(value_name: str) -> None:
    if os.name != "nt":
        return
    try:
        import winreg  # type: ignore

        key_path = r"Software\Khronos\Vulkan\ExplicitLayers"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, value_name)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
    except OSError:
        return
