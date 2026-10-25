"""Optional local crash reports with path/username redaction + optional upload.

Upload requires explicit user opt-in (settings.crash_upload_opt_in).
Payloads are always redacted before disk/network.
"""

from __future__ import annotations

import getpass
import json
import os
import re
import traceback
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from buusdo.core.config_store import load_settings, save_settings
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
    out = re.sub(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+", r"\1=<redacted>", out)
    return out


def crash_upload_opted_in() -> bool:
    return bool(load_settings().get("crash_upload_opt_in"))


def _audit_path() -> Path:
    return user_config_dir() / "crash_opt_in_audit.jsonl"


def append_crash_opt_in_audit(*, enabled: bool, note: str = "") -> Path:
    """Append opt-in change audit (never stores raw crash bodies)."""
    path = _audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "crash_upload_opt_in": bool(enabled),
        "note": redact(note) if note else "",
        "raw_payload_uploaded": False,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


def set_crash_upload_opt_in(enabled: bool) -> None:
    data = load_settings()
    prev = bool(data.get("crash_upload_opt_in"))
    data["crash_upload_opt_in"] = bool(enabled)
    if enabled:
        data["crash_reports_enabled"] = True
    save_settings(data)
    if prev != bool(enabled):
        append_crash_opt_in_audit(
            enabled=bool(enabled),
            note="user toggled opt-in; redacted reports only, no raw upload of originals",
        )


def _sentry_store_url(dsn_or_endpoint: str) -> str:
    if dsn_or_endpoint.startswith(("http://", "https://")):
        hostpart = dsn_or_endpoint.split("://", 1)[-1].split("/", 1)[0]
        if "@" not in hostpart:
            return dsn_or_endpoint
    m = re.match(r"^(https?)://([^@]+)@([^/]+)/(\d+)$", dsn_or_endpoint.strip())
    if not m:
        return dsn_or_endpoint
    scheme, key, host, project = m.groups()
    return f"{scheme}://{host}/api/{project}/envelope/?sentry_key={key}&sentry_version=7"


def _build_sentry_envelope(payload: dict[str, Any]) -> bytes:
    event_id = uuid.uuid4().hex
    header = {"event_id": event_id, "sent_at": datetime.now(timezone.utc).isoformat()}
    item_header = {"type": "event", "content_type": "application/json"}
    event = {
        "event_id": event_id,
        "timestamp": payload.get("ts"),
        "platform": "python",
        "level": "error",
        "message": payload.get("message"),
        "exception": {
            "values": [{"type": payload.get("type"), "value": payload.get("message")}]
        },
        "extra": {
            "traceback": payload.get("traceback"),
            "context": payload.get("context"),
        },
        "tags": {"app": "buusdo", "redacted": "true"},
    }
    lines = [
        json.dumps(header, separators=(",", ":")),
        json.dumps(item_header, separators=(",", ":")),
        json.dumps(event, separators=(",", ":"), ensure_ascii=False),
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _upload(payload: dict[str, Any]) -> dict[str, Any]:
    if not crash_upload_opted_in():
        return {"uploaded": False, "reason": "opt_in_required"}
    raw = os.environ.get("BUUSDO_CRASH_ENDPOINT") or os.environ.get("BUUSDO_CRASH_DSN")
    if not raw:
        return {"uploaded": False, "reason": "no_endpoint"}

    use_envelope = bool(os.environ.get("BUUSDO_CRASH_DSN")) or os.environ.get(
        "BUUSDO_CRASH_FORMAT", "envelope"
    ).lower() in {"envelope", "sentry"}
    endpoint = _sentry_store_url(raw) if use_envelope else raw
    if use_envelope:
        body = _build_sentry_envelope(payload)
        content_type = "application/x-sentry-envelope"
    else:
        body = json.dumps(
            {
                "message": payload.get("message"),
                "type": payload.get("type"),
                "traceback": payload.get("traceback"),
                "context": payload.get("context"),
                "tags": {"app": "buusdo", "redacted": "true"},
            }
        ).encode("utf-8")
        content_type = "application/json"

    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": content_type, "User-Agent": "buusdo-crash/2"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:  # noqa: S310
            return {
                "uploaded": True,
                "status": getattr(resp, "status", 200),
                "format": "envelope" if use_envelope else "json",
            }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"uploaded": False, "error": redact(str(exc))}


def capture_exception(exc: BaseException, *, context: dict[str, Any] | None = None) -> Path | None:
    env_on = os.environ.get("BUUSDO_CRASH_REPORTS", "0") in {"1", "true", "TRUE", "yes"}
    settings = load_settings()
    if not (env_on or settings.get("crash_reports_enabled") or crash_upload_opted_in()):
        return None
    reports_dir().mkdir(parents=True, exist_ok=True)
    safe_ctx: dict[str, str] = {}
    for k, v in (context or {}).items():
        key_l = str(k).lower()
        if any(s in key_l for s in ("token", "secret", "password", "api_key", "apikey", "dsn")):
            safe_ctx[str(k)] = "<redacted>"
        else:
            safe_ctx[str(k)] = redact(str(v))
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": type(exc).__name__,
        "message": redact(str(exc)),
        "traceback": redact("".join(traceback.format_exception(type(exc), exc, exc.__traceback__))),
        "context": safe_ctx,
        "upload": False,
    }
    path = reports_dir() / f"crash_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    want_upload = os.environ.get("BUUSDO_CRASH_UPLOAD") in {"1", "true", "TRUE", "yes"}
    if want_upload:
        payload["upload_result"] = _upload(payload)
        payload["upload"] = bool(payload["upload_result"].get("uploaded"))
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
