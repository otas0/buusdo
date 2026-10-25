"""Proton prefix health checks for discovered games."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from buusdo.core.backend import EnhancementTarget
from buusdo.core.i18n import t


@dataclass(frozen=True)
class ProtonHealth:
    ok: bool
    code: str
    message: str
    prefix: Path | None = None
    steam_uri: str | None = None
    steam_url: str | None = None


def check_proton_prefix(target: EnhancementTarget) -> ProtonHealth | None:
    runtime = target.metadata.get("runtime")
    prefix_raw = target.metadata.get("proton_prefix")
    app_id = target.metadata.get("app_id")
    steam_uri = f"steam://run/{app_id}" if app_id else None
    steam_url = f"https://store.steampowered.com/app/{app_id}/" if app_id else None

    if runtime != "proton" and not prefix_raw:
        return None

    if not prefix_raw:
        return ProtonHealth(
            ok=False,
            code="missing_prefix_meta",
            message=t("proton.missing_prefix"),
            prefix=None,
            steam_uri=steam_uri,
            steam_url=steam_url,
        )

    prefix = Path(str(prefix_raw))
    if not prefix.is_dir():
        return ProtonHealth(
            ok=False,
            code="compatdata_missing",
            message=t("proton.missing_prefix"),
            prefix=prefix,
            steam_uri=steam_uri,
            steam_url=steam_url,
        )

    drive_c = prefix / "drive_c"
    if not drive_c.is_dir():
        return ProtonHealth(
            ok=False,
            code="incomplete_prefix",
            message=t("proton.incomplete_prefix"),
            prefix=prefix,
            steam_uri=steam_uri,
            steam_url=steam_url,
        )

    return ProtonHealth(
        ok=True,
        code="ok",
        message=t("proton.ok"),
        prefix=prefix,
        steam_uri=steam_uri,
        steam_url=steam_url,
    )
