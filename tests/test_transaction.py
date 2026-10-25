from pathlib import Path

import pytest

from buusdo.core.transaction import Transaction


def test_write_commits(tmp_path: Path) -> None:
    path = tmp_path / "a.txt"
    with Transaction() as tx:
        tx.write_text(path, "hello")
    assert path.read_text() == "hello"


def test_rollback_restores_previous_bytes(tmp_path: Path) -> None:
    path = tmp_path / "a.txt"
    path.write_text("original")
    with pytest.raises(RuntimeError):
        with Transaction() as tx:
            tx.write_text(path, "changed")
            raise RuntimeError("boom")
    assert path.read_text() == "original"


def test_rollback_removes_created_file(tmp_path: Path) -> None:
    path = tmp_path / "new.txt"
    with pytest.raises(ValueError):
        with Transaction() as tx:
            tx.write_text(path, "new")
            raise ValueError("fail")
    assert not path.exists()


def test_delete_restored_on_rollback(tmp_path: Path) -> None:
    path = tmp_path / "keep.txt"
    path.write_bytes(b"exact-bytes")
    with pytest.raises(RuntimeError):
        with Transaction() as tx:
            tx.delete(path)
            raise RuntimeError("abort")
    assert path.read_bytes() == b"exact-bytes"
