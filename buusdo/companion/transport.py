"""LAN HTTP transport for companion protocol v1 (no cloud relay).

Starts only when the desktop user requests it. Auth: Bearer device token after
pairing; ``/v1/pair`` accepts a short-lived pairing code.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import urlparse

from buusdo.companion.devices import add_device, token_is_paired
from buusdo.companion.host import CompanionHost
from buusdo.companion.netinfo import DEFAULT_PORT
from buusdo.companion.pairing import PairAttemptLimit, PairingDesk
from buusdo.companion.protocol import PROTOCOL_VERSION

ScanCallback = Callable[[], str]


class CompanionHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        *,
        host: CompanionHost,
        pairing: PairingDesk,
        pair_limit: PairAttemptLimit,
    ) -> None:
        self.companion_host = host
        self.pairing = pairing
        self.pair_limit = pair_limit
        super().__init__(server_address, _CompanionHandler)


class _CompanionHandler(BaseHTTPRequestHandler):
    server: CompanionHTTPServer

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        # Keep desktop console quiet; tests assert via responses.
        return

    def _json(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > 1_000_000:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _bearer(self) -> str:
        auth = self.headers.get("Authorization") or ""
        if auth.lower().startswith("bearer "):
            return auth[7:].strip()
        return ""

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/v1/health"):
            self._json(
                200,
                {
                    "ok": True,
                    "protocol_version": PROTOCOL_VERSION,
                    "service": "buusdo-companion",
                },
            )
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        payload = self._read_json()

        if path == "/v1/pair":
            client = ""
            if self.client_address:
                client = str(self.client_address[0])
            if not self.server.pair_limit.allow(client):
                self._json(429, {"ok": False, "error": "too many pairing attempts"})
                return
            code = str(payload.get("code") or "").strip()
            label = str(payload.get("label") or "mobile")[:64]
            if not self.server.pairing.consume(code):
                self._json(403, {"ok": False, "error": "invalid or expired pairing code"})
                return
            device = add_device(label=label)
            self.server.companion_host.paired = True
            self._json(
                200,
                {
                    "ok": True,
                    "protocol_version": PROTOCOL_VERSION,
                    "device_id": device.device_id,
                    "token": device.token,
                    "label": device.label,
                },
            )
            return

        if path == "/v1/rpc":
            token = self._bearer()
            if not token_is_paired(token):
                self._json(401, {"ok": False, "error": "unauthorized"})
                return
            self.server.companion_host.paired = True
            resp = self.server.companion_host.handle(payload)
            # Always HTTP 200 for RPC; clients read CompanionResponse.ok.
            self._json(200, resp.to_dict())
            return

        self._json(404, {"ok": False, "error": "not found"})


class CompanionTransport:
    """Owns the HTTP server thread; user-start / user-stop only."""

    def __init__(
        self,
        *,
        host: CompanionHost,
        pairing: PairingDesk | None = None,
        bind_host: str = "0.0.0.0",
        port: int = DEFAULT_PORT,
        pair_limit: PairAttemptLimit | None = None,
    ) -> None:
        self.host = host
        self.pairing = pairing or PairingDesk()
        self.pair_limit = pair_limit or PairAttemptLimit()
        self.bind_host = bind_host
        self.port = int(port)
        self._httpd: CompanionHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._httpd is not None

    def start(self) -> None:
        if self._httpd is not None:
            return
        httpd = CompanionHTTPServer(
            (self.bind_host, self.port),
            host=self.host,
            pairing=self.pairing,
            pair_limit=self.pair_limit,
        )
        # Honour OS-assigned port when bind used port 0.
        self.port = int(httpd.server_address[1])
        self._httpd = httpd
        thread = threading.Thread(
            target=httpd.serve_forever,
            name="buusdo-companion-http",
            daemon=True,
        )
        self._thread = thread
        thread.start()

    def stop(self) -> None:
        httpd = self._httpd
        self._httpd = None
        if httpd is not None:
            httpd.shutdown()
            httpd.server_close()
        self._thread = None
        self.pairing.clear()
