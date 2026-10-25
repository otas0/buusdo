"""Describe Steam library cache / resume scan progress for the UI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from buusdo.core.library_cache import _cache_path, _fingerprint
from buusdo.core.platform_detect import steam_roots


def resume_scan_status(steam_root_list: list[Path] | None = None) -> dict[str, Any]:
    """Return progress for a partial cache: scanned N manifests, fingerprint match."""
    roots = steam_root_list if steam_root_list is not None else steam_roots()
    fp = _fingerprint(roots)
    path = _cache_path()
    if not path.is_file():
        return {
            "partial": False,
            "fingerprint_match": False,
            "scanned": 0,
            "games_cached": 0,
            "total_manifests": len([k for k in fp if "appmanifest_" in k]),
        }
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"partial": False, "fingerprint_match": False, "scanned": 0, "games_cached": 0}
    scanned = raw.get("scanned_manifests") or {}
    total = len([k for k in fp if "appmanifest_" in str(k)])
    match = raw.get("fingerprint") == fp
    return {
        "partial": bool(raw.get("partial")),
        "fingerprint_match": match,
        "scanned": len(scanned),
        "games_cached": len(raw.get("games") or []),
        "total_manifests": total,
        "resume": bool(raw.get("partial") and match),
    }
