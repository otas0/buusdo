"""Probe Steam client deep-link URIs (properties / run) without hardcoding one scheme."""

from __future__ import annotations

from typing import Iterable


def game_properties_uri_candidates(app_id: str | int) -> list[str]:
    app_id = str(app_id)
    return [
        f"steam://gameproperties/{app_id}",
        f"steam://open/gameproperties/{app_id}",
        f"steam://url/GameHub/{app_id}",
        f"steam://nav/games/details/{app_id}",
        f"steam://store/{app_id}",
    ]


def run_uri(app_id: str | int) -> str:
    return f"steam://run/{app_id}"


def probe_open_uris(
    uris: Iterable[str],
    *,
    opener,
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
            return {"opened": True, "uri": uri, "tried": tried}
    return {"opened": False, "uri": None, "tried": tried}
