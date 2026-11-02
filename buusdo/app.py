"""Application entrypoint."""

from __future__ import annotations

import sys

from buusdo.backends import get_backend
from buusdo.core.crash_report import capture_exception
from buusdo.core.errors import BuusdoError
from buusdo.macos_name import ensure_process_name


def main(argv: list[str] | None = None) -> int:
    # Before Qt: Dock/menu should say "buusdo", not "Python".
    ensure_process_name("buusdo")

    argv = list(sys.argv if argv is None else argv)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            "PySide6 is required to launch the UI. Install with: pip install 'buusdo[ui]'",
            file=sys.stderr,
        )
        return 1

    from buusdo.core.config_store import load_settings
    from buusdo.ui.main_window import MainWindow
    from buusdo.ui.theme import ThemeName, apply_theme
    from buusdo.ui.tray_icon import app_icon

    app = QApplication(argv)
    app.setApplicationName("buusdo")
    app.setApplicationDisplayName("buusdo")
    app.setOrganizationName("buusdo")
    app.setOrganizationDomain("buusdo.app")

    settings = load_settings()
    mode: ThemeName = "dark" if settings.get("ui_theme") == "dark" else "light"
    apply_theme(app, mode)

    # On macOS, Qt setWindowIcon replaces the Dock tile with a hard square
    # (system squircle mask is skipped). Launch via Buusdo.app so Dock uses
    # CFBundleIconFile / AppIcon.icns instead.
    if sys.platform != "darwin":
        app.setWindowIcon(app_icon())

    try:
        backend = get_backend()
    except BuusdoError as exc:
        capture_exception(exc, context={"op": "startup"})
        print(exc, file=sys.stderr)
        return 1
    window = MainWindow(backend=backend)
    window.show()
    return app.exec()
