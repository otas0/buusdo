"""Background Steam library scan worker with cancel support.

UI receivers MUST be QObject methods living on the GUI thread. Connecting a
bare Python callable — even with QueuedConnection — posts into the *worker*
QThread event loop under PySide, which then mutates widgets off-thread and
SEGVs (recursive paint / null paint device).
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot

from buusdo.backends import get_backend
from buusdo.core.backend import EnhancementTarget
from buusdo.core.discovery import DiscoveryCancelled
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

    @Slot()
    def run(self) -> None:
        try:
            if self._force:
                invalidate_cache()
            if self._cancel:
                self.failed.emit("cancelled")
                return
            self.progress.emit("start", 0.0)
            backend = get_backend()

            def should_cancel() -> bool:
                return self._cancel

            last_pct = -1

            def on_progress(stage: str, value: float) -> None:
                nonlocal last_pct
                # Coalesce floods: only emit when integer percent changes.
                pct = int(max(0, min(100, float(value) * 100)))
                if pct == last_pct and not str(stage).startswith("resume:"):
                    return
                last_pct = pct
                self.progress.emit(str(stage), float(value))

            games: list[EnhancementTarget] = backend.discover_games(
                should_cancel=should_cancel, progress=on_progress
            )
            if self._cancel:
                self.failed.emit("cancelled")
                return
            self.progress.emit("done", 1.0)
            # Plain dicts only — Path/dataclass objects are unsafe across QueuedConnection.
            self.finished.emit([g.to_payload() for g in games])
        except DiscoveryCancelled:
            self.failed.emit("cancelled")
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


def assert_gui_thread(context: str = "") -> None:
    """Raise if called off the QApplication thread (debug / test guard)."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        return
    if QThread.currentThread() is not app.thread():
        where = f" ({context})" if context else ""
        raise RuntimeError(f"UI update off GUI thread{where}")


def start_scan(
    *,
    force: bool,
    receiver: QObject,
    on_progress: str = "on_scan_progress",
    on_finished: str = "on_scan_finished",
    on_failed: str = "on_scan_failed",
) -> tuple[QThread, ScanWorker]:
    """Start a scan; *receiver* must be a GUI-thread QObject with named slots."""
    if not isinstance(receiver, QObject):
        raise TypeError("start_scan requires a QObject receiver (GUI-thread slots)")

    thread = QThread()
    worker = ScanWorker(force=force)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)

    progress_slot = getattr(receiver, on_progress)
    finished_slot = getattr(receiver, on_finished)
    failed_slot = getattr(receiver, on_failed)

    # AutoConnection is correct once the receiver is a QObject on the GUI thread;
    # force Queued as belt-and-suspenders against affinity mistakes.
    queued = Qt.ConnectionType.QueuedConnection
    worker.progress.connect(progress_slot, queued)
    worker.finished.connect(finished_slot, queued)
    worker.failed.connect(failed_slot, queued)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()
    return thread, worker
