"""Main window — backend-agnostic (C3)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from buusdo.assets import logo_path
from buusdo.backends import get_backend
from buusdo.core.backend import EnhancementBackend, EnhancementTarget
from buusdo.core.config_store import (
    export_configs,
    get_optiscaler_kit_path,
    get_reshade_kit_path,
    import_configs,
    load_settings,
    save_settings,
    set_optiscaler_kit_path,
    set_reshade_kit_path,
    update_game_config,
)
from buusdo.core.conflict_preview import (
    preview_optiscaler_deploy,
    preview_reshade_deploy,
    preview_triple_matrix,
)
from buusdo.core.crash_report import capture_exception
from buusdo.core.errors import BuusdoError, UnsafeTargetError
from buusdo.core.graphics_detect import GraphicsApi
from buusdo.core.history import list_events
from buusdo.core.i18n import available_locales, get_locale, set_locale, t
from buusdo.core.platform_detect import steam_roots
from buusdo.core.recent_games import list_recent
from buusdo.core.steam_launch import list_steam_users
from buusdo.ui.blocked_page import BlockedPage
from buusdo.ui.scan_worker import start_scan
from buusdo.ui.theme import badge_color
from buusdo.ui.tray_icon import make_mark_icon
from buusdo.ui.wizard import FirstRunWizard, needs_wizard


class MainWindow(QMainWindow):
    def __init__(self, backend: EnhancementBackend | None = None):
        super().__init__()
        self.setWindowTitle("buusdo")
        self.resize(980, 720)

        logo = logo_path()
        if logo.is_file():
            self.setWindowIcon(QIcon(str(logo)))

        self._backend = backend or get_backend()
        self._target: EnhancementTarget | None = None
        self._games: list[EnhancementTarget] = []
        self._filtered: list[EnhancementTarget] = []
        self._scan_thread = None
        self._scan_worker = None

        settings = load_settings()
        if settings.get("locale") in available_locales():
            set_locale(settings["locale"])

        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)

        brand = QHBoxLayout()
        logo_label = QLabel()
        logo_label.setAccessibleName("buusdo logo")
        if logo.is_file():
            pix = QPixmap(str(logo)).scaledToHeight(48, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pix)
        else:
            logo_label.setText("buusdo")
        brand.addWidget(logo_label)
        brand_text = QVBoxLayout()
        title = QLabel("buusdo")
        tf = title.font()
        tf.setPointSize(18)
        tf.setBold(True)
        title.setFont(tf)
        brand_text.addWidget(title)
        self._subtitle = QLabel(t("app.subtitle"))
        self._subtitle.setObjectName("brandSubtitle")
        brand_text.addWidget(self._subtitle)
        brand.addLayout(brand_text)
        brand.addStretch(1)
        self._lang = QComboBox()
        for loc in available_locales():
            self._lang.addItem(loc, loc)
        self._lang.setCurrentIndex(self._lang.findData(get_locale()))
        self._lang.currentIndexChanged.connect(self._on_locale_changed)
        brand.addWidget(self._lang)
        outer.addLayout(brand)
        outer.addWidget(QLabel(f"backend: {self._backend.platform_id()}"))

        self._stack = QStackedWidget()
        outer.addWidget(self._stack, stretch=1)

        self._home = QWidget()
        home = QVBoxLayout(self._home)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter"))
        self._filter = QLineEdit()
        self._filter.setAccessibleName("游戏列表过滤")
        self._filter.textChanged.connect(self._refresh_game_list)
        filter_row.addWidget(self._filter)
        home.addLayout(filter_row)

        home.addWidget(QLabel("Games"))
        self._game_list = QListWidget()
        self._game_list.setAccessibleName("游戏列表")
        self._game_list.currentRowChanged.connect(self._on_game_selected)
        home.addWidget(self._game_list, stretch=1)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setVisible(False)
        home.addWidget(self._progress)

        pref_row = QHBoxLayout()
        pref_row.addWidget(QLabel("EXE"))
        self._exe_combo = QComboBox()
        pref_row.addWidget(self._exe_combo, stretch=1)
        pref_row.addWidget(QLabel("API"))
        self._api_combo = QComboBox()
        self._api_combo.addItem("auto", "")
        for api in GraphicsApi:
            if api is GraphicsApi.UNKNOWN:
                continue
            self._api_combo.addItem(api.value, api.value)
        pref_row.addWidget(self._api_combo)
        home.addLayout(pref_row)

        user_row = QHBoxLayout()
        user_row.addWidget(QLabel("Steam user"))
        self._steam_user = QComboBox()
        user_row.addWidget(self._steam_user, stretch=1)
        home.addLayout(user_row)
        self._reload_steam_users()

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode"))
        self._mode_combo = QComboBox()
        for mode, label in (
            ("reshade", "ReShade"),
            ("optiscaler", "OptiScaler"),
            ("vkbasalt", "vkBasalt"),
            ("goverlay", "Goverlay"),
            ("display_profile", "Display/HDR"),
            ("preview", "Conflict preview"),
            ("rtx_remix_enable", "Remix enable"),
            ("rtx_remix_disable", "Remix disable"),
            ("dwm_hdr", "DWM HDR prototype"),
        ):
            self._mode_combo.addItem(label, mode)
        mode_row.addWidget(self._mode_combo)
        home.addLayout(mode_row)

        home.addWidget(QLabel("Capabilities"))
        self._cap_list = QListWidget()
        home.addWidget(self._cap_list)

        home.addWidget(QLabel("History"))
        self._history_list = QListWidget()
        home.addWidget(self._history_list)

        buttons = QHBoxLayout()
        self._btn_scan = QPushButton(t("action.scan"))
        self._btn_force = QPushButton(t("action.force_scan"))
        self._btn_cancel = QPushButton(t("action.cancel_scan"))
        self._btn_cancel.setEnabled(False)
        self._btn_preview = QPushButton(t("conflict.title"))
        self._btn_steam = QPushButton(t("proton.open_steam"))
        self._btn_kit = QPushButton("ReShade…")
        self._btn_opti = QPushButton("OptiScaler…")
        self._btn_install = QPushButton(t("action.deploy"))
        self._btn_uninstall = QPushButton(t("action.uninstall"))
        self._btn_export = QPushButton("Export")
        self._btn_import = QPushButton("Import")
        self._btn_history = QPushButton("History")
        for b in (
            self._btn_scan,
            self._btn_force,
            self._btn_cancel,
            self._btn_preview,
            self._btn_steam,
            self._btn_kit,
            self._btn_opti,
            self._btn_install,
            self._btn_uninstall,
            self._btn_export,
            self._btn_import,
            self._btn_history,
        ):
            buttons.addWidget(b)
        home.addLayout(buttons)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        self._status.setAccessibleName("状态栏")
        home.addWidget(self._status)

        self._stack.addWidget(self._home)

        self._btn_scan.clicked.connect(lambda: self._scan_games(force=False))
        self._btn_force.clicked.connect(lambda: self._scan_games(force=True))
        self._btn_cancel.clicked.connect(self._cancel_scan)
        self._btn_preview.clicked.connect(self._on_preview)
        self._btn_steam.clicked.connect(self._open_steam_for_target)
        self._btn_kit.clicked.connect(self._pick_reshade_kit)
        self._btn_opti.clicked.connect(self._pick_optiscaler_kit)
        self._btn_install.clicked.connect(self._on_install)
        self._btn_uninstall.clicked.connect(self._on_uninstall)
        self._btn_export.clicked.connect(self._on_export)
        self._btn_import.clicked.connect(self._on_import)
        self._btn_history.clicked.connect(self._refresh_history)

        kit = get_reshade_kit_path()
        if kit:
            self._status.setText(f"ReShade: {kit}")
        self._refresh_history()
        self._setup_tray()

        if needs_wizard():
            FirstRunWizard(self).exec()

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._tray = QSystemTrayIcon(make_mark_icon(64), self)
        self._tray.setToolTip("buusdo")
        show = QAction("Show", self)
        show.triggered.connect(self.showNormal)
        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(self.close)
        from PySide6.QtWidgets import QMenu

        menu = QMenu()
        menu.addAction(show)
        recent_menu = menu.addMenu("Uninstall recent")
        self._tray_recent_menu = recent_menu
        self._rebuild_tray_recent()
        menu.addAction(quit_act)
        self._tray.setContextMenu(menu)
        self._tray.show()

    def _rebuild_tray_recent(self) -> None:
        menu = getattr(self, "_tray_recent_menu", None)
        if menu is None:
            return
        menu.clear()
        for item in list_recent():
            name = str(item.get("name") or "game")
            act = QAction(f"Uninstall {name}", self)
            act.triggered.connect(lambda _=False, data=item: self._tray_uninstall(data))
            menu.addAction(act)
        if menu.isEmpty():
            empty = QAction("(none)", self)
            empty.setEnabled(False)
            menu.addAction(empty)

    def _tray_uninstall(self, data: dict) -> None:
        target = EnhancementTarget(
            name=str(data.get("name") or "game"),
            install_path=Path(str(data.get("install_path"))),
            executable=Path(data["executable"]) if data.get("executable") else None,
            metadata=dict(data.get("metadata") or {}),
        )
        try:
            result = self._backend.uninstall(target)
            self._status.setText(result.message)
            if hasattr(self, "_tray"):
                self._tray.showMessage("buusdo", result.message)
        except (BuusdoError, UnsafeTargetError) as exc:
            QMessageBox.warning(self, "buusdo", str(exc))

    def _on_locale_changed(self) -> None:
        loc = self._lang.currentData()
        if not loc:
            return
        set_locale(loc)
        data = load_settings()
        data["locale"] = loc
        save_settings(data)
        self._subtitle.setText(t("app.subtitle"))
        self._btn_scan.setText(t("action.scan"))
        self._btn_force.setText(t("action.force_scan"))
        self._btn_cancel.setText(t("action.cancel_scan"))
        self._btn_install.setText(t("action.deploy"))
        self._btn_uninstall.setText(t("action.uninstall"))
        self._btn_preview.setText(t("conflict.title"))

    def _reload_steam_users(self) -> None:
        self._steam_user.clear()
        self._steam_user.addItem("(default)", "")
        for profile in list_steam_users(steam_roots()):
            self._steam_user.addItem(profile.label, profile.steam_id3)

    def _scan_games(self, *, force: bool) -> None:
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._status.setText(t("scan.progress"))
        self._btn_scan.setEnabled(False)
        self._btn_force.setEnabled(False)
        self._btn_cancel.setEnabled(True)

        def on_progress(_stage: str, value: float) -> None:
            self._progress.setValue(int(value * 100))

        def on_finished(games: list) -> None:
            self._games = games
            self._refresh_game_list()
            self._reload_steam_users()
            self._status.setText(f"{len(games)} games")
            self._progress.setVisible(False)
            self._btn_scan.setEnabled(True)
            self._btn_force.setEnabled(True)
            self._btn_cancel.setEnabled(False)
            self._rebuild_tray_recent()

        def on_failed(message: str) -> None:
            self._status.setText(message)
            self._progress.setVisible(False)
            self._btn_scan.setEnabled(True)
            self._btn_force.setEnabled(True)
            self._btn_cancel.setEnabled(False)
            if message != "cancelled":
                capture_exception(RuntimeError(message), context={"op": "scan"})

        self._scan_thread, self._scan_worker = start_scan(
            force=force,
            on_progress=on_progress,
            on_finished=on_finished,
            on_failed=on_failed,
        )

    def _cancel_scan(self) -> None:
        if self._scan_worker is not None:
            self._scan_worker.cancel()
        self._status.setText(t("action.cancel_scan"))

    def _open_steam_for_target(self) -> None:
        if not self._target:
            return
        st = self._backend.status(self._target)
        health = st.get("proton_health") or {}
        uri = health.get("steam_uri") or (
            f"steam://run/{self._target.metadata['app_id']}"
            if self._target.metadata.get("app_id")
            else None
        )
        if not uri:
            QMessageBox.information(self, "buusdo", t("proton.missing_prefix"))
            return
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl(uri))
        if not health.get("ok", True):
            QMessageBox.information(self, "buusdo", t("proton.missing_prefix"))

    def _refresh_game_list(self) -> None:
        needle = self._filter.text().strip().lower()
        self._game_list.clear()
        self._filtered = []
        for game in self._games:
            if needle and needle not in game.name.lower():
                continue
            st = self._backend.status(game)
            kind, badge = self._badge_for_status(st)
            runtime = " [Proton]" if game.metadata.get("runtime") == "proton" else ""
            health = st.get("proton_health") or {}
            warn = ""
            if health and not health.get("ok", True):
                warn = " ⚠"
            item = QListWidgetItem(f"{badge}{warn} {game.name}{runtime}")
            tip = str(game.install_path)
            if health and not health.get("ok", True):
                tip += f"\n{health.get('message')}"
            item.setToolTip(tip)
            item.setForeground(badge_color(kind if not warn else "warn"))
            self._game_list.addItem(item)
            self._filtered.append(game)

    def _badge_for_status(self, st: dict) -> tuple[str, str]:
        if st.get("installed") or (st.get("reshade") or {}).get("installed"):
            return "ok", t("badge.deployed")
        if st.get("vkbasalt_configured"):
            return "warn", "[vkBasalt]"
        return "muted", t("badge.none")

    def _on_game_selected(self, row: int) -> None:
        if row < 0 or row >= len(self._filtered):
            self._target = None
            self._cap_list.clear()
            self._exe_combo.clear()
            return
        self._target = self._filtered[row]
        self._refresh_capabilities()
        self._populate_exe_combo()
        st = self._backend.status(self._target)
        _, badge = self._badge_for_status(st)
        msg = f"{self._target.name} — {badge}\n{self._target.install_path}"
        health = st.get("proton_health")
        if health and not health.get("ok", True):
            msg += f"\n{health.get('message')}"
        self._status.setText(msg)

    def _populate_exe_combo(self) -> None:
        self._exe_combo.clear()
        if not self._target:
            return
        exes = self._target.metadata.get("executables") or []
        if not exes and self._target.executable:
            exes = [str(self._target.executable)]
        for path in exes:
            self._exe_combo.addItem(Path(path).name, path)
        if self._target.executable:
            idx = self._exe_combo.findData(str(self._target.executable))
            if idx >= 0:
                self._exe_combo.setCurrentIndex(idx)

    def _refresh_capabilities(self) -> None:
        self._cap_list.clear()
        if not self._target:
            return
        for cap in self._backend.list_capabilities(self._target):
            avail = "Y" if cap.available else "N"
            self._cap_list.addItem(f"[{avail}] {cap.title} — {cap.description}")

    def _refresh_history(self) -> None:
        self._history_list.clear()
        for event in list_events(limit=50):
            ok = "OK" if event.get("success") else "FAIL"
            self._history_list.addItem(
                f"{event.get('ts', '')} [{ok}] {event.get('action')} · {event.get('target')}"
            )

    def _pick_reshade_kit(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "ReShade")
        if path:
            set_reshade_kit_path(path)
            self._status.setText(path)

    def _pick_optiscaler_kit(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "OptiScaler")
        if path:
            set_optiscaler_kit_path(path)
            self._status.setText(path)

    def _install_options(self) -> dict:
        opts: dict = {"mode": self._mode_combo.currentData()}
        exe = self._exe_combo.currentData()
        if exe:
            opts["executable"] = exe
        api = self._api_combo.currentData()
        if api:
            opts["api"] = api
        steam_id3 = self._steam_user.currentData()
        if steam_id3:
            opts["steam_id3"] = steam_id3
            if self._target and self._target.metadata.get("app_id"):
                update_game_config(str(self._target.metadata["app_id"]), steam_id3=steam_id3)
        if opts["mode"] == "display_profile":
            opts["hdr_preferred"] = True
        if opts["mode"] == "preview":
            opts["preview_mode"] = "reshade"
        return opts

    def _show_conflict_dialog(self, details: dict) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(t("conflict.title"))
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel(t("conflict.title")))
        lst = QListWidget()
        for item in details.get("diffs") or []:
            lst.addItem(f"{item.get('action')}: {item.get('path') or ''} {item.get('detail')}")
        layout.addWidget(lst)
        close = QPushButton("OK")
        close.clicked.connect(dlg.accept)
        layout.addWidget(close)
        dlg.resize(560, 360)
        dlg.exec()

    def _on_preview(self) -> None:
        if not self._target:
            QMessageBox.information(self, "buusdo", "Select a game first.")
            return
        mode = self._mode_combo.currentData()
        try:
            r_kit = get_reshade_kit_path()
            o_kit = get_optiscaler_kit_path()
            api_raw = self._api_combo.currentData()
            api = GraphicsApi(api_raw) if api_raw else None
            if mode == "optiscaler":
                if not o_kit:
                    raise BuusdoError("OptiScaler kit not configured")
                details = preview_optiscaler_deploy(self._target, Path(o_kit))
            else:
                details = preview_triple_matrix(
                    self._target,
                    reshade_kit=Path(r_kit) if r_kit else None,
                    optiscaler_kit=Path(o_kit) if o_kit else None,
                    api=api,
                )
        except BuusdoError as exc:
            QMessageBox.warning(self, "buusdo", str(exc))
            return
        self._show_conflict_dialog(details)

    def _show_blocked(self, error: UnsafeTargetError) -> None:
        page = BlockedPage(error)
        while self._stack.count() > 1:
            w = self._stack.widget(1)
            self._stack.removeWidget(w)
            w.deleteLater()
        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)

    def _on_install(self) -> None:
        if not self._target:
            QMessageBox.information(self, "buusdo", "Select a game first.")
            return
        try:
            result = self._backend.install(self._target, self._install_options())
        except UnsafeTargetError as exc:
            self._show_blocked(exc)
            self._refresh_history()
            return
        except BuusdoError as exc:
            capture_exception(exc, context={"op": "install", "target": self._target.name})
            QMessageBox.warning(self, "buusdo", str(exc))
            self._refresh_history()
            return
        if self._mode_combo.currentData() == "preview":
            self._show_conflict_dialog(result.details)
        self._status.setText(result.message)
        self._stack.setCurrentWidget(self._home)
        self._refresh_game_list()
        self._refresh_history()

    def _on_uninstall(self) -> None:
        if not self._target:
            return
        try:
            result = self._backend.uninstall(self._target)
        except UnsafeTargetError as exc:
            self._show_blocked(exc)
            return
        except BuusdoError as exc:
            QMessageBox.warning(self, "buusdo", str(exc))
            return
        self._status.setText(result.message)
        self._refresh_game_list()
        self._refresh_history()

    def _on_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export", "buusdo-config.zip", "Zip (*.zip)")
        if path:
            export_configs(path)

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import", "", "Zip (*.zip)")
        if path:
            import_configs(path)
