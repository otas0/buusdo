"""Phase 3 DWM SDR→HDR color fallback.

Default: unavailable. Prototype behind BUUSDO_ENABLE_DWM_HDR_PROTOTYPE=1
(still not claimed as shipping Phase 3).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from buusdo.core.errors import BuusdoError
from buusdo.core.transaction import Transaction

_STATE = ".buusdo/dwm_hdr_prototype.json"


@dataclass(frozen=True)
class DwmHdrPlan:
    target_name: str
    mode: str  # "sdr_to_hdr_shader_patch"
    notes: str = "Phase 3 prototype — records intent only unless explicitly enabled."


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


def install(tx: Transaction | None = None, game_dir: Path | None = None, *, target_name: str = "") -> dict:
    if not prototype_enabled():
        from buusdo.core.i18n import t

        raise BuusdoError(t("err.dwm_phase3"))
    if game_dir is None:
        raise BuusdoError("dwm_hdr.prototype requires game_dir")
    own_tx = tx is None
    tx = tx or Transaction()
    state_path = game_dir / _STATE
    payload = {
        "target": target_name,
        "mode": "sdr_to_hdr_shader_patch",
        "prototype": True,
        "copy": "原型：仅记录 SDR→HDR 色彩兜底意图，未修补 DWM 着色器。",
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
        from buusdo.core.i18n import t

        raise BuusdoError(t("err.dwm_phase3"))
    if game_dir is None:
        return {"removed": False}
    state_path = game_dir / _STATE
    own_tx = tx is None
    tx = tx or Transaction()

    def _rm(active: Transaction) -> dict:
        if state_path.is_file():
            active.delete(state_path)
            return {"removed": True}
        return {"removed": False}

    if own_tx:
        with tx:
            return _rm(tx)
    return _rm(tx)


def status(_game_dir: Path | None = None) -> dict:
    installed = bool(_game_dir and (_game_dir / _STATE).is_file())
    return {
        "available": is_available(),
        "prototype_enabled": prototype_enabled(),
        "phase": 3,
        "installed": installed,
        "description": "DWM SDR→HDR 着色器修补（可选模块，Phase 3；原型默认关闭）",
    }
