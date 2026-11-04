"""User-initiated pairing codes (ephemeral; not persisted)."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass


DEFAULT_TTL_SEC = 300


@dataclass
class PairingSession:
    code: str
    expires_at: float
    consumed: bool = False

    def alive(self, now: float | None = None) -> bool:
        ts = time.time() if now is None else now
        return (not self.consumed) and ts < self.expires_at


class PairingDesk:
    """Holds at most one active pairing code until consumed or expired."""

    def __init__(self, *, ttl_sec: int = DEFAULT_TTL_SEC) -> None:
        self._ttl = max(30, int(ttl_sec))
        self._session: PairingSession | None = None

    def start(self) -> PairingSession:
        code = f"{secrets.randbelow(1_000_000):06d}"
        session = PairingSession(
            code=code,
            expires_at=time.time() + self._ttl,
        )
        self._session = session
        return session

    def clear(self) -> None:
        self._session = None

    def peek(self) -> PairingSession | None:
        if self._session is None or not self._session.alive():
            self._session = None
            return None
        return self._session

    def consume(self, code: str) -> bool:
        session = self.peek()
        if session is None:
            return False
        if secrets.compare_digest(session.code, str(code).strip()):
            session.consumed = True
            self._session = None
            return True
        return False


class PairAttemptLimit:
    """Per-client sliding window for /v1/pair (no cloud; LAN brute-force brake)."""

    def __init__(self, *, max_attempts: int = 8, window_sec: float = 60.0) -> None:
        self.max_attempts = max(1, int(max_attempts))
        self.window_sec = float(window_sec)
        self._hits: dict[str, list[float]] = {}

    def allow(self, client_key: str, *, now: float | None = None) -> bool:
        ts = time.time() if now is None else now
        key = client_key or "unknown"
        recent = [t for t in self._hits.get(key, []) if ts - t < self.window_sec]
        if len(recent) >= self.max_attempts:
            self._hits[key] = recent
            return False
        recent.append(ts)
        self._hits[key] = recent
        return True

    def retry_after_sec(self, client_key: str, *, now: float | None = None) -> float:
        """Seconds until the oldest hit in the window expires (0 if under limit)."""
        ts = time.time() if now is None else now
        key = client_key or "unknown"
        recent = [t for t in self._hits.get(key, []) if ts - t < self.window_sec]
        self._hits[key] = recent
        if len(recent) < self.max_attempts:
            return 0.0
        oldest = min(recent)
        return max(0.0, self.window_sec - (ts - oldest))
