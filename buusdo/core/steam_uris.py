"""Probe Steam client deep-link URIs (properties / run) without hardcoding one scheme."""

from __future__ import annotations

from typing import Iterable

from buusdo.core.config_store import load_settings, save_settings


def game_properties_uri_candidates(app_id: str | int) -> list[str]:
    app_id = str(app_id)
    cached = cached_properties_template()
    if cached:
        # Prefer last-known working scheme first.
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


def cached_properties_template() -> str | None:
    tpl = load_settings().get("steam_properties_uri_template")
    return str(tpl) if tpl else None


def cache_properties_uri(uri: str) -> None:
    """Persist working URI as a template with {app_id} placeholder."""
    # Replace trailing numeric app id with placeholder.
    import re

    templated = re.sub(r"/\d+$", "/{app_id}", uri)
    if "{app_id}" not in templated:
        # GameHub style may embed id differently
        templated = re.sub(r"(\D)\d+$", r"\1{app_id}", uri)
    data = load_settings()
    data["steam_properties_uri_template"] = templated
    data["steam_properties_uri_last"] = uri
    save_settings(data)


def clear_properties_uri_cache() -> bool:
    """Drop cached Steam properties URI template (e.g. after all probes fail)."""
    data = load_settings()
    changed = "steam_properties_uri_template" in data or "steam_properties_uri_last" in data
    data.pop("steam_properties_uri_template", None)
    data.pop("steam_properties_uri_last", None)
    if changed:
        save_settings(data)
    return changed


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
