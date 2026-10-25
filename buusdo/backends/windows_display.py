"""Windows display mode / HDR apply via Win32 + CCD advanced color APIs."""

from __future__ import annotations

import ctypes
import json
import os
import re
from ctypes import wintypes
from pathlib import Path
from typing import Any

from buusdo.core.display_profile import DisplayProfile
from buusdo.core.errors import BuusdoError
from buusdo.core.platform_detect import user_config_dir

ENUM_CURRENT_SETTINGS = -1
CDS_UPDATEREGISTRY = 0x00000001
CDS_TEST = 0x00000002
DISP_CHANGE_SUCCESSFUL = 0
QDC_ONLY_ACTIVE_PATHS = 2

DISPLAYCONFIG_DEVICE_INFO_GET_ADVANCED_COLOR_INFO = 9
DISPLAYCONFIG_DEVICE_INFO_SET_ADVANCED_COLOR_STATE = 10
DISPLAYCONFIG_OUTPUT_TECHNOLOGY_OTHER = -1

DM_PELSWIDTH = 0x00080000
DM_PELSHEIGHT = 0x00100000
DM_DISPLAYFREQUENCY = 0x00400000


class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", wintypes.WCHAR * 32),
        ("dmSpecVersion", wintypes.WORD),
        ("dmDriverVersion", wintypes.WORD),
        ("dmSize", wintypes.WORD),
        ("dmDriverExtra", wintypes.WORD),
        ("dmFields", wintypes.DWORD),
        ("dmPositionX", ctypes.c_long),
        ("dmPositionY", ctypes.c_long),
        ("dmDisplayOrientation", wintypes.DWORD),
        ("dmDisplayFixedOutput", wintypes.DWORD),
        ("dmColor", wintypes.SHORT),
        ("dmDuplex", wintypes.SHORT),
        ("dmYResolution", wintypes.SHORT),
        ("dmTTOption", wintypes.SHORT),
        ("dmCollate", wintypes.SHORT),
        ("dmFormName", wintypes.WCHAR * 32),
        ("dmLogPixels", wintypes.WORD),
        ("dmBitsPerPel", wintypes.DWORD),
        ("dmPelsWidth", wintypes.DWORD),
        ("dmPelsHeight", wintypes.DWORD),
        ("dmDisplayFlags", wintypes.DWORD),
        ("dmDisplayFrequency", wintypes.DWORD),
        ("dmICMMethod", wintypes.DWORD),
        ("dmICMIntent", wintypes.DWORD),
        ("dmMediaType", wintypes.DWORD),
        ("dmDitherType", wintypes.DWORD),
        ("dmReserved1", wintypes.DWORD),
        ("dmReserved2", wintypes.DWORD),
        ("dmPanningWidth", wintypes.DWORD),
        ("dmPanningHeight", wintypes.DWORD),
    ]


class LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]


class DISPLAYCONFIG_PATH_SOURCE_INFO(ctypes.Structure):
    _fields_ = [
        ("adapterId", LUID),
        ("id", wintypes.UINT),
        ("modeInfoIdx", wintypes.UINT),
        ("statusFlags", wintypes.UINT),
    ]


class DISPLAYCONFIG_PATH_TARGET_INFO(ctypes.Structure):
    _fields_ = [
        ("adapterId", LUID),
        ("id", wintypes.UINT),
        ("modeInfoIdx", wintypes.UINT),
        ("outputTechnology", wintypes.UINT),
        ("rotation", wintypes.UINT),
        ("scaling", wintypes.UINT),
        ("refreshRate_num", wintypes.UINT),
        ("refreshRate_den", wintypes.UINT),
        ("scanLineOrdering", wintypes.UINT),
        ("targetAvailable", wintypes.BOOL),
        ("statusFlags", wintypes.UINT),
    ]


class DISPLAYCONFIG_PATH_INFO(ctypes.Structure):
    _fields_ = [
        ("sourceInfo", DISPLAYCONFIG_PATH_SOURCE_INFO),
        ("targetInfo", DISPLAYCONFIG_PATH_TARGET_INFO),
        ("flags", wintypes.UINT),
    ]


class DISPLAYCONFIG_MODE_INFO(ctypes.Structure):
    # Sized generously; we only need path target adapter/id from PATH_INFO.
    _fields_ = [("raw", ctypes.c_byte * 64)]


class DISPLAYCONFIG_DEVICE_INFO_HEADER(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.INT),
        ("size", wintypes.UINT),
        ("adapterId", LUID),
        ("id", wintypes.UINT),
    ]


