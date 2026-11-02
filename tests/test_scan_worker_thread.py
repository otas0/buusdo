"""Scan worker must deliver UI updates onto the GUI thread via QObject slots."""

from __future__ import annotations

import pytest


def test_start_scan_connects_qobject_slots_queued(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QObject, Qt, Slot
    from PySide6.QtWidgets import QApplication

    from buusdo.ui import scan_worker as sw

    app = QApplication.instance() or QApplication([])

    seen: list[tuple[object, object]] = []

    class FakeSignal:
        def connect(self, slot, connection_type=None):  # noqa: ANN001
            seen.append((slot, connection_type))

    class FakeWorker:
        progress = FakeSignal()
        finished = FakeSignal()
        failed = FakeSignal()

        def __init__(self, *, force: bool = False) -> None:
            self.force = force

        def run(self) -> None:
            return None

        def moveToThread(self, _thread) -> None:  # noqa: ANN001, N802
            return None

        def deleteLater(self) -> None:  # noqa: N802
            return None

    class FakeThread:
        started = FakeSignal()
        finished = FakeSignal()

        def start(self) -> None:
            return None

        def quit(self) -> None:
            return None

        def deleteLater(self) -> None:  # noqa: N802
            return None

    class Receiver(QObject):
        @Slot(str, float)
        def on_scan_progress(self, _stage: str, _value: float) -> None:
            return None

        @Slot(list)
        def on_scan_finished(self, _games: list) -> None:
            return None

        @Slot(str)
        def on_scan_failed(self, _message: str) -> None:
            return None

    monkeypatch.setattr(sw, "QThread", FakeThread)
    monkeypatch.setattr(sw, "ScanWorker", FakeWorker)

    receiver = Receiver()
    sw.start_scan(force=True, receiver=receiver)

    queued = Qt.ConnectionType.QueuedConnection
    ui_slots = {
        receiver.on_scan_progress,
        receiver.on_scan_finished,
        receiver.on_scan_failed,
    }
    ui_conns = [(slot, ct) for slot, ct in seen if slot in ui_slots]
    assert len(ui_conns) == 3
    assert all(ct == queued for _, ct in ui_conns)

    with pytest.raises(TypeError):
        sw.start_scan(force=False, receiver="not-a-qobject")  # type: ignore[arg-type]

    app.processEvents()


def test_cancel_ignores_late_progress(qtbot=None) -> None:  # noqa: ANN001
    """After cancel, progress must not touch the progress bar."""
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QObject, Signal, Slot
    from PySide6.QtWidgets import QApplication, QProgressBar

    app = QApplication.instance() or QApplication([])

    class FakeWorker(QObject):
        progress = Signal(str, float)
        finished = Signal(list)
        failed = Signal(str)

        def cancel(self) -> None:
            return None

    class Host(QObject):
        def __init__(self) -> None:
            super().__init__()
            self._scan_accepting = True
            self._scan_generation = 1
            self._scan_worker: FakeWorker | None = FakeWorker()
            self._scan_worker.setProperty("scanGeneration", 1)
            self._progress = QProgressBar()
            self._progress.setValue(0)
            self._touched = 0

        @Slot(str, float)
        def on_scan_progress(self, stage: str, value: float) -> None:
            from buusdo.ui.scan_worker import assert_gui_thread

            assert_gui_thread("test_progress")
            if not self._scan_accepting:
                return
            self._touched += 1
            self._progress.setValue(int(value * 100))

        def cancel_like_main_window(self) -> None:
            self._scan_accepting = False
            self._scan_generation += 1
            if self._scan_worker is not None:
                self._scan_worker.cancel()
            self._progress.setValue(0)

    host = Host()
    worker = host._scan_worker
    assert worker is not None
    worker.progress.connect(host.on_scan_progress)

    worker.progress.emit("mid", 0.4)
    app.processEvents()
    assert host._touched == 1
    assert host._progress.value() == 40

    host.cancel_like_main_window()
    worker.progress.emit("late", 0.9)
    app.processEvents()
    assert host._touched == 1
    assert host._progress.value() == 0
