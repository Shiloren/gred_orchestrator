import pytest
from pathlib import Path
from tools.repo_orchestrator.services.registry_service import RegistryService
from tools.repo_orchestrator.config import REPO_REGISTRY_PATH
import json

@pytest.fixture
def mock_registry(tmp_path):
    # Temporarily override the registry path
    temp_registry = tmp_path / "repo_registry.json"
    
    # We can't easy monkeypatch the constant in the module if it's already imported, 
    # but we can monkeypatch the Service class if we modify it to accept a path, 
    # or just use unittest.mock.patch
    with unittest.mock.patch("tools.repo_orchestrator.services.registry_service.REPO_REGISTRY_PATH", temp_registry):
        yield temp_registry

def test_load_empty_registry(tmp_path):
    # Setup
    registry_file = tmp_path / "test_registry.json"
    class MockService(RegistryService):
        pass
    
    # Inject constraint
    import tools.repo_orchestrator.services.registry_service as mod
    original = mod.REPO_REGISTRY_PATH
    mod.REPO_REGISTRY_PATH = registry_file
    
    try:
        data = MockService.load_registry()
        assert data["repos"] == []
        assert data["active_repo"] is None
    finally:
        mod.REPO_REGISTRY_PATH = original

def test_save_and_load_registry(tmp_path):
    registry_file = tmp_path / "test_registry_2.json"
    import tools.repo_orchestrator.services.registry_service as mod
    original = mod.REPO_REGISTRY_PATH
    mod.REPO_REGISTRY_PATH = registry_file
    
    try:
        data = {"active_repo": "/tmp/foo", "repos": ["/tmp/foo", "/tmp/bar"]}
        RegistryService.save_registry(data)
        
        loaded = RegistryService.load_registry()
        assert loaded["active_repo"] == "/tmp/foo"
        assert len(loaded["repos"]) == 2
    finally:
        mod.REPO_REGISTRY_PATH = original
