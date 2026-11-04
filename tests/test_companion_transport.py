"""LAN companion HTTP: pair + rpc allowlist; no inject endpoint."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from buusdo.companion import devices as devices_mod
from buusdo.companion.devices import clear_devices, list_devices
from buusdo.companion.host import CompanionHost
from buusdo.companion.pairing import PairAttemptLimit, PairingDesk
from buusdo.companion.transport import CompanionTransport


@pytest.fixture()
def transport(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(devices_mod, "user_config_dir", lambda: tmp_path)
    clear_devices()
    host = CompanionHost(
        host_label="test",
        paired=False,
        recent_names=lambda: ["Demo"],
        history_summary=lambda: "none",
        request_scan=lambda: "queued",
        translate=lambda k: k,
    )
    pairing = PairingDesk(ttl_sec=60)
    # Bind loopback; pick ephemeral port.
    t = CompanionTransport(host=host, pairing=pairing, bind_host="127.0.0.1", port=0)
    # ThreadingHTTPServer needs concrete port — start then read.
    import socket

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    t.port = port
    t.start()
    yield t, pairing, port
    t.stop()


def _post(port: int, path: str, payload: dict, *, token: str | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_health_and_pair_flow(transport) -> None:
    t, pairing, port = transport
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/health", timeout=5) as resp:
        health = json.loads(resp.read().decode("utf-8"))
    assert health["ok"] is True

    session = pairing.start()
    paired = _post(port, "/v1/pair", {"code": session.code, "label": "pixel"})
    assert paired["ok"] is True
    token = paired["token"]
    assert list_devices()

    status = _post(
        port,
        "/v1/rpc",
        {"protocol_version": 1, "op": "status"},
        token=token,
    )
    assert status["ok"] is True
    assert status["data"]["recent_game_names"] == ["Demo"]

    scan = _post(
        port,
        "/v1/rpc",
        {"protocol_version": 1, "op": "request_scan"},
        token=token,
    )
    assert scan["ok"] is True
    assert scan["data"]["message"] == "queued"


def test_rpc_rejects_without_token(transport) -> None:
    _t, _pairing, port = transport
    with pytest.raises(urllib.error.HTTPError) as ei:
        _post(port, "/v1/rpc", {"protocol_version": 1, "op": "status"})
    assert ei.value.code == 401


def test_loopback_bind_and_last_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(devices_mod, "user_config_dir", lambda: tmp_path)
    clear_devices()
    host = CompanionHost(host_label="test", paired=False)
    pairing = PairingDesk(ttl_sec=60)
    t = CompanionTransport(
        host=host,
        pairing=pairing,
        bind_host="0.0.0.0",
        port=0,
        pair_limit=PairAttemptLimit(max_attempts=1, window_sec=60),
    )
    t.set_loopback_only(True)
    assert t.bind_host == "127.0.0.1"
    t.start()
    try:
        assert t.running
        pairing.start()
        with pytest.raises(urllib.error.HTTPError) as first:
            _post(t.port, "/v1/pair", {"code": "000000"})
        assert first.value.code == 403
        with pytest.raises(urllib.error.HTTPError) as second:
            _post(t.port, "/v1/pair", {"code": "000000"})
        assert second.value.code == 429
        body = json.loads(second.value.read().decode("utf-8"))
        assert body.get("retry_after", 0) >= 1
        assert "too many" in t.last_error
        assert t.rate_limit_remaining_sec() >= 1
    finally:
        t.stop()


def test_pair_rate_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from buusdo.companion.pairing import PairAttemptLimit

    monkeypatch.setattr(devices_mod, "user_config_dir", lambda: tmp_path)
    clear_devices()
    host = CompanionHost(host_label="test", paired=False)
    pairing = PairingDesk(ttl_sec=60)
    limit = PairAttemptLimit(max_attempts=2, window_sec=60)
    t = CompanionTransport(
        host=host,
        pairing=pairing,
        bind_host="127.0.0.1",
        port=0,
        pair_limit=limit,
    )
    t.start()
    try:
        port = t.port
        pairing.start()
        for _ in range(2):
            try:
                _post(port, "/v1/pair", {"code": "000000"})
            except urllib.error.HTTPError as exc:
                assert exc.code == 403
        with pytest.raises(urllib.error.HTTPError) as ei:
            _post(port, "/v1/pair", {"code": "000000"})
        assert ei.value.code == 429
    finally:
        t.stop()


def test_forbidden_op_still_rejected_when_paired(transport) -> None:
    _t, pairing, port = transport
    session = pairing.start()
    paired = _post(port, "/v1/pair", {"code": session.code})
    token = paired["token"]
    resp = _post(
        port,
        "/v1/rpc",
        {"protocol_version": 1, "op": "inject"},
        token=token,
    )
    assert resp["ok"] is False
    assert "forbidden" in resp["error"]
