"""Bundled static assets (logo, etc.)."""

from __future__ import annotations

from pathlib import Path


def asset_path(name: str) -> Path:
    return Path(__file__).resolve().parent / name


def logo_path() -> Path:
    return asset_path("logo.png")
