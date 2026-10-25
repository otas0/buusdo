"""Platform-agnostic core: detection, guards, transactions, backend contract."""

from buusdo.core.errors import BuusdoError, UnsafeTargetError
from buusdo.core.backend import EnhancementBackend, EnhancementTarget, InstallResult

__all__ = [
    "BuusdoError",
    "UnsafeTargetError",
    "EnhancementBackend",
    "EnhancementTarget",
    "InstallResult",
]
