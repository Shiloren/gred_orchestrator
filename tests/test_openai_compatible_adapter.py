import asyncio
import pytest
import respx
from httpx import Response
from tools.gimo_server.adapters.openai_compatible import OpenAICompatibleAdapter, AgentStatus

@pytest.mark.asyncio
@respx.mock
async def test_openai_compatible_adapter_spawn_and_result():
    base_url = "http://localhost:1234/v1"
    model_name = "test-model"
    adapter = OpenAICompatibleAdapter(base_url=base_url, model_name=model_name)
    
    # Mock the LLM response
    respx.post(f"{base_url}/chat/completions").mock(return_value=Response(200, json={
        "choices": [{"message": {"role": "assistant", "content": "Hello world"}, "index": 0, "finish_reason": "stop"}],
        "usage": {"total_tokens": 10}
    }))
    
    session = await adapter.spawn("Repeat 'Hello world'")
    assert session is not None
    
    result = await session.get_result()
    assert result.status == AgentStatus.COMPLETED
    assert result.output == "Hello world"
    assert result.metrics["tokens_used"] == 10

@pytest.mark.asyncio
@respx.mock
async def test_openai_compatible_adapter_tool_call():
    base_url = "http://localhost:1234/v1"
    model_name = "test-model"
    adapter = OpenAICompatibleAdapter(base_url=base_url, model_name=model_name)
    
    # Mock the first response with a tool call
    respx.post(f"{base_url}/chat/completions").mock(return_value=Response(200, json={
        "choices": [{
            "message": {
                "role": "assistant", 
                "content": None,
                "tool_calls": [{
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "test_tool", "arguments": '{"arg1": "val1"}'}
                }]
            }, 
            "index": 0
        }],
        "usage": {"total_tokens": 20}
    }))
    
    session = await adapter.spawn("Call test_tool")
    
    # Wait for background task to update status
    import asyncio
    for _ in range(10):
        if await session.get_status() == AgentStatus.PAUSED:
            break
        await asyncio.sleep(0.1)
        
    assert await session.get_status() == AgentStatus.PAUSED
    proposals = await session.capture_proposals()
    assert len(proposals) == 1
    assert proposals[0].tool == "test_tool"
    assert proposals[0].params == {"arg1": "val1"}

    # Mock the second response after tool result
    respx.post(f"{base_url}/chat/completions").mock(return_value=Response(200, json={
        "choices": [{"message": {"role": "assistant", "content": "Tool executed successfully"}, "index": 0}],
        "usage": {"total_tokens": 5}
    }))

    await session.allow("call_123")
    
    # Wait for background task
    for _ in range(10):
        if await session.get_status() == AgentStatus.COMPLETED:
            break
        await asyncio.sleep(0.1)

    result = await session.get_result()
    assert result.status == AgentStatus.COMPLETED
    assert result.output == "Tool executed successfully"
    assert result.metrics["tokens_used"] == 25

@pytest.mark.asyncio
@respx.mock
async def test_openai_compatible_adapter_deny():
    base_url = "http://localhost:1234/v1"
    model_name = "test-model"
    adapter = OpenAICompatibleAdapter(base_url=base_url, model_name=model_name)
    
    respx.post(f"{base_url}/chat/completions").mock(return_value=Response(200, json={
        "choices": [{
            "message": {
                "role": "assistant", 
                "content": None,
                "tool_calls": [{"id": "call_456", "type": "function", "function": {"name": "unsafe_tool", "arguments": "{}"}}]
            }, 
            "index": 0
        }],
        "usage": {"total_tokens": 10}
    }))
    
    session = await adapter.spawn("Call unsafe_tool")
    await asyncio.sleep(0.2)
    
    # Mock response after deny
    respx.post(f"{base_url}/chat/completions").mock(return_value=Response(200, json={
        "choices": [{"message": {"role": "assistant", "content": "I understand you denied that."}, "index": 0}],
        "usage": {"total_tokens": 5}
    }))
    
    await session.deny("call_456", reason="Not safe")
    await asyncio.sleep(0.2)
    
    result = await session.get_result()
    assert result.output == "I understand you denied that."

@pytest.mark.asyncio
@respx.mock
async def test_openai_compatible_adapter_error():
    base_url = "http://localhost:1234/v1"
    model_name = "test-model"
    adapter = OpenAICompatibleAdapter(base_url=base_url, model_name=model_name)
    
    respx.post(f"{base_url}/chat/completions").mock(return_value=Response(500))
    
    session = await adapter.spawn("Fail")
    await asyncio.sleep(0.2)
    
    result = await session.get_result()
    assert result.status == AgentStatus.FAILED
    assert "error" in result.metrics
