"""Optional local crash reports with path/username redaction + optional upload."""

from __future__ import annotations

import getpass
import json
import os
import re
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from buusdo.core.platform_detect import user_config_dir


def reports_dir() -> Path:
    return user_config_dir() / "crash_reports"


def redact(text: str) -> str:
    user = getpass.getuser()
    home = str(Path.home())
    out = text.replace(home, "~")
    out = out.replace(user, "<user>")
    out = re.sub(r"(/Users|/home)/[^/\s]+", r"\1/<user>", out)
    out = re.sub(r"[A-Za-z]:\\Users\\[^\\]+", r"C:\\Users\\<user>", out)
    # Strip likely secrets
    out = re.sub(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+", r"\1=<redacted>", out)
    return out


def _upload(payload: dict[str, Any]) -> dict[str, Any]:
    """Upload redacted JSON to Sentry-compatible store or custom endpoint.

    Env:
      BUUSDO_CRASH_UPLOAD=1
      BUUSDO_CRASH_ENDPOINT=https://...  (self-host or Sentry envelope URL)
      BUUSDO_CRASH_DSN=... optional; if set, posts a minimal Sentry event store body
    """
    endpoint = os.environ.get("BUUSDO_CRASH_ENDPOINT") or os.environ.get("BUUSDO_CRASH_DSN")
    if not endpoint:
        return {"uploaded": False, "reason": "no_endpoint"}

    body = json.dumps(
        {
            "message": payload.get("message"),
            "exception": {
                "values": [
                    {
                        "type": payload.get("type"),
                        "value": payload.get("message"),
                        "stacktrace": {"frames": []},
                    }
                ]
            },
            "extra": {
                "traceback": payload.get("traceback"),
                "context": payload.get("context"),
            },
            "tags": {"app": "buusdo", "redacted": "true"},
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "buusdo-crash/1"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:  # noqa: S310 — user-configured endpoint
            return {"uploaded": True, "status": getattr(resp, "status", 200)}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"uploaded": False, "error": redact(str(exc))}


def capture_exception(exc: BaseException, *, context: dict[str, Any] | None = None) -> Path | None:
    if os.environ.get("BUUSDO_CRASH_REPORTS", "0") not in {"1", "true", "TRUE", "yes"}:
        return None
    reports_dir().mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": type(exc).__name__,
        "message": redact(str(exc)),
        "traceback": redact("".join(traceback.format_exception(type(exc), exc, exc.__traceback__))),
        "context": {k: redact(str(v)) for k, v in (context or {}).items()},
        "upload": False,
    }
    path = reports_dir() / f"crash_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    if os.environ.get("BUUSDO_CRASH_UPLOAD") in {"1", "true", "TRUE", "yes"}:
        payload["upload_result"] = _upload(payload)
        payload["upload"] = bool(payload["upload_result"].get("uploaded"))
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
