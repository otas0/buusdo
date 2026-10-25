"""Batch AD: docs language gate; schema-drift step summary; steam try-next index."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from buusdo.core.i18n import t


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_check_docs_language_clean() -> None:
    mod = _load("check_docs_language", Path("scripts/check_docs_language.py"))
    assert mod.main() == 0


def test_schema_drift_writes_step_summary(tmp_path: Path, monkeypatch) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    mod = _load(
        "check_conflict_export_schema_drift",
        Path("scripts/check_conflict_export_schema_drift.py"),
    )
    assert mod.main() == 0
    text = summary.read_text(encoding="utf-8")
    assert "Conflict-export schema drift" in text
    assert "schema_version" in text
    assert "```json" in text


def test_steam_try_next_and_exhausted_copy() -> None:
    assert "Try next" in t("settings.steam_uri_try_next") or "试开" in t(
        "settings.steam_uri_try_next"
    )
    assert "3" in t("settings.steam_uri_try_exhausted", total=3)
