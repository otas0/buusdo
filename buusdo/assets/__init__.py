"""Bundled static assets (logo, icons)."""

from __future__ import annotations

from pathlib import Path


def asset_path(name: str) -> Path:
    return Path(__file__).resolve().parent / name


def logo_path() -> Path:
    """Primary product logo (wordmark). Prefer logo.png over the pixel brand mark."""
    logo = asset_path("logo.png")
    if logo.is_file():
        return logo
    mark = asset_path("brand_mark.png")
    if mark.is_file():
        return mark
    return logo


def brand_mark_path() -> Path:
    return asset_path("brand_mark.png")


def logo_ico_path() -> Path:
    """Windows .ico derived from logo.png (generated on demand if missing)."""
    return asset_path("logo.ico")
