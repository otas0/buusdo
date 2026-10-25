#!/usr/bin/env python3
"""Offline fxc/dxc compile for phase3 DWM HDR HLSL PoC.

Does not patch DWM. Looks up fxc.exe / dxc.exe on PATH or Windows Kits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def _find_compiler() -> tuple[str, list[str]] | None:
    for name, args in (("dxc", ["-T", "ps_6_0", "-E", "MainPS"]), ("fxc", ["/T", "ps_5_0", "/E", "MainPS"])):
        path = shutil.which(name) or shutil.which(f"{name}.exe")
        if path:
            return path, args
    kits = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Windows Kits" / "10" / "bin"
    if kits.is_dir():
        for ver in sorted(kits.iterdir(), reverse=True):
            for name, args in (("dxc.exe", ["-T", "ps_6_0", "-E", "MainPS"]), ("fxc.exe", ["/T", "ps_5_0", "/E", "MainPS"])):
                cand = ver / "x64" / name
                if cand.is_file():
                    return str(cand), args
    return None


def _hlsl_sha256_list(src_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not src_root.is_dir():
        return rows
    for p in sorted(src_root.rglob("*")):
        if p.is_file() and p.suffix.lower() in {".hlsl", ".hlsli", ".h"}:
            rows.append(
                {
                    "path": str(p.relative_to(src_root)).replace("\\", "/"),
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                }
            )
    return rows


def _pack_hlsl_sources(src_root: Path, out_dir: Path) -> tuple[Path, list[dict[str, str]]]:
    pack = out_dir / "hlsl_sources"
    pack.mkdir(parents=True, exist_ok=True)
    hashes = _hlsl_sha256_list(src_root)
    if src_root.is_dir():
        for p in src_root.rglob("*"):
            if p.is_file():
                dest = pack / p.relative_to(src_root)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)
    (pack / "README.txt").write_text(
        "HLSL sources packaged for offline Kits comparison (skipped_no_compiler or always).\n",
        encoding="utf-8",
    )
    zpath = out_dir / "hlsl_sources.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(pack.rglob("*")):
            if p.is_file():
                zf.write(p, arcname=str(p.relative_to(pack)).replace("\\", "/"))
    return zpath, hashes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Output directory for .cso + manifest")
    parser.add_argument("--hlsl", type=Path, default=None)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    src_root = root / "buusdo" / "core" / "dwm_hdr_shaders"
    hlsl = args.hlsl or (src_root / "sdr_to_hdr_tonemap.hlsl")
    if not hlsl.is_file():
        print(f"HLSL missing: {hlsl} (checkout phase3/dwm-hdr)", file=sys.stderr)
        return 2
    compiler = _find_compiler()
    args.out.mkdir(parents=True, exist_ok=True)
    cso = args.out / "sdr_to_hdr_tonemap.cso"
    hlsl_sha = _hlsl_sha256_list(src_root)
    manifest = {
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "hlsl": str(hlsl),
        "hlsl_sha256": hlsl_sha,
        "live_dwm_patch": False,
        "signing_draft": "sha256 of cso recorded; Authenticode optional later",
    }
    if compiler is None:
        # Still materialize HLSL + unsigned placeholder for CI hosts without SDK.
        shutil.copy2(hlsl, args.out / hlsl.name)
        (args.out / "COMPILE_SKIPPED.txt").write_text(
            "fxc/dxc not found — HLSL copied only. See docs/DWM_HDR_SIGNING_DRAFT.md\n",
            encoding="utf-8",
        )
        zpath, hashes = _pack_hlsl_sources(src_root, args.out)
        manifest["status"] = "skipped_no_compiler"
        manifest["hlsl_sha256"] = hashes
        manifest["hlsl_sources_zip"] = str(zpath.name)
        (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(manifest, indent=2))
        return 0
    path, base_args = compiler
    # fxc uses /Fo out, dxc uses -Fo out — normalize:
    if "fxc" in Path(path).name.lower():
        cmd = [path, "/T", "ps_5_0", "/E", "MainPS", f"/Fo{cso}", str(hlsl)]
    else:
        cmd = [path, "-T", "ps_6_0", "-E", "MainPS", "-Fo", str(cso), str(hlsl)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    manifest["compiler"] = path
    manifest["cmd"] = cmd
    manifest["returncode"] = proc.returncode
    manifest["stdout"] = proc.stdout[-2000:]
    manifest["stderr"] = proc.stderr[-2000:]
    if proc.returncode != 0 or not cso.is_file():
        manifest["status"] = "compile_failed"
        (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(proc.stderr or proc.stdout, file=sys.stderr)
        return 1
    digest = hashlib.sha256(cso.read_bytes()).hexdigest()
    manifest["status"] = "ok"
    manifest["sha256"] = digest
    # Always attach source hashes for audit; zip only when useful for skipped path.
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
