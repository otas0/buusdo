"""Phase 3 DWM SDR→HDR color fallback.

Default: unavailable. Prototype behind BUUSDO_ENABLE_DWM_HDR_PROTOTYPE=1
(still not claimed as shipping Phase 3).

On branch phase3/dwm-hdr this module can materialize an HLSL PoC sidecar.
It never patches live DWM shaders.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from buusdo.core.errors import BuusdoError
from buusdo.core.transaction import Transaction

_STATE = ".buusdo/dwm_hdr_prototype.json"
_POC_DIR = ".buusdo/dwm_hdr_poc"
_SHADER_NAME = "sdr_to_hdr_tonemap.hlsl"


@dataclass(frozen=True)
class DwmHdrPlan:
    target_name: str
    mode: str  # "sdr_to_hdr_shader_patch"
    notes: str = "Phase 3 prototype — HLSL PoC sidecar only; no live DWM patch."


def prototype_enabled() -> bool:
    return os.environ.get("BUUSDO_ENABLE_DWM_HDR_PROTOTYPE", "0") in {
        "1",
        "true",
        "TRUE",
        "yes",
    }


def is_available() -> bool:
    # Product capability stays False by default (Phase 3). Prototype can run when flagged.
    return False


def plan(target_name: str) -> DwmHdrPlan:
    return DwmHdrPlan(target_name=target_name, mode="sdr_to_hdr_shader_patch")


def _shader_source() -> str:
    try:
        root = resources.files("buusdo.core.dwm_hdr_shaders")
        return (root / _SHADER_NAME).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, TypeError):
        fallback = Path(__file__).parent / "dwm_hdr_shaders" / _SHADER_NAME
        return fallback.read_text(encoding="utf-8")


def materialize_shader_poc(game_dir: Path, *, target_name: str = "") -> dict[str, Any]:
    """Write HLSL PoC + manifest under game_dir/.buusdo/dwm_hdr_poc/ (no DWM touch)."""
    poc_root = Path(game_dir) / _POC_DIR
    poc_root.mkdir(parents=True, exist_ok=True)
    shader_path = poc_root / _SHADER_NAME
    shader_path.write_text(_shader_source(), encoding="utf-8")
    manifest = {
        "target": target_name,
        "mode": "sdr_to_hdr_shader_patch",
        "prototype": True,
        "live_dwm_patch": False,
        "shader": str(shader_path),
        "copy": "PoC：已写出 SDR→HDR 色调映射 HLSL 旁路文件；未修补 DWM。",
    }
    (poc_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def install(tx: Transaction | None = None, game_dir: Path | None = None, *, target_name: str = "") -> dict:
    if not prototype_enabled():
        raise BuusdoError("DWM SDR→HDR 模块为 Phase 3，当前不可用（接口已预留）。")
    if game_dir is None:
        raise BuusdoError("dwm_hdr.prototype requires game_dir")
    own_tx = tx is None
    tx = tx or Transaction()
    state_path = game_dir / _STATE
    poc = materialize_shader_poc(game_dir, target_name=target_name)
    payload = {
        "target": target_name,
        "mode": "sdr_to_hdr_shader_patch",
        "prototype": True,
        "live_dwm_patch": False,
        "shader_poc": poc,
        "copy": poc["copy"],
    }

    def _write(active: Transaction) -> dict:
        active.ensure_dir(state_path.parent)
        active.write_text(state_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        return payload

    if own_tx:
        with tx:
            return _write(tx)
    return _write(tx)


def uninstall(tx: Transaction | None = None, game_dir: Path | None = None) -> dict:
    if not prototype_enabled():
        raise BuusdoError("DWM SDR→HDR 模块为 Phase 3，当前不可用（接口已预留）。")
    if game_dir is None:
        return {"removed": False}
    state_path = game_dir / _STATE
    poc_root = game_dir / _POC_DIR
    own_tx = tx is None
    tx = tx or Transaction()

    def _rm(active: Transaction) -> dict:
        removed_state = False
        if state_path.is_file():
            active.delete(state_path)
            removed_state = True
        removed_poc = False
        if poc_root.is_dir():
            shutil.rmtree(poc_root, ignore_errors=True)
            removed_poc = True
        return {"removed": removed_state or removed_poc, "state": removed_state, "poc": removed_poc}

    if own_tx:
        with tx:
            return _rm(tx)
    return _rm(tx)


def status(_game_dir: Path | None = None) -> dict:
    installed = bool(_game_dir and (_game_dir / _STATE).is_file())
    poc = bool(_game_dir and (_game_dir / _POC_DIR / _SHADER_NAME).is_file())
    return {
        "available": is_available(),
        "prototype_enabled": prototype_enabled(),
        "phase": 3,
        "installed": installed,
        "shader_poc": poc,
        "live_dwm_patch": False,
        "description": "DWM SDR→HDR 着色器修补 PoC（phase3 分支；默认不合并 main；不触碰 live DWM）",
    }
