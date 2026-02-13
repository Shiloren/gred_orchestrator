import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from tools.repo_orchestrator.services.git_service import GitService


def test_get_diff_success(tmp_path):
    mock_process = MagicMock()
    mock_process.communicate.return_value = ("file1.py | 5 ++-\n", "")
    mock_process.returncode = 0

    with patch("tools.repo_orchestrator.services.git_service.subprocess.Popen", return_value=mock_process):
        result = GitService.get_diff(tmp_path, "main", "HEAD")

    assert "file1.py" in result


def test_get_diff_error(tmp_path):
    mock_process = MagicMock()
    mock_process.communicate.return_value = ("", "fatal: bad revision")
    mock_process.returncode = 1

    with patch("tools.repo_orchestrator.services.git_service.subprocess.Popen", return_value=mock_process):
        with pytest.raises(RuntimeError, match="Git error"):
            GitService.get_diff(tmp_path, "invalid", "HEAD")


def test_get_diff_timeout(tmp_path):
    mock_process = MagicMock()
    mock_process.communicate.side_effect = TimeoutError("timed out")

    with patch("tools.repo_orchestrator.services.git_service.subprocess.Popen", return_value=mock_process):
        with pytest.raises(RuntimeError, match="Internal git execution error"):
            GitService.get_diff(tmp_path)


def test_list_repos(tmp_path):
    (tmp_path / "repo-alpha").mkdir()
    (tmp_path / "repo-beta").mkdir()
    (tmp_path / ".hidden-dir").mkdir()
    (tmp_path / "some-file.txt").write_text("not a dir")

    result = GitService.list_repos(tmp_path)

    names = [r["name"] for r in result]
    assert "repo-alpha" in names
    assert "repo-beta" in names
    assert ".hidden-dir" not in names
    assert "some-file.txt" not in names
    # Should be sorted alphabetically
    assert result[0]["name"] == "repo-alpha"


def test_list_repos_empty(tmp_path):
    result = GitService.list_repos(tmp_path)
    assert result == []


def test_list_repos_nonexistent():
    result = GitService.list_repos(Path("/nonexistent/path"))
    assert result == []
