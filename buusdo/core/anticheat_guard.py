"""Mandatory anti-cheat gate (C1).

Semantics: presence of anti-cheat => refuse. No risk acknowledgment bypass.
"""

from __future__ import annotations

from pathlib import Path

import psutil

from buusdo.core.backend import EnhancementTarget
from buusdo.core.errors import UnsafeTargetError
from buusdo.core.platform_detect import HostPlatform

# Known anti-cheat process / service / module name fragments (lowercase).
# Expand over time; matching is substring-based on purpose (strict gate).
_KNOWN_ANTICHEAT_MARKERS: frozenset[str] = frozenset(
    {
        "easyanticheat",
        "easy anti-cheat",
        "eac_",
        "eacservice",
        "battleye",
        "beservice",
        "beclient",
        "vanguard",
        "vgk",
        "vgc",
        "faceit",
        "faceitservice",
        "nprotect",
        "gameguard",
        "xigncode",
        "ricochet",
        "mrac",
        "wpfg",
        "equ8",
        "neac",
        "tenprotect",
        "ace-tray",
        "anticheatexpert",
    }
)

_KNOWN_ANTICHEAT_PATH_MARKERS: frozenset[str] = frozenset(
    {
        "easyanticheat",
        "battleye",
        "vanguard",
        "faceit",
        "gameguard",
        "xigncode",
        "ricochet",
        "nprotect",
    }
)


def _normalize(s: str) -> str:
    return s.lower().replace("\\", "/")


def _matches_marker(value: str, markers: frozenset[str]) -> str | None:
    norm = _normalize(value)
    for marker in markers:
        if marker in norm:
            return marker
    return None


def _scan_install_tree(root: Path) -> list[str]:
    evidence: list[str] = []
    if not root.exists():
        return evidence
    try:
        for path in root.rglob("*"):
            hit = _matches_marker(path.name, _KNOWN_ANTICHEAT_PATH_MARKERS)
            if hit:
                evidence.append(f"path:{path}")
            if len(evidence) >= 20:
                break
    except OSError:
        pass
    return evidence


def _scan_running_processes() -> list[str]:
    evidence: list[str] = []
    try:
        for proc in psutil.process_iter(["name", "exe"]):
            info = proc.info
            for field in ("name", "exe"):
                value = info.get(field)
                if not value:
                    continue
                hit = _matches_marker(str(value), _KNOWN_ANTICHEAT_MARKERS)
                if hit:
                    evidence.append(f"process:{value}")
                    break
            if len(evidence) >= 20:
                break
    except (psutil.Error, OSError):
        pass
    return evidence


def check(target: EnhancementTarget, platform: HostPlatform | str) -> None:
    """Raise UnsafeTargetError if anti-cheat is detected for the target.

    Must be the first step of every install() / inject / config-write path.
    ``platform`` is accepted for API completeness; gate semantics are the same
    on every host (including Proton on Linux).
    """
    _ = platform  # same refuse-on-presence semantics on all platforms (C1)
    evidence: list[str] = []
    evidence.extend(_scan_install_tree(target.install_path))
    evidence.extend(_scan_running_processes())

    if evidence:
        raise UnsafeTargetError(
            target_name=target.name,
            reason="anti-cheat detected; enhancement refused",
            evidence=evidence,
        )
