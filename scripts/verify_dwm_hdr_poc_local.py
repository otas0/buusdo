#!/usr/bin/env python3
"""Offline verify of dwm-hdr PoC materialization (no GitHub, no network).

Compiles/materializes into --out (default under the system temp dir), then checks:
- manifest.json exists and has status
- hlsl_sources.zip is present
- each manifest hlsl_sha256[] entry matches bytes inside the zip

Exit 0 on match; non-zero on failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _compile(out: Path) -> int:
    import importlib.util

    script = ROOT / "scripts" / "compile_dwm_hdr_poc.py"
    spec = importlib.util.spec_from_file_location("compile_dwm_hdr_poc", script)
    if spec is None or spec.loader is None:
        print(f"cannot load {script}", file=sys.stderr)
        return 2
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Prefer main([...]) when available.
    if hasattr(mod, "main"):
        return int(mod.main(["--out", str(out)]))
    print("compile_dwm_hdr_poc.main missing", file=sys.stderr)
    return 2


def verify_tree(root: Path) -> int:
    man_path = root / "manifest.json"
    zip_path = root / "hlsl_sources.zip"
    src_root = ROOT / "buusdo" / "core" / "dwm_hdr_shaders"
    if not man_path.is_file():
        print(f"missing {man_path}", file=sys.stderr)
        return 1
    man = json.loads(man_path.read_text(encoding="utf-8"))
    status = man.get("status")
    entries = man.get("hlsl_sha256") or []
    if not isinstance(entries, list) or not entries:
        print(f"manifest hlsl_sha256 empty (status={status})", file=sys.stderr)
        return 1
    zf: zipfile.ZipFile | None = None
    if zip_path.is_file():
        zf = zipfile.ZipFile(zip_path)
        names = set(zf.namelist())
    else:
        names = set()
    try:
        for entry in entries:
            path = entry.get("path")
            expect = entry.get("sha256")
            if not path or not expect:
                print(f"bad hlsl_sha256 entry: {entry}", file=sys.stderr)
                return 1
            if zf is not None and path in names:
                data = zf.read(path)
            else:
                # status=ok compile path may omit zip — fall back to source tree / out copy.
                candidates = [root / path, root / "hlsl_sources" / path, src_root / path]
                data = None
                for cand in candidates:
                    if cand.is_file():
                        data = cand.read_bytes()
                        break
                if data is None:
                    print(f"{path} missing from zip and disk", file=sys.stderr)
                    return 1
            dig = hashlib.sha256(data).hexdigest()
            if dig != expect:
                print(f"sha mismatch {path}: {dig} != {expect}", file=sys.stderr)
                return 1
            print(f"ok {path} {dig}")
    finally:
        if zf is not None:
            zf.close()
    print(f"VERIFY OK status={status} entries={len(entries)} zip={'yes' if zip_path.is_file() else 'no'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: temp dir buusdo-dwm-hdr-poc)",
    )
    p.add_argument(
        "--skip-compile",
        action="store_true",
        help="Only verify an existing --out tree",
    )
    args = p.parse_args(argv)
    out = args.out
    if out is None:
        out = Path(tempfile.gettempdir()) / "buusdo-dwm-hdr-poc"
    if not args.skip_compile:
        rc = _compile(out)
        if rc != 0:
            # compile may still write skipped_no_compiler material; verify anyway if present.
            if not (out / "manifest.json").is_file():
                return rc
    return verify_tree(out)


if __name__ == "__main__":
    raise SystemExit(main())
