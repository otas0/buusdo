"""Redirect user config / history into a temp dir for every test."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_user_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = tmp_path / "buusdo-config"
    cfg.mkdir()
    monkeypatch.setattr("buusdo.core.platform_detect.user_config_dir", lambda platform=None: cfg)
    monkeypatch.setattr("buusdo.core.config_store.user_config_dir", lambda: cfg)
    monkeypatch.setattr("buusdo.core.history.user_config_dir", lambda: cfg)
