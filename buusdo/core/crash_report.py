"""Optional local crash reports with path/username redaction. Upload off by default."""

from __future__ import annotations

import getpass
import json
import os
import re
import traceback
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
    # Absolute-ish paths
    out = re.sub(r"(/Users|/home)/[^/\s]+", r"\1/<user>", out)
    out = re.sub(r"[A-Za-z]:\\Users\\[^\\]+", r"C:\\Users\\<user>", out)
    return out


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
        "note": "Local only unless BUUSDO_CRASH_UPLOAD=1 (still redacted; no network impl yet).",
    }
    path = reports_dir() / f"crash_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if os.environ.get("BUUSDO_CRASH_UPLOAD") in {"1", "true", "TRUE"}:
        # Intentionally no network upload implementation yet — record intent only.
        payload["upload_attempted"] = True
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
