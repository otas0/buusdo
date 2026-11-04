"""Paired companion device tokens under user_config_dir (C2 Transaction)."""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from buusdo.core.platform_detect import user_config_dir
from buusdo.core.transaction import Transaction

_DEVICES_NAME = "companion_devices.json"


def devices_path() -> Path:
    return user_config_dir() / _DEVICES_NAME


@dataclass(frozen=True)
class PairedDevice:
    device_id: str
    token: str
    label: str
    paired_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "token": self.token,
            "label": self.label,
            "paired_at": self.paired_at,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> PairedDevice:
        return PairedDevice(
            device_id=str(data.get("device_id") or ""),
            token=str(data.get("token") or ""),
            label=str(data.get("label") or "mobile"),
            paired_at=str(data.get("paired_at") or ""),
        )


def _load_raw() -> dict[str, Any]:
    path = devices_path()
    if not path.exists():
        return {"schema_version": 1, "devices": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "devices": []}
    if not isinstance(data, dict):
        return {"schema_version": 1, "devices": []}
    data.setdefault("schema_version", 1)
    if not isinstance(data.get("devices"), list):
        data["devices"] = []
    return data


def list_devices() -> list[PairedDevice]:
    raw = _load_raw()
    out: list[PairedDevice] = []
    for item in raw.get("devices") or []:
        if isinstance(item, dict) and item.get("token") and item.get("device_id"):
            out.append(PairedDevice.from_dict(item))
    return out


def _save(raw: dict[str, Any]) -> None:
    path = devices_path()
    payload = json.dumps(raw, indent=2, ensure_ascii=False) + "\n"
    with Transaction() as tx:
        tx.ensure_dir(path.parent)
        tx.write_text(path, payload)
        tx.commit()


def add_device(*, label: str = "mobile") -> PairedDevice:
    """Create a paired device with a fresh bearer token (transactional write)."""
    from buusdo.core.config_store import set_companion_last_paired_label

    device = PairedDevice(
        device_id=secrets.token_hex(8),
        token=secrets.token_urlsafe(32),
        label=(label or "mobile")[:64],
        paired_at=datetime.now(timezone.utc).isoformat(),
    )
    raw = _load_raw()
    devices = [d for d in list_devices() if d.device_id != device.device_id]
    devices.append(device)
    raw["devices"] = [d.to_dict() for d in devices]
    _save(raw)
    # Label only (feature-flagged); tokens stay in companion_devices.json via Transaction.
    set_companion_last_paired_label(device.label)
    return device


def remove_device(device_id: str) -> bool:
    raw = _load_raw()
    before = list_devices()
    kept = [d for d in before if d.device_id != device_id]
    if len(kept) == len(before):
        return False
    raw["devices"] = [d.to_dict() for d in kept]
    _save(raw)
    return True


def clear_devices() -> None:
    _save({"schema_version": 1, "devices": []})


def token_is_paired(token: str) -> bool:
    needle = (token or "").strip()
    if not needle:
        return False
    return any(d.token == needle for d in list_devices())
