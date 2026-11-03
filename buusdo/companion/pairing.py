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
