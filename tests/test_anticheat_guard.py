from pathlib import Path

import pytest

from buusdo.core.anticheat_guard import check
from buusdo.core.backend import EnhancementTarget
from buusdo.core.errors import UnsafeTargetError
from buusdo.core.platform_detect import HostPlatform


def test_clean_target_passes(tmp_path: Path) -> None:
    target = EnhancementTarget(name="Clean", install_path=tmp_path)
    check(target, HostPlatform.MACOS)


def test_anticheat_path_blocks(tmp_path: Path) -> None:
    eac = tmp_path / "EasyAntiCheat"
    eac.mkdir()
    (eac / "EasyAntiCheat_EOS_Setup.exe").write_text("x")
    target = EnhancementTarget(name="Risky", install_path=tmp_path)
    with pytest.raises(UnsafeTargetError) as excinfo:
        check(target, HostPlatform.LINUX)
    assert "anti-cheat" in excinfo.value.reason
    assert excinfo.value.evidence
