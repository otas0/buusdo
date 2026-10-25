"""EnhancementBackend contract. UI talks only to this interface (C3)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

CancelCb = Callable[[], bool]


@dataclass(frozen=True)
class EnhancementTarget:
    """A game or app the user wants to enhance."""

    name: str
    install_path: Path
    executable: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Capability:
    """A named capability with honest user-facing copy (C4)."""

    id: str
    title: str
    description: str
    available: bool
    notes: str = ""


@dataclass(frozen=True)
class InstallResult:
    success: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


class EnhancementBackend(ABC):
    """Platform backend. Every mutating path must pass anticheat + Transaction."""

    @abstractmethod
    def platform_id(self) -> str:
        """Stable id: windows | linux | macos."""

    @abstractmethod
    def discover_games(
        self,
        *,
        should_cancel: CancelCb | None = None,
        progress: Callable[[str, float], None] | None = None,
    ) -> list[EnhancementTarget]:
        """Enumerate known games (e.g. Steam). should_cancel() True aborts mid-scan."""

    @abstractmethod
    def list_capabilities(self, target: EnhancementTarget) -> list[Capability]:
        """Capabilities for this target; wording must obey C4."""

    @abstractmethod
    def install(self, target: EnhancementTarget, options: dict[str, Any] | None = None) -> InstallResult:
        """Apply enhancements. Must call anticheat_guard.check first (C1)
        and perform all writes inside Transaction (C2).
        """

    @abstractmethod
    def uninstall(self, target: EnhancementTarget) -> InstallResult:
        """Restore originals byte-for-byte via Transaction (C2)."""

    @abstractmethod
    def status(self, target: EnhancementTarget) -> dict[str, Any]:
        """Current enhancement state for the target."""
