import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from tools.repo_orchestrator.main import app
from tools.repo_orchestrator.models import SubAgent, SubAgentConfig

client = TestClient(app)

@pytest.fixture
def mock_sub_agents():
    config = SubAgentConfig(model="llama3", temperature=0.7, max_tokens=100)
    agent = SubAgent(
        id="sub-1", 
        parentId="api", 
        name="Test Sub", 
        model="llama3", 
        status="working", 
        config=config
    )
    with patch('tools.repo_orchestrator.services.sub_agent_manager.SubAgentManager.get_sub_agents') as mock:
        mock.return_value = [agent]
        yield mock

@pytest.fixture
def mock_no_sub_agents():
    with patch('tools.repo_orchestrator.services.sub_agent_manager.SubAgentManager.get_sub_agents') as mock:
        mock.return_value = []
        yield mock

def test_graph_endpoint_with_sub_agents(mock_sub_agents):
    # Mock token verification to bypass auth
    app.dependency_overrides = {} # Reset
    # We might need to mock verify_token if not covered by default TestClient setup or if it fails
    # But usually provided token in headers works if logic is simple. 
    # Let's try with a dummy token if the endpoint requires it.
    
    # Actually, let's just patch the dependency or pass header
    headers = {"Authorization": "Bearer test-token"} 
    # Note: The actual implementation of verify_token might need a valid token format or db lookup
    # Let's mock verify_token to be sure
    from tools.repo_orchestrator.security import verify_token
    app.dependency_overrides[verify_token] = lambda: "test-user"

    response = client.get("/ui/graph", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    api_node = next(n for n in data['nodes'] if n['id'] == 'api')
    assert api_node['type'] == 'cluster'
    assert len(api_node['data']['subAgents']) == 1
    assert api_node['data']['subAgents'][0]['id'] == 'sub-1'

def test_graph_endpoint_without_sub_agents(mock_no_sub_agents):
    from tools.repo_orchestrator.security import verify_token
    app.dependency_overrides[verify_token] = lambda: "test-user"
    
    response = client.get("/ui/graph")
    assert response.status_code == 200
    data = response.json()
    
    api_node = next(n for n in data['nodes'] if n['id'] == 'api')
    assert api_node['type'] == 'orchestrator'
    # subAgents might be None or empty list depending on Pydantic defaults, 
    # but based on code: "subAgents=api_sub_agents" which is []
    # Pydantic might omit None fields if exclude_none=True, or show them.
    # Our code passes [].
    if 'subAgents' in api_node['data']:
        assert len(api_node['data']['subAgents']) == 0
