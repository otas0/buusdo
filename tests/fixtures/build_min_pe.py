"""Build a minimal PE32+ that imports a chosen DLL (for graphics_detect tests)."""

from __future__ import annotations

import struct
from pathlib import Path


def build_pe_importing(dll_name: str = "d3d11.dll") -> bytes:
    """Return bytes of a tiny x64 PE with a single import DLL name."""
    dll = dll_name.encode("ascii") + b"\x00"
    # Layout (all RVAs within section at file offset 0x200, VA 0x1000)
    # 0x00: Import Directory (20 bytes + null desc)
    # 0x28: ILT (8+8)
    # 0x38: IAT (8+8)
    # 0x48: Hint/Name for Sleep
    # 0x58: DLL name
    section_raw = 0x200
    section_va = 0x1000

    import_dir_rva = section_va + 0x00
    ilt_rva = section_va + 0x28
    iat_rva = section_va + 0x38
    hint_rva = section_va + 0x48
    dll_rva = section_va + 0x58

    section = bytearray(0x200)
    # IMAGE_IMPORT_DESCRIPTOR
    struct.pack_into("<IIIII", section, 0x00, ilt_rva, 0, 0, dll_rva, iat_rva)
    # null descriptor already zeros
    # ILT / IAT point to hint/name
    struct.pack_into("<Q", section, 0x28, hint_rva)
    struct.pack_into("<Q", section, 0x38, hint_rva)
    # Hint/Name: hint=0, name="Sleep"
    section[0x48:0x4A] = b"\x00\x00"
    section[0x4A:0x4A + 6] = b"Sleep\x00"
    section[0x58 : 0x58 + len(dll)] = dll

    # DOS header
    dos = bytearray(0x80)
    dos[0:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 0x80)  # e_lfanew

    # PE + COFF + optional header (PE32+)
    pe = bytearray()
    pe += b"PE\x00\x00"
    # COFF: Machine AMD64, 1 section, SizeOfOptionalHeader=0xF0
    pe += struct.pack("<HHIIIHH", 0x8664, 1, 0, 0, 0, 0xF0, 0x22)  # characteristics EXECUTABLE|LARGE
    # Optional magic PE32+
    opt = bytearray(0xF0)
    struct.pack_into("<H", opt, 0, 0x20B)
    struct.pack_into("<I", opt, 16, 0x1000)  # AddressOfEntryPoint
    struct.pack_into("<Q", opt, 24, 0x140000000)  # ImageBase
    struct.pack_into("<I", opt, 32, 0x1000)  # SectionAlignment
    struct.pack_into("<I", opt, 36, 0x200)  # FileAlignment
    struct.pack_into("<H", opt, 40, 6)  # Major OS
    struct.pack_into("<H", opt, 42, 0)
    struct.pack_into("<H", opt, 48, 6)  # Major Subsystem
    struct.pack_into("<I", opt, 56, 0x2000)  # SizeOfImage
    struct.pack_into("<I", opt, 60, 0x200)  # SizeOfHeaders
    struct.pack_into("<H", opt, 68, 3)  # Subsystem WINDOWS_CUI
    struct.pack_into("<I", opt, 108, 16)  # NumberOfRvaAndSizes
    # DataDirectory[1] = IMPORT
    struct.pack_into("<II", opt, 112 + 8, import_dir_rva, 40)
    pe += opt

    # Section header .text
    sh = bytearray(40)
    sh[0:5] = b".text"
    struct.pack_into("<I", sh, 8, 0x200)  # VirtualSize
    struct.pack_into("<I", sh, 12, section_va)
    struct.pack_into("<I", sh, 16, 0x200)  # SizeOfRawData
    struct.pack_into("<I", sh, 20, section_raw)
    struct.pack_into("<I", sh, 36, 0xE0000020)  # code|exec|read|write
    pe += sh

    header = dos + pe
    assert len(header) <= section_raw
    padding = b"\x00" * (section_raw - len(header))
    return bytes(header + padding + section)


def main() -> None:
    out = Path(__file__).with_name("min_d3d11.exe")
    out.write_bytes(build_pe_importing("d3d11.dll"))
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
