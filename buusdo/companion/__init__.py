"""Desktop↔mobile companion protocol (read-mostly; no remote injection)."""

from buusdo.companion.honesty import MOBILE_NON_GOALS, companion_capabilities
from buusdo.companion.host import CompanionHost
from buusdo.companion.pairing import PairingDesk
from buusdo.companion.protocol import (
    PROTOCOL_VERSION,
    AllowedOp,
    CompanionError,
    CompanionRequest,
    CompanionResponse,
    parse_request,
)
from buusdo.companion.status import StatusSnapshot, build_status_snapshot
from buusdo.companion.transport import CompanionTransport

__all__ = [
    "PROTOCOL_VERSION",
    "AllowedOp",
    "CompanionError",
    "CompanionHost",
    "CompanionRequest",
    "CompanionResponse",
    "CompanionTransport",
    "MOBILE_NON_GOALS",
    "PairingDesk",
    "StatusSnapshot",
    "build_status_snapshot",
    "companion_capabilities",
    "parse_request",
]
