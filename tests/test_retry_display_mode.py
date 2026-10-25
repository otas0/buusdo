"""Unit tests for retry_display_mode with mocked Win32 display APIs."""

from __future__ import annotations

import ctypes
from types import SimpleNamespace

import pytest

from buusdo.backends import windows_display as wd


class _FakeUser32:
    def __init__(self, *, enum_ok: bool = True, change_code: int = 0):
        self.enum_ok = enum_ok
        self.change_code = change_code
        self.ex_calls: list[tuple] = []
        self.w_calls: list[tuple] = []

    def EnumDisplaySettingsW(self, device, mode_num, dm_ref):
        if not self.enum_ok:
            return 0
        # dm_ref is byref(DEVMODEW); leave fields for caller to overwrite.
        return 1

    def ChangeDisplaySettingsExW(self, device, mode, hwnd, flags, lparam):
        self.ex_calls.append((device, flags))
        return self.change_code

    def ChangeDisplaySettingsW(self, mode, flags):
        self.w_calls.append((flags,))
        return self.change_code


@pytest.fixture
def fake_user32(monkeypatch):
    fake = _FakeUser32()
    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(user32=fake), raising=False)
    return fake


def test_retry_display_mode_ex_success(fake_user32) -> None:
    out = wd.retry_display_mode(
        device=r"\\.\DISPLAY2",
        width=1920,
        height=1080,
        refresh_hz=60,
        dry_run=False,
    )
    assert out["ok"] is True
    assert out["action"] == "ChangeDisplaySettingsExW"
    assert out["device"] == r"\\.\DISPLAY2"
    assert out["code"] == 0
    assert fake_user32.ex_calls
    assert fake_user32.ex_calls[0][0] == r"\\.\DISPLAY2"


def test_retry_display_mode_dry_run_uses_cds_test(fake_user32) -> None:
    out = wd.retry_display_mode(
        device=r"\\.\DISPLAY1",
        width=2560,
        height=1440,
        dry_run=True,
    )
    assert out["ok"] is True
    assert out["dry_run"] is True
    assert fake_user32.ex_calls[0][1] == wd.CDS_TEST


def test_retry_display_mode_enum_fail(monkeypatch) -> None:
    fake = _FakeUser32(enum_ok=False)
    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(user32=fake), raising=False)
    out = wd.retry_display_mode(device=None, width=800, height=600)
    assert out["ok"] is False
    assert out["action"] == "enum"


def test_retry_display_mode_change_fail(monkeypatch) -> None:
    fake = _FakeUser32(change_code=1)
    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(user32=fake), raising=False)
    out = wd.retry_display_mode(
        device=r"\\.\DISPLAY1", width=1280, height=720, refresh_hz=75
    )
    assert out["ok"] is False
    assert out["code"] == 1


def test_retry_hdr_target_failure(monkeypatch) -> None:
    class FakeUser32:
        def DisplayConfigSetDeviceInfo(self, req_ref):
            return 87  # ERROR_INVALID_PARAMETER-ish

    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(user32=FakeUser32()), raising=False)
    out = wd.retry_hdr_target(
        adapter_low=9, adapter_high=0, target_id=2, enable=False, dry_run=False
    )
    assert out["ok"] is False
    assert out["status"] == 87
