import pytest
import time
from pathlib import Path
from unittest.mock import patch
from tools.gimo_server.services.snapshot_service import SnapshotService


@pytest.fixture
def snapshot_dir(tmp_path):
    snap_dir = tmp_path / "snapshots"
    with patch("tools.gimo_server.services.snapshot_service.SNAPSHOT_DIR", snap_dir):
        yield snap_dir


def test_ensure_snapshot_dir(snapshot_dir):
    assert not snapshot_dir.exists()
    SnapshotService.ensure_snapshot_dir()
    assert snapshot_dir.exists()


def test_create_snapshot(snapshot_dir, tmp_path):
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    source_file = tmp_path / "test_file.py"
    source_file.write_text("print('hello')")

    snapshot_path = SnapshotService.create_snapshot(source_file)

    assert snapshot_path.exists()
    assert snapshot_path.read_text() == "print('hello')"
    assert snapshot_path.parent == snapshot_dir


def test_cleanup_old_snapshots(snapshot_dir):
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    # Create a "fresh" file
    fresh_file = snapshot_dir / "fresh.py"
    fresh_file.write_text("fresh content")

    # Create an "old" file and backdate its mtime
    old_file = snapshot_dir / "old.py"
    old_file.write_text("old content")
    # Set mtime to 1 hour ago (well beyond any TTL)
    import os
    old_time = time.time() - 3600
    os.utime(old_file, (old_time, old_time))

    with patch("tools.gimo_server.services.snapshot_service.SNAPSHOT_TTL", 300):
        SnapshotService.cleanup_old_snapshots()

    assert fresh_file.exists()
    assert not old_file.exists()


def test_cleanup_nonexistent_dir():
    with patch("tools.gimo_server.services.snapshot_service.SNAPSHOT_DIR", Path("/nonexistent")):
        # Should not raise
        SnapshotService.cleanup_old_snapshots()