class DISPLAYCONFIG_SET_ADVANCED_COLOR_STATE(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("enableAdvancedColor", wintypes.BOOL),
    ]


class DISPLAYCONFIG_GET_ADVANCED_COLOR_INFO(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("value", wintypes.UINT),
        ("colorEncoding", wintypes.UINT),
        ("bitsPerColorChannel", wintypes.UINT),
    ]


def _session_path() -> Path:
    return user_config_dir() / "display_session.json"


def capture_current_mode() -> dict[str, Any]:
    """Snapshot current primary display mode for later rollback."""
    if os.name != "nt":
        return {"platform": "non_windows"}
    user32 = ctypes.windll.user32
    mode = DEVMODEW()
    mode.dmSize = ctypes.sizeof(DEVMODEW)
    if not user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(mode)):
        raise BuusdoError("EnumDisplaySettingsW failed while capturing mode")
    snap = {
        "width": int(mode.dmPelsWidth),
        "height": int(mode.dmPelsHeight),
        "refresh_hz": int(mode.dmDisplayFrequency),
        "hdr": _query_hdr_enabled(),
    }
    path = _session_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    return snap


def rollback_display_session(*, dry_run: bool = False) -> dict[str, Any]:
    """Restore resolution/refresh/HDR from the last captured session."""
    path = _session_path()
    if not path.is_file():
        return {"restored": False, "reason": "no_session"}
    snap = json.loads(path.read_text(encoding="utf-8"))
    if os.name != "nt":
        return {"restored": False, "reason": "not_windows", "snap": snap}
    profile = DisplayProfile(
        name="rollback",
        resolution=f"{snap['width']}x{snap['height']}",
        refresh_hz=snap.get("refresh_hz"),
        hdr_preferred=bool(snap.get("hdr")),
    )
    result = apply_display_profile(profile, dry_run=dry_run, capture_before=False)
    if result.get("applied") and not dry_run:
        path.unlink(missing_ok=True)
    return {"restored": bool(result.get("applied")), "details": result, "snap": snap}


def apply_display_profile(
    profile: DisplayProfile,
    *,
    dry_run: bool = False,
    capture_before: bool = True,
) -> dict[str, Any]:
    """Apply resolution/refresh via ChangeDisplaySettingsW; HDR via SET_ADVANCED_COLOR_STATE."""
    if os.name != "nt":
        return {
            "applied": False,
            "reason": "not_windows",
            "profile": profile.to_dict(),
        }

    prior = None
    if capture_before and not dry_run:
        prior = capture_current_mode()

    result: dict[str, Any] = {
        "applied": False,
        "mode": "win32_ccd",
        "profile": profile.to_dict(),
        "steps": [],
        "prior": prior,
    }

    width = height = None
    if profile.resolution:
        m = re.match(r"^(\d+)\s*[xX×]\s*(\d+)$", profile.resolution.strip())
        if not m:
            raise BuusdoError(f"Invalid resolution: {profile.resolution}")
        width, height = int(m.group(1)), int(m.group(2))

    if width and height:
        step = _apply_mode(width, height, profile.refresh_hz, dry_run=dry_run)
        result["steps"].append(step)
        if not step.get("ok"):
            raise BuusdoError(step.get("error") or "ChangeDisplaySettings failed")

    hdr_step = _set_hdr_advanced_color(bool(profile.hdr_preferred), dry_run=dry_run)
    result["steps"].append(hdr_step)

    result["applied"] = all(s.get("ok", False) for s in result["steps"]) or (
        not width and hdr_step.get("ok")
    )
    result["note"] = (
        "已通过 Win32/CCD 应用显示偏好（含 SET_ADVANCED_COLOR_STATE）；"
        "不宣称「已开启光线追踪」。"
    )
    return result


def _apply_mode(
    width: int, height: int, refresh_hz: int | None, *, dry_run: bool
) -> dict[str, Any]:
    user32 = ctypes.windll.user32
    mode = DEVMODEW()
    mode.dmSize = ctypes.sizeof(DEVMODEW)
    if not user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(mode)):
        return {"ok": False, "action": "enum", "error": "EnumDisplaySettingsW failed"}

    mode.dmPelsWidth = width
    mode.dmPelsHeight = height
    mode.dmFields = DM_PELSWIDTH | DM_PELSHEIGHT
    if refresh_hz:
        mode.dmDisplayFrequency = int(refresh_hz)
        mode.dmFields |= DM_DISPLAYFREQUENCY

    flags = CDS_TEST if dry_run else CDS_UPDATEREGISTRY
    code = user32.ChangeDisplaySettingsW(ctypes.byref(mode), flags)
    return {
        "ok": code == DISP_CHANGE_SUCCESSFUL,
        "action": "ChangeDisplaySettingsW",
        "width": width,
        "height": height,
        "refresh_hz": refresh_hz,
        "dry_run": dry_run,
        "code": int(code),
    }


