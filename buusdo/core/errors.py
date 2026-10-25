"""Shared error types. UnsafeTargetError is non-bypassable (C1)."""


class BuusdoError(Exception):
    """Base error for recoverable and user-facing failures."""


class UnsafeTargetError(BuusdoError):
    """Raised when anti-cheat or other safety checks block a target.

    UI must show a blocking page with no "continue anyway" path (C1).
    """

    def __init__(self, target_name: str, reason: str, evidence: list[str] | None = None):
        self.target_name = target_name
        self.reason = reason
        self.evidence = evidence or []
        super().__init__(f"Unsafe target '{target_name}': {reason}")
