"""Detect graphics API used by a Windows PE executable (works under Proton too)."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

import pefile


class GraphicsApi(str, Enum):
    D3D9 = "d3d9"
    D3D10 = "d3d10"
    D3D11 = "d3d11"
    D3D12 = "d3d12"
    OPENGL = "opengl"
    VULKAN = "vulkan"
    UNKNOWN = "unknown"


# ReShade sidecar DLL name for each API (official ReShade installer mapping).
RESHADE_PROXY_DLL: dict[GraphicsApi, str | None] = {
    GraphicsApi.D3D9: "d3d9.dll",
    GraphicsApi.D3D10: "dxgi.dll",
    GraphicsApi.D3D11: "dxgi.dll",
    GraphicsApi.D3D12: "dxgi.dll",
    GraphicsApi.OPENGL: "opengl32.dll",
    # Vulkan uses an explicit layer JSON, not a proxy DLL next to the exe.
    GraphicsApi.VULKAN: None,
    GraphicsApi.UNKNOWN: "dxgi.dll",  # common default when unsure
}


_IMPORT_HINTS: list[tuple[str, GraphicsApi]] = [
    ("d3d12.dll", GraphicsApi.D3D12),
    ("d3d11.dll", GraphicsApi.D3D11),
    ("d3d10.dll", GraphicsApi.D3D10),
    ("d3d9.dll", GraphicsApi.D3D9),
    ("opengl32.dll", GraphicsApi.OPENGL),
    ("vulkan-1.dll", GraphicsApi.VULKAN),
]


def detect_graphics_api(executable: Path | None) -> GraphicsApi:
    """Inspect PE imports; prefer the newest Direct3D / Vulkan / OpenGL hit."""
    if executable is None or not executable.is_file():
        return GraphicsApi.UNKNOWN
    if executable.suffix.lower() != ".exe":
        return GraphicsApi.UNKNOWN
    try:
        pe = pefile.PE(str(executable), fast_load=True)
        pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
        )
    except (OSError, pefile.PEFormatError, AttributeError, ValueError):
        return GraphicsApi.UNKNOWN

    imports: set[str] = set()
    try:
        entries = getattr(pe, "DIRECTORY_ENTRY_IMPORT", None) or []
        for entry in entries:
            name = entry.dll.decode("ascii", errors="ignore").lower()
            imports.add(name)
    finally:
        pe.close()

    for dll, api in _IMPORT_HINTS:
        if dll in imports:
            return api
    return GraphicsApi.UNKNOWN


def is_pe64(executable: Path | None) -> bool:
    if executable is None or not executable.is_file():
        return True
    try:
        pe = pefile.PE(str(executable), fast_load=True)
        machine = pe.FILE_HEADER.Machine
        pe.close()
    except (OSError, pefile.PEFormatError, AttributeError, ValueError):
        return True
    # IMAGE_FILE_MACHINE_AMD64 / ARM64
    return machine in {0x8664, 0xAA64}
