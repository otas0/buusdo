"""Windows display mode / HDR apply via Win32 + CCD advanced color APIs."""

from __future__ import annotations

import ctypes
import json
import os
import re
import time
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


SESSION_MAX_AGE_S = 12 * 3600
SESSION_WARN_AGE_S = 10 * 3600  # UI tip before hard expiry
_SESSION_REQUIRED = ("captured_at", "displays")


def _session_path() -> Path:
    return user_config_dir() / "display_session.json"


def clear_display_session() -> None:
    path = _session_path()
    path.unlink(missing_ok=True)


def heal_display_session() -> dict[str, Any]:
    """Drop corrupt or expired display_session.json. Returns heal status."""
    path = _session_path()
    if not path.is_file():
        return {"ok": True, "action": "absent"}
    try:
        snap = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        clear_display_session()
        return {"ok": True, "action": "deleted_corrupt"}
    if not isinstance(snap, dict):
        clear_display_session()
        return {"ok": True, "action": "deleted_invalid_type"}
    # Migrate legacy single-monitor sessions.
    if "displays" not in snap and "width" in snap and "height" in snap:
        snap["displays"] = [
            {
                "device": None,
                "width": snap["width"],
                "height": snap["height"],
                "refresh_hz": snap.get("refresh_hz"),
                "primary": True,
            }
        ]
    for key in _SESSION_REQUIRED:
        if key not in snap:
            clear_display_session()
            return {"ok": True, "action": "deleted_missing_fields", "missing": key}
    try:
        age = time.time() - float(snap["captured_at"])
    except (TypeError, ValueError):
        clear_display_session()
        return {"ok": True, "action": "deleted_bad_timestamp"}
    if age > SESSION_MAX_AGE_S or age < 0:
        clear_display_session()
        return {"ok": True, "action": "deleted_expired", "age_s": age}
    warn = age >= SESSION_WARN_AGE_S
    return {
        "ok": True,
        "action": "kept",
        "age_s": age,
        "snap": snap,
        "warn_expiring": warn,
        "ttl_remaining_s": max(0, SESSION_MAX_AGE_S - age),
    }


def display_session_status() -> dict[str, Any]:
    """UI helper: residual / expiring session without deleting yet."""
    path = _session_path()
    if not path.is_file():
        return {"present": False}
    status = heal_display_session()
    if status.get("action") != "kept":
        return {"present": False, "healed": status}
    return {
        "present": True,
        "warn_expiring": bool(status.get("warn_expiring")),
        "age_s": status.get("age_s"),
        "ttl_remaining_s": status.get("ttl_remaining_s"),
        "displays": len((status.get("snap") or {}).get("displays") or []),
    }


def load_display_session() -> dict[str, Any] | None:
    """Return a valid session snap, or None after self-heal."""
    status = heal_display_session()
    if status.get("action") != "kept":
        return None
    snap = status.get("snap")
    return snap if isinstance(snap, dict) else None


def list_display_modes() -> list[dict[str, Any]]:
    """Per-attached-monitor resolution/refresh via EnumDisplayDevices + EnumDisplaySettings."""
    if os.name != "nt":
        return []
    user32 = ctypes.windll.user32

    class DISPLAY_DEVICEW(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("DeviceName", wintypes.WCHAR * 32),
            ("DeviceString", wintypes.WCHAR * 128),
            ("StateFlags", wintypes.DWORD),
            ("DeviceID", wintypes.WCHAR * 128),
            ("DeviceKey", wintypes.WCHAR * 128),
        ]

    DISPLAY_DEVICE_ATTACHED_TO_DESKTOP = 0x1
    DISPLAY_DEVICE_PRIMARY_DEVICE = 0x4
    out: list[dict[str, Any]] = []
    i = 0
    while True:
        dev = DISPLAY_DEVICEW()
        dev.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        if not user32.EnumDisplayDevicesW(None, i, ctypes.byref(dev), 0):
            break
        i += 1
        if not (dev.StateFlags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP):
            continue
        mode = DEVMODEW()
        mode.dmSize = ctypes.sizeof(DEVMODEW)
        if not user32.EnumDisplaySettingsW(dev.DeviceName, ENUM_CURRENT_SETTINGS, ctypes.byref(mode)):
            continue
        out.append(
            {
                "device": str(dev.DeviceName),
                "device_string": str(dev.DeviceString),
                "width": int(mode.dmPelsWidth),
                "height": int(mode.dmPelsHeight),
                "refresh_hz": int(mode.dmDisplayFrequency),
                "primary": bool(dev.StateFlags & DISPLAY_DEVICE_PRIMARY_DEVICE),
            }
        )
    return out


