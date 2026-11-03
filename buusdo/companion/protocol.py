"""JSON companion protocol v1 — allowlisted ops only."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


PROTOCOL_VERSION = 1


class AllowedOp(str, Enum):
    """Ops the desktop host may honor for a paired mobile client."""

    STATUS = "status"
    HISTORY_SUMMARY = "history_summary"
    REQUEST_SCAN = "request_scan"
    CAPABILITIES = "capabilities"
    PING = "ping"


# Explicit denylist names for tests / docs — never register these as AllowedOp.
FORBIDDEN_OPS: frozenset[str] = frozenset(
    {
        "install",
        "uninstall",
        "inject",
        "deploy_reshade",
        "write_config",
        "bypass_anticheat",
        "enable_ray_tracing",
        "ram_as_gpu",
    }
)


class CompanionError(ValueError):
    """Invalid or forbidden companion request."""


@dataclass(frozen=True)
class CompanionRequest:
    protocol_version: int
    op: AllowedOp
    request_id: str = ""
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.protocol_version,
            "op": self.op.value,
            "request_id": self.request_id,
            "params": dict(self.params),
        }


@dataclass(frozen=True)
class CompanionResponse:
    protocol_version: int
    ok: bool
    request_id: str = ""
    op: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_request(payload: dict[str, Any]) -> CompanionRequest:
    """Validate a client payload; refuse unknown/forbidden ops."""
    if not isinstance(payload, dict):
        raise CompanionError("payload must be an object")

    version = int(payload.get("protocol_version") or 0)
    if version != PROTOCOL_VERSION:
        raise CompanionError(
            f"unsupported protocol_version {version}; need {PROTOCOL_VERSION}"
        )

    raw_op = str(payload.get("op") or "").strip()
    if not raw_op:
        raise CompanionError("op is required")
    if raw_op in FORBIDDEN_OPS:
        raise CompanionError(f"forbidden op: {raw_op}")
    try:
        op = AllowedOp(raw_op)
    except ValueError as exc:
        raise CompanionError(f"unknown op: {raw_op}") from exc

    params = payload.get("params") or {}
    if not isinstance(params, dict):
        raise CompanionError("params must be an object")

    return CompanionRequest(
        protocol_version=version,
        op=op,
        request_id=str(payload.get("request_id") or ""),
        params=dict(params),
    )
