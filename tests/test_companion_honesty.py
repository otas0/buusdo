"""Mobile companion honesty rows stay non-features where required."""

from __future__ import annotations

from buusdo.companion.honesty import MOBILE_NON_GOALS, companion_capabilities
from buusdo.companion.host import CompanionHost
from buusdo.core.hardware_notes import HARDWARE_NOTES


def test_mobile_non_goals_stable_ids() -> None:
    ids = [n.id for n in MOBILE_NON_GOALS]
    assert ids == [
        "no_remote_inject",
        "no_phone_gpu",
        "no_bypass_anticheat",
    ]


def test_companion_capabilities_include_hardware_doctrine() -> None:
    rows = companion_capabilities(t=lambda k: k)
    ids = {r.id for r in rows}
    assert "mobile.companion_status" in ids
    assert "mobile.no_remote_inject" in ids
    for note in HARDWARE_NOTES:
        assert f"hw.{note.id}" in ids
    # Non-goals and hardware honesty must not look like boosts.
    for row in rows:
        if row.id.startswith("mobile.no_") or row.id.startswith("hw."):
            assert row.available is False


def test_host_capabilities_op() -> None:
    host = CompanionHost(translate=lambda k: k)
    resp = host.handle({"protocol_version": 1, "op": "capabilities"})
    assert resp.ok is True
    caps = resp.data["capabilities"]
    assert any(c["id"] == "mobile.no_remote_inject" for c in caps)
    assert any(c["available"] is False and c["id"].startswith("hw.") for c in caps)
