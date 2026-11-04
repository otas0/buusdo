"""Companion bind address helpers."""

from __future__ import annotations

from buusdo.companion.netinfo import companion_bind_addr, truncate_bind_addr
from buusdo.companion.pairing import PairAttemptLimit


def test_truncate_bind_addr_keeps_port() -> None:
    long_ip = "192.168.100.200:8765"
    short = truncate_bind_addr(long_ip, max_len=18)
    assert short.endswith(":8765")
    assert "…" in short
    assert len(short) <= 18


def test_truncate_short_unchanged() -> None:
    assert truncate_bind_addr("127.0.0.1:8765") == "127.0.0.1:8765"


def test_companion_bind_addr_loopback() -> None:
    assert companion_bind_addr(loopback_only=True, port=8765) == "127.0.0.1:8765"


def test_pair_attempt_retry_after() -> None:
    limit = PairAttemptLimit(max_attempts=1, window_sec=30)
    assert limit.retry_after_sec("c") == 0.0
    assert limit.allow("c", now=1000.0) is True
    assert limit.allow("c", now=1001.0) is False
    left = limit.retry_after_sec("c", now=1001.0)
    assert 28.0 <= left <= 30.0
