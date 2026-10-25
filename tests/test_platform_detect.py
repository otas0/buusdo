import sys

from buusdo.core.platform_detect import HostPlatform, detect_host_platform


def test_detect_matches_sys_platform() -> None:
    host = detect_host_platform()
    if sys.platform == "darwin":
        assert host is HostPlatform.MACOS
    elif sys.platform == "win32":
        assert host is HostPlatform.WINDOWS
    elif sys.platform.startswith("linux"):
        assert host is HostPlatform.LINUX
    else:
        assert host is HostPlatform.UNSUPPORTED
