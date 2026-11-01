"""Bundled static assets (logo, icons)."""

from __future__ import annotations

from pathlib import Path


def asset_path(name: str) -> Path:
    return Path(__file__).resolve().parent / name


def logo_path() -> Path:
    """Primary raster logo (wordmark). Prefer logo.png; brand_mark.png is legacy fallback only."""
    logo = asset_path("logo.png")
    if logo.is_file():
        return logo
    mark = asset_path("brand_mark.png")
    if mark.is_file():
        return mark
    return logo


def logo_svg_path() -> Path:
    """Vector wordmark for UI chrome (themeable fills). Generated from logo.png."""
    return asset_path("logo.svg")


def brand_mark_path() -> Path:
    """Legacy pixel mark — keep on disk for fallback; do not use in share/UI surfaces."""
    return asset_path("brand_mark.png")


def logo_ico_path() -> Path:
    """Windows .ico derived from logo.png (generated on demand if missing)."""
    return asset_path("logo.ico")


def logo_icns_path() -> Path:
    """macOS .icns derived from logo.png (Mac package track)."""
    return asset_path("logo.icns")
