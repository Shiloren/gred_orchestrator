import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from tools.repo_orchestrator.services.file_service import FileService


def test_tail_audit_lines(tmp_path):
    log_file = tmp_path / "audit.log"
    lines = [f"Line {i}" for i in range(20)]
    log_file.write_text("\n".join(lines))

    with patch("tools.repo_orchestrator.services.file_service.AUDIT_LOG_PATH", log_file):
        result = FileService.tail_audit_lines(limit=5)

    assert len(result) == 5
    assert result[0] == "Line 15"
    assert result[-1] == "Line 19"


def test_tail_audit_lines_no_file():
    with patch("tools.repo_orchestrator.services.file_service.AUDIT_LOG_PATH", Path("/nonexistent/audit.log")):
        result = FileService.tail_audit_lines()
    assert result == []


def test_tail_audit_lines_empty_file(tmp_path):
    log_file = tmp_path / "audit.log"
    log_file.write_text("")

    with patch("tools.repo_orchestrator.services.file_service.AUDIT_LOG_PATH", log_file):
        result = FileService.tail_audit_lines()
    assert result == []


def test_get_file_content(tmp_path):
    source_file = tmp_path / "test.py"
    source_file.write_text("line1\nline2\nline3\nline4\nline5\n")

    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()

    with patch("tools.repo_orchestrator.services.file_service.SnapshotService.create_snapshot") as mock_snap, \
         patch("tools.repo_orchestrator.services.file_service.audit_log") as mock_audit, \
         patch("tools.repo_orchestrator.services.file_service.redact_sensitive_data", side_effect=lambda x: x), \
         patch("tools.repo_orchestrator.services.file_service.MAX_LINES", 500), \
         patch("tools.repo_orchestrator.services.file_service.MAX_BYTES", 250000):

        mock_snap.return_value = source_file  # Use the original file as "snapshot"

        content, content_hash = FileService.get_file_content(source_file, 1, 3, "test-token")

    assert "line1" in content
    assert "line3" in content
    assert len(content_hash) == 64  # SHA256 hex
    mock_audit.assert_called_once()


def test_get_file_content_truncation(tmp_path):
    source_file = tmp_path / "big.py"
    # Create a file with many lines
    big_content = "\n".join([f"line {i}" for i in range(100)])
    source_file.write_text(big_content)

    with patch("tools.repo_orchestrator.services.file_service.SnapshotService.create_snapshot", return_value=source_file), \
         patch("tools.repo_orchestrator.services.file_service.audit_log"), \
         patch("tools.repo_orchestrator.services.file_service.redact_sensitive_data", side_effect=lambda x: x), \
         patch("tools.repo_orchestrator.services.file_service.MAX_LINES", 10), \
         patch("tools.repo_orchestrator.services.file_service.MAX_BYTES", 250000):

        content, _ = FileService.get_file_content(source_file, 1, 100, "test-token")

    # Should be truncated to MAX_LINES
    assert "TRUNCATED" in content
