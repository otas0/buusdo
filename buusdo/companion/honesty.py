"""Mobile companion honesty (C4) — what the phone must never claim."""

from __future__ import annotations

from dataclasses import dataclass

from buusdo.core.backend import Capability
from buusdo.core.hardware_notes import honesty_capabilities


@dataclass(frozen=True)
class MobileNonGoal:
    id: str
    title_key: str
    body_key: str


# Stable ids for docs + tests. Copy lives in locale keys (mobile.*).
MOBILE_NON_GOALS: tuple[MobileNonGoal, ...] = (
    MobileNonGoal(
        "no_remote_inject",
        "mobile.no_remote_inject.title",
        "mobile.no_remote_inject.body",
    ),
    MobileNonGoal(
        "no_phone_gpu",
        "mobile.no_phone_gpu.title",
        "mobile.no_phone_gpu.body",
    ),
    MobileNonGoal(
        "no_bypass_anticheat",
        "mobile.no_bypass_anticheat.title",
        "mobile.no_bypass_anticheat.body",
    ),
)


def companion_capabilities(*, t) -> list[Capability]:
    """Honest capability rows for mobile About / capabilities screens."""
    rows: list[Capability] = [
        Capability(
            id="mobile.companion_status",
            title=t("mobile.cap.status.title"),
            description=t("mobile.cap.status.body"),
            available=True,
            notes=t("mobile.cap.status.notes"),
        ),
        Capability(
            id="mobile.companion_scan_request",
            title=t("mobile.cap.scan.title"),
            description=t("mobile.cap.scan.body"),
            available=True,
            notes=t("mobile.cap.scan.notes"),
        ),
    ]
    for ng in MOBILE_NON_GOALS:
        rows.append(
            Capability(
                id=f"mobile.{ng.id}",
                title=t(ng.title_key),
                description=t(ng.body_key),
                available=False,
                notes=t("mobile.not_a_feature"),
            )
        )
    # Reuse desktop hardware doctrine so phone copy cannot drift (C4).
    rows.extend(honesty_capabilities(t=t))
    return rows
