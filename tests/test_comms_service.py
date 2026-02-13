import pytest
from tools.repo_orchestrator.services.comms_service import CommsService
from tools.repo_orchestrator.models import AgentMessage

def test_send_and_get_messages():
    agent_id = "test-agent"
    CommsService.clear_messages(agent_id)
    
    CommsService.send_message(agent_id, "orchestrator", "instruction", "Hello agent")
    CommsService.send_message(agent_id, "agent", "report", "Hello orchestrator")
    
    messages = CommsService.get_messages(agent_id)
    assert len(messages) == 2
    assert messages[0].content == "Hello agent"
    assert messages[1].from_role == "agent"
    
def test_clear_messages():
    agent_id = "test-agent-2"
    CommsService.send_message(agent_id, "orchestrator", "instruction", "Message")
    CommsService.clear_messages(agent_id)
    assert len(CommsService.get_messages(agent_id)) == 0
