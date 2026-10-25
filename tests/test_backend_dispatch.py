from pathlib import Path

import pytest

from buusdo.backends import get_backend
from buusdo.backends.macos import MacOSBackend
from buusdo.core.backend import EnhancementTarget
from buusdo.core.errors import UnsafeTargetError
from buusdo.core.platform_detect import HostPlatform


def test_factory_macos() -> None:
    backend = get_backend(HostPlatform.MACOS)
    assert backend.platform_id() == "macos"
    assert isinstance(backend, MacOSBackend)


def test_macos_blocks_unconfirmed_compat(tmp_path: Path) -> None:
    backend = get_backend(HostPlatform.MACOS)
    target = EnhancementTarget(name="Unknown", install_path=tmp_path)
    with pytest.raises(UnsafeTargetError):
        backend.install(target)


def test_macos_install_with_confirmed_compat(tmp_path: Path) -> None:
    backend = get_backend(HostPlatform.MACOS)
    target = EnhancementTarget(
        name="Safe",
        install_path=tmp_path,
        metadata={"compat_confirmed": True},
    )
    result = backend.install(target)
    assert result.success
    marker = tmp_path / ".buusdo" / "metalfx" / "buusdo_metalfx.json"
    assert marker.exists()
    text = marker.read_text()
    assert "metalfx_compat" in text
    assert "DLSS" not in text


def test_macos_module_has_no_injection_strings() -> None:
    src = Path(__file__).resolve().parents[1] / "buusdo" / "backends" / "macos.py"
    text = src.read_text(encoding="utf-8")
    # Documented as forbidden constants only — must not be *used* as injection.
    assert "os.environ" not in text or "DYLD_INSERT_LIBRARIES" not in text.split("os.environ")[0]
    assert "ctypes" not in text
    assert "task_for_pid(" not in text
    assert "mach_inject(" not in text
