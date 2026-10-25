"""UI smoke: blocked page has no continue/bypass button.

Requires PySide6 (`pip install -e '.[devui]'`). Skips otherwise.
"""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QPushButton  # noqa: E402

from buusdo.core.errors import UnsafeTargetError  # noqa: E402
from buusdo.ui.blocked_page import BlockedPage  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_blocked_page_has_no_continue_button(qapp) -> None:
    err = UnsafeTargetError("Game", "anti-cheat detected", evidence=["path:EAC"])
    page = BlockedPage(err)
    page.show()
    qapp.processEvents()
    buttons = page.findChildren(QPushButton)
    texts = " ".join(b.text() for b in buttons).lower()
    assert buttons == [] or ("continue" not in texts and "继续" not in texts and "已知晓" not in texts)
    assert page.objectName() == "blockedPage"
