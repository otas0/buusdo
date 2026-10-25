"""Batch AB: migrate --diff-keys-only; watch_ci_billing classifier helpers."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_migrate_diff_keys_only(tmp_path: Path, capsys) -> None:
    src = tmp_path / "v1.json"
    src.write_text(
        json.dumps({"schema_version": 1, "mode": "reshade", "blocked": False, "diffs": []}),
        encoding="utf-8",
    )
    mod = _load("migrate_conflict_export", Path("scripts/migrate_conflict_export.py"))
    assert mod.main([str(src), "--dry-run", "--diff-keys-only"]) == 0
    out = capsys.readouterr().out
    assert "WOULD migrate" in out
    lines = [ln for ln in out.splitlines() if ln.startswith("{")]
    assert lines, out
    row = json.loads(lines[0])
    assert row["op"] in {"add", "change"}
    assert "schema_version" in row["key"] or row["key"] == "schema_version"
    assert mod.main([str(src), "--diff-keys-only"]) == 2  # requires --dry-run


def test_watch_ci_billing_classify_empty_steps() -> None:
    mod = _load("watch_ci_billing", Path("scripts/watch_ci_billing.py"))

    def fake_get(path: str):
        assert "jobs" in path
        return {
            "jobs": [
                {
                    "name": "test",
                    "started_at": "2026-10-25T10:00:00Z",
                    "completed_at": "2026-10-25T10:00:03Z",
                    "steps": [],
                },
                {
                    "name": "dwm",
                    "started_at": "2026-10-25T10:00:00Z",
                    "completed_at": "2026-10-25T10:00:03Z",
                    "steps": [],
                },
            ]
        }

    mod._get = fake_get  # type: ignore[attr-defined]
    info = mod.classify_run("otas0/buusdo", 1)
    assert info["billing_blocked_likely"] is True
    assert info["empty_step_jobs"] == 2


def test_flatten_keys_stable() -> None:
    mod = _load("migrate_conflict_export", Path("scripts/migrate_conflict_export.py"))
    flat = mod._flatten_keys({"a": {"b": 1}, "c": [2, {"d": 3}]})
    assert flat["a.b"] == 1
    assert flat["c[0]"] == 2
    assert flat["c[1].d"] == 3
