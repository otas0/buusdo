"""Batch AF: selection clear helper; verify --json; steam exhaust disables next."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from buusdo.core.steam_uris import try_steam_uri_candidate
from buusdo.ui.selection_utils import clear_row_selections


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_try_steam_uri_exhaust_remaining_zero() -> None:
    uris = ["steam://a/1", "steam://b/1"]

    def fail(_u: str) -> bool:
        return False

    r0 = try_steam_uri_candidate(uris, 0, opener=fail, cache_success=False)
    r1 = try_steam_uri_candidate(uris, r0["next_index"], opener=fail, cache_success=False)
    assert r1["exhausted"] is True
    assert r1["remaining"] == 0
    assert r1["next_index"] == 2


def test_verify_dwm_hdr_poc_local_json(tmp_path: Path, capsys) -> None:
    mod = _load("verify_dwm_hdr_poc_local", Path("scripts/verify_dwm_hdr_poc_local.py"))
    out = tmp_path / "poc"
    assert mod.main(["--out", str(out), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["ok"] is True
    assert payload["entries"]
    assert all(e["match"] for e in payload["entries"])


def test_clear_row_selections_list_and_table() -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QListWidget, QListWidgetItem, QTableWidget

    app = QApplication.instance() or QApplication([])
    lst = QListWidget()
    lst.addItem(QListWidgetItem("a"))
    lst.addItem(QListWidgetItem("b"))
    lst.setCurrentRow(1)
    table = QTableWidget(2, 2)
    table.setCurrentCell(1, 0)
    assert lst.currentRow() == 1
    assert table.currentRow() == 1
    clear_row_selections(lst, table)
    app.processEvents()
    assert lst.currentRow() == -1
    assert table.currentRow() == -1
    assert lst.selectedItems() == []
