"""Scan finished payload is plain dicts (safe across QueuedConnection)."""

from __future__ import annotations

from pathlib import Path

from buusdo.core.backend import EnhancementTarget


def test_enhancement_target_payload_roundtrip() -> None:
    target = EnhancementTarget(
        name="Demo",
        install_path=Path("/games/demo"),
        executable=Path("/games/demo/demo.exe"),
        metadata={"app_id": "42", "tags": ["a"]},
    )
    payload = target.to_payload()
    assert isinstance(payload["install_path"], str)
    assert isinstance(payload["executable"], str)
    assert payload["metadata"]["app_id"] == "42"
    restored = EnhancementTarget.from_payload(payload)
    assert restored.name == "Demo"
    assert restored.install_path == Path("/games/demo")
    assert restored.executable == Path("/games/demo/demo.exe")
    assert restored.metadata["app_id"] == "42"


def test_force_scan_finished_list_roundtrip() -> None:
    """Worker emits list[dict]; MainWindow.on_scan_finished rebuilds targets."""
    games = [
        EnhancementTarget(
            name=f"Game {i}",
            install_path=Path(f"/games/g{i}"),
            executable=Path(f"/games/g{i}/g.exe"),
            metadata={"app_id": str(100 + i), "proton_prefix": f"/pfx/{i}"},
        )
        for i in range(3)
    ]
    # Same shape as ScanWorker.finished.emit([...])
    payloads = [g.to_payload() for g in games]
    assert all(isinstance(p, dict) for p in payloads)

    restored: list[EnhancementTarget] = []
    for item in payloads:
        if isinstance(item, EnhancementTarget):
            restored.append(item)
        elif isinstance(item, dict):
            restored.append(EnhancementTarget.from_payload(item))
    assert [g.name for g in restored] == ["Game 0", "Game 1", "Game 2"]
    assert restored[1].metadata["app_id"] == "101"
    assert restored[2].install_path == Path("/games/g2")
