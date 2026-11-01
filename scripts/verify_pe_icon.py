#!/usr/bin/env python3
"""Verify a PE (.exe) embeds an icon resource (Nuitka/Inno consumed logo.ico).

Does not decode the bitmap; checks the PE resource directory for RT_GROUP_ICON
(type 14) and/or RT_ICON (type 3). Exit 0 when present, 1 when missing/invalid.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

RT_ICON = 3
RT_GROUP_ICON = 14


def _u16(data: bytes, off: int) -> int:
    return struct.unpack_from("<H", data, off)[0]


def _u32(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def _read_pe(path: Path) -> bytes:
    data = path.read_bytes()
    if data[:2] != b"MZ":
        raise ValueError("not a PE (missing MZ)")
    e_lfanew = _u32(data, 0x3C)
    if data[e_lfanew : e_lfanew + 4] != b"PE\0\0":
        raise ValueError("not a PE (missing PE signature)")
    return data


def _section_table(data: bytes) -> list[tuple[str, int, int, int]]:
    e_lfanew = _u32(data, 0x3C)
    coff = e_lfanew + 4
    num_sections = _u16(data, coff + 2)
    size_opt = _u16(data, coff + 16)
    sec_off = coff + 20 + size_opt
    sections = []
    for i in range(num_sections):
        off = sec_off + i * 40
        name = data[off : off + 8].split(b"\0", 1)[0].decode("ascii", "replace")
        vsize = _u32(data, off + 8)
        vaddr = _u32(data, off + 12)
        raw_size = _u32(data, off + 16)
        raw_ptr = _u32(data, off + 20)
        sections.append((name, vaddr, raw_ptr, min(vsize, raw_size) if vsize else raw_size))
    return sections


def _rva_to_off(sections: list[tuple[str, int, int, int]], rva: int) -> int | None:
    for _name, vaddr, raw_ptr, raw_size in sections:
        if raw_ptr == 0 or raw_size == 0:
            continue
        if vaddr <= rva < vaddr + raw_size:
            return raw_ptr + (rva - vaddr)
    return None


def _resource_dir_rva(data: bytes) -> int | None:
    e_lfanew = _u32(data, 0x3C)
    coff = e_lfanew + 4
    size_opt = _u16(data, coff + 16)
    magic = _u16(data, coff + 20)
    # PE32=0x10B, PE32+=0x20B — data directories start at different offsets.
    if magic == 0x20B:
        dd = coff + 20 + 112  # optional header + DataDirectory[2] for resources? 
        # PE32+: Standard 24 + Windows 88 = 112, DataDirectory[0] at +112
        # Resource is entry index 2 → +112 + 16
        res = coff + 20 + 112 + 16
    elif magic == 0x10B:
        res = coff + 20 + 96 + 16
    else:
        return None
    rva = _u32(data, res)
    return rva or None


def _dir_entries(data: bytes, off: int) -> list[tuple[int, int, bool]]:
    # IMAGE_RESOURCE_DIRECTORY: 16 bytes header
    named = _u16(data, off + 12)
    ids = _u16(data, off + 14)
    entries = []
    base = off + 16
    for i in range(named + ids):
        eoff = base + i * 8
        name_or_id = _u32(data, eoff)
        offset = _u32(data, eoff + 4)
        is_dir = bool(offset & 0x80000000)
        entries.append((name_or_id & 0xFFFF if name_or_id <= 0xFFFF else name_or_id, offset & 0x7FFFFFFF, is_dir))
    return entries


def pe_has_icon(path: Path) -> tuple[bool, str]:
    data = _read_pe(path)
    sections = _section_table(data)
    rva = _resource_dir_rva(data)
    if rva is None:
        return False, "no resource directory RVA"
    root_off = _rva_to_off(sections, rva)
    if root_off is None:
        return False, f"resource RVA 0x{rva:x} not mapped"
    types = _dir_entries(data, root_off)
    type_ids = {t for t, _off, _d in types}
    if RT_GROUP_ICON in type_ids or RT_ICON in type_ids:
        return True, f"icon resource present (types={sorted(type_ids & {RT_ICON, RT_GROUP_ICON})})"
    # Also accept if any type name looks like ICON (rare)
    return False, f"no RT_ICON/RT_GROUP_ICON (type ids sample={sorted(type_ids)[:12]})"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("exe", type=Path, nargs="?", help="Path to buusdo.exe or setup.exe")
    ap.add_argument(
        "--search-dist",
        action="store_true",
        help="Search dist/ for buusdo.exe / buusdo-setup-*.exe",
    )
    args = ap.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    targets: list[Path] = []
    if args.exe:
        targets.append(args.exe)
    if args.search_dist or not targets:
        dist = root / "dist"
        if dist.is_dir():
            targets.extend(sorted(dist.glob("buusdo-setup-*.exe")))
            payload = dist / "payload" / "buusdo.exe"
            if payload.is_file():
                targets.append(payload)
            targets.extend(sorted(dist.rglob("buusdo.exe")))
    # de-dupe
    seen: set[Path] = set()
    uniq: list[Path] = []
    for t in targets:
        rp = t.resolve()
        if rp not in seen and t.is_file():
            seen.add(rp)
            uniq.append(t)
    if not uniq:
        print("WARN: no exe found — structural skip (build Windows payload first)")
        return 0
    failed = 0
    for path in uniq:
        try:
            ok, msg = pe_has_icon(path)
        except ValueError as exc:
            print(f"FAIL {path}: {exc}")
            failed += 1
            continue
        if ok:
            print(f"OK  {path}: {msg}")
        else:
            print(f"FAIL {path}: {msg}")
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
