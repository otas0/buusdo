"""Companion device tokens persist via Transaction under user_config_dir."""

from __future__ import annotations

from pathlib import Path

import pytest

from buusdo.companion import devices as devices_mod
from buusdo.companion.devices import (
    add_device,
    clear_devices,
    list_devices,
    remove_device,
    token_is_paired,
)


@pytest.fixture()
def companion_cfg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(devices_mod, "user_config_dir", lambda: tmp_path)
    return tmp_path


def test_add_and_auth_token(companion_cfg: Path) -> None:
    clear_devices()
    assert list_devices() == []
    d = add_device(label="phone")
    assert (companion_cfg / "companion_devices.json").is_file()
    assert token_is_paired(d.token)
    assert not token_is_paired("nope")
    assert len(list_devices()) == 1


def test_remove_and_clear(companion_cfg: Path) -> None:
    clear_devices()
    a = add_device(label="a")
    b = add_device(label="b")
    assert remove_device(a.device_id)
    assert not token_is_paired(a.token)
    assert token_is_paired(b.token)
    clear_devices()
    assert list_devices() == []
