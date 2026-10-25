"""Mandatory anti-cheat gate (C1).

Semantics: presence of anti-cheat => refuse. No risk acknowledgment bypass.
"""

from __future__ import annotations

from pathlib import Path

import psutil

from buusdo.core.backend import EnhancementTarget
from buusdo.core.errors import UnsafeTargetError
from buusdo.core.platform_detect import HostPlatform

_KNOWN_ANTICHEAT_MARKERS: frozenset[str] = frozenset(
    {
        "easyanticheat",
        "easy anti-cheat",
        "eac_",
        "eacservice",
        "eac_launcher",
        "battleye",
        "beservice",
        "beclient",
        "beservice_x64",
        "vanguard",
        "vgk",
        "vgc",
        "vgtray",
        "faceit",
        "faceitservice",
        "faceitclient",
        "nprotect",
        "npgamemon",
        "gameguard",
        "gameguard.des",
        "xigncode",
        "x3.xem",
        "ricochet",
        "mrac",
        "wpfg",
        "equ8",
        "neac",
        "tenprotect",
        "tcls",
        "ace-tray",
        "aces-svc",
        "anticheatexpert",
        "pbea",
        "fairfight",
        "punkbuster",
        "pbsvc",
        "hackshield",
        "hsbclhsvc",
        "wellbia",
        "theia",
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
        "punkbuster",
        "hackshield",
        "anticheatexpert",
        "fairfight",
    }
)

_KNOWN_ANTICHEAT_MODULE_MARKERS: frozenset[str] = frozenset(
    {
        "easyanticheat",
        "eac_",
        "beclient",
        "beservice",
        "vgk",
        "vgc",
        "faceit",
        "gameguard",
        "xigncode",
        "npgamemon",
        "ace-",
        "equ8",
        "mrac",
        "ricochet",
        "pbsvc",
        "hackshield",
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
            if len(evidence) >= 30:
                break
    except OSError:
        pass
    return evidence


def _target_process_names(target: EnhancementTarget) -> set[str]:
    names: set[str] = set()
    if target.executable:
        names.add(target.executable.name.lower())
        names.add(target.executable.stem.lower())
    for raw in target.metadata.get("executables") or []:
        p = Path(str(raw))
        names.add(p.name.lower())
        names.add(p.stem.lower())
    # Folder token as weak association
    folder = target.install_path.name.lower().replace(" ", "")
    if len(folder) >= 4:
        names.add(folder)
    return {n for n in names if n}


def _process_matches_target(proc_name: str, exe_path: str, target_names: set[str]) -> bool:
    if not target_names:
        return True  # no hint → keep broad scan (safe/strict)
    blob = _normalize(f"{proc_name} {exe_path}")
    return any(n in blob for n in target_names)


def _scan_running_processes(target: EnhancementTarget) -> list[str]:
    evidence: list[str] = []
    target_names = _target_process_names(target)
    try:
        for proc in psutil.process_iter(["name", "exe"]):
            info = proc.info
            pname = str(info.get("name") or "")
            pexe = str(info.get("exe") or "")
            # Always refuse global anti-cheat services (EAC service, Vanguard, etc.)
            global_hit = _matches_marker(pname, _KNOWN_ANTICHEAT_MARKERS) or _matches_marker(
                pexe, _KNOWN_ANTICHEAT_MARKERS
            )
            if not global_hit:
                continue
            # For game-bundled clients, prefer association with target to cut noise;
            # services with no path still count as global.
            if pexe and not _process_matches_target(pname, pexe, target_names):
                # Still block well-known always-on services
                if not any(
                    s in _normalize(pname)
                    for s in ("eacservice", "beservice", "vgc", "vgk", "faceitservice")
                ):
                    continue
            evidence.append(f"process:{pname or pexe}")
            if len(evidence) >= 30:
                break
    except (psutil.Error, OSError):
        pass
    return evidence


def _scan_loaded_modules(target: EnhancementTarget) -> list[str]:
    """Scan modules of processes associated with the target (reduces false positives)."""
    evidence: list[str] = []
    target_names = _target_process_names(target)
    try:
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            info = proc.info
            pname = str(info.get("name") or "")
            pexe = str(info.get("exe") or "")
            associated = _process_matches_target(pname, pexe, target_names)
            # Always inspect known AC helper processes; otherwise only target-associated.
            is_ac_helper = bool(
                _matches_marker(pname, _KNOWN_ANTICHEAT_MARKERS)
                or _matches_marker(pexe, _KNOWN_ANTICHEAT_MARKERS)
            )
            if not associated and not is_ac_helper:
                continue
            try:
                maps = proc.memory_maps(grouped=False)
            except (psutil.Error, OSError, AttributeError):
                continue
            for mmap in maps:
                path = getattr(mmap, "path", "") or ""
                if not path:
                    continue
                hit = _matches_marker(path, _KNOWN_ANTICHEAT_MODULE_MARKERS)
                if hit:
                    evidence.append(f"module:{path}")
                    if len(evidence) >= 30:
                        return evidence
    except (psutil.Error, OSError):
        pass
    return evidence


def check(target: EnhancementTarget, platform: HostPlatform | str) -> None:
    """Raise UnsafeTargetError if anti-cheat is detected for the target."""
    _ = platform
    evidence: list[str] = []
    evidence.extend(_scan_install_tree(target.install_path))
    evidence.extend(_scan_running_processes(target))
    evidence.extend(_scan_loaded_modules(target))

    if evidence:
        raise UnsafeTargetError(
            target_name=target.name,
            reason="anti-cheat detected; enhancement refused",
            evidence=evidence,
        )
