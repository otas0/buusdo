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


def check_proton_prefix(target: EnhancementTarget) -> ProtonHealth | None:
    """Return health for Proton-marked targets; None if not a Proton game."""
    runtime = target.metadata.get("runtime")
    prefix_raw = target.metadata.get("proton_prefix")
    if runtime != "proton" and not prefix_raw:
        # Heuristic: Windows exe on Linux install without prefix
        return None

    if not prefix_raw:
        return ProtonHealth(
            ok=False,
            code="missing_prefix_meta",
            message=t("proton.missing_prefix"),
            prefix=None,
        )

    prefix = Path(str(prefix_raw))
    if not prefix.is_dir():
        return ProtonHealth(
            ok=False,
            code="compatdata_missing",
            message=t("proton.missing_prefix"),
            prefix=prefix,
        )

    drive_c = prefix / "drive_c"
    if not drive_c.is_dir():
        return ProtonHealth(
            ok=False,
            code="incomplete_prefix",
            message="Proton prefix exists but drive_c is missing (incomplete).",
            prefix=prefix,
        )

    return ProtonHealth(ok=True, code="ok", message="Proton prefix healthy", prefix=prefix)
