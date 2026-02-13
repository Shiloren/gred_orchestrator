import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from tools.repo_orchestrator.services.repo_service import RepoService


def test_list_repos():
    mock_repos = [{"name": "alpha", "path": "/repos/alpha"}, {"name": "beta", "path": "/repos/beta"}]
    with patch("tools.repo_orchestrator.services.repo_service.GitService.list_repos", return_value=mock_repos):
        repos = RepoService.list_repos()

    assert len(repos) == 2
    assert repos[0].name == "alpha"
    assert repos[1].path == "/repos/beta"


def test_walk_tree(tmp_path):
    # Create a small directory structure
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    (src / "config.json").write_text("{}")
    (src / "readme.md").write_text("# Hi")  # Not in ALLOWED_EXTENSIONS

    sub = src / "sub"
    sub.mkdir()
    (sub / "helper.py").write_text("pass")

    result = RepoService.walk_tree(tmp_path, max_depth=3)

    py_files = [f for f in result if f.endswith(".py")]
    json_files = [f for f in result if f.endswith(".json")]
    md_files = [f for f in result if f.endswith(".md")]

    assert len(py_files) >= 1
    assert len(json_files) >= 1
    assert len(md_files) == 0  # .md not in ALLOWED_EXTENSIONS


def test_walk_tree_skips_hidden(tmp_path):
    hidden = tmp_path / ".git"
    hidden.mkdir()
    (hidden / "config").write_text("data")

    result = RepoService.walk_tree(tmp_path, max_depth=3)
    assert all(".git" not in f for f in result)


def test_perform_search(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def hello():\n    return 'world'\n")
    (src / "config.json").write_text('{"key": "hello"}')

    result = RepoService.perform_search(tmp_path, "hello", ext=None)
    assert len(result) >= 1
    assert any("hello" in hit.get("content", "") for hit in result)


def test_perform_search_with_ext_filter(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def hello(): pass")
    (src / "util.py").write_text("def hello(): pass")
    (src / "config.json").write_text('{"hello": true}')

    result = RepoService.perform_search(tmp_path, "hello", ext=".py")
    # Only .py files should be included
    assert all(hit["file"].endswith(".py") for hit in result)


def test_should_skip_dir():
    assert RepoService._should_skip_dir(".git") is True
    assert RepoService._should_skip_dir("node_modules") is True
    assert RepoService._should_skip_dir(".venv") is True
    assert RepoService._should_skip_dir("src") is False
