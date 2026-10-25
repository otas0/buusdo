"""First-run setup wizard for kit paths with integrity checks."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
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

_HIGHLIGHT = (
    "color: #C73E1D; font-weight: 600; border: 1px solid #C73E1D; padding: 4px;"
)
_NORMAL = ""


def needs_wizard() -> bool:
    settings = load_settings()
    if settings.get("wizard_completed"):
        return False
    return get_reshade_kit_path() is None and get_optiscaler_kit_path() is None


class FirstRunWizard(QDialog):
    def __init__(self, parent=None, *, focus_side: str | None = None):
        super().__init__(parent)
        # focus_side: "reshade" | "optiscaler" | None — highlight / auto-open missing side.
        self._focus_side = focus_side if focus_side in ("reshade", "optiscaler") else None
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
        self._pick_reshade_btn = QPushButton("ReShade…")
        self._pick_reshade_btn.clicked.connect(self._pick_reshade)
        self._reselect_reshade = QPushButton(t("action.reselect_kit"))
        self._reselect_reshade.clicked.connect(self._pick_reshade)
        self._open_reshade = QPushButton(t("action.open_kit_folder"))
        self._open_reshade.clicked.connect(lambda: self._open_folder(get_reshade_kit_path()))
        row1.addWidget(self._pick_reshade_btn)
        row1.addWidget(self._reshade)
        row1.addWidget(self._reselect_reshade)
        row1.addWidget(self._open_reshade)
        layout.addLayout(row1)
        layout.addWidget(self._reshade_status)

        row2 = QHBoxLayout()
        self._pick_opti_btn = QPushButton("OptiScaler…")
        self._pick_opti_btn.clicked.connect(self._pick_opti)
        self._reselect_opti = QPushButton(t("action.reselect_kit"))
        self._reselect_opti.clicked.connect(self._pick_opti)
        self._open_opti = QPushButton(t("action.open_kit_folder"))
        self._open_opti.clicked.connect(lambda: self._open_folder(get_optiscaler_kit_path()))
        row2.addWidget(self._pick_opti_btn)
        row2.addWidget(self._opti)
        row2.addWidget(self._reselect_opti)
        row2.addWidget(self._open_opti)
        layout.addLayout(row2)
        layout.addWidget(self._opti_status)

        actions = QHBoxLayout()
        self._skip = QPushButton("Skip / 跳过")
        self._done = QPushButton("Done / 完成")
        self._skip.clicked.connect(self._finish_skip)
        self._done.clicked.connect(self._finish_done)
        actions.addWidget(self._skip)
        actions.addWidget(self._done)
        layout.addLayout(actions)

        self._refresh_status()
        self._apply_focus_side()

    def _apply_focus_side(self) -> None:
        if self._focus_side == "reshade":
            self._set_highlight(self._pick_reshade_btn, True)
            self._pick_reshade_btn.setDefault(True)
            self._pick_reshade_btn.setFocus()
        elif self._focus_side == "optiscaler":
            self._set_highlight(self._pick_opti_btn, True)
            self._pick_opti_btn.setDefault(True)
            self._pick_opti_btn.setFocus()

    def _has_valid_kit(self) -> bool:
        return validate_reshade_kit(get_reshade_kit_path()).ok or validate_optiscaler_kit(
            get_optiscaler_kit_path()
        ).ok

    @staticmethod
    def _open_folder(path: Path | str | None) -> None:
        if not path:
            return
        p = Path(path)
        if p.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(p.resolve())))

    @staticmethod
    def _set_status(label: QLabel, ok: bool, detail: str) -> None:
        if ok:
            label.setText(f"{t('wizard.kit_ok')}: {detail}")
            label.setStyleSheet("color: #2E86AB;")
        else:
            label.setText(f"{t('wizard.kit_bad')}: {detail}")
            label.setStyleSheet("color: #C73E1D; font-weight: 600;")

    @staticmethod
    def _set_highlight(btn: QPushButton, on: bool) -> None:
        btn.setStyleSheet(_HIGHLIGHT if on else _NORMAL)
        btn.setEnabled(True)

    def _refresh_status(self) -> None:
        rs = validate_reshade_kit(get_reshade_kit_path())
        self._set_status(
            self._reshade_status,
            rs.ok,
            ", ".join(rs.found) if rs.ok else ", ".join(rs.missing) or rs.message,
        )
        missing_r = bool(get_reshade_kit_path()) and not rs.ok
        self._open_reshade.setEnabled(bool(get_reshade_kit_path()))
        self._set_highlight(self._open_reshade, missing_r)
        self._set_highlight(self._reselect_reshade, missing_r or get_reshade_kit_path() is None)

        op = validate_optiscaler_kit(get_optiscaler_kit_path())
        self._set_status(
            self._opti_status,
            op.ok,
            ", ".join(op.found) if op.ok else ", ".join(op.missing) or op.message,
        )
        missing_o = bool(get_optiscaler_kit_path()) and not op.ok
        self._open_opti.setEnabled(bool(get_optiscaler_kit_path()))
        self._set_highlight(self._open_opti, missing_o)
        self._set_highlight(self._reselect_opti, missing_o or get_optiscaler_kit_path() is None)

        self._done.setEnabled(self._has_valid_kit())

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

    def _finish_skip(self) -> None:
        reply = QMessageBox.question(
            self,
            "buusdo",
            t("wizard.skip_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        data = load_settings()
        data["wizard_completed"] = True
        data["wizard_skipped_kits"] = True
        save_settings(data)
        self.accept()

    def _finish_done(self) -> None:
        if not self._has_valid_kit():
            QMessageBox.warning(self, "buusdo", t("wizard.need_kit"))
            return
        data = load_settings()
        data["wizard_completed"] = True
        data["wizard_skipped_kits"] = False
        save_settings(data)
        self.accept()
