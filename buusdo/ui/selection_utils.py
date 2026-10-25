"""Small Qt selection helpers (testable without MainWindow)."""

from __future__ import annotations

from typing import Any


def clear_row_selections(*widgets: Any) -> None:
    """Clear list/table current selection and current index/cell."""
    for w in widgets:
        if w is None:
            continue
        clearer = getattr(w, "clearSelection", None)
        if callable(clearer):
            clearer()
        set_row = getattr(w, "setCurrentRow", None)
        if callable(set_row):
            set_row(-1)
        set_cell = getattr(w, "setCurrentCell", None)
        if callable(set_cell):
            set_cell(-1, -1)