def capture_current_mode() -> dict[str, Any]:
    """Snapshot every attached display mode for later per-monitor rollback."""
    if os.name != "nt":
        return {
            "platform": "non_windows",
            "captured_at": time.time(),
            "displays": [],
        }
    displays = list_display_modes()
    if not displays:
        # Fallback primary-only
        user32 = ctypes.windll.user32
        mode = DEVMODEW()
        mode.dmSize = ctypes.sizeof(DEVMODEW)
        if not user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(mode)):
            from buusdo.core.i18n import t

            raise BuusdoError(t("err.display_enum"))
        displays = [
            {
                "device": None,
                "width": int(mode.dmPelsWidth),
                "height": int(mode.dmPelsHeight),
                "refresh_hz": int(mode.dmDisplayFrequency),
                "primary": True,
            }
        ]
    primary = next((d for d in displays if d.get("primary")), displays[0])
    snap = {
        "width": primary["width"],
        "height": primary["height"],
        "refresh_hz": primary.get("refresh_hz"),
        "hdr": _query_hdr_enabled(),
        "captured_at": time.time(),
        "displays": displays,
        "targets": list_advanced_color_targets(),
    }
    path = _session_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    return snap


def rollback_display_session(*, dry_run: bool = False) -> dict[str, Any]:
    """Restore each monitor's resolution/refresh + HDR from the last session."""
    snap = load_display_session()
    if snap is None:
        return {"restored": False, "reason": "no_session"}
    if os.name != "nt":
        return {"restored": False, "reason": "not_windows", "snap": snap}
    steps: list[dict[str, Any]] = []
    for disp in snap.get("displays") or []:
        step = _apply_mode(
            int(disp["width"]),
            int(disp["height"]),
            disp.get("refresh_hz"),
            dry_run=dry_run,
            device=disp.get("device"),
        )
        step["device_string"] = disp.get("device_string")
        step["primary"] = bool(disp.get("primary"))
        steps.append(step)
    hdr_step = _set_hdr_advanced_color(bool(snap.get("hdr")), dry_run=dry_run)
    steps.append(hdr_step)
    mode_steps = [
        s
        for s in steps
        if s.get("action") in {"ChangeDisplaySettingsW", "ChangeDisplaySettingsExW"}
    ]
    failed_displays = [
        {
            "device": s.get("device"),
            "device_string": s.get("device_string"),
            "primary": s.get("primary"),
            "action": s.get("action"),
            "code": s.get("code"),
            "error": s.get("error"),
            "width": s.get("width"),
            "height": s.get("height"),
            "refresh_hz": s.get("refresh_hz"),
        }
        for s in mode_steps
        if not s.get("ok")
    ]
    mode_ok = bool(mode_steps) and all(s.get("ok") for s in mode_steps)
    applied = bool(mode_ok or (not snap.get("displays") and hdr_step.get("ok")))
    if applied and not dry_run:
        clear_display_session()
    return {
        "restored": applied,
        "failed_displays": failed_displays,
        "details": {"steps": steps, "hdr": hdr_step, "failed_displays": failed_displays},
        "snap": snap,
    }