def _active_paths() -> tuple[list[DISPLAYCONFIG_PATH_INFO], int] | tuple[None, dict]:
    user32 = ctypes.windll.user32
    path_count = wintypes.UINT()
    mode_count = wintypes.UINT()
    err = user32.GetDisplayConfigBufferSizes(
        QDC_ONLY_ACTIVE_PATHS, ctypes.byref(path_count), ctypes.byref(mode_count)
    )
    if err != 0:
        return None, {"ok": False, "error": f"GetDisplayConfigBufferSizes={err}"}
    if path_count.value == 0:
        return None, {"ok": False, "error": "no_active_paths"}

    paths = (DISPLAYCONFIG_PATH_INFO * path_count.value)()
    modes = (DISPLAYCONFIG_MODE_INFO * mode_count.value)()
    flags = wintypes.UINT()
    status = user32.QueryDisplayConfig(
        QDC_ONLY_ACTIVE_PATHS,
        ctypes.byref(path_count),
        paths,
        ctypes.byref(mode_count),
        modes,
        ctypes.byref(flags),
    )
    if status != 0:
        return None, {"ok": False, "error": f"QueryDisplayConfig={status}"}
    return list(paths[: path_count.value]), 0


def _query_hdr_enabled() -> bool | None:
    if os.name != "nt":
        return None
    try:
        user32 = ctypes.windll.user32
        paths, err = _active_paths()
        if paths is None:
            return None
        path = paths[0]
        info = DISPLAYCONFIG_GET_ADVANCED_COLOR_INFO()
        info.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_ADVANCED_COLOR_INFO
        info.header.size = ctypes.sizeof(DISPLAYCONFIG_GET_ADVANCED_COLOR_INFO)
        info.header.adapterId = path.targetInfo.adapterId
        info.header.id = path.targetInfo.id
        status = user32.DisplayConfigGetDeviceInfo(ctypes.byref(info))
        if status != 0:
            return None
        # bit0 advancedColorSupported, bit1 advancedColorEnabled (approx)
        return bool(info.value & 0x2)
    except Exception:
        return None


def _set_hdr_advanced_color(enable: bool, *, dry_run: bool) -> dict[str, Any]:
    """Toggle HDR via DISPLAYCONFIG_DEVICE_INFO_SET_ADVANCED_COLOR_STATE per target."""
    try:
        user32 = ctypes.windll.user32
    except AttributeError:
        return {"ok": False, "action": "hdr", "error": "user32 missing"}

    paths, err = _active_paths()
    if paths is None:
        return {"ok": False, "action": "hdr", "enable": enable, **(err or {})}

    if dry_run:
        targets = [
            {
                "adapterLow": p.targetInfo.adapterId.LowPart,
                "adapterHigh": p.targetInfo.adapterId.HighPart,
                "id": p.targetInfo.id,
            }
            for p in paths
        ]
        return {
            "ok": True,
            "action": "hdr_dry_run",
            "enable": enable,
            "targets": targets,
        }

    results = []
    for path in paths:
        req = DISPLAYCONFIG_SET_ADVANCED_COLOR_STATE()
        req.header.type = DISPLAYCONFIG_DEVICE_INFO_SET_ADVANCED_COLOR_STATE
        req.header.size = ctypes.sizeof(DISPLAYCONFIG_SET_ADVANCED_COLOR_STATE)
        req.header.adapterId = path.targetInfo.adapterId
        req.header.id = path.targetInfo.id
        req.enableAdvancedColor = bool(enable)
        status = user32.DisplayConfigSetDeviceInfo(ctypes.byref(req))
        results.append(
            {
                "adapterLow": path.targetInfo.adapterId.LowPart,
                "adapterHigh": path.targetInfo.adapterId.HighPart,
                "id": int(path.targetInfo.id),
                "status": int(status),
                "ok": status == 0,
            }
        )

    ok = any(r["ok"] for r in results)
    return {
        "ok": ok,
        "action": "SET_ADVANCED_COLOR_STATE",
        "enable": enable,
        "targets": results,
        "note": None
        if ok
        else "DisplayConfigSetDeviceInfo failed on all targets (driver/OS may block).",
    }
