from pathlib import Path

from buusdo.core.graphics_detect import GraphicsApi, detect_graphics_api, is_pe64
from tests.fixtures.build_min_pe import build_pe_importing


def test_detect_d3d11_from_minimal_pe(tmp_path: Path) -> None:
    exe = tmp_path / "game.exe"
    exe.write_bytes(build_pe_importing("d3d11.dll"))
    assert detect_graphics_api(exe) is GraphicsApi.D3D11
    assert is_pe64(exe) is True


def test_detect_vulkan_from_minimal_pe(tmp_path: Path) -> None:
    exe = tmp_path / "vk.exe"
    exe.write_bytes(build_pe_importing("vulkan-1.dll"))
    assert detect_graphics_api(exe) is GraphicsApi.VULKAN


def test_fixture_file_on_disk() -> None:
    fixture = Path(__file__).parent / "fixtures" / "min_d3d11.exe"
    if fixture.is_file():
        assert detect_graphics_api(fixture) is GraphicsApi.D3D11
