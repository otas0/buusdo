"""Bundled static assets (logo, etc.)."""

from __future__ import annotations

from pathlib import Path


def asset_path(name: str) -> Path:
    return Path(__file__).resolve().parent / name


def logo_path() -> Path:
    """Prefer the original dot-matrix brand mark; fall back to logo.png."""
    mark = asset_path("brand_mark.png")
    if mark.is_file():
        return mark
    return asset_path("logo.png")


def brand_mark_path() -> Path:
    return asset_path("brand_mark.png")
