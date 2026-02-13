import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def mock_ws_manager():
    mock_mgr = AsyncMock()
    mock_mgr.broadcast = AsyncMock()
    with patch("tools.repo_orchestrator.ws.manager.manager", mock_mgr):
        yield mock_mgr


@pytest.mark.asyncio
async def test_send_and_get_messages():
    from tools.repo_orchestrator.services.comms_service import CommsService

    agent_id = "test-agent"
    CommsService.clear_messages(agent_id)

    await CommsService.send_message(agent_id, "orchestrator", "instruction", "Hello agent")
    await CommsService.send_message(agent_id, "agent", "report", "Hello orchestrator")

    messages = CommsService.get_messages(agent_id)
    assert len(messages) == 2
    assert messages[0].content == "Hello agent"
    assert messages[1].from_role == "agent"


@pytest.mark.asyncio
async def test_clear_messages():
    from tools.repo_orchestrator.services.comms_service import CommsService

    agent_id = "test-agent-2"
    await CommsService.send_message(agent_id, "orchestrator", "instruction", "Message")
    CommsService.clear_messages(agent_id)
    assert len(CommsService.get_messages(agent_id)) == 0


@pytest.mark.asyncio
async def test_broadcast_on_send(mock_ws_manager):
    from tools.repo_orchestrator.services.comms_service import CommsService

    agent_id = "test-agent-3"
    CommsService.clear_messages(agent_id)

    await CommsService.send_message(agent_id, "orchestrator", "instruction", "Test broadcast")
    mock_ws_manager.broadcast.assert_called_once()
    call_data = mock_ws_manager.broadcast.call_args[0][0]
    assert call_data["type"] == "chat_message"
    assert call_data["agent_id"] == agent_id
