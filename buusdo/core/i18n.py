"""Locale catalogs for UI copy (C4-honest). One active language at a time.

Catalogs live in ``buusdo/locales/*.json``. Missing keys fall back to **English
only** — never to another language — so the UI stays monolingual.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# (code, native display name, search haystack)
_LOCALE_META: list[tuple[str, str, str]] = [
    ("en", "English", "english en"),
    ("zh", "简体中文", "chinese simplified zh hans 简体"),
    ("zh-Hant", "繁體中文", "chinese traditional zh hant 繁体 繁體 繁體中文"),
    ("ja", "日本語", "japanese ja にほんご 日本語"),
    ("ko", "한국어", "korean ko 한국"),
    ("pt-BR", "Português (Brasil)", "portuguese brazil brasil pt-br"),
    ("pt", "Português", "portuguese portugal pt"),
    ("es", "Español", "spanish castellano es"),
    ("de", "Deutsch", "german deutsch de"),
    ("fr", "Français", "french francais fr"),
    ("it", "Italiano", "italian italiano it"),
    ("ru", "Русский", "russian русский ru"),
]

_LOCALE = "en"
_STRINGS: dict[str, dict[str, str]] = {}


def _locales_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "locales"


@lru_cache(maxsize=1)
def _load_all() -> dict[str, dict[str, str]]:
    root = _locales_dir()
    out: dict[str, dict[str, str]] = {}
    if not root.is_dir():
        return out
    for path in sorted(root.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data:
            out[path.stem] = {str(k): str(v) for k, v in data.items()}
    return out


def reload_catalogs() -> None:
    """Clear cache and refresh in-memory tables (tests / hot reload)."""
    global _STRINGS
    _load_all.cache_clear()
    _STRINGS = dict(_load_all())


def catalogs() -> dict[str, dict[str, str]]:
    """Return loaded locale → strings (loads on first use)."""
    _ensure_loaded()
    return _STRINGS


def _ensure_loaded() -> None:
    global _STRINGS
    if not _STRINGS:
        _STRINGS = dict(_load_all())


def set_locale(locale: str) -> None:
    global _LOCALE
    _ensure_loaded()
    if locale not in _STRINGS and locale not in {c for c, _, _ in _LOCALE_META}:
        raise ValueError(f"Unsupported locale: {locale}")
    if locale not in _STRINGS:
        raise ValueError(f"Locale catalog missing: {locale}")
    _LOCALE = locale


def get_locale() -> str:
    return _LOCALE


def t(key: str, **kwargs: Any) -> str:
    _ensure_loaded()
    table = _STRINGS.get(_LOCALE) or {}
    # Monolingual fallback: English only (never bleed zh into other locales).
    text = table.get(key) or (_STRINGS.get("en") or {}).get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def available_locales() -> list[str]:
    _ensure_loaded()
    meta_codes = [c for c, _, _ in _LOCALE_META if c in _STRINGS]
    extras = sorted(c for c in _STRINGS if c not in meta_codes)
    return meta_codes + extras


def locale_display_name(code: str) -> str:
    for c, name, _ in _LOCALE_META:
        if c == code:
            return name
    _ensure_loaded()
    return (_STRINGS.get(code) or {}).get("lang.name") or code


def locale_search_blob(code: str) -> str:
    for c, name, hay in _LOCALE_META:
        if c == code:
            return f"{c} {name} {hay}".lower()
    return f"{code} {locale_display_name(code)}".lower()


def filter_locales(query: str) -> list[str]:
    """Return available locale codes matching *query* (empty → all)."""
    codes = available_locales()
    q = (query or "").strip().lower()
    if not q:
        return codes
    return [c for c in codes if q in locale_search_blob(c)]
