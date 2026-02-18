import pytest
import asyncio
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from tools.gimo_server.ops_models import WorkflowNode, WorkflowGraph, ToolEntry
from tools.gimo_server.services.graph_engine import GraphEngine

# Tests for _execute_node logic
@pytest.mark.asyncio
async def test_llm_call_execution():
    # Mock ProviderService
    with patch("tools.gimo_server.services.graph_engine.ProviderService") as MockProvider:
        mock_instance = MockProvider.return_value
        mock_instance.generate = AsyncMock(return_value={
            "provider": "mock_provider",
            "model": "gpt-4",
            "content": "Hello from LLM",
            "tokens_used": 100,
            "cost_usd": 0.001
        })
        
        node = WorkflowNode(
            id="llm_1",
            type="llm_call",
            config={"prompt": "Hi", "selected_model": "gpt-4"}
        )
        graph = WorkflowGraph(id="test_graph", nodes=[node], edges=[])
        engine = GraphEngine(graph)
        
        # Initialize state
        engine.state.data = {"history": []}
        
        # Execute directly
        result = await engine._execute_node(node)
        
        assert result["role"] == "assistant"
        assert result["content"] == "Hello from LLM"
        assert result["provider"] == "mock_provider"
        assert result["model_used"] == "gpt-4"
        
        mock_instance.generate.assert_called_once()


@pytest.mark.asyncio
async def test_mcp_tool_call_execution():
    # Mock ToolRegistryService, ProviderService, McpClient
    with patch("tools.gimo_server.services.graph_engine.ToolRegistryService") as MockRegistry, \
         patch("tools.gimo_server.services.graph_engine.ProviderService") as MockProvider, \
         patch("tools.gimo_server.services.graph_engine.McpClient") as MockMcpClient:
         
        # Setup Registry
        entry = ToolEntry(
            name="dummy_tool", 
            metadata={"mcp_server": "dummy_server", "mcp_tool": "real_tool_name"}
        )
        MockRegistry.get_tool.return_value = entry
        
        # Setup Provider Config (for MCP server config)
        mock_ops_config = MagicMock()
        mock_server_config = MagicMock()
        mock_ops_config.mcp_servers = {"dummy_server": mock_server_config}
        MockProvider.get_config.return_value = mock_ops_config
        
        # Setup McpClient
        mock_client_instance = AsyncMock()
        mock_client_instance.call_tool.return_value = {"result": "success"}
        MockMcpClient.return_value.__aenter__.return_value = mock_client_instance
        
        node = WorkflowNode(
            id="tool_1",
            type="tool_call",
            config={"tool_name": "dummy_tool", "arguments": {"x": 1}}
        )
        graph = WorkflowGraph(id="test_graph", nodes=[node], edges=[])
        engine = GraphEngine(graph)
        
        result = await engine._execute_node(node)
        
        assert result["tool"] == "dummy_tool"
        assert result["output"] == {"result": "success"}
        assert result["mcp_server"] == "dummy_server"
        
        # Verify McpClient called correctly
        MockMcpClient.assert_called_with("dummy_server", mock_server_config)
        mock_client_instance.call_tool.assert_called_with("real_tool_name", {"x": 1})

if __name__ == "__main__":
    # Manual run for quick verification outside of pytest runner
    async def run_checks():
        print("Running test_llm_call_execution...")
        await test_llm_call_execution()
        print("Passed.")
        
        print("Running test_mcp_tool_call_execution...")
        await test_mcp_tool_call_execution()
        print("Passed.")
        
    asyncio.run(run_checks())
