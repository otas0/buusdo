"""Write Steam launch options into localconfig.vdf (transactional)."""

from __future__ import annotations

import re
from pathlib import Path

from buusdo.core.errors import BuusdoError
from buusdo.core.transaction import Transaction
from buusdo.core.vdf import parse_vdf


def find_localconfig(steam_roots: list[Path]) -> Path | None:
    for root in steam_roots:
        userdata = root / "userdata"
        if not userdata.is_dir():
            # Flatpak / symlink layouts
            alt = root / "steam" / "userdata"
            userdata = alt if alt.is_dir() else userdata
        if not userdata.is_dir():
            continue
        for user_dir in sorted(userdata.iterdir()):
            if not user_dir.is_dir() or not user_dir.name.isdigit():
                continue
            candidate = user_dir / "config" / "localconfig.vdf"
            if candidate.is_file():
                return candidate
    return None


def set_launch_options(
    tx: Transaction,
    localconfig: Path,
    app_id: str,
    launch_options: str,
) -> dict:
    """Set LaunchOptions for app_id inside localconfig.vdf.

    Uses a conservative text rewrite when the Apps subtree exists; otherwise
    raises so we never invent a broken VDF document.
    """
    if not localconfig.is_file():
        raise BuusdoError(f"localconfig.vdf not found: {localconfig}")
    text = localconfig.read_text(encoding="utf-8", errors="replace")
    try:
        parse_vdf(text)  # validate readable
    except ValueError as exc:
        raise BuusdoError(f"Invalid localconfig.vdf: {exc}") from exc

    app_id = str(app_id)
    # Prefer precise in-place replacement of an existing LaunchOptions line under the app.
    pattern = re.compile(
        rf'("{re.escape(app_id)}"\s*\{{(?:[^{{}}]|\\{{|\\}})*?"LaunchOptions"\s*")([^"]*)(")',
        re.DOTALL,
    )
    if pattern.search(text):
        new_text = pattern.sub(rf'\1{launch_options}\3', text, count=1)
    else:
        # Insert LaunchOptions into an existing app block if present.
        app_block = re.compile(
            rf'("{re.escape(app_id)}"\s*\{{)',
            re.DOTALL,
        )
        match = app_block.search(text)
        if not match:
            raise BuusdoError(
                f"localconfig.vdf 中未找到 app {app_id}；请先在 Steam 中至少启动过该游戏。"
            )
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
