"""Companion protocol: allowlist + forbidden ops."""

from __future__ import annotations

import pytest

from buusdo.companion.host import CompanionHost
from buusdo.companion.protocol import (
    FORBIDDEN_OPS,
    PROTOCOL_VERSION,
    AllowedOp,
    CompanionError,
    parse_request,
)


def test_protocol_version_constant() -> None:
    assert PROTOCOL_VERSION == 1


def test_parse_status_ok() -> None:
    req = parse_request(
        {
            "protocol_version": 1,
            "op": "status",
            "request_id": "r1",
            "params": {},
        }
    )
    assert req.op is AllowedOp.STATUS
    assert req.request_id == "r1"


@pytest.mark.parametrize("op", sorted(FORBIDDEN_OPS))
def test_forbidden_ops_rejected(op: str) -> None:
    with pytest.raises(CompanionError, match="forbidden"):
        parse_request({"protocol_version": 1, "op": op})


def test_unknown_op_rejected() -> None:
    with pytest.raises(CompanionError, match="unknown"):
        parse_request({"protocol_version": 1, "op": "teleport_vram"})


def test_bad_version_rejected() -> None:
    with pytest.raises(CompanionError, match="protocol_version"):
        parse_request({"protocol_version": 99, "op": "ping"})


def test_host_ping_and_status() -> None:
    host = CompanionHost(
        host_label="test-host",
        paired=True,
        recent_names=lambda: ["Alpha", "Beta"],
        history_summary=lambda: "ok",
    )
    ping = host.handle({"protocol_version": 1, "op": "ping", "request_id": "p"})
    assert ping.ok is True
    assert ping.data["pong"] is True

    status = host.handle({"protocol_version": 1, "op": "status"})
    assert status.ok is True
    assert status.data["host_label"] == "test-host"
    assert status.data["recent_game_names"] == ["Alpha", "Beta"]
    assert "Companion is read-mostly" in status.data["notes"][0]


def test_host_refuses_unpaired_scan() -> None:
    host = CompanionHost(paired=False, request_scan=lambda: "should-not-run")
    resp = host.handle({"protocol_version": 1, "op": "request_scan"})
    assert resp.ok is False
    assert "not paired" in resp.error


def test_host_scan_when_paired() -> None:
    called: list[str] = []
    host = CompanionHost(
        paired=True,
        request_scan=lambda: called.append("x") or "queued",
    )
    resp = host.handle({"protocol_version": 1, "op": "request_scan"})
    assert resp.ok is True
    assert resp.data["message"] == "queued"
    assert called == ["x"]


def test_host_rejects_forbidden_payload() -> None:
    host = CompanionHost(paired=True)
    resp = host.handle({"protocol_version": 1, "op": "inject"})
    assert resp.ok is False
    assert "forbidden" in resp.error
