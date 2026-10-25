"""Main window — backend-agnostic (C3)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from buusdo.assets import logo_path
from buusdo.backends import get_backend
from buusdo.core.backend import EnhancementBackend, EnhancementTarget
from buusdo.core.config_store import (
    export_configs,
    get_reshade_kit_path,
    import_configs,
    set_optiscaler_kit_path,
    set_reshade_kit_path,
    update_game_config,
)
from buusdo.core.errors import BuusdoError, UnsafeTargetError
from buusdo.core.graphics_detect import GraphicsApi
from buusdo.core.history import list_events
from buusdo.core.library_cache import invalidate_cache
from buusdo.core.platform_detect import steam_roots
from buusdo.core.steam_launch import list_steam_users
from buusdo.ui.blocked_page import BlockedPage
from buusdo.ui.theme import badge_color


class MainWindow(QMainWindow):
    def __init__(self, backend: EnhancementBackend | None = None):
        super().__init__()
        self.setWindowTitle("buusdo")
        self.resize(960, 680)

        logo = logo_path()
        if logo.is_file():
            self.setWindowIcon(QIcon(str(logo)))

        self._backend = backend or get_backend()
        self._target: EnhancementTarget | None = None
        self._games: list[EnhancementTarget] = []
        self._filtered: list[EnhancementTarget] = []

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
        sub = QLabel("图形增强调度器 · 配置协调器")
        sub.setObjectName("brandSubtitle")
        brand_text.addWidget(sub)
        brand.addLayout(brand_text)
        brand.addStretch(1)
        outer.addLayout(brand)
        outer.addWidget(QLabel(f"后端：{self._backend.platform_id()}"))

        self._stack = QStackedWidget()
        outer.addWidget(self._stack, stretch=1)

        self._home = QWidget()
        home = QVBoxLayout(self._home)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("过滤："))
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("按名称搜索…")
        self._filter.setAccessibleName("游戏列表过滤")
        self._filter.textChanged.connect(self._refresh_game_list)
        filter_row.addWidget(self._filter)
        home.addLayout(filter_row)

        home.addWidget(QLabel("已发现的游戏："))
        self._game_list = QListWidget()
        self._game_list.setAccessibleName("游戏列表")
        self._game_list.currentRowChanged.connect(self._on_game_selected)
        home.addWidget(self._game_list, stretch=1)

        pref_row = QHBoxLayout()
        pref_row.addWidget(QLabel("可执行文件："))
        self._exe_combo = QComboBox()
        pref_row.addWidget(self._exe_combo, stretch=1)
        pref_row.addWidget(QLabel("API："))
        self._api_combo = QComboBox()
        self._api_combo.addItem("自动", "")
        for api in GraphicsApi:
            if api is GraphicsApi.UNKNOWN:
                continue
            self._api_combo.addItem(api.value, api.value)
        pref_row.addWidget(self._api_combo)
        home.addLayout(pref_row)

        user_row = QHBoxLayout()
        user_row.addWidget(QLabel("Steam 用户："))
        self._steam_user = QComboBox()
        self._steam_user.setAccessibleName("Steam 用户选择")
        user_row.addWidget(self._steam_user, stretch=1)
        home.addLayout(user_row)
        self._reload_steam_users()

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("安装模式："))
        self._mode_combo = QComboBox()
        for mode, label in (
            ("reshade", "ReShade"),
            ("optiscaler", "OptiScaler / 神经画质"),
            ("vkbasalt", "vkBasalt（近似）"),
            ("goverlay", "Goverlay"),
            ("display_profile", "显示/HDR 配置"),
            ("rtx_remix_enable", "启用 RTX Remix mod"),
            ("rtx_remix_disable", "禁用 RTX Remix mod"),
        ):
            self._mode_combo.addItem(label, mode)
        mode_row.addWidget(self._mode_combo)
        home.addLayout(mode_row)

        home.addWidget(QLabel("能力："))
        self._cap_list = QListWidget()
        home.addWidget(self._cap_list)

        home.addWidget(QLabel("操作历史："))
        self._history_list = QListWidget()
        home.addWidget(self._history_list)

        buttons = QHBoxLayout()
        self._btn_scan = QPushButton("扫描 Steam 库")
        self._btn_force = QPushButton("强制全量刷新")
        self._btn_kit = QPushButton("ReShade 工具包…")
        self._btn_opti = QPushButton("OptiScaler 工具包…")
        self._btn_install = QPushButton("部署增强")
        self._btn_uninstall = QPushButton("卸载")
        self._btn_export = QPushButton("导出配置")
        self._btn_import = QPushButton("导入配置")
        self._btn_history = QPushButton("刷新历史")
        for b in (
            self._btn_scan,
            self._btn_force,
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
        self._btn_kit.clicked.connect(self._pick_reshade_kit)
        self._btn_opti.clicked.connect(self._pick_optiscaler_kit)
        self._btn_install.clicked.connect(self._on_install)
        self._btn_uninstall.clicked.connect(self._on_uninstall)
        self._btn_export.clicked.connect(self._on_export)
        self._btn_import.clicked.connect(self._on_import)
        self._btn_history.clicked.connect(self._refresh_history)

        kit = get_reshade_kit_path()
        if kit:
            self._status.setText(f"ReShade 工具包：{kit}")
        self._refresh_history()

    def _reload_steam_users(self) -> None:
        self._steam_user.clear()
        self._steam_user.addItem("（默认第一个）", "")
        try:
            roots = steam_roots()
        except Exception:
            roots = []
        for profile in list_steam_users(roots):
            self._steam_user.addItem(profile.label, profile.steam_id3)

    def _scan_games(self, *, force: bool) -> None:
        if force:
            invalidate_cache()
        # force path: backends use cache; invalidate then rediscover
        self._games = self._backend.discover_games()
        if force:
            # second pass after invalidate already done; discover fills cache
            pass
        self._refresh_game_list()
        self._reload_steam_users()
        self._status.setText(f"发现 {len(self._games)} 个 Steam 游戏。")

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
            item = QListWidgetItem(f"{badge} {game.name}{runtime}")
            item.setToolTip(str(game.install_path))
            item.setForeground(badge_color(kind))
            self._game_list.addItem(item)
            self._filtered.append(game)

    def _badge_for_status(self, st: dict) -> tuple[str, str]:
        if st.get("installed") or (st.get("reshade") or {}).get("installed"):
            return "ok", "[已部署]"
        if st.get("vkbasalt_configured"):
            return "warn", "[vkBasalt]"
        if (st.get("optiscaler") or {}).get("installed"):
            return "ok", "[神经画质]"
        remix = st.get("rtx_remix") or {}
        if remix.get("enabled") is True:
            return "warn", "[Remix已启用]"
        if remix.get("present"):
            return "warn", "[Remix可用]"
        return "muted", "[未部署]"

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
        self._status.setText(f"{self._target.name} — {badge}\n{self._target.install_path}")

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
        api = self._target.metadata.get("graphics_api")
        if api:
            idx = self._api_combo.findData(api)
            if idx >= 0:
                self._api_combo.setCurrentIndex(idx)
        steam_id3 = self._target.metadata.get("steam_id3")
        if steam_id3:
            idx = self._steam_user.findData(str(steam_id3))
            if idx >= 0:
                self._steam_user.setCurrentIndex(idx)

    def _refresh_capabilities(self) -> None:
        self._cap_list.clear()
        if not self._target:
            return
        for cap in self._backend.list_capabilities(self._target):
            avail = "可用" if cap.available else "不可用"
            line = f"[{avail}] {cap.title} — {cap.description}"
            if cap.notes:
                line += f"（{cap.notes}）"
            self._cap_list.addItem(line)

    def _refresh_history(self) -> None:
        self._history_list.clear()
        for event in list_events(limit=50):
            ok = "OK" if event.get("success") else "FAIL"
            self._history_list.addItem(
                f"{event.get('ts', '')} [{ok}] {event.get('action')} · "
                f"{event.get('target')} — {event.get('message', '')}"
            )

    def _pick_reshade_kit(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择 ReShade 工具包目录")
        if path:
            set_reshade_kit_path(path)
            self._status.setText(f"ReShade 工具包：{path}")

    def _pick_optiscaler_kit(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择 OptiScaler 工具包目录")
        if path:
            set_optiscaler_kit_path(path)
            self._status.setText(f"OptiScaler 工具包：{path}")

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
            opts["notes"] = "UI 保存的 HDR 偏好（非宣称已开启光追）"
        return opts

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
            QMessageBox.information(self, "buusdo", "请先扫描并选择游戏。")
            return
        try:
            result = self._backend.install(self._target, self._install_options())
        except UnsafeTargetError as exc:
            self._show_blocked(exc)
            self._refresh_history()
            return
        except BuusdoError as exc:
            QMessageBox.warning(self, "buusdo", str(exc))
            self._refresh_history()
            return
        self._status.setText(result.message)
        self._stack.setCurrentWidget(self._home)
        self._refresh_game_list()
        self._refresh_history()

    def _on_uninstall(self) -> None:
        if not self._target:
            QMessageBox.information(self, "buusdo", "请先扫描并选择游戏。")
            return
        try:
            result = self._backend.uninstall(self._target)
        except UnsafeTargetError as exc:
            self._show_blocked(exc)
            self._refresh_history()
            return
        except BuusdoError as exc:
            QMessageBox.warning(self, "buusdo", str(exc))
            self._refresh_history()
            return
        self._status.setText(result.message)
        self._refresh_game_list()
        self._refresh_history()

    def _on_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "导出配置", "buusdo-config.zip", "Zip (*.zip)")
        if not path:
            return
        export_configs(path)
        self._status.setText(f"已导出配置：{path}")

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "导入配置", "", "Zip (*.zip)")
        if not path:
            return
        result = import_configs(path)
        self._status.setText(f"已导入：{', '.join(result.get('imported') or [])}")
