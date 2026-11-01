"""Batch AI: brand mark; primary/accent actions; CI uv sync; dialog chrome."""

from __future__ import annotations

from pathlib import Path

import pytest

from buusdo.assets import brand_mark_path, logo_path


def test_brand_mark_asset_exists() -> None:
    path = brand_mark_path()
    assert path.is_file()
    assert path.stat().st_size > 50


def test_logo_path_prefers_logo_png() -> None:
    path = logo_path()
    assert path.is_file()
    assert path.name == "logo.png"
    assert path.stat().st_size > 50


def test_ci_uses_uv_sync_extra_devui() -> None:
    ci = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "astral-sh/setup-uv" in ci
    assert "uv sync --extra devui" in ci
    assert "uv sync --extra dev" in ci
    assert "uv run pytest" in ci


def test_main_window_action_roles() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from buusdo.core.backend import (
        Capability,
        EnhancementBackend,
        EnhancementTarget,
        InstallResult,
    )
    from buusdo.ui.main_window import MainWindow
    from buusdo.ui.theme import apply_product_theme

    class Stub(EnhancementBackend):
        def platform_id(self) -> str:
            return "macos"

        def discover_games(self, *, should_cancel=None, progress=None):
            return []

        def list_capabilities(self, target: EnhancementTarget):
            return []

        def install(self, target, options=None):
            return InstallResult(True, "ok")

        def uninstall(self, target):
            return InstallResult(True, "ok")

        def status(self, target):
            return {}

    app = QApplication.instance() or QApplication([])
    apply_product_theme(app)
    win = MainWindow(backend=Stub())
    assert win._btn_install.objectName() == "primaryAction"
    assert win._btn_scan.objectName() == "accentAction"
    assert win._btn_complete_kits.objectName() == "accentAction"
    win.close()


def test_ci_artifacts_one_dispatch_policy() -> None:
    text = Path("docs/CI_ARTIFACTS.md").read_text(encoding="utf-8")
    assert "one" in text.lower() and "workflow_dispatch" in text
    assert "LaunchAgent" in text
    assert "agent-poll" in text or "Do not agent-poll" in text
