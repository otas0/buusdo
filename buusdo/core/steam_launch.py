"""Write Steam launch options into localconfig.vdf (transactional)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from buusdo.core.errors import BuusdoError
from buusdo.core.transaction import Transaction
from buusdo.core.vdf import parse_vdf


@dataclass(frozen=True)
class SteamUserProfile:
    steam_id3: str
    localconfig: Path
    persona_name: str | None = None

    @property
    def label(self) -> str:
        if self.persona_name:
            return f"{self.persona_name} ({self.steam_id3})"
        return self.steam_id3


def list_steam_users(steam_roots: list[Path]) -> list[SteamUserProfile]:
    """Enumerate all userdata/<id>/config/localconfig.vdf profiles."""
    profiles: list[SteamUserProfile] = []
    seen: set[Path] = set()
    for root in steam_roots:
        for userdata in _userdata_dirs(root):
            for user_dir in sorted(userdata.iterdir()):
                if not user_dir.is_dir() or not user_dir.name.isdigit():
                    continue
                candidate = user_dir / "config" / "localconfig.vdf"
                if not candidate.is_file():
                    continue
                try:
                    resolved = candidate.resolve()
                except OSError:
                    resolved = candidate
                if resolved in seen:
                    continue
                seen.add(resolved)
                profiles.append(
                    SteamUserProfile(
                        steam_id3=user_dir.name,
                        localconfig=candidate,
                        persona_name=_read_persona_name(candidate),
                    )
                )
    return profiles


def find_localconfig(
    steam_roots: list[Path],
    *,
    steam_id3: str | None = None,
) -> Path | None:
    """Return one localconfig. Prefer explicit steam_id3; else first profile."""
    profiles = list_steam_users(steam_roots)
    if not profiles:
        return None
    if steam_id3:
        for p in profiles:
            if p.steam_id3 == str(steam_id3):
                return p.localconfig
        return None
    return profiles[0].localconfig


def _userdata_dirs(steam_root: Path) -> list[Path]:
    out: list[Path] = []
    for candidate in (steam_root / "userdata", steam_root / "steam" / "userdata"):
        if candidate.is_dir():
            out.append(candidate)
    return out


def _read_persona_name(localconfig: Path) -> str | None:
    try:
        text = localconfig.read_text(encoding="utf-8", errors="replace")
        data = parse_vdf(text)
    except (OSError, ValueError):
        return None
    # Walk common locations for PersonaName
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key).lower() == "personaname" and isinstance(value, str) and value.strip():
                    return value.strip()
                if isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(node, list):
            stack.extend(node)
    return None


def set_launch_options(
    tx: Transaction,
    localconfig: Path,
    app_id: str,
    launch_options: str,
) -> dict:
    """Set LaunchOptions for app_id inside localconfig.vdf."""
    if not localconfig.is_file():
        raise BuusdoError(f"localconfig.vdf not found: {localconfig}")
    text = localconfig.read_text(encoding="utf-8", errors="replace")
    try:
        parse_vdf(text)
    except ValueError as exc:
        raise BuusdoError(f"Invalid localconfig.vdf: {exc}") from exc

    app_id = str(app_id)
    pattern = re.compile(
        rf'("{re.escape(app_id)}"\s*\{{(?:[^{{}}]|\\{{|\\}})*?"LaunchOptions"\s*")([^"]*)(")',
        re.DOTALL,
    )
    if pattern.search(text):
        new_text = pattern.sub(rf"\1{launch_options}\3", text, count=1)
    else:
        app_block = re.compile(rf'("{re.escape(app_id)}"\s*\{{)', re.DOTALL)
        match = app_block.search(text)
        if not match:
            from buusdo.core.i18n import t

            raise BuusdoError(t("err.app_not_in_localconfig", app_id=app_id))
        insert = f'\n\t\t\t\t"LaunchOptions"\t\t"{launch_options}"'
        new_text = text[: match.end()] + insert + text[match.end() :]

    tx.write_text(localconfig, new_text)
    return {
        "localconfig": str(localconfig),
        "app_id": app_id,
        "launch_options": launch_options,
    }


def clear_launch_options(tx: Transaction, localconfig: Path, app_id: str) -> dict:
    return set_launch_options(tx, localconfig, app_id, "")


def write_proton_launch_note(
    tx: Transaction,
    localconfig: Path,
    app_id: str,
    *,
    note: str,
    preserve_existing: bool = True,
) -> dict:
    """Write a user-visible Proton reminder into LaunchOptions (and a buusdo_note key)."""
    if not localconfig.is_file():
        raise BuusdoError(f"localconfig.vdf not found: {localconfig}")
    text = localconfig.read_text(encoding="utf-8", errors="replace")
    app_id = str(app_id)
    existing = ""
    lo_pat = re.compile(
        rf'("{re.escape(app_id)}"\s*\{{(?:[^{{}}]|\\{{|\\}})*?"LaunchOptions"\s*")([^"]*)(")',
        re.DOTALL,
    )
    m = lo_pat.search(text)
    if m and preserve_existing:
        existing = m.group(2).strip()
    # Keep existing command chain; prepend a short note token Steam shows in Properties.
    if existing and "%command%" in existing:
        launch = existing
    elif existing:
        launch = f"{existing} %command%" if "%command%" not in existing else existing
    else:
        launch = "%command%"
    # Store note as a separate VDF key inside the app block when possible.
    note_pat = re.compile(
        rf'("{re.escape(app_id)}"\s*\{{)',
        re.DOTALL,
    )
    note_key = re.compile(
        rf'("{re.escape(app_id)}"\s*\{{(?:[^{{}}]|\\{{|\\}})*?"buusdo_note"\s*")([^"]*)(")',
        re.DOTALL,
    )
    if note_key.search(text):
        text = note_key.sub(rf"\1{note}\3", text, count=1)
    else:
        nm = note_pat.search(text)
        if nm:
            insert = f'\n\t\t\t\t"buusdo_note"\t\t"{note}"'
            text = text[: nm.end()] + insert + text[nm.end() :]
    # Write updated text then set launch options via helper path
    tx.write_text(localconfig, text)
    result = set_launch_options(tx, localconfig, app_id, launch)
    result["buusdo_note"] = note
    return result
