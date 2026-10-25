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
        if not self.root.is_dir():
            raise BuusdoError(f"ReShade kit not found: {self.root}")
        if not self.dll64.is_file() and not self.dll32.is_file():
            raise BuusdoError(
                f"ReShade kit missing ReShade64.dll / ReShade32.dll under {self.root}"
            )


@dataclass(frozen=True)
class ReshadeDeployPlan:
    api: GraphicsApi
    proxy_dll_name: str
    source_dll: Path
    dest_dll: Path
    source_ini: Path | None
    dest_ini: Path | None
    state_path: Path


def resolve_kit(kit_path: Path | str) -> ReshadeKit:
    kit = ReshadeKit(root=Path(kit_path).expanduser())
    kit.validate()
    return kit


def plan_deploy(
    game_dir: Path,
    kit: ReshadeKit,
    *,
    executable: Path | None = None,
    api: GraphicsApi | None = None,
) -> ReshadeDeployPlan:
    resolved_api = api or detect_graphics_api(executable)
    proxy = RESHADE_PROXY_DLL.get(resolved_api)
    if proxy is None:
        raise BuusdoError(
            "Vulkan ReShade uses an explicit layer, not a proxy DLL; "
            "Vulkan deploy is not implemented in this phase."
        )

    use64 = is_pe64(executable)
    source = kit.dll64 if use64 else kit.dll32
    if not source.is_file():
        source = kit.dll64 if kit.dll64.is_file() else kit.dll32
    if not source.is_file():
        raise BuusdoError("No usable ReShade DLL in kit")

    dest_dll = game_dir / proxy
    source_ini = kit.ini if kit.ini.is_file() else None
    dest_ini = game_dir / "ReShade.ini" if source_ini is not None else None
    state_path = game_dir / STATE_DIR / STATE_FILE
    return ReshadeDeployPlan(
        api=resolved_api,
        proxy_dll_name=proxy,
        source_dll=source,
        dest_dll=dest_dll,
        source_ini=source_ini,
        dest_ini=dest_ini,
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
        "proxy": plan.proxy_dll_name,
        "created_dll": dll_backup is None,
    }

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

    dll = deployed.get("dll")
    if dll:
        path = Path(dll)
        backup = backups.get(str(path))
        if backup and backup.get("existed") and backup.get("data_b64") is not None:
            tx.write_bytes(path, base64.b64decode(backup["data_b64"]))
            restored.append(str(path))
        elif path.is_file():
            tx.delete(path)
            removed.append(str(path))

    ini = deployed.get("ini")
    if ini:
        path = Path(ini)
        backup = backups.get(str(path))
        if backup and backup.get("existed") and backup.get("data_b64") is not None:
            tx.write_bytes(path, base64.b64decode(backup["data_b64"]))
            restored.append(str(path))
        elif path.is_file():
            tx.delete(path)
            removed.append(str(path))

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
