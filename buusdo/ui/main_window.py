"""Main window — backend-agnostic (C3)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
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
    QSpinBox,
    QStackedWidget,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
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
    migrate_conflict_export,
    preview_optiscaler_deploy,
    preview_reshade_deploy,
    preview_triple_matrix,
)
from buusdo.backends.windows_display import (
    clear_display_session,
    display_session_status,
    drop_session_ccd_target,
    retry_display_mode,
    retry_hdr_target,
    rollback_display_session,
)
from buusdo.core.crash_report import (
    capture_exception,
    clear_crash_opt_in_audit,
    crash_upload_opted_in,
    export_crash_opt_in_audit,
    redact,
    set_crash_upload_opt_in,
)
from buusdo.core.errors import BuusdoError, UnsafeTargetError
from buusdo.core.graphics_detect import GraphicsApi
from buusdo.core.history import list_events
from buusdo.core.i18n import available_locales, get_locale, set_locale, t
from buusdo.core.kit_validate import validate_optiscaler_kit, validate_reshade_kit
from buusdo.core.library_progress import resume_scan_status
from buusdo.core.platform_detect import steam_roots
from buusdo.core.recent_games import (
    clear_uninstalled,
    is_greyed,
    list_recent,
    mark_uninstalled,
    push_recent,
)
from buusdo.core.steam_launch import find_localconfig, list_steam_users, write_proton_launch_note
from buusdo.core.steam_uris import (
    DEFAULT_STEAM_URI_CACHE_TTL_S,
    clear_properties_uri_cache,
    game_properties_uri_candidates,
    probe_open_uris,
    set_steam_uri_cache_ttl_s,
    steam_uri_cache_status,
    steam_uri_cache_ttl_s,
)
from buusdo.core.transaction import Transaction
from buusdo.core.vkbasalt_template import list_presets
from buusdo.ui.blocked_page import BlockedPage
from buusdo.ui.linux_deploy_dialog import LinuxDeployDialog
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

        self._kits_banner = QLabel("")
        self._kits_banner.setWordWrap(True)
        self._kits_banner.setStyleSheet("color: #B08900;")
        self._btn_complete_kits = QPushButton(t("settings.complete_kits"))
        self._btn_complete_kits.clicked.connect(self._complete_kits_setup)
        kits_row = QHBoxLayout()
        kits_row.addWidget(self._kits_banner, stretch=1)
        kits_row.addWidget(self._btn_complete_kits)
        home.addLayout(kits_row)
        self._refresh_kits_banner()

        home.addWidget(QLabel("Games"))
        self._game_list = QListWidget()
        self._game_list.setAccessibleName("游戏列表")
        self._game_list.currentRowChanged.connect(self._on_game_selected)
        home.addWidget(self._game_list, stretch=1)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFormat("%p%")
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
        mode_row.addWidget(QLabel("vkBasalt"))
        self._vk_preset = QComboBox()
        for name in list_presets():
            self._vk_preset.addItem(name, name)
        idx = self._vk_preset.findData("cas")
        if idx >= 0:
            self._vk_preset.setCurrentIndex(idx)
        mode_row.addWidget(self._vk_preset)
        home.addLayout(mode_row)

        self._crash_opt = QCheckBox(t("action.crash_opt_in"))
        self._crash_opt.setChecked(crash_upload_opted_in())
        self._crash_opt.toggled.connect(self._on_crash_opt_toggled)
        home.addWidget(self._crash_opt)
        audit_row = QHBoxLayout()
        self._btn_export_audit = QPushButton(t("action.export_audit"))
        self._btn_clear_audit = QPushButton(t("action.clear_audit"))
        self._btn_export_audit.clicked.connect(self._export_crash_audit)
        self._btn_clear_audit.clicked.connect(self._clear_crash_audit)
        audit_row.addWidget(self._btn_export_audit)
        audit_row.addWidget(self._btn_clear_audit)
        home.addLayout(audit_row)

        ttl_row = QHBoxLayout()
        ttl_row.addWidget(QLabel(t("settings.steam_uri_ttl")))
        self._steam_ttl = QSpinBox()
        self._steam_ttl.setRange(1, 90)
        self._steam_ttl.setSuffix(t("settings.steam_uri_ttl_suffix"))
        days = max(1, int(round(steam_uri_cache_ttl_s() / 86400)))
        self._steam_ttl.setValue(days)
        self._steam_ttl.setToolTip(
            t("settings.steam_uri_ttl_tip", default_days=DEFAULT_STEAM_URI_CACHE_TTL_S // 86400)
        )
        self._steam_ttl.valueChanged.connect(self._on_steam_ttl_changed)
        ttl_row.addWidget(self._steam_ttl)
        self._btn_clear_steam_uri = QPushButton(t("settings.steam_uri_clear"))
        self._btn_clear_steam_uri.clicked.connect(self._clear_steam_uri_cache)
        ttl_row.addWidget(self._btn_clear_steam_uri)
        self._btn_steam_try_first = QPushButton(t("settings.steam_uri_try_first"))
        self._btn_steam_try_first.setToolTip(t("settings.steam_uri_try_first"))
        self._btn_steam_try_first.clicked.connect(lambda: self._try_open_steam_uri_candidate(0))
        ttl_row.addWidget(self._btn_steam_try_first)
        self._btn_steam_try_next = QPushButton(t("settings.steam_uri_try_next"))
        self._btn_steam_try_next.setToolTip(t("settings.steam_uri_try_next"))
        self._btn_steam_try_next.clicked.connect(self._try_open_next_steam_uri)
        self._btn_steam_try_next.setEnabled(False)
        ttl_row.addWidget(self._btn_steam_try_next)
        self._steam_uri_try_index = 0
        self._steam_uri_cache_label = QLabel("")
        self._steam_uri_cache_label.setWordWrap(True)
        ttl_row.addWidget(self._steam_uri_cache_label, stretch=1)
        home.addLayout(ttl_row)
        self._refresh_steam_uri_controls()

        self._session_banner = QLabel("")
        self._session_banner.setWordWrap(True)
        self._session_banner.setStyleSheet("color: #B08900;")
        self._btn_clear_session = QPushButton(t("action.clear_display_session"))
        self._btn_clear_session.clicked.connect(self._clear_display_session)
        self._btn_rollback_now = QPushButton(t("action.rollback_now"))
        self._btn_rollback_now.clicked.connect(self._rollback_display_now)
        sess_row = QHBoxLayout()
        sess_row.addWidget(self._session_banner, stretch=1)
        sess_row.addWidget(self._btn_rollback_now)
        sess_row.addWidget(self._btn_clear_session)
        home.addLayout(sess_row)
        self._refresh_session_banner()

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
        self._btn_proton_note = QPushButton(t("action.proton_note"))
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
            self._btn_proton_note,
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
        self._btn_proton_note.clicked.connect(self._write_proton_note)
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
            self._refresh_kits_banner()

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
            if is_greyed(item):
                grey = QAction(f"{name} {t('tray.uninstalled')}", self)
                grey.setEnabled(False)
                menu.addAction(grey)
                clear_act = QAction(t("tray.clear_uninstalled"), self)
                clear_act.triggered.connect(
                    lambda _=False, data=item: self._tray_clear_uninstalled(data)
                )
                menu.addAction(clear_act)
            else:
                act = QAction(f"Uninstall {name}", self)
                act.triggered.connect(lambda _=False, data=item: self._tray_uninstall(data))
                menu.addAction(act)
        if menu.isEmpty():
            empty = QAction("(none)", self)
            empty.setEnabled(False)
            menu.addAction(empty)

    def _tray_clear_uninstalled(self, data: dict) -> None:
        name = str(data.get("name") or "game")
        reply = QMessageBox.question(
            self,
            "buusdo",
            t("tray.clear_uninstalled_confirm", name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if clear_uninstalled(data):
            # Re-push to the front of recent so the tray order reflects a reinstall.
            push_recent(dict(data))
            self._rebuild_tray_recent()
            self._status.setText(t("tray.clear_uninstalled"))

    def _has_valid_kit(self) -> bool:
        return validate_reshade_kit(get_reshade_kit_path()).ok or validate_optiscaler_kit(
            get_optiscaler_kit_path()
        ).ok

    def _kits_both_valid(self) -> bool:
        return validate_reshade_kit(get_reshade_kit_path()).ok and validate_optiscaler_kit(
            get_optiscaler_kit_path()
        ).ok

    def _missing_kit_side(self) -> str | None:
        """When exactly one kit is valid, return the side that still needs a path."""
        r_ok = validate_reshade_kit(get_reshade_kit_path()).ok
        o_ok = validate_optiscaler_kit(get_optiscaler_kit_path()).ok
        if r_ok and not o_ok:
            return "optiscaler"
        if o_ok and not r_ok:
            return "reshade"
        return None

    def _kit_banner_state(self) -> tuple[str, str]:
        """Return (text, severity): empty | one_side | incomplete."""
        r_path = get_reshade_kit_path()
        o_path = get_optiscaler_kit_path()
        r_ok = validate_reshade_kit(r_path).ok
        o_ok = validate_optiscaler_kit(o_path).ok
        r_set = r_path is not None
        o_set = o_path is not None

        parts: list[str] = []
        # Exactly one kit is valid → dedicated one-side copy.
        if r_ok ^ o_ok:
            parts.append(t("settings.kits_one_side"))
            severity = "one_side"
        else:
            parts.append(t("settings.kits_banner"))
            severity = "empty"

        incomplete = False
        if r_set and not r_ok:
            incomplete = True
            rs = validate_reshade_kit(r_path)
            miss = ", ".join(rs.missing) if rs.missing else rs.message
            parts.append(f"ReShade: {t('wizard.kit_bad')} ({miss})")
        elif not r_set:
            parts.append(f"ReShade: {t('settings.kits_path_empty')}")
        else:
            parts.append(f"ReShade: {t('wizard.kit_ok')}")

        if o_set and not o_ok:
            incomplete = True
            os_ = validate_optiscaler_kit(o_path)
            miss = ", ".join(os_.missing) if os_.missing else os_.message
            parts.append(f"OptiScaler: {t('wizard.kit_bad')} ({miss})")
        elif not o_set:
            parts.append(f"OptiScaler: {t('settings.kits_path_empty')}")
        else:
            parts.append(f"OptiScaler: {t('wizard.kit_ok')}")

        if incomplete and severity != "one_side":
            severity = "incomplete"
        elif incomplete and severity == "one_side":
            # Keep one_side as primary, but prefer red styling when DLL incomplete.
            severity = "incomplete"
        return "\n".join(parts), severity

    def _refresh_kits_banner(self) -> None:
        skipped = bool(load_settings().get("wizard_skipped_kits"))
        # Keep banner while either side is missing/invalid (incl. one-side-valid).
        show = skipped and not self._kits_both_valid()
        if not show:
            self._kits_banner.setText("")
            self._kits_banner.setStyleSheet("")
            self._btn_complete_kits.setVisible(False)
            return
        text, severity = self._kit_banner_state()
        self._kits_banner.setText(text)
        # empty: amber; one_side: blue; incomplete DLLs: red
        if severity == "incomplete":
            self._kits_banner.setStyleSheet("color: #C73E1D; font-weight: 600;")
        elif severity == "one_side":
            self._kits_banner.setStyleSheet("color: #2E86AB; font-weight: 600;")
        else:
            self._kits_banner.setStyleSheet("color: #B08900;")
        missing = self._missing_kit_side()
        if missing == "reshade":
            self._btn_complete_kits.setText(t("settings.complete_kits_reshade"))
        elif missing == "optiscaler":
            self._btn_complete_kits.setText(t("settings.complete_kits_optiscaler"))
        else:
            self._btn_complete_kits.setText(t("settings.complete_kits"))
        self._btn_complete_kits.setVisible(True)

    def _on_steam_ttl_changed(self, days: int) -> None:
        set_steam_uri_cache_ttl_s(int(days) * 86400)
        self._refresh_steam_uri_controls()
        self._status.setText(t("settings.steam_uri_ttl_saved", days=int(days)))

    def _refresh_steam_uri_controls(self) -> None:
        st = steam_uri_cache_status()
        has_game = bool(self._target and self._target.metadata.get("app_id"))
        if st.get("cached"):
            self._steam_uri_cache_label.setText(
                t("settings.steam_uri_cache_on", template=str(st.get("template") or ""))
            )
            self._btn_clear_steam_uri.setEnabled(True)
            tip = str(st.get("template") or "")
        else:
            self._steam_uri_cache_label.setText(t("settings.steam_uri_cache_off"))
            self._btn_clear_steam_uri.setEnabled(False)
            tip = t("settings.steam_uri_cache_off")
        self._btn_clear_steam_uri.setToolTip(tip)
        self._btn_steam_try_first.setEnabled(has_game)
        # "Try next" only after a failed attempt with remaining candidates.
        can_next = (
            has_game
            and getattr(self, "_steam_uri_try_index", 0) > 0
            and self._steam_uri_candidates_left() > 0
        )
        self._btn_steam_try_next.setEnabled(bool(can_next))
        if hasattr(self, "_btn_steam"):
            self._btn_steam.setToolTip(tip)

    def _steam_uri_candidates(self) -> list[str]:
        if not self._target or not self._target.metadata.get("app_id"):
            return []
        return game_properties_uri_candidates(str(self._target.metadata["app_id"]))

    def _steam_uri_candidates_left(self) -> int:
        uris = self._steam_uri_candidates()
        idx = int(getattr(self, "_steam_uri_try_index", 0))
        return max(0, len(uris) - idx)

    def _steam_uri_probe_preview_text(self) -> str:
        """List URI candidates for the selected game after cache clear (no desktop open)."""
        if not self._target or not self._target.metadata.get("app_id"):
            return t("settings.steam_uri_probe_no_game")
        uris = self._steam_uri_candidates()
        return t("settings.steam_uri_probe_preview", uris="\n".join(f"  {u}" for u in uris))

    def _try_open_steam_uri_candidate(self, index: int) -> None:
        """Open one properties URI candidate by index; offer Try next on failure."""
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        uris = self._steam_uri_candidates()
        if not uris:
            self._steam_uri_try_index = 0
            self._toast(t("settings.steam_uri_probe_no_game"))
            self._refresh_steam_uri_controls()
            return
        if index < 0 or index >= len(uris):
            self._steam_uri_try_index = len(uris)
            self._toast(t("settings.steam_uri_try_exhausted", total=len(uris)))
            self._refresh_steam_uri_controls()
            return
        uri = uris[index]
        total = len(uris)

        def _open(u: str) -> bool:
            return bool(QDesktopServices.openUrl(QUrl(u)))

        result = probe_open_uris([uri], opener=_open, cache_success=True, clear_cache_on_fail=False)
        if result.get("opened"):
            self._steam_uri_try_index = 0
            self._refresh_steam_uri_controls()
            self._toast(
                t(
                    "settings.steam_uri_try_first_ok",
                    index=index + 1,
                    total=total,
                    uri=uri,
                )
            )
            return
        # Advance so "Try next" opens the following candidate.
        self._steam_uri_try_index = index + 1
        self._refresh_steam_uri_controls()
        if self._steam_uri_try_index >= total:
            self._toast(t("settings.steam_uri_try_exhausted", total=total))
        else:
            self._toast(
                t(
                    "settings.steam_uri_try_first_fail",
                    index=index + 1,
                    total=total,
                    uri=uri,
                )
            )

    def _try_open_next_steam_uri(self) -> None:
        self._try_open_steam_uri_candidate(int(getattr(self, "_steam_uri_try_index", 0)))

    def _clear_steam_uri_cache(self) -> None:
        cleared = clear_properties_uri_cache()
        self._steam_uri_try_index = 0
        self._refresh_steam_uri_controls()
        preview = self._steam_uri_probe_preview_text()
        base = t("settings.steam_uri_cleared") if cleared else t("settings.steam_uri_clear_empty")
        self._status.setText(f"{base}\n{preview}")
        if hasattr(self, "_tray"):
            self._tray.showMessage("buusdo", base)

    def _toast(self, message: str) -> None:
        self._status.setText(message)
        if hasattr(self, "_tray"):
            self._tray.showMessage("buusdo", message)

    def _kit_side_toast(self, *, side: str, saved: bool) -> None:
        if not saved:
            self._toast(t("settings.kit_side_cancelled"))
            return
        if self._kits_both_valid():
            self._toast(t("settings.kit_both_ready"))
        else:
            self._toast(t("settings.kit_still_missing", side=side))

    def _complete_kits_setup(self) -> None:
        focus = self._missing_kit_side()
        if focus == "reshade":
            # One-side CTA: jump straight to the missing side picker, then toast.
            ok = self._pick_reshade_kit()
            self._kit_side_toast(side="ReShade", saved=ok)
        elif focus == "optiscaler":
            ok = self._pick_optiscaler_kit()
            self._kit_side_toast(side="OptiScaler", saved=ok)
        else:
            FirstRunWizard(self, focus_side=focus).exec()
            if self._kits_both_valid():
                self._toast(t("settings.kit_both_ready"))
        data = load_settings()
        if self._kits_both_valid():
            data["wizard_skipped_kits"] = False
            data["wizard_completed"] = True
            save_settings(data)
        self._refresh_kits_banner()
        kit = get_reshade_kit_path()
        if kit and focus is None and not self._kits_both_valid():
            self._status.setText(f"ReShade: {kit}")

    def _tray_uninstall(self, data: dict) -> None:
        name = str(data.get("name") or "game")
        reply = QMessageBox.question(
            self,
            "buusdo",
            t("action.confirm_uninstall", name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        target = EnhancementTarget(
            name=name,
            install_path=Path(str(data.get("install_path"))),
            executable=Path(data["executable"]) if data.get("executable") else None,
            metadata=dict(data.get("metadata") or {}),
        )
        try:
            result = self._backend.uninstall(target)
            mark_uninstalled(data)
            self._status.setText(result.message)
            if hasattr(self, "_tray"):
                self._tray.showMessage("buusdo", result.message)
            self._rebuild_tray_recent()
            self._refresh_game_list()
            self._refresh_history()
            self._refresh_session_banner()
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

        def on_progress(stage: str, value: float) -> None:
            pct = int(max(0, min(100, value * 100)))
            self._progress.setValue(pct)
            if isinstance(stage, str) and stage.startswith("resume:"):
                st = resume_scan_status()
                scanned = int(st.get("scanned", 0) or 0)
                total = max(1, int(st.get("total_manifests", 0) or 1))
                resume_pct = int(100 * scanned / total)
                self._progress.setValue(max(pct, min(99, resume_pct)))
                self._status.setText(
                    t(
                        "scan.resume",
                        scanned=scanned,
                        total=total,
                        match=st.get("fingerprint_match"),
                    )
                )

        # Surface pending resume before worker starts
        resume = resume_scan_status()
        if resume.get("resume"):
            scanned = int(resume.get("scanned", 0) or 0)
            total = max(1, int(resume.get("total_manifests", 0) or 1))
            self._progress.setValue(int(100 * scanned / total))
            self._status.setText(
                t(
                    "scan.resume",
                    scanned=scanned,
                    total=total,
                    match=resume.get("fingerprint_match"),
                )
            )

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
        # Indeterminate flash then clear so a cancelled resume does not leave a stale %.
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)
        self._progress.repaint()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFormat("%p%")
        self._progress.setVisible(False)
        resume = resume_scan_status()
        if resume.get("partial") or resume.get("resume"):
            self._status.setText(
                t(
                    "scan.cancel_resume",
                    scanned=int(resume.get("scanned") or 0),
                    total=int(resume.get("total_manifests") or 0),
                )
            )
        else:
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

    def _write_proton_note(self) -> None:
        if not self._target or not self._target.metadata.get("app_id"):
            QMessageBox.information(self, "buusdo", t("proton.missing_prefix"))
            return
        steam_id3 = self._steam_user.currentData() or self._target.metadata.get("steam_id3")
        localconfig = find_localconfig(steam_roots(), steam_id3=steam_id3 or None)
        if localconfig is None:
            QMessageBox.warning(self, "buusdo", t("proton.missing_prefix"))
            return
        try:
            with Transaction() as tx:
                write_proton_launch_note(
                    tx,
                    localconfig,
                    str(self._target.metadata["app_id"]),
                    note=t("proton.note_text"),
                )
        except BuusdoError as exc:
            QMessageBox.warning(self, "buusdo", str(exc))
            return
        self._status.setText(t("proton.note_written"))
        QMessageBox.information(self, "buusdo", t("proton.note_written"))
        app_id = str(self._target.metadata["app_id"])
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        def _open(uri: str) -> bool:
            return bool(QDesktopServices.openUrl(QUrl(uri)))

        probe_open_uris(game_properties_uri_candidates(app_id), opener=_open)
        self._refresh_steam_uri_controls()

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
        self._steam_uri_try_index = 0
        self._refresh_capabilities()
        self._populate_exe_combo()
        self._refresh_steam_uri_controls()
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

    def _pick_reshade_kit(self) -> bool:
        path = QFileDialog.getExistingDirectory(self, "ReShade")
        if not path:
            return False
        set_reshade_kit_path(path)
        self._status.setText(path)
        if self._kits_both_valid():
            data = load_settings()
            data["wizard_skipped_kits"] = False
            save_settings(data)
        self._refresh_kits_banner()
        return True

    def _pick_optiscaler_kit(self) -> bool:
        path = QFileDialog.getExistingDirectory(self, "OptiScaler")
        if not path:
            return False
        set_optiscaler_kit_path(path)
        self._status.setText(path)
        if self._kits_both_valid():
            data = load_settings()
            data["wizard_skipped_kits"] = False
            save_settings(data)
        self._refresh_kits_banner()
        return True

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
            opts["triple_matrix"] = True
        if opts["mode"] == "vkbasalt":
            dlg = LinuxDeployDialog(
                self,
                preset=str(self._vk_preset.currentData() or "cas"),
            )
            if dlg.exec() != QDialog.DialogCode.Accepted:
                opts["_abort"] = True
                return opts
            opts.update(dlg.options())
            idx = self._vk_preset.findData(opts.get("vkbasalt_preset"))
            if idx >= 0:
                self._vk_preset.setCurrentIndex(idx)
        return opts

    def _severity_rank(self, severity: str) -> int:
        order = {"block": 0, "warning": 1, "info": 2, "conflict": 3, "": 4}
        return order.get(severity, 5)

    def _show_conflict_dialog(self, details: dict) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(t("conflict.title"))
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel(t("conflict.title")))
        schema_v = details.get("schema_version") or 1
        badge = QLabel(t("conflict.schema_badge", version=schema_v))
        badge.setStyleSheet(
            "color: #2E86AB; font-weight: 600; border: 1px solid #2E86AB; "
            "padding: 2px 8px; align-self: flex-start;"
        )
        layout.addWidget(badge)
        rows = []
        for item in details.get("diffs") or []:
            detail = str(item.get("detail") or "")
            severity = ""
            if item.get("action") == "conflict":
                if detail.startswith("[block]"):
                    severity = "block"
                elif detail.startswith("[warning]"):
                    severity = "warning"
                elif detail.startswith("[info]"):
                    severity = "info"
                else:
                    severity = "conflict"
            rows.append((severity, item, detail))
        rows.sort(key=lambda r: self._severity_rank(r[0]))
        table = QTableWidget(len(rows), 4)
        table.setHorizontalHeaderLabels(
            [
                t("conflict.col.severity"),
                t("conflict.col.action"),
                t("conflict.col.path"),
                t("conflict.col.detail"),
            ]
        )
        table.setSortingEnabled(True)
        colors = {
            "block": QColor("#C73E1D"),
            "warning": QColor("#B08900"),
            "info": QColor("#2E86AB"),
        }
        for i, (severity, item, detail) in enumerate(rows):
            values = [
                severity,
                str(item.get("action") or ""),
                str(item.get("path") or ""),
                detail,
            ]
            color = colors.get(severity)
            for col, text in enumerate(values):
                cell = QTableWidgetItem(text)
                if color is not None:
                    cell.setForeground(color)
                table.setItem(i, col, cell)
        table.resizeColumnsToContents()
        layout.addWidget(table)
        payload = migrate_conflict_export(
            {
                "schema_version": details.get("schema_version", 1),
                "mode": details.get("mode"),
                "blocked": details.get("blocked"),
                "triple_matrix_summary": details.get("triple_matrix_summary"),
                "diffs": details.get("diffs") or [],
            }
        )
        actions = QHBoxLayout()
        copy_btn = QPushButton(t("action.copy_json"))
        export_btn = QPushButton(t("action.export_json"))
        close = QPushButton("OK")

        def _copy() -> None:
            from PySide6.QtWidgets import QApplication
            import json as _json

            QApplication.clipboard().setText(_json.dumps(payload, indent=2, ensure_ascii=False))

        def _export() -> None:
            import json as _json

            path, _ = QFileDialog.getSaveFileName(
                dlg, t("action.export_json"), "conflict-preview.json", "JSON (*.json)"
            )
            if path:
                Path(path).write_text(
                    _json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )

        copy_btn.clicked.connect(_copy)
        export_btn.clicked.connect(_export)
        close.clicked.connect(dlg.accept)
        actions.addWidget(copy_btn)
        actions.addWidget(export_btn)
        actions.addWidget(close)
        layout.addLayout(actions)
        dlg.resize(720, 420)
        dlg.exec()

    def _on_crash_opt_toggled(self, enabled: bool) -> None:
        if not enabled:
            set_crash_upload_opt_in(False)
            return
        sample = redact(f"boom at {Path.home()}/secret token=sekrit")
        preview = QMessageBox(self)
        preview.setWindowTitle(t("action.crash_opt_preview"))
        preview.setText(t("action.crash_opt_confirm"))
        preview.setInformativeText(sample)
        preview.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        preview.setDefaultButton(QMessageBox.StandardButton.No)
        if preview.exec() != QMessageBox.StandardButton.Yes:
            self._crash_opt.blockSignals(True)
            self._crash_opt.setChecked(False)
            self._crash_opt.blockSignals(False)
            return
        set_crash_upload_opt_in(True)

    def _refresh_session_banner(self) -> None:
        st = display_session_status()
        if not st.get("present"):
            self._session_banner.setText("")
            self._btn_clear_session.setEnabled(False)
            self._btn_rollback_now.setEnabled(False)
            return
        self._btn_clear_session.setEnabled(True)
        self._btn_rollback_now.setEnabled(True)
        mins = max(1, int((st.get("ttl_remaining_s") or 0) / 60))
        self._session_banner.setText(
            t(
                "display.session_warn",
                minutes=mins,
                displays=int(st.get("displays") or 0),
                targets=int(st.get("targets") or 0),
            )
        )

    def _clear_display_session(self) -> None:
        clear_display_session()
        self._refresh_session_banner()
        self._status.setText(t("action.clear_display_session"))

    def _rollback_display_now(self) -> None:
        result = rollback_display_session(dry_run=False)
        self._refresh_session_banner()
        if result.get("restored"):
            self._status.setText(t("display.rollback_ok"))
            if hasattr(self, "_tray"):
                self._tray.showMessage("buusdo", t("display.rollback_ok"))
            self._refresh_capabilities()
            self._refresh_game_list()
            return
        failed = result.get("failed_displays") or []
        succeeded = result.get("succeeded_displays") or []
        if failed:
            if succeeded or result.get("partial"):
                msg = t(
                    "display.rollback_partial",
                    ok=len(succeeded),
                    fail=len(failed),
                )
                self._status.setText(msg)
                if hasattr(self, "_tray"):
                    self._tray.showMessage("buusdo", msg)
                self._refresh_capabilities()
            self._show_rollback_failures(failed, hdr_step=result.get("details", {}).get("hdr"))
        else:
            self._status.setText(str(result.get("reason") or "no_session"))

    def _show_rollback_failures(self, failed: list, *, hdr_step: dict | None = None) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(t("display.fail_table"))
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel(t("display.fail_table")))
        table = QTableWidget(len(failed), 7)
        table.setHorizontalHeaderLabels(
            ["device", "name", "code", "size", "refresh", "adapter", "targetId"]
        )
        for i, row in enumerate(failed):
            table.setItem(i, 0, QTableWidgetItem(str(row.get("device") or "")))
            table.setItem(i, 1, QTableWidgetItem(str(row.get("device_string") or "")))
            table.setItem(i, 2, QTableWidgetItem(str(row.get("code") if row.get("code") is not None else row.get("error") or "")))
            table.setItem(
                i,
                3,
                QTableWidgetItem(f"{row.get('width')}x{row.get('height')}"),
            )
            table.setItem(i, 4, QTableWidgetItem(str(row.get("refresh_hz") or "")))
            adapter = ""
            if row.get("adapterLow") is not None:
                adapter = f"{row.get('adapterLow')}/{row.get('adapterHigh') or 0}"
            table.setItem(i, 5, QTableWidgetItem(adapter))
            table.setItem(i, 6, QTableWidgetItem(str(row.get("targetId") if row.get("targetId") is not None else "")))
        table.resizeColumnsToContents()
        layout.addWidget(table)
        remaining = QLabel("")
        remaining.setWordWrap(True)
        remaining_list = QListWidget()
        remaining_list.setAccessibleName(t("display.session_targets_list"))

        def _sync_remaining_targets() -> None:
            st = display_session_status()
            remaining_list.clear()
            if not st.get("present"):
                remaining.setText(t("display.session_targets_cleared"))
                return
            remaining.setText(
                t(
                    "display.session_targets_left",
                    targets=int(st.get("targets") or 0),
                    displays=int(st.get("displays") or 0),
                )
            )
            for tgt in st.get("target_rows") or []:
                low = tgt.get("adapterLow")
                high = tgt.get("adapterHigh") if tgt.get("adapterHigh") is not None else 0
                tid = tgt.get("targetId")
                if tid is None and tgt.get("id") is not None:
                    tid = tgt.get("id")
                label = f"adapter={low}/{high} targetId={tid}"
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, {
                    "adapterLow": low,
                    "adapterHigh": high,
                    "targetId": tid,
                })
                remaining_list.addItem(item)

        _sync_remaining_targets()
        layout.addWidget(remaining)
        layout.addWidget(QLabel(t("display.session_targets_list")))
        layout.addWidget(remaining_list)
        layout.addWidget(QLabel(t("display.retry_hdr_shortcut")))
        retry = QPushButton(t("display.retry_one"))
        retry_hdr = QPushButton(t("display.retry_hdr"))
        retry_hdr_sel = QPushButton(t("display.retry_hdr_selected"))
        retry_hdr_sel.setToolTip(t("display.retry_hdr_shortcut"))
        remaining_list.setToolTip(t("display.retry_hdr_shortcut"))

        def _retry() -> None:
            r = table.currentRow()
            if r < 0 or r >= len(failed):
                return
            row = failed[r]
            out = retry_display_mode(
                device=row.get("device"),
                width=int(row.get("width") or 0),
                height=int(row.get("height") or 0),
                refresh_hz=row.get("refresh_hz"),
                dry_run=False,
            )
            if out.get("ok"):
                QMessageBox.information(self, "buusdo", t("display.rollback_ok"))
                table.removeRow(r)
                failed.pop(r)
            else:
                QMessageBox.warning(
                    self,
                    "buusdo",
                    t(
                        "display.rollback_failed",
                        devices=str(row.get("device_string") or row.get("device")),
                    ),
                )

        def _hdr_enable_for(row: dict | None) -> bool:
            enable = bool((row or {}).get("hdr_enable"))
            if hdr_step and hdr_step.get("enable") is not None:
                enable = bool(hdr_step.get("enable"))
            return enable

        def _apply_hdr_retry(
            *,
            adapter_low: int,
            adapter_high: int,
            target_id: int,
            enable: bool,
            row: dict | None,
            row_index: int,
        ) -> None:
            out = retry_hdr_target(
                adapter_low=int(adapter_low),
                adapter_high=int(adapter_high or 0),
                target_id=int(target_id),
                enable=enable,
                dry_run=False,
            )
            if out.get("ok"):
                QMessageBox.information(self, "buusdo", t("display.rollback_ok"))
                drop_session_ccd_target(
                    adapter_low=int(adapter_low),
                    adapter_high=int(adapter_high or 0),
                    target_id=int(target_id),
                )
                self._refresh_session_banner()
                _sync_remaining_targets()
                if row is not None and 0 <= row_index < len(failed):
                    if (
                        row.get("targetId") is not None
                        and int(row.get("targetId")) == int(target_id)
                    ) or (
                        row.get("adapterLow") is not None
                        and int(row.get("adapterLow")) == int(adapter_low)
                    ):
                        table.removeRow(row_index)
                        failed.pop(row_index)
            else:
                QMessageBox.warning(
                    self,
                    "buusdo",
                    t("display.rollback_failed", devices=f"HDR target {target_id}"),
                )

        def _retry_hdr() -> None:
            r = table.currentRow()
            row = failed[r] if 0 <= r < len(failed) else None
            enable = _hdr_enable_for(row)
            adapter_low = (row or {}).get("adapterLow")
            adapter_high = (row or {}).get("adapterHigh") or 0
            target_id = (row or {}).get("targetId")
            if target_id is None or adapter_low is None:
                targets = list((hdr_step or {}).get("targets") or [])
                bad = next((tg for tg in targets if not tg.get("ok")), None)
                if not bad:
                    QMessageBox.information(self, "buusdo", t("display.retry_hdr_need_id"))
                    return
                adapter_low = bad.get("adapterLow")
                adapter_high = bad.get("adapterHigh") or 0
                target_id = bad.get("id") if bad.get("id") is not None else bad.get("targetId")
            _apply_hdr_retry(
                adapter_low=int(adapter_low),
                adapter_high=int(adapter_high or 0),
                target_id=int(target_id),
                enable=enable,
                row=row,
                row_index=r,
            )

        def _retry_hdr_selected() -> None:
            item = remaining_list.currentItem()
            if item is None:
                QMessageBox.information(self, "buusdo", t("display.retry_hdr_need_id"))
                return
            data = item.data(Qt.ItemDataRole.UserRole) or {}
            if data.get("adapterLow") is None or data.get("targetId") is None:
                QMessageBox.information(self, "buusdo", t("display.retry_hdr_need_id"))
                return
            # Prefer matching fail-table row when present.
            match_i = -1
            match_row = None
            for i, row in enumerate(failed):
                if (
                    row.get("targetId") is not None
                    and int(row.get("targetId")) == int(data["targetId"])
                    and row.get("adapterLow") is not None
                    and int(row.get("adapterLow")) == int(data["adapterLow"])
                ):
                    match_i = i
                    match_row = row
                    break
            _apply_hdr_retry(
                adapter_low=int(data["adapterLow"]),
                adapter_high=int(data.get("adapterHigh") or 0),
                target_id=int(data["targetId"]),
                enable=_hdr_enable_for(match_row),
                row=match_row,
                row_index=match_i,
            )

        def _clear_hdr_selection() -> None:
            remaining_list.clearSelection()
            remaining_list.setCurrentRow(-1)

        retry.clicked.connect(_retry)
        retry_hdr.clicked.connect(_retry_hdr)
        retry_hdr_sel.clicked.connect(_retry_hdr_selected)
        remaining_list.itemDoubleClicked.connect(lambda _item: _retry_hdr_selected())
        # Keyboard: Return / Ctrl+Return retries; Esc clears selection.
        QShortcut(QKeySequence(Qt.Key.Key_Return), remaining_list, activated=_retry_hdr_selected)
        QShortcut(QKeySequence(Qt.Key.Key_Enter), remaining_list, activated=_retry_hdr_selected)
        QShortcut(QKeySequence("Ctrl+Return"), remaining_list, activated=_retry_hdr_selected)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), remaining_list, activated=_clear_hdr_selection)
        close = QPushButton("OK")
        close.clicked.connect(dlg.accept)
        row = QHBoxLayout()
        row.addWidget(retry)
        row.addWidget(retry_hdr)
        row.addWidget(retry_hdr_sel)
        row.addWidget(close)
        layout.addLayout(row)
        dlg.resize(720, 420)
        dlg.exec()

    def _export_crash_audit(self) -> None:
        data = load_settings()
        last_dir = str(data.get("crash_audit_export_dir") or "")
        suggested = str(Path(last_dir) / "buusdo-crash-audit.jsonl") if last_dir else "buusdo-crash-audit.jsonl"
        while True:
            path, _ = QFileDialog.getSaveFileName(
                self, t("action.export_audit"), suggested, "JSONL (*.jsonl)"
            )
            if not path:
                return
            try:
                export_crash_opt_in_audit(Path(path))
                settings = load_settings()
                settings["crash_audit_export_dir"] = str(Path(path).expanduser().parent)
                save_settings(settings)
                self._status.setText(t("action.export_audit"))
                return
            except OSError as exc:
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Icon.Warning)
                box.setWindowTitle("buusdo")
                box.setText(t("action.export_audit_failed", error=str(exc)))
                retry = box.addButton(
                    t("action.export_audit_retry"), QMessageBox.ButtonRole.AcceptRole
                )
                box.addButton(QMessageBox.StandardButton.Cancel)
                box.exec()
                if box.clickedButton() is not retry:
                    return
                # Remember the failed directory so the next dialog opens there.
                failed_dir = str(Path(path).expanduser().parent)
                settings = load_settings()
                settings["crash_audit_export_dir"] = failed_dir
                save_settings(settings)
                suggested = str(Path(failed_dir) / Path(path).name)

    def _clear_crash_audit(self) -> None:
        clear_crash_opt_in_audit()
        self._status.setText(t("action.clear_audit"))

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
                    raise BuusdoError(t("err.optiscaler_kit"))
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
        opts = self._install_options()
        if opts.pop("_abort", False):
            return
        try:
            result = self._backend.install(self._target, opts)
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
        self._rebuild_tray_recent()
        self._refresh_session_banner()

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
