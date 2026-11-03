"""In-process companion host: dispatch allowlisted ops only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from buusdo.companion.honesty import companion_capabilities
from buusdo.companion.protocol import (
    AllowedOp,
    CompanionError,
    CompanionRequest,
    CompanionResponse,
    PROTOCOL_VERSION,
    parse_request,
)
from buusdo.companion.status import StatusSnapshot, build_status_snapshot


ScanRequester = Callable[[], str]
HistorySummary = Callable[[], str]
RecentNames = Callable[[], list[str]]
Translator = Callable[[str], str]


def _identity_t(key: str) -> str:
    return key


@dataclass
class CompanionHost:
    """Desktop-side dispatcher. Never exposes install/inject."""

    host_label: str = "desktop"
    paired: bool = False
    request_scan: ScanRequester | None = None
    history_summary: HistorySummary | None = None
    recent_names: RecentNames | None = None
    translate: Translator = field(default=_identity_t)

    def handle(self, payload: dict[str, Any]) -> CompanionResponse:
        try:
            req = parse_request(payload)
        except CompanionError as exc:
            return CompanionResponse(
                protocol_version=PROTOCOL_VERSION,
                ok=False,
                error=str(exc),
            )
        return self._dispatch(req)

    def _dispatch(self, req: CompanionRequest) -> CompanionResponse:
        if req.op is AllowedOp.PING:
            return self._ok(req, {"pong": True})

        if req.op is AllowedOp.STATUS:
            snap = self.status_snapshot()
            return self._ok(req, snap.to_dict())

        if req.op is AllowedOp.HISTORY_SUMMARY:
            summary = ""
            if self.history_summary is not None:
                summary = str(self.history_summary() or "")[:500]
            return self._ok(req, {"summary": summary})

        if req.op is AllowedOp.REQUEST_SCAN:
            if not self.paired:
                return CompanionResponse(
                    protocol_version=PROTOCOL_VERSION,
                    ok=False,
                    request_id=req.request_id,
                    op=req.op.value,
                    error="not paired",
                )
            if self.request_scan is None:
                return CompanionResponse(
                    protocol_version=PROTOCOL_VERSION,
                    ok=False,
                    request_id=req.request_id,
                    op=req.op.value,
                    error="scan not wired",
                )
            msg = str(self.request_scan() or "scan requested")
            return self._ok(req, {"message": msg})

        if req.op is AllowedOp.CAPABILITIES:
            caps = companion_capabilities(t=self.translate)
            return self._ok(
                req,
                {
                    "capabilities": [
                        {
                            "id": c.id,
                            "title": c.title,
                            "description": c.description,
                            "available": c.available,
                            "notes": c.notes,
                        }
                        for c in caps
                    ]
                },
            )

        return CompanionResponse(
            protocol_version=PROTOCOL_VERSION,
            ok=False,
            request_id=req.request_id,
            op=req.op.value,
            error=f"unhandled op: {req.op.value}",
        )

    def status_snapshot(self) -> StatusSnapshot:
        names: list[str] = []
        if self.recent_names is not None:
            names = list(self.recent_names() or [])
        summary = ""
        if self.history_summary is not None:
            summary = str(self.history_summary() or "")
        return build_status_snapshot(
            host_label=self.host_label,
            paired=self.paired,
            recent_game_names=names,
            last_history_summary=summary,
        )

    @staticmethod
    def _ok(req: CompanionRequest, data: dict[str, Any]) -> CompanionResponse:
        return CompanionResponse(
            protocol_version=PROTOCOL_VERSION,
            ok=True,
            request_id=req.request_id,
            op=req.op.value,
            data=data,
        )