def list_advanced_color_targets() -> list[dict[str, Any]]:
    """Enumerate active CCD paths with adapterId/targetId for multi-monitor HDR verify."""
    if os.name != "nt":
        return []
    paths, err = _active_paths()
    if paths is None:
        return []
    out: list[dict[str, Any]] = []
    user32 = ctypes.windll.user32
    for path in paths:
        info = DISPLAYCONFIG_GET_ADVANCED_COLOR_INFO()
        info.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_ADVANCED_COLOR_INFO
        info.header.size = ctypes.sizeof(DISPLAYCONFIG_GET_ADVANCED_COLOR_INFO)
        info.header.adapterId = path.targetInfo.adapterId
        info.header.id = path.targetInfo.id
        status = user32.DisplayConfigGetDeviceInfo(ctypes.byref(info))
        out.append(
            {
                "adapterLow": int(path.targetInfo.adapterId.LowPart),
                "adapterHigh": int(path.targetInfo.adapterId.HighPart),
                "targetId": int(path.targetInfo.id),
                "get_status": int(status),
                "advancedColorSupported": bool(info.value & 0x1) if status == 0 else None,
                "advancedColorEnabled": bool(info.value & 0x2) if status == 0 else None,
            }
        )
    return out


def verify_set_advanced_color_state(*, enable: bool, dry_run: bool = True) -> dict[str, Any]:
    """Multi-monitor verification helper for SET_ADVANCED_COLOR_STATE (real machine / dry-run)."""
    before = list_advanced_color_targets()
    if os.name != "nt":
        return {
            "ok": False,
            "reason": "not_windows",
            "before": before,
            "note": "Run on a Windows host with multiple displays to verify adapterId/targetId.",
        }
    applied = _set_hdr_advanced_color(enable, dry_run=dry_run)
    after = before if dry_run else list_advanced_color_targets()
    return {
        "ok": bool(applied.get("ok")),
        "dry_run": dry_run,
        "enable": enable,
        "before": before,
        "after": after,
        "apply": applied,
        "multi_monitor": len(before) > 1,
    }


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
            from buusdo.core.i18n import t

            raise BuusdoError(t("err.display_resolution", resolution=profile.resolution))
        width, height = int(m.group(1)), int(m.group(2))

    if width and height:
        # Apply preferred mode to primary; other monitors keep captured session values on rollback.
        step = _apply_mode(width, height, profile.refresh_hz, dry_run=dry_run, device=None)
        result["steps"].append(step)
        if not step.get("ok"):
            from buusdo.core.i18n import t

            raise BuusdoError(step.get("error") or t("err.display_change"))

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
    width: int,
    height: int,
    refresh_hz: int | None,
    *,
    dry_run: bool,
    device: str | None = None,
) -> dict[str, Any]:
    user32 = ctypes.windll.user32
    mode = DEVMODEW()
    mode.dmSize = ctypes.sizeof(DEVMODEW)
    if not user32.EnumDisplaySettingsW(device, ENUM_CURRENT_SETTINGS, ctypes.byref(mode)):
        return {
            "ok": False,
            "action": "enum",
            "error": "EnumDisplaySettingsW failed",
            "device": device,
        }

    mode.dmPelsWidth = width
    mode.dmPelsHeight = height
    mode.dmFields = DM_PELSWIDTH | DM_PELSHEIGHT
    if refresh_hz:
        mode.dmDisplayFrequency = int(refresh_hz)
        mode.dmFields |= DM_DISPLAYFREQUENCY

    flags = CDS_TEST if dry_run else CDS_UPDATEREGISTRY
    if device:
        code = user32.ChangeDisplaySettingsExW(device, ctypes.byref(mode), None, flags, None)
        action = "ChangeDisplaySettingsExW"
    else:
        code = user32.ChangeDisplaySettingsW(ctypes.byref(mode), flags)
        action = "ChangeDisplaySettingsW"
    return {
        "ok": code == DISP_CHANGE_SUCCESSFUL,
        "action": action,
        "device": device,
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
