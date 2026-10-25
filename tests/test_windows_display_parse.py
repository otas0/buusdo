"""Non-Windows unit coverage for display profile parsing helpers."""

from buusdo.backends.windows_display import apply_display_profile
from buusdo.core.display_profile import DisplayProfile
from buusdo.core.errors import BuusdoError
import pytest


def test_apply_on_non_windows_is_noop() -> None:
    profile = DisplayProfile(name="t", resolution="1920x1080", hdr_preferred=True)
    result = apply_display_profile(profile, dry_run=True)
    # On macOS/Linux CI this returns not_windows
    assert "applied" in result
    assert result.get("reason") == "not_windows" or "steps" in result


def test_invalid_resolution_raises_on_windows_only() -> None:
    profile = DisplayProfile(name="t", resolution="nope")
    # On non-Windows, apply returns early before parse — so only assert shape
    try:
        result = apply_display_profile(profile)
        assert result.get("reason") == "not_windows"
    except BuusdoError:
        # Windows path
        pass
