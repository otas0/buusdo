"""Companion loopback preference in settings.json."""

from __future__ import annotations

from pathlib import Path

import pytest

from buusdo.core import config_store as store


@pytest.fixture()
def cfg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(store, "user_config_dir", lambda: tmp_path)
    return tmp_path


def test_companion_loopback_default_false(cfg: Path) -> None:
    assert store.get_companion_loopback_only() is False


def test_companion_loopback_roundtrip(cfg: Path) -> None:
    store.set_companion_loopback_only(True)
    assert store.get_companion_loopback_only() is True
    raw = (cfg / "settings.json").read_text(encoding="utf-8")
    assert "companion_loopback_only" in raw
    store.set_companion_loopback_only(False)
    assert store.get_companion_loopback_only() is False
