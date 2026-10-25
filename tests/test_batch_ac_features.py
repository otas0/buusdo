"""Batch AC: schema-drift JSONL gate; steam try-first index copy shape."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from buusdo.core.i18n import t


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_conflict_export_schema_drift_script() -> None:
    mod = _load(
        "check_conflict_export_schema_drift",
        Path("scripts/check_conflict_export_schema_drift.py"),
    )
    assert mod.main() == 0


def test_steam_try_first_status_includes_index() -> None:
    msg = t(
        "settings.steam_uri_try_first_ok",
        index=1,
        total=5,
        uri="steam://url/GameHub/570",
    )
    assert "[1/5]" in msg
    assert "GameHub/570" in msg
