"""Linux vkBasalt deploy options dialog (preset / sharpness / Steam / config path)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from buusdo.core.i18n import t
from buusdo.core.vkbasalt_prefs import get_remembered_config_path, set_remembered_config_path
from buusdo.core.vkbasalt_template import list_presets


class LinuxDeployDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        preset: str = "cas",
        sharpness: float = 0.4,
        config_path: str = "",
    ):
        super().__init__(parent)
        self.setWindowTitle(t("linux.deploy_title"))
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._preset = QComboBox()
        for name in list_presets():
            self._preset.addItem(name, name)
        idx = self._preset.findData(preset)
        if idx >= 0:
            self._preset.setCurrentIndex(idx)
        form.addRow(t("linux.preset"), self._preset)
        self._sharp = QDoubleSpinBox()
        self._sharp.setRange(0.0, 1.0)
        self._sharp.setSingleStep(0.05)
        self._sharp.setValue(float(sharpness))
        form.addRow(t("linux.sharpness"), self._sharp)
        path_row = QHBoxLayout()
        self._config = QLineEdit(config_path or get_remembered_config_path())
        self._config.setPlaceholderText("vkBasalt.conf")
        browse = QPushButton(t("linux.browse_config"))
        browse.clicked.connect(self._browse)
        path_row.addWidget(self._config)
        path_row.addWidget(browse)
        form.addRow(t("linux.config_path"), path_row)
        self._write_steam = QCheckBox(t("linux.write_steam"))
        self._write_steam.setChecked(True)
        form.addRow(self._write_steam)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, t("linux.config_path"), "", "Config (*.conf);;All (*)"
        )
        if path:
            self._config.setText(path)

    def options(self) -> dict:
        opts = {
            "vkbasalt_preset": self._preset.currentData() or "cas",
            "cas_sharpness": float(self._sharp.value()),
            "write_steam_launch": self._write_steam.isChecked(),
        }
        conf = self._config.text().strip()
        if conf:
            opts["VKBASALT_CONFIG_FILE"] = str(Path(conf).expanduser())
            set_remembered_config_path(opts["VKBASALT_CONFIG_FILE"])
        return opts
