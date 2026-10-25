"""Main window — backend-agnostic (C3)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from buusdo.backends import get_backend
from buusdo.core.backend import EnhancementBackend, EnhancementTarget
from buusdo.core.config_store import get_reshade_kit_path, set_reshade_kit_path
from buusdo.core.errors import BuusdoError, UnsafeTargetError
from buusdo.ui.blocked_page import BlockedPage


class MainWindow(QMainWindow):
    def __init__(self, backend: EnhancementBackend | None = None):
        super().__init__()
        self.setWindowTitle("buusdo")
        self.resize(820, 560)

        self._backend = backend or get_backend()
        self._target: EnhancementTarget | None = None
        self._games: list[EnhancementTarget] = []

        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)

        header = QLabel("buusdo")
        hf = header.font()
        hf.setPointSize(20)
        hf.setBold(True)
        header.setFont(hf)
        outer.addWidget(header)

        subtitle = QLabel("图形增强调度器 · 配置协调器")
        outer.addWidget(subtitle)
        outer.addWidget(QLabel(f"后端：{self._backend.platform_id()}"))

        self._stack = QStackedWidget()
        outer.addWidget(self._stack, stretch=1)

        self._home = QWidget()
        home_layout = QVBoxLayout(self._home)

        home_layout.addWidget(QLabel("已发现的游戏："))
        self._game_list = QListWidget()
        self._game_list.currentRowChanged.connect(self._on_game_selected)
        home_layout.addWidget(self._game_list, stretch=1)

        home_layout.addWidget(QLabel("能力："))
        self._cap_list = QListWidget()
        home_layout.addWidget(self._cap_list)

        buttons = QHBoxLayout()
        self._btn_scan = QPushButton("扫描 Steam 库")
        self._btn_kit = QPushButton("选择 ReShade 工具包…")
        self._btn_install = QPushButton("部署增强")
        self._btn_uninstall = QPushButton("卸载")
        buttons.addWidget(self._btn_scan)
        buttons.addWidget(self._btn_kit)
        buttons.addWidget(self._btn_install)
        buttons.addWidget(self._btn_uninstall)
        home_layout.addLayout(buttons)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        home_layout.addWidget(self._status)

        self._stack.addWidget(self._home)

        self._btn_scan.clicked.connect(self._scan_games)
        self._btn_kit.clicked.connect(self._pick_reshade_kit)
        self._btn_install.clicked.connect(self._on_install)
        self._btn_uninstall.clicked.connect(self._on_uninstall)

        kit = get_reshade_kit_path()
        if kit:
            self._status.setText(f"ReShade 工具包：{kit}")

    def _scan_games(self) -> None:
        self._games = self._backend.discover_games()
        self._game_list.clear()
        for game in self._games:
            runtime = game.metadata.get("runtime")
            suffix = " [Proton]" if runtime == "proton" else ""
            item = QListWidgetItem(f"{game.name}{suffix}")
            item.setToolTip(str(game.install_path))
            self._game_list.addItem(item)
        self._status.setText(f"发现 {len(self._games)} 个 Steam 游戏。")
        if not self._games:
            self._status.setText("未发现 Steam 游戏。可检查 STEAM_ROOT 环境变量。")

    def _on_game_selected(self, row: int) -> None:
        if row < 0 or row >= len(self._games):
            self._target = None
            self._cap_list.clear()
            return
        self._target = self._games[row]
        self._refresh_capabilities()
        st = self._backend.status(self._target)
        installed = "已部署" if st.get("installed") or st.get("vkbasalt_configured") else "未部署"
        self._status.setText(f"{self._target.name} — {installed}\n{self._target.install_path}")

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

    def _pick_reshade_kit(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择 ReShade 工具包目录（含 ReShade64.dll）")
        if not path:
            return
        set_reshade_kit_path(path)
        self._status.setText(f"ReShade 工具包：{path}")

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
            result = self._backend.install(self._target)
        except UnsafeTargetError as exc:
            self._show_blocked(exc)
            return
        except BuusdoError as exc:
            QMessageBox.warning(self, "buusdo", str(exc))
            return
        self._status.setText(result.message)
        self._stack.setCurrentWidget(self._home)
        self._refresh_capabilities()

    def _on_uninstall(self) -> None:
        if not self._target:
            QMessageBox.information(self, "buusdo", "请先扫描并选择游戏。")
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
        self._stack.setCurrentWidget(self._home)
