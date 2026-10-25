"""Probe Steam client deep-link URIs (properties / run) without hardcoding one scheme."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from buusdo.core.config_store import load_settings, save_settings

# Prefer re-probing after a week so a Steam client update cannot pin a dead scheme forever.
DEFAULT_STEAM_URI_CACHE_TTL_S = 7 * 24 * 3600
# Back-compat alias.
STEAM_URI_CACHE_TTL_S = DEFAULT_STEAM_URI_CACHE_TTL_S


def steam_uri_cache_ttl_s() -> int:
    """Settings-configurable TTL (seconds); default 7 days. Floor at 1 hour."""
    raw = load_settings().get("steam_properties_uri_ttl_s")
    try:
        ttl = int(raw) if raw is not None else DEFAULT_STEAM_URI_CACHE_TTL_S
    except (TypeError, ValueError):
        ttl = DEFAULT_STEAM_URI_CACHE_TTL_S
    return max(3600, ttl)


def set_steam_uri_cache_ttl_s(seconds: int) -> None:
    data = load_settings()
    data["steam_properties_uri_ttl_s"] = max(3600, int(seconds))
    save_settings(data)


def game_properties_uri_candidates(app_id: str | int) -> list[str]:
    app_id = str(app_id)
    cached = cached_properties_template()
    if cached:
        preferred = cached.replace("{app_id}", app_id)
        rest = [
            u
            for u in [
                f"steam://gameproperties/{app_id}",
                f"steam://open/gameproperties/{app_id}",
                f"steam://url/GameHub/{app_id}",
                f"steam://nav/games/details/{app_id}",
                f"steam://store/{app_id}",
            ]
            if u != preferred
        ]
        return [preferred, *rest]
    return [
        f"steam://gameproperties/{app_id}",
        f"steam://open/gameproperties/{app_id}",
        f"steam://url/GameHub/{app_id}",
        f"steam://nav/games/details/{app_id}",
        f"steam://store/{app_id}",
    ]


def run_uri(app_id: str | int) -> str:
    return f"steam://run/{app_id}"


def _parse_probed_at(raw: object) -> datetime | None:
    if not raw:
        return None
    try:
        text = str(raw)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def cached_properties_template(*, now: datetime | None = None) -> str | None:
    """Return cached template, or None if missing / TTL expired (auto-clears)."""
    data = load_settings()
    tpl = data.get("steam_properties_uri_template")
    if not tpl:
        return None
    probed = _parse_probed_at(data.get("steam_properties_uri_probed_at"))
    clock = now or datetime.now(timezone.utc)
    ttl = steam_uri_cache_ttl_s()
    if probed is not None:
        if probed.tzinfo is None:
            probed = probed.replace(tzinfo=timezone.utc)
        age = (clock - probed).total_seconds()
        if age < 0 or age > ttl:
            clear_properties_uri_cache()
            return None
    return str(tpl)


def cache_properties_uri(uri: str) -> None:
    """Persist working URI as a template with {app_id} placeholder + probed_at."""
    import re

    templated = re.sub(r"/\d+$", "/{app_id}", uri)
    if "{app_id}" not in templated:
        templated = re.sub(r"(\D)\d+$", r"\1{app_id}", uri)
    data = load_settings()
    data["steam_properties_uri_template"] = templated
    data["steam_properties_uri_last"] = uri
    data["steam_properties_uri_probed_at"] = datetime.now(timezone.utc).isoformat()
    save_settings(data)


def clear_properties_uri_cache() -> bool:
    """Drop cached Steam properties URI template (e.g. after all probes fail)."""
    data = load_settings()
    keys = (
        "steam_properties_uri_template",
        "steam_properties_uri_last",
        "steam_properties_uri_probed_at",
    )
    changed = any(k in data for k in keys)
    for k in keys:
        data.pop(k, None)
    if changed:
        save_settings(data)
    return changed


def steam_uri_cache_status(*, now: datetime | None = None) -> dict:
    """UI helper: whether a preferred properties URI template is active."""
    tpl = cached_properties_template(now=now)
    data = load_settings()
    probed = _parse_probed_at(data.get("steam_properties_uri_probed_at")) if tpl else None
    return {
        "cached": bool(tpl),
        "template": tpl,
        "probed_at": probed.isoformat() if probed else None,
        "ttl_s": steam_uri_cache_ttl_s(),
    }


def probe_open_uris(
    uris: Iterable[str],
    *,
    opener,
    cache_success: bool = True,
    clear_cache_on_fail: bool = True,
) -> dict:
    """Try URIs in order; opener(url) -> bool (True if accepted by desktop services)."""
    tried: list[str] = []
    for uri in uris:
        tried.append(uri)
        try:
            ok = bool(opener(uri))
        except Exception:
            ok = False
        if ok:
            if cache_success:
                cache_properties_uri(uri)
            return {"opened": True, "uri": uri, "tried": tried, "cached": cache_success}
    cleared = False
    if clear_cache_on_fail:
        cleared = clear_properties_uri_cache()
    return {
        "opened": False,
        "uri": None,
        "tried": tried,
        "cached": False,
        "cache_cleared": cleared,
    }


def try_steam_uri_candidate(
    uris: list[str],
    index: int,
    *,
    opener,
    cache_success: bool = True,
) -> dict:
    """Open one candidate by index; return next_index for a UI \"Try next\" control.

    ``next_index`` is 0 after success, ``index+1`` after failure (capped at ``len(uris)``
    when exhausted). Does not clear the properties cache on failure.
    """
    total = len(uris)
    if total == 0:
        return {
            "opened": False,
            "uri": None,
            "index": index,
            "total": 0,
            "next_index": 0,
            "exhausted": True,
            "remaining": 0,
        }
    if index < 0 or index >= total:
        return {
            "opened": False,
            "uri": None,
            "index": index,
            "total": total,
            "next_index": total,
            "exhausted": True,
            "remaining": 0,
        }
    uri = uris[index]
    result = probe_open_uris(
        [uri], opener=opener, cache_success=cache_success, clear_cache_on_fail=False
    )
    if result.get("opened"):
        return {
            "opened": True,
            "uri": uri,
            "index": index,
            "total": total,
            "next_index": 0,
            "exhausted": False,
            "remaining": total,
        }
    next_index = index + 1
    exhausted = next_index >= total
    return {
        "opened": False,
        "uri": uri,
        "index": index,
        "total": total,
        "next_index": next_index if not exhausted else total,
        "exhausted": exhausted,
        "remaining": max(0, total - next_index),
    }
