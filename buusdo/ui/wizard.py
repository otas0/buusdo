"""First-run setup wizard for kit paths with integrity checks."""

from __future__ import annotations

from pathlib import Path

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
from buusdo.core.kit_validate import validate_optiscaler_kit, validate_reshade_kit


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
        self._reshade_status = QLabel("")
        self._opti = QLabel(str(get_optiscaler_kit_path() or "—"))
        self._opti_status = QLabel("")

        row1 = QHBoxLayout()
        b1 = QPushButton("ReShade…")
        b1.clicked.connect(self._pick_reshade)
        row1.addWidget(b1)
        row1.addWidget(self._reshade)
        layout.addLayout(row1)
        layout.addWidget(self._reshade_status)

        row2 = QHBoxLayout()
        b2 = QPushButton("OptiScaler…")
        b2.clicked.connect(self._pick_opti)
        row2.addWidget(b2)
        row2.addWidget(self._opti)
        layout.addLayout(row2)
        layout.addWidget(self._opti_status)

        actions = QHBoxLayout()
        skip = QPushButton("Skip / 跳过")
        done = QPushButton("Done / 完成")
        skip.clicked.connect(self._finish)
        done.clicked.connect(self._finish)
        actions.addWidget(skip)
        actions.addWidget(done)
        layout.addLayout(actions)

        self._refresh_status()

    @staticmethod
    def _set_status(label: QLabel, ok: bool, detail: str) -> None:
        if ok:
            label.setText(f"{t('wizard.kit_ok')}: {detail}")
            label.setStyleSheet("color: #2E86AB;")
        else:
            label.setText(f"{t('wizard.kit_bad')}: {detail}")
            label.setStyleSheet("color: #C73E1D; font-weight: 600;")

    def _refresh_status(self) -> None:
        rs = validate_reshade_kit(get_reshade_kit_path())
        self._set_status(
            self._reshade_status,
            rs.ok,
            ", ".join(rs.found) if rs.ok else ", ".join(rs.missing) or rs.message,
        )
        op = validate_optiscaler_kit(get_optiscaler_kit_path())
        self._set_status(
            self._opti_status,
            op.ok,
            ", ".join(op.found) if op.ok else ", ".join(op.missing) or op.message,
        )

    def _pick_reshade(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "ReShade kit")
        if path:
            set_reshade_kit_path(path)
            self._reshade.setText(path)
            self._refresh_status()

    def _pick_opti(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "OptiScaler kit")
        if path:
            set_optiscaler_kit_path(path)
            self._opti.setText(path)
            self._refresh_status()

    def _finish(self) -> None:
        data = load_settings()
        data["wizard_completed"] = True
        save_settings(data)
        self.accept()
