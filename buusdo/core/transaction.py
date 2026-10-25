"""Transactional filesystem mutations (C2).

Snapshot before change → record each mutation → on failure restore in reverse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class _FileSnapshot:
    path: Path
    existed: bool
    data: bytes | None = None


@dataclass
class _Change:
    kind: Literal["write", "create", "delete", "mkdir"]
    path: Path
    snapshot: _FileSnapshot | None = None


@dataclass
class Transaction:
    """Context manager for atomic-ish install/uninstall file ops."""

    _changes: list[_Change] = field(default_factory=list)
    _committed: bool = False
    _entered: bool = False

    def __enter__(self) -> Transaction:
        self._entered = True
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self.rollback()
        elif not self._committed:
            # Successful body without explicit commit still keeps changes on disk;
            # commit() marks intent and clears the undo log after success.
            self.commit()
        return False

    def _require_active(self) -> None:
        if not self._entered or self._committed:
            raise RuntimeError("Transaction is not active")

    def _snapshot_file(self, path: Path) -> _FileSnapshot:
        if path.exists() and path.is_file():
            return _FileSnapshot(path=path, existed=True, data=path.read_bytes())
        return _FileSnapshot(path=path, existed=False, data=None)

    def write_bytes(self, path: Path, data: bytes) -> None:
        """Write file contents; restore previous bytes (or delete) on rollback."""
        self._require_active()
        path = Path(path)
        snap = self._snapshot_file(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        kind: Literal["write", "create"] = "write" if snap.existed else "create"
        self._changes.append(_Change(kind=kind, path=path, snapshot=snap))

    def write_text(self, path: Path, text: str, encoding: str = "utf-8") -> None:
        self.write_bytes(path, text.encode(encoding))

    def ensure_dir(self, path: Path) -> None:
        self._require_active()
        path = Path(path)
        if path.exists():
            return
        path.mkdir(parents=True, exist_ok=True)
        self._changes.append(_Change(kind="mkdir", path=path, snapshot=None))

    def delete(self, path: Path) -> None:
        """Delete a file; restore exact bytes on rollback / uninstall restore."""
        self._require_active()
        path = Path(path)
        if not path.exists():
            return
        if not path.is_file():
            raise IsADirectoryError(f"Transaction.delete only supports files: {path}")
        snap = self._snapshot_file(path)
        path.unlink()
        self._changes.append(_Change(kind="delete", path=path, snapshot=snap))

    def restore_file(self, path: Path, original: bytes) -> None:
        """Byte-for-byte restore used by uninstall paths."""
        self.write_bytes(path, original)

    def commit(self) -> None:
        self._committed = True
        self._changes.clear()

    def rollback(self) -> None:
        for change in reversed(self._changes):
            self._undo(change)
        self._changes.clear()

    def _undo(self, change: _Change) -> None:
        if change.kind in ("write", "create"):
            assert change.snapshot is not None
            if change.snapshot.existed and change.snapshot.data is not None:
                change.path.write_bytes(change.snapshot.data)
            elif change.path.exists():
                change.path.unlink()
        elif change.kind == "delete":
            assert change.snapshot is not None
            if change.snapshot.existed and change.snapshot.data is not None:
                change.path.parent.mkdir(parents=True, exist_ok=True)
                change.path.write_bytes(change.snapshot.data)
        elif change.kind == "mkdir":
            if change.path.exists() and change.path.is_dir():
                try:
                    change.path.rmdir()
                except OSError:
                    # Non-empty after partial work — leave for next rollback steps
                    pass

    def copy_file(self, src: Path, dest: Path) -> None:
        """Copy a file into place under transaction semantics."""
        data = Path(src).read_bytes()
        self.write_bytes(dest, data)

    def backup_tree_note(self) -> None:
        """Placeholder for future tree-level backups; file ops cover Phase 1."""
        return
