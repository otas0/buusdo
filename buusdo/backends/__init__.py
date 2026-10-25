"""Backend factory. Platform dispatch lives only here and in platform_detect (C3)."""

from __future__ import annotations

from buusdo.core.backend import EnhancementBackend
from buusdo.core.errors import BuusdoError
from buusdo.core.platform_detect import HostPlatform, detect_host_platform


def get_backend(platform: HostPlatform | None = None) -> EnhancementBackend:
    host = platform if platform is not None else detect_host_platform()
    if host is HostPlatform.WINDOWS:
        from buusdo.backends.windows import WindowsBackend

        return WindowsBackend()
    if host is HostPlatform.LINUX:
        from buusdo.backends.linux import LinuxBackend

        return LinuxBackend()
    if host is HostPlatform.MACOS:
        from buusdo.backends.macos import MacOSBackend

        return MacOSBackend()
    raise BuusdoError(f"Unsupported host platform: {host}")


__all__ = ["get_backend"]
