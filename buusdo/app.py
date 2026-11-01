"""Application entrypoint."""

from __future__ import annotations

import sys

from buusdo.backends import get_backend
from buusdo.core.crash_report import capture_exception
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
    from buusdo.ui.theme import apply_dark_theme
    from buusdo.ui.tray_icon import app_icon

    app = QApplication(argv)
    app.setApplicationName("buusdo")
    apply_dark_theme(app)
    icon = app_icon()
    app.setWindowIcon(icon)
    try:
        backend = get_backend()
    except BuusdoError as exc:
        capture_exception(exc, context={"op": "startup"})
        print(exc, file=sys.stderr)
        return 1
    window = MainWindow(backend=backend)
    window.show()
    return app.exec()
