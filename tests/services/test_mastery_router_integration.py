import pytest
from fastapi.testclient import TestClient
from tools.gimo_server.main import app
from tools.gimo_server.security import verify_token
from tools.gimo_server.security.auth import AuthContext
from unittest.mock import MagicMock

# Define a mock AuthContext
mock_auth = AuthContext(
    token="test_token_that_is_long_enough_for_validation",
    role="admin"
)

# Override security and config dependencies
@pytest.fixture(autouse=True)
def setup_mocks():
    from tools.gimo_server.services.ops_service import OpsService
    from tools.gimo_server.ops_models import OpsConfig
    
    # Mock Auth
    app.dependency_overrides[verify_token] = lambda: mock_auth
    
    # Mock OpsService.get_config to return show_cost_predictions=True
    mock_config = OpsConfig()
    mock_config.economy.show_cost_predictions = True
    OpsService.get_config = MagicMock(return_value=mock_config)
    
    yield
    app.dependency_overrides.clear()
    # Reset mock after test
    import importlib
    import tools.gimo_server.services.ops_service
    importlib.reload(tools.gimo_server.services.ops_service)

def test_predict_endpoint():
    client = TestClient(app)
    
    # Mock node data
    workflow_data = {
        "nodes": [
            {
                "id": "node1", 
                "type": "llm_call", 
                "config": {"task_type": "coding", "model": "haiku"}
            }
        ],
        "initial_state": {}
    }
    
    response = client.post("/ops/mastery/predict", json=workflow_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "estimated_cost" in data
    assert "confidence_score" in data
    assert "model_breakdown" in data
    assert "haiku" in data["model_breakdown"]
