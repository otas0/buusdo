"""Batch AE: try_steam_uri_candidate advance; local dwm-hdr verify; docs root scan."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from buusdo.core.steam_uris import try_steam_uri_candidate


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_try_steam_uri_candidate_index_advance_with_fake_opener() -> None:
    uris = [
        "steam://a/1",
        "steam://b/1",
        "steam://c/1",
    ]

    def fail(_u: str) -> bool:
        return False

    r0 = try_steam_uri_candidate(uris, 0, opener=fail, cache_success=False)
    assert r0["opened"] is False
    assert r0["next_index"] == 1
    assert r0["remaining"] == 2
    assert r0["exhausted"] is False

    r1 = try_steam_uri_candidate(uris, r0["next_index"], opener=fail, cache_success=False)
    assert r1["next_index"] == 2
    assert r1["remaining"] == 1

    def ok_only_last(u: str) -> bool:
        return u == uris[-1]

    r2 = try_steam_uri_candidate(uris, r1["next_index"], opener=ok_only_last, cache_success=False)
    assert r2["opened"] is True
    assert r2["next_index"] == 0

    r_ex = try_steam_uri_candidate(uris, 2, opener=fail, cache_success=False)
    assert r_ex["exhausted"] is True
    assert r_ex["next_index"] == 3
    assert r_ex["remaining"] == 0


def test_verify_dwm_hdr_poc_local_smoke(tmp_path: Path) -> None:
    mod = _load("verify_dwm_hdr_poc_local", Path("scripts/verify_dwm_hdr_poc_local.py"))
    out = tmp_path / "poc"
    assert mod.main(["--out", str(out)]) == 0
    assert (out / "manifest.json").is_file()
    assert (out / "hlsl_sources.zip").is_file()
    # Re-verify without recompile
    assert mod.main(["--out", str(out), "--skip-compile"]) == 0


def test_check_docs_language_includes_root_markdown() -> None:
    mod = _load("check_docs_language", Path("scripts/check_docs_language.py"))
    assert mod.main() == 0
    assert Path("README.md").is_file()
    assert Path("AGENTS.md").is_file()
