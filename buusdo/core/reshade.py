"""ReShade file deployment — schedules existing ReShade kits; does not ship binaries.

Writes must run inside an active ``Transaction`` (C2). Callers must run
``anticheat_guard.check`` before invoking deploy (C1).
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path

from buusdo.core.errors import BuusdoError
from buusdo.core.graphics_detect import (
    RESHADE_PROXY_DLL,
    GraphicsApi,
    detect_graphics_api,
    is_pe64,
)
from buusdo.core.transaction import Transaction

STATE_DIR = ".buusdo"
STATE_FILE = "reshade_state.json"

_VULKAN_LAYER_NAME = "VK_LAYER_RESHADE"
_VULKAN_JSON_64 = "ReShade64.json"
_VULKAN_JSON_32 = "ReShade32.json"
_VULKAN_DLL_64 = "ReShade64.dll"
_VULKAN_DLL_32 = "ReShade32.dll"


@dataclass(frozen=True)
class ReshadeKit:
    """Local ReShade kit produced by the official installer / zip."""

    root: Path

    @property
    def dll64(self) -> Path:
        return self.root / "ReShade64.dll"

    @property
    def dll32(self) -> Path:
        return self.root / "ReShade32.dll"

    @property
    def ini(self) -> Path:
        return self.root / "ReShade.ini"

    def validate(self) -> None:
        from buusdo.core.i18n import t

        if not self.root.is_dir():
            raise BuusdoError(t("err.reshade_kit_missing", path=self.root))
        if not self.dll64.is_file() and not self.dll32.is_file():
            raise BuusdoError(t("err.reshade_kit_dlls", path=self.root))


@dataclass(frozen=True)
class ReshadeDeployPlan:
    api: GraphicsApi
    mode: str  # "proxy" | "vulkan_layer"
    proxy_dll_name: str | None
    source_dll: Path
    dest_dll: Path
    source_ini: Path | None
    dest_ini: Path | None
    vulkan_json_name: str | None
    state_path: Path


def resolve_kit(kit_path: Path | str) -> ReshadeKit:
    kit = ReshadeKit(root=Path(kit_path).expanduser())
    kit.validate()
    return kit


def _vulkan_layer_json(library_filename: str) -> str:
    payload = {
        "file_format_version": "1.0.0",
        "layer": {
            "name": _VULKAN_LAYER_NAME,
            "type": "GLOBAL",
            "library_path": library_filename,
            "api_version": "1.2.0",
            "implementation_version": "1",
            "description": "ReShade",
        },
    }
    return json.dumps(payload, indent=2) + "\n"


def plan_deploy(
    game_dir: Path,
    kit: ReshadeKit,
    *,
    executable: Path | None = None,
    api: GraphicsApi | None = None,
) -> ReshadeDeployPlan:
    resolved_api = api or detect_graphics_api(executable)
    use64 = is_pe64(executable)
    source = kit.dll64 if use64 else kit.dll32
    if not source.is_file():
        source = kit.dll64 if kit.dll64.is_file() else kit.dll32
    if not source.is_file():
        from buusdo.core.i18n import t

        raise BuusdoError(t("err.reshade_no_dll"))

    source_ini = kit.ini if kit.ini.is_file() else None
    dest_ini = game_dir / "ReShade.ini" if source_ini is not None else None
    state_path = game_dir / STATE_DIR / STATE_FILE

    if resolved_api is GraphicsApi.VULKAN:
        dll_name = _VULKAN_DLL_64 if (use64 and kit.dll64.is_file()) or not kit.dll32.is_file() else _VULKAN_DLL_32
        json_name = _VULKAN_JSON_64 if dll_name == _VULKAN_DLL_64 else _VULKAN_JSON_32
        return ReshadeDeployPlan(
            api=resolved_api,
            mode="vulkan_layer",
            proxy_dll_name=None,
            source_dll=source,
            dest_dll=game_dir / dll_name,
            source_ini=source_ini,
            dest_ini=dest_ini,
            vulkan_json_name=json_name,
            state_path=state_path,
        )

    proxy = RESHADE_PROXY_DLL.get(resolved_api) or "dxgi.dll"
    return ReshadeDeployPlan(
        api=resolved_api,
        mode="proxy",
        proxy_dll_name=proxy,
        source_dll=source,
        dest_dll=game_dir / proxy,
        source_ini=source_ini,
        dest_ini=dest_ini,
        vulkan_json_name=None,
        state_path=state_path,
    )


def _snapshot_existing(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return {
        "path": str(path),
        "existed": True,
        "data_b64": base64.b64encode(path.read_bytes()).decode("ascii"),
    }


def deploy(tx: Transaction, plan: ReshadeDeployPlan, *, target_name: str) -> dict:
    """Copy ReShade into the game directory under the given transaction."""
    backups: list[dict] = []
    dll_backup = _snapshot_existing(plan.dest_dll)
    if dll_backup:
        backups.append(dll_backup)

    tx.ensure_dir(plan.state_path.parent)
    tx.copy_file(plan.source_dll, plan.dest_dll)
    deployed: dict = {
        "dll": str(plan.dest_dll),
        "api": plan.api.value,
        "mode": plan.mode,
        "proxy": plan.proxy_dll_name,
        "created_dll": dll_backup is None,
    }

    if plan.mode == "vulkan_layer" and plan.vulkan_json_name:
        json_path = plan.dest_dll.parent / plan.vulkan_json_name
        json_backup = _snapshot_existing(json_path)
        if json_backup:
            backups.append(json_backup)
        tx.write_text(json_path, _vulkan_layer_json(plan.dest_dll.name))
        deployed["vulkan_json"] = str(json_path)
        deployed["vulkan_layer"] = _VULKAN_LAYER_NAME
        deployed["steam_launch_hint"] = (
            f"VK_LAYER_PATH=\"{plan.dest_dll.parent}\" "
            f"VK_INSTANCE_LAYERS={_VULKAN_LAYER_NAME} %command%"
        )

    if plan.dest_ini is not None and plan.source_ini is not None:
        ini_backup = _snapshot_existing(plan.dest_ini)
        if ini_backup:
            backups.append(ini_backup)
        tx.copy_file(plan.source_ini, plan.dest_ini)
        deployed["ini"] = str(plan.dest_ini)
        deployed["created_ini"] = ini_backup is None

    for folder_name in ("Shaders", "Textures", "reshade-shaders"):
        src = plan.source_dll.parent / folder_name
        if src.is_dir():
            dest = plan.dest_dll.parent / folder_name
            _copy_tree(tx, src, dest)
            deployed.setdefault("folders", []).append(str(dest))

    state = {
        "target": target_name,
        "api": plan.api.value,
        "mode": plan.mode,
        "proxy_dll": plan.proxy_dll_name,
        "deployed": deployed,
        "backups": backups,
    }
    tx.write_text(plan.state_path, json.dumps(state, indent=2) + "\n")
    return state


def uninstall(tx: Transaction, game_dir: Path) -> dict:
    """Remove ReShade artifacts and byte-restore any overwritten originals (C2)."""
    state_path = game_dir / STATE_DIR / STATE_FILE
    if not state_path.is_file():
        return {"removed": False, "reason": "no reshade state"}

    state = json.loads(state_path.read_text(encoding="utf-8"))
    deployed = state.get("deployed") or {}
    backups = {b["path"]: b for b in state.get("backups") or [] if "path" in b}
    restored: list[str] = []
    removed: list[str] = []

    def _restore_or_delete(path_str: str | None) -> None:
        if not path_str:
            return
        path = Path(path_str)
        backup = backups.get(str(path))
        if backup and backup.get("existed") and backup.get("data_b64") is not None:
            tx.write_bytes(path, base64.b64decode(backup["data_b64"]))
            restored.append(str(path))
        elif path.is_file():
            tx.delete(path)
            removed.append(str(path))

    _restore_or_delete(deployed.get("dll"))
    _restore_or_delete(deployed.get("ini"))
    _restore_or_delete(deployed.get("vulkan_json"))

    for folder in deployed.get("folders") or []:
        _delete_tree_files(tx, Path(folder))
        removed.append(folder)

    if state_path.is_file():
        tx.delete(state_path)
        removed.append(str(state_path))

    return {"removed": True, "restored": restored, "deleted": removed}


def status(game_dir: Path) -> dict:
    state_path = game_dir / STATE_DIR / STATE_FILE
    if not state_path.is_file():
        return {"installed": False}
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"installed": False, "corrupt_state": True}
    dll = Path((state.get("deployed") or {}).get("dll", ""))
    return {
        "installed": dll.is_file() if dll.parts else False,
        "state": state,
        "state_path": str(state_path),
    }


def _copy_tree(tx: Transaction, src: Path, dest: Path) -> None:
    tx.ensure_dir(dest)
    for path in src.rglob("*"):
        rel = path.relative_to(src)
        target = dest / rel
        if path.is_dir():
            tx.ensure_dir(target)
        elif path.is_file():
            tx.ensure_dir(target.parent)
            tx.copy_file(path, target)


def _delete_tree_files(tx: Transaction, root: Path) -> None:
    if not root.exists():
        return
    files = [p for p in root.rglob("*") if p.is_file()]
    files.sort(key=lambda p: len(p.parts), reverse=True)
    for path in files:
        tx.delete(path)
