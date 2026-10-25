"""Validate ReShade / OptiScaler kit directories for the first-run wizard."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KitStatus:
    ok: bool
    missing: tuple[str, ...]
    found: tuple[str, ...]
    message: str


def validate_reshade_kit(path: Path | None) -> KitStatus:
    if path is None or not Path(path).is_dir():
        return KitStatus(False, ("ReShade64.dll", "ReShade32.dll"), (), "directory missing")
    root = Path(path)
    need_any = ("ReShade64.dll", "ReShade32.dll")
    found = tuple(n for n in need_any if (root / n).is_file())
    missing = tuple(n for n in need_any if n not in found)
    ok = bool(found)
    return KitStatus(ok, missing if not ok else (), found, "ok" if ok else "missing reshade dll")


def validate_optiscaler_kit(path: Path | None) -> KitStatus:
    markers = ("OptiScaler.dll", "optiscaler.dll", "nvngx.dll", "libxess.dll")
    if path is None or not Path(path).is_dir():
        return KitStatus(False, markers, (), "directory missing")
    root = Path(path)
    found = tuple(n for n in markers if (root / n).is_file())
    ok = bool(found)
    return KitStatus(
        ok,
        () if ok else markers,
        found,
        "ok" if ok else "missing optiscaler markers",
    )
