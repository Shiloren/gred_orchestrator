import pytest
from unittest.mock import patch, AsyncMock
from tools.repo_orchestrator.services.sub_agent_manager import SubAgentManager
from tools.repo_orchestrator.models import DelegationRequest

@pytest.fixture
def mock_model_service():
    with patch('tools.repo_orchestrator.services.sub_agent_manager.ModelService') as mock:
        mock.is_backend_ready = AsyncMock(return_value=True)
        mock.generate = AsyncMock(return_value="Mocked Response")
        yield mock

def test_create_sub_agent():
    req = DelegationRequest(subTaskDescription="Test task", modelPreference="llama3")
    agent = SubAgentManager.create_sub_agent("parent-123", req)
    
    assert agent.parentId == "parent-123"
    assert agent.model == "llama3"
    assert agent.status == "starting"
    assert agent.id in SubAgentManager._sub_agents

def test_get_sub_agents():
    SubAgentManager._sub_agents.clear()
    req = DelegationRequest(subTaskDescription="Test task", modelPreference="llama3")
    SubAgentManager.create_sub_agent("parent-A", req)
    SubAgentManager.create_sub_agent("parent-A", req)
    SubAgentManager.create_sub_agent("parent-B", req)
    
    agents_a = SubAgentManager.get_sub_agents("parent-A")
    assert len(agents_a) == 2
    
    agents_all = SubAgentManager.get_sub_agents()
    assert len(agents_all) == 3

def test_terminate_sub_agent():
    req = DelegationRequest(subTaskDescription="Test task", modelPreference="llama3")
    agent = SubAgentManager.create_sub_agent("parent-123", req)
    
    SubAgentManager.terminate_sub_agent(agent.id)
    assert agent.status == "terminated"

@pytest.mark.asyncio
async def test_execute_task(mock_model_service):
    req = DelegationRequest(subTaskDescription="Test task", modelPreference="llama3")
    agent = SubAgentManager.create_sub_agent("parent-123", req)
    
    response = await SubAgentManager.execute_task(agent.id, "Do something")
    
    assert response == "Mocked Response"
    assert agent.status == "idle" # After execution
    mock_model_service.generate.assert_called_once()
