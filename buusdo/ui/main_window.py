"""Main window — backend-agnostic (C3)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from buusdo.backends import get_backend
from buusdo.core.backend import EnhancementBackend, EnhancementTarget
from buusdo.core.errors import UnsafeTargetError
from buusdo.ui.blocked_page import BlockedPage


class MainWindow(QMainWindow):
    def __init__(self, backend: EnhancementBackend | None = None):
        super().__init__()
        self.setWindowTitle("buusdo")
        self.resize(720, 480)

        self._backend = backend or get_backend()
        self._target: EnhancementTarget | None = None

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

        platform_label = QLabel(f"后端：{self._backend.platform_id()}")
        outer.addWidget(platform_label)

        self._stack = QStackedWidget()
        outer.addWidget(self._stack, stretch=1)

        self._home = QWidget()
        home_layout = QVBoxLayout(self._home)
        home_layout.addWidget(QLabel("能力一览（选中演示目标后刷新）："))
        self._cap_list = QListWidget()
        home_layout.addWidget(self._cap_list)

        buttons = QHBoxLayout()
        self._btn_demo = QPushButton("加载演示目标")
        self._btn_install = QPushButton("应用增强（scaffold）")
        self._btn_uninstall = QPushButton("卸载")
        buttons.addWidget(self._btn_demo)
        buttons.addWidget(self._btn_install)
        buttons.addWidget(self._btn_uninstall)
        home_layout.addLayout(buttons)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        home_layout.addWidget(self._status)

        self._stack.addWidget(self._home)

        self._btn_demo.clicked.connect(self._load_demo_target)
        self._btn_install.clicked.connect(self._on_install)
        self._btn_uninstall.clicked.connect(self._on_uninstall)

    def _load_demo_target(self) -> None:
        demo_root = Path.home() / ".buusdo-demo-target"
        demo_root.mkdir(parents=True, exist_ok=True)
        # Backend-agnostic demo metadata; macOS uses compat_confirmed, others ignore.
        self._target = EnhancementTarget(
            name="Demo Target",
            install_path=demo_root,
            metadata={"compat_confirmed": True},
        )
        self._refresh_capabilities()
        self._status.setText(f"演示目标：{demo_root}")

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

    def _show_blocked(self, error: UnsafeTargetError) -> None:
        page = BlockedPage(error)
        # Replace any previous blocked page beyond home.
        while self._stack.count() > 1:
            w = self._stack.widget(1)
            self._stack.removeWidget(w)
            w.deleteLater()
        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)

    def _on_install(self) -> None:
        if not self._target:
            QMessageBox.information(self, "buusdo", "请先加载演示目标。")
            return
        try:
            result = self._backend.install(self._target)
        except UnsafeTargetError as exc:
            self._show_blocked(exc)
            return
        self._status.setText(result.message)
        self._stack.setCurrentWidget(self._home)

    def _on_uninstall(self) -> None:
        if not self._target:
            QMessageBox.information(self, "buusdo", "请先加载演示目标。")
            return
        try:
            result = self._backend.uninstall(self._target)
        except UnsafeTargetError as exc:
            self._show_blocked(exc)
            return
        self._status.setText(result.message)
        self._stack.setCurrentWidget(self._home)
