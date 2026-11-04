"""Companion loopback preference in settings.json."""

from __future__ import annotations

from pathlib import Path

import pytest

from buusdo.companion.bindpref import apply_companion_bind_preference
from buusdo.companion.host import CompanionHost
from buusdo.companion.pairing import PairingDesk
from buusdo.companion.transport import CompanionTransport
from buusdo.core import config_store as store


@pytest.fixture()
def cfg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(store, "user_config_dir", lambda: tmp_path)
    return tmp_path


def test_companion_loopback_default_false(cfg: Path) -> None:
    assert store.get_companion_loopback_only() is False


def test_companion_loopback_roundtrip(cfg: Path) -> None:
    store.set_companion_loopback_only(True)
    assert store.get_companion_loopback_only() is True
    raw = (cfg / "settings.json").read_text(encoding="utf-8")
    assert "companion_loopback_only" in raw
    store.set_companion_loopback_only(False)
    assert store.get_companion_loopback_only() is False


def test_startup_honors_companion_loopback_only_without_ui(cfg: Path) -> None:
    """Desktop startup path: settings → apply_companion_bind_preference → bind."""
    store.set_companion_loopback_only(True)
    host = CompanionHost(host_label="test", paired=False)
    transport = CompanionTransport(
        host=host,
        pairing=PairingDesk(ttl_sec=60),
        bind_host="0.0.0.0",
        port=0,
    )
    assert transport.loopback_only is False
    apply_companion_bind_preference(transport)
    assert transport.loopback_only is True
    assert transport.bind_host == "127.0.0.1"
    transport.start()
    try:
        assert transport.running
        assert transport.bind_host == "127.0.0.1"
    finally:
        transport.stop()
