import pytest
import subprocess
from pathlib import Path
from tools.gimo_server.services.git_service import GitService

@pytest.fixture
def git_repo(tmp_path):
    """Creates a temporary git repository."""
    repo_dir = tmp_path / "main_repo"
    repo_dir.mkdir()
    
    # Initialize git
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    
    # Create a commit
    (repo_dir / "README.md").write_text("Main Repo")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True)
    
    return repo_dir

def test_add_worktree_success(git_repo, tmp_path):
    worktree_path = tmp_path / "wt1"
    
    GitService.add_worktree(git_repo, worktree_path)
    
    assert worktree_path.exists()
    assert (worktree_path / "README.md").exists()
    
    # Check if registered
    wt_list = GitService.list_worktrees(git_repo)
    assert any(str(worktree_path.resolve()) in str(Path(wt).resolve()) for wt in wt_list)

def test_remove_worktree_success(git_repo, tmp_path):
    worktree_path = tmp_path / "wt2"
    GitService.add_worktree(git_repo, worktree_path)
    assert worktree_path.exists()
    
    GitService.remove_worktree(git_repo, worktree_path)
    
    assert not worktree_path.exists()
    
    # Check if unregistered
    wt_list = GitService.list_worktrees(git_repo)
    assert not any(str(worktree_path.resolve()) in str(Path(wt).resolve()) for wt in wt_list)

def test_list_worktrees(git_repo, tmp_path):
    wt1 = tmp_path / "wt_a"
    wt2 = tmp_path / "wt_b"
    
    GitService.add_worktree(git_repo, wt1)
    GitService.add_worktree(git_repo, wt2)
    
    wt_list = GitService.list_worktrees(git_repo)
    
    # Should have main repo + 2 worktrees
    assert len(wt_list) >= 3
    assert any(str(wt1.resolve()) in str(Path(w).resolve()) for w in wt_list)
    assert any(str(wt2.resolve()) in str(Path(w).resolve()) for w in wt_list)
