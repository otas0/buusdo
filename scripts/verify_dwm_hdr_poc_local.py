#!/usr/bin/env python3
"""Offline verify of dwm-hdr PoC materialization (no GitHub, no network).

Compiles/materializes into --out (default under the system temp dir), then checks:
- manifest.json exists and has status
- hlsl_sources.zip when present; else fall back to source/out copies
- each manifest hlsl_sha256[] entry matches bytes

Exit 0 on match; non-zero on failure.
Use ``--json`` for a single machine-readable summary object on stdout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

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
    if hasattr(mod, "main"):
        return int(mod.main(["--out", str(out)]))
    print("compile_dwm_hdr_poc.main missing", file=sys.stderr)
    return 2


def verify_tree(root: Path, *, as_json: bool = False) -> int:
    man_path = root / "manifest.json"
    zip_path = root / "hlsl_sources.zip"
    src_root = ROOT / "buusdo" / "core" / "dwm_hdr_shaders"
    summary: dict[str, Any] = {
        "ok": False,
        "out": str(root),
        "status": None,
        "zip": zip_path.is_file(),
        "entries": [],
        "error": None,
    }
    if not man_path.is_file():
        summary["error"] = f"missing {man_path}"
        return _emit(summary, as_json=as_json, rc=1)
    man = json.loads(man_path.read_text(encoding="utf-8"))
    status = man.get("status")
    summary["status"] = status
    entries = man.get("hlsl_sha256") or []
    if not isinstance(entries, list) or not entries:
        summary["error"] = f"manifest hlsl_sha256 empty (status={status})"
        return _emit(summary, as_json=as_json, rc=1)
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
                summary["error"] = f"bad hlsl_sha256 entry: {entry}"
                return _emit(summary, as_json=as_json, rc=1)
            source = "zip" if zf is not None and path in names else "disk"
            if source == "zip":
                assert zf is not None
                data = zf.read(path)
            else:
                candidates = [root / path, root / "hlsl_sources" / path, src_root / path]
                data = None
                for cand in candidates:
                    if cand.is_file():
                        data = cand.read_bytes()
                        break
                if data is None:
                    summary["error"] = f"{path} missing from zip and disk"
                    return _emit(summary, as_json=as_json, rc=1)
            dig = hashlib.sha256(data).hexdigest()
            row = {"path": path, "sha256": dig, "match": dig == expect, "source": source}
            summary["entries"].append(row)
            if dig != expect:
                summary["error"] = f"sha mismatch {path}: {dig} != {expect}"
                return _emit(summary, as_json=as_json, rc=1)
            if not as_json:
                print(f"ok {path} {dig}")
    finally:
        if zf is not None:
            zf.close()
    summary["ok"] = True
    if not as_json:
        print(
            f"VERIFY OK status={status} entries={len(entries)} "
            f"zip={'yes' if zip_path.is_file() else 'no'}"
        )
    return _emit(summary, as_json=as_json, rc=0)


def _emit(summary: dict[str, Any], *, as_json: bool, rc: int) -> int:
    if as_json:
        print(json.dumps(summary, ensure_ascii=False))
    elif summary.get("error") and rc != 0:
        print(str(summary["error"]), file=sys.stderr)
    return rc


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
    p.add_argument(
        "--json",
        action="store_true",
        help="Print one JSON summary object on stdout (machine-readable)",
    )
    args = p.parse_args(argv)
    out = args.out
    if out is None:
        out = Path(tempfile.gettempdir()) / "buusdo-dwm-hdr-poc"
    if not args.skip_compile:
        # Suppress compile JSON noise when --json requested.
        if args.json:
            import contextlib
            import io

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = _compile(out)
        else:
            rc = _compile(out)
        if rc != 0 and not (out / "manifest.json").is_file():
            if args.json:
                print(
                    json.dumps(
                        {"ok": False, "out": str(out), "error": f"compile failed rc={rc}"},
                        ensure_ascii=False,
                    )
                )
            return rc
    return verify_tree(out, as_json=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
