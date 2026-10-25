"""Application entrypoint."""

from __future__ import annotations

import sys

from buusdo.backends import get_backend
from buusdo.core.errors import BuusdoError


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    try:
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            "PySide6 is required to launch the UI. Install with: pip install 'buusdo[ui]'",
            file=sys.stderr,
        )
        return 1

    from buusdo.assets import logo_path
    from buusdo.ui.main_window import MainWindow
    from buusdo.ui.theme import apply_dark_theme

    app = QApplication(argv)
    app.setApplicationName("buusdo")
    apply_dark_theme(app)
    logo = logo_path()
    if logo.is_file():
        app.setWindowIcon(QIcon(str(logo)))
    try:
        backend = get_backend()
    except BuusdoError as exc:
        print(exc, file=sys.stderr)
        return 1
    window = MainWindow(backend=backend)
    window.show()
    return app.exec()
