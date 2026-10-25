"""Background Steam library scan worker with cancel support."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from buusdo.backends import get_backend
from buusdo.core.backend import EnhancementTarget
from buusdo.core.library_cache import invalidate_cache


class ScanWorker(QObject):
    progress = Signal(str, float)
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, *, force: bool = False):
        super().__init__()
        self._force = force
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        try:
            if self._force:
                invalidate_cache()
            if self._cancel:
                self.failed.emit("cancelled")
                return
            self.progress.emit("start", 0.0)
            backend = get_backend()
            self.progress.emit("discover", 0.3)
            if self._cancel:
                self.failed.emit("cancelled")
                return
            games: list[EnhancementTarget] = backend.discover_games()
            if self._cancel:
                self.failed.emit("cancelled")
                return
            self.progress.emit("done", 1.0)
            self.finished.emit(games)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


def start_scan(*, force: bool, on_progress, on_finished, on_failed) -> tuple[QThread, ScanWorker]:
    thread = QThread()
    worker = ScanWorker(force=force)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.progress.connect(on_progress)
    worker.finished.connect(on_finished)
    worker.failed.connect(on_failed)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    worker.failed.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()
    return thread, worker
