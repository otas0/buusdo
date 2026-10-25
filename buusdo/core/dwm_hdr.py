"""Phase 3 DWM SDR→HDR color fallback — interface reserved, not implemented.

available must remain False until Phase 3 ships.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from buusdo.core.errors import BuusdoError


@dataclass(frozen=True)
class DwmHdrPlan:
    target_name: str
    mode: str  # "sdr_to_hdr_shader_patch"
    notes: str = "Phase 3 only — interface reserved."


def is_available() -> bool:
    return False


def plan(target_name: str) -> DwmHdrPlan:
    return DwmHdrPlan(target_name=target_name, mode="sdr_to_hdr_shader_patch")


def install(*_args: Any, **_kwargs: Any) -> dict:
    raise BuusdoError("DWM SDR→HDR 模块为 Phase 3，当前不可用（接口已预留）。")


def uninstall(*_args: Any, **_kwargs: Any) -> dict:
    raise BuusdoError("DWM SDR→HDR 模块为 Phase 3，当前不可用（接口已预留）。")


def status(_game_dir: Path | None = None) -> dict:
    return {
        "available": False,
        "phase": 3,
        "installed": False,
        "description": "DWM SDR→HDR 着色器修补（可选模块，Phase 3）",
    }
