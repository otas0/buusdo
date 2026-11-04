"""User-initiated companion pairing dialog (LAN URL + code)."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from buusdo.companion.devices import clear_devices, list_devices, remove_device
from buusdo.companion.host import CompanionHost
from buusdo.companion.netinfo import companion_base_url
from buusdo.companion.pairing import PairingDesk
from buusdo.companion.transport import CompanionTransport
from buusdo.core.config_store import get_companion_loopback_only, set_companion_loopback_only
from buusdo.core.i18n import t


class CompanionDialog(QDialog):
    """Start/stop LAN companion host; show pairing code only after user clicks Start."""

    def __init__(
        self,
        parent=None,
        *,
        host: CompanionHost,
        transport: CompanionTransport,
        pairing: PairingDesk,
    ) -> None:
        super().__init__(parent)
        self._host = host
        self._transport = transport
        self._pairing = pairing
        self.setObjectName("instrumentDialog")
        self.setWindowTitle(t("companion.title"))
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        intro = QLabel(t("companion.intro"))
        intro.setWordWrap(True)
        intro.setObjectName("brandSubtitle")
        layout.addWidget(intro)

        self._url = QLabel(t("companion.url_idle"))
        self._url.setWordWrap(True)
        self._url.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._url)

        self._code = QLabel(t("companion.code_idle"))
        self._code.setObjectName("sectionLabel")
        self._code.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._code)

        warn = QLabel(t("companion.no_cloud"))
        warn.setWordWrap(True)
        warn.setObjectName("brandSubtitle")
        layout.addWidget(warn)

        self._loopback = QCheckBox(t("companion.loopback_only"))
        preferred = get_companion_loopback_only() or self._transport.loopback_only
        self._loopback.setChecked(preferred)
        self._loopback.setToolTip(t("companion.loopback_hint"))
        layout.addWidget(self._loopback)

        row = QHBoxLayout()
        self._btn_start = QPushButton(t("companion.start"))
        self._btn_start.setObjectName("accentAction")
        self._btn_start.clicked.connect(self._start_pairing)
        self._btn_stop = QPushButton(t("companion.stop"))
        self._btn_stop.clicked.connect(self._stop_pairing)
        row.addWidget(self._btn_start)
        row.addWidget(self._btn_stop)
        layout.addLayout(row)

        devices_hdr = QLabel(t("companion.devices"))
        devices_hdr.setObjectName("sectionLabel")
        layout.addWidget(devices_hdr)
        self._devices = QListWidget()
        layout.addWidget(self._devices)

        dev_row = QHBoxLayout()
        self._btn_unpair = QPushButton(t("companion.unpair"))
        self._btn_unpair.clicked.connect(self._unpair_selected)
        self._btn_clear = QPushButton(t("companion.clear_all"))
        self._btn_clear.clicked.connect(self._clear_all)
        close = QPushButton(t("companion.close"))
        close.setObjectName("primaryAction")
        close.setDefault(True)
        close.clicked.connect(self.accept)
        dev_row.addWidget(self._btn_unpair)
        dev_row.addWidget(self._btn_clear)
        dev_row.addWidget(close)
        layout.addLayout(dev_row)

        self._refresh_devices()
        self._sync_running_ui()

    def _start_pairing(self) -> None:
        try:
            loopback = self._loopback.isChecked()
            self._transport.set_loopback_only(loopback)
            set_companion_loopback_only(loopback)
            self._transport.start()
        except Exception as exc:
            self._transport.last_error = str(exc)
            QMessageBox.warning(self, t("companion.title"), str(exc))
            self._sync_running_ui()
            return
        session = self._pairing.start()
        host = "127.0.0.1" if self._transport.loopback_only else None
        base = companion_base_url(host=host, port=self._transport.port)
        self._url.setText(t("companion.url_active", url=base))
        self._code.setText(t("companion.code_active", code=session.code))
        self._sync_running_ui()

    def _stop_pairing(self) -> None:
        self._transport.stop()
        self._url.setText(t("companion.url_idle"))
        self._code.setText(t("companion.code_idle"))
        self._sync_running_ui()

    def _sync_running_ui(self) -> None:
        running = self._transport.running
        self._btn_start.setEnabled(not running)
        self._btn_stop.setEnabled(running)
        self._loopback.setEnabled(not running)

    def _refresh_devices(self) -> None:
        self._devices.clear()
        for d in list_devices():
            self._devices.addItem(f"{d.label} · {d.device_id} · {d.paired_at}")
            self._devices.item(self._devices.count() - 1).setData(Qt.ItemDataRole.UserRole, d.device_id)
        self._host.paired = bool(list_devices())

    def _unpair_selected(self) -> None:
        item = self._devices.currentItem()
        if item is None:
            return
        device_id = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if device_id:
            remove_device(device_id)
        self._refresh_devices()

    def _clear_all(self) -> None:
        if (
            QMessageBox.question(self, t("companion.title"), t("companion.clear_confirm"))
            != QMessageBox.StandardButton.Yes
        ):
            return
        clear_devices()
        self._refresh_devices()

    def closeEvent(self, event) -> None:  # noqa: N802
        # Leave transport running if user started it; only clear ephemeral code on stop.
        super().closeEvent(event)


def show_companion_dialog(
    parent=None,
    *,
    host: CompanionHost,
    transport: CompanionTransport,
    pairing: PairingDesk,
) -> None:
    dlg = CompanionDialog(parent, host=host, transport=transport, pairing=pairing)
    dlg.exec()


def make_desktop_companion_host(
    *,
    request_scan: Callable[[], str] | None = None,
) -> CompanionHost:
    """Factory wired to recent games + history (read-only)."""
    from buusdo.core.history import list_events
    from buusdo.core.i18n import t as translate
    from buusdo.core.recent_games import list_recent

    def recent_names() -> list[str]:
        return [str(g.get("name") or g.get("app_id") or "") for g in list_recent()][:20]

    def history_summary() -> str:
        events = list_events(limit=5)
        if not events:
            return ""
        parts = []
        for ev in events:
            status = "ok" if ev.get("success") else "fail"
            parts.append(f"{ev.get('action')}:{status}:{ev.get('target')}")
        return "; ".join(parts)

    return CompanionHost(
        host_label="desktop",
        paired=bool(list_devices()),
        request_scan=request_scan,
        history_summary=history_summary,
        recent_names=recent_names,
        translate=translate,
    )
