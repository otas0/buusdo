"""First-run setup wizard for kit paths."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from buusdo.core.config_store import (
    get_optiscaler_kit_path,
    get_reshade_kit_path,
    load_settings,
    save_settings,
    set_optiscaler_kit_path,
    set_reshade_kit_path,
)
from buusdo.core.i18n import t


def needs_wizard() -> bool:
    settings = load_settings()
    if settings.get("wizard_completed"):
        return False
    return get_reshade_kit_path() is None and get_optiscaler_kit_path() is None


class FirstRunWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("wizard.title"))
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(t("wizard.title")))
        hint = QLabel(t("wizard.hint"))
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._reshade = QLabel(str(get_reshade_kit_path() or "—"))
        self._opti = QLabel(str(get_optiscaler_kit_path() or "—"))
        row1 = QHBoxLayout()
        b1 = QPushButton("ReShade…")
        b1.clicked.connect(self._pick_reshade)
        row1.addWidget(b1)
        row1.addWidget(self._reshade)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        b2 = QPushButton("OptiScaler…")
        b2.clicked.connect(self._pick_opti)
        row2.addWidget(b2)
        row2.addWidget(self._opti)
        layout.addLayout(row2)

        actions = QHBoxLayout()
        skip = QPushButton("Skip / 跳过")
        done = QPushButton("Done / 完成")
        skip.clicked.connect(self._finish)
        done.clicked.connect(self._finish)
        actions.addWidget(skip)
        actions.addWidget(done)
        layout.addLayout(actions)

    def _pick_reshade(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "ReShade kit")
        if path:
            set_reshade_kit_path(path)
            self._reshade.setText(path)

    def _pick_opti(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "OptiScaler kit")
        if path:
            set_optiscaler_kit_path(path)
            self._opti.setText(path)

    def _finish(self) -> None:
        data = load_settings()
        data["wizard_completed"] = True
        save_settings(data)
        self.accept()
