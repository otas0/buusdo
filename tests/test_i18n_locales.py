"""Locale catalogs: monolingual coverage + English-only fallback."""

from __future__ import annotations

import json
from pathlib import Path

from buusdo.core.i18n import (
    available_locales,
    filter_locales,
    locale_display_name,
    reload_catalogs,
    set_locale,
    t,
)

LOCALES = Path(__file__).resolve().parents[1] / "buusdo" / "locales"


def test_locale_files_match_en_keys() -> None:
    en = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))
    assert "lang.pick_title" in en
    assert "wizard.skip" in en
    for path in sorted(LOCALES.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) == set(en), path.name


def test_available_locales_include_mainstream() -> None:
    reload_catalogs()
    codes = available_locales()
    for need in ("en", "zh", "zh-Hant", "ja", "pt-BR", "es", "de", "fr", "ko", "ru", "it", "pt"):
        assert need in codes, need


def test_monolingual_fallback_is_english_not_zh() -> None:
    reload_catalogs()
    set_locale("en")
    en_scan = t("action.scan")
    set_locale("ja")
    ja_scan = t("action.scan")
    assert ja_scan != en_scan
    # Missing key must not pull Chinese
    set_locale("ja")
    missing = t("__does_not_exist__")
    assert missing == "__does_not_exist__"


def test_filter_locales_search() -> None:
    reload_catalogs()
    hits = filter_locales("portug")
    assert "pt" in hits or "pt-BR" in hits
    assert locale_display_name("ja") == "日本語"
    assert "ja" in filter_locales("日本語")
    assert "zh-Hant" in filter_locales("繁體中文")


def test_support_os_names_three_platforms() -> None:
    reload_catalogs()
    for code in ("en", "zh", "ja", "pt-BR"):
        set_locale(code)
        text = t("about.support_os")
        assert "Windows" in text
        assert "Linux" in text
        assert "macOS" in text or "MacOS" in text
