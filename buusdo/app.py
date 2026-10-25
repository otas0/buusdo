"""Application entrypoint."""

from __future__ import annotations

import sys

from buusdo.backends import get_backend
from buusdo.core.errors import BuusdoError


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            "PySide6 is required to launch the UI. Install with: pip install 'buusdo[ui]'",
            file=sys.stderr,
        )
        return 1

    from buusdo.ui.main_window import MainWindow

    app = QApplication(argv)
    app.setApplicationName("buusdo")
    try:
        backend = get_backend()
    except BuusdoError as exc:
        print(exc, file=sys.stderr)
        return 1
    window = MainWindow(backend=backend)
    window.show()
    return app.exec()
