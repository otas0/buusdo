"""Monolingual UI quality: no bilingual slash labels; pt vs pt-BR; layout budgets."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from buusdo.core.i18n import catalogs, reload_catalogs, set_locale, t

LOCALES = Path(__file__).resolve().parents[1] / "buusdo" / "locales"

# Chrome / button strings that must stay short enough for the top bar.
_CHROME_KEYS = (
    "action.scan",
    "action.force_scan",
    "action.cancel_scan",
    "action.deploy",
    "action.uninstall",
    "about.button",
    "theme.to_dark",
    "theme.to_light",
    "lang.button",
    "wizard.skip",
    "wizard.done",
    "lang.confirm",
)


def test_no_bilingual_slash_labels() -> None:
    """Catch 'Skip / 跳过' dual chrome labels — not product 'A / B' separators."""
    reload_catalogs()
    dual = re.compile(
        r"(?i)\b(skip|done|cancel|continue|language|dark|light|scan|deploy|uninstall|"
        r"about|ok|yes|no)\b\s*/\s*[\u3400-\u9fff]"
        r"|[\u3400-\u9fff]{1,8}\s*/\s*\b(skip|done|cancel|continue|language|dark|light|"
        r"scan|deploy|uninstall|about|ok|yes|no)\b"
    )
    for code, table in catalogs().items():
        for key, text in table.items():
            assert not dual.search(text), f"{code}:{key}={text!r}"


def test_cjk_locales_are_not_english_ui() -> None:
    reload_catalogs()
    for code in ("zh", "zh-Hant", "ja", "ko"):
        set_locale(code)
        scan = t("action.scan")
        skip = t("wizard.skip")
        assert scan != "Scan Steam library"
        assert skip != "Skip"
        # Must contain CJK for these locales
        assert re.search(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]", scan + skip)


def test_pt_br_ja_zh_hant_monolingual_chrome() -> None:
    """Switching to pt-BR / ja / zh-Hant must not leave Chinese or English chrome."""
    reload_catalogs()
    zh_skip = catalogs()["zh"]["wizard.skip"]
    en_skip = catalogs()["en"]["wizard.skip"]
    for code in ("pt-BR", "ja", "zh-Hant"):
        set_locale(code)
        skip = t("wizard.skip")
        confirm = t("lang.confirm")
        lang_btn = t("lang.button")
        assert skip not in (en_skip, zh_skip) or code.startswith("zh")
        if code == "zh-Hant":
            assert skip != en_skip
            assert "跳过" not in skip  # simplified must not bleed into Hant chrome
        if code == "ja":
            assert skip != zh_skip and skip != en_skip
            assert re.search(r"[\u3040-\u30ff]", skip + confirm + lang_btn)
        if code == "pt-BR":
            assert skip == "Ignorar"
            assert confirm == "Continuar"
            assert not re.search(r"[\u3400-\u9fff]", skip + confirm + lang_btn)


def test_latin_locales_have_no_han() -> None:
    reload_catalogs()
    han = re.compile(r"[\u3400-\u9fff]")
    for code in ("en", "pt", "pt-BR", "es", "de", "fr", "it", "ru"):
        table = catalogs()[code]
        for key, text in table.items():
            if key == "lang.name":
                continue
            assert not han.search(text), f"{code}:{key} has Han: {text!r}"


def test_pt_vs_pt_br_terminology() -> None:
    pt = json.loads((LOCALES / "pt.json").read_text(encoding="utf-8"))
    br = json.loads((LOCALES / "pt-BR.json").read_text(encoding="utf-8"))
    # European Portuguese preferences
    assert "ecrã" in pt["action.clear_display_session"].lower()
    assert "guardar" in pt["wizard.save_failed"].lower()
    assert "definições" in pt["wizard.save_failed"].lower()
    assert "directório" in pt["msg.reshade_proton"].lower()
    assert "diretório" not in pt["msg.reshade_proton"].lower()
    assert "ficheiro" in pt["linux.config_path"].lower()
    assert "arquivo" not in pt["linux.config_path"].lower()
    assert "sistema operativo" in pt["about.support_os"].lower()
    # Brazilian preferences
    assert "salvar" in br["wizard.save_failed"].lower()
    assert "configurações" in br["wizard.save_failed"].lower()
    assert "tela" in br["display.retry_one"].lower()
    assert "diretório" in br["msg.reshade_proton"].lower()
    assert "directório" not in br["msg.reshade_proton"].lower()
    assert "arquivo" in br["linux.config_path"].lower()
    assert "ficheiro" not in br["linux.config_path"].lower()
    assert "sistema operacional" in br["about.support_os"].lower()


def test_chrome_string_length_budget_de_ru() -> None:
    """Top-bar / primary actions should stay within a conservative glyph budget."""
    reload_catalogs()
    for code in ("de", "ru", "en"):
        set_locale(code)
        for key in _CHROME_KEYS:
            text = t(key)
            # Soft budget: primary row buttons wrap poorly above ~42 glyphs.
            assert len(text) <= 42, f"{code}:{key} too long ({len(text)}): {text}"


def test_cap_experimental_is_capability_badge_only() -> None:
    """Platform support copy must not brand the whole OS as experimental."""
    reload_catalogs()
    for code in catalogs():
        set_locale(code)
        support = t("about.support_os").lower()
        assert "experimental" not in support
        assert "实验" not in support
        # Badge string itself may still exist for per-capability titles
        assert t("cap.experimental")
    linux = Path("buusdo/backends/linux.py").read_text(encoding="utf-8")
    macos = Path("buusdo/backends/macos.py").read_text(encoding="utf-8")
    assert 't("cap.experimental")' in linux
    assert 't("cap.experimental")' in macos
    assert "title=f\"{t('cap.vkbasalt')} ({exp})\"" in linux or "({exp})" in linux
    mac_doc = Path("docs/MAC_PACKAGE.md").read_text(encoding="utf-8")
    assert mac_doc.lstrip().lower().startswith("# macos package track (config-only)")
