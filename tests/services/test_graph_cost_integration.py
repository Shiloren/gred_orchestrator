
import asyncio
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from tools.gimo_server.ops_models import (
    WorkflowGraph,
    WorkflowNode,
    CostEvent
)
from tools.gimo_server.services.graph_engine import GraphEngine
from tools.gimo_server.services.storage_service import StorageService
from tools.gimo_server.services.storage.cost_storage import CostStorage

@pytest.mark.asyncio
async def test_graph_engine_saves_cost_event():
    # 1. Setup Graph
    nodes = [
        WorkflowNode(
            id="node_a", 
            type="llm_call", 
            config={"model": "gpt-4", "task_type": "generation"}
        )
    ]
    graph = WorkflowGraph(id="cost_test_graph", nodes=nodes, edges=[])
    
    # 2. Setup Mock Storage
    mock_storage = MagicMock(spec=StorageService)
    mock_cost = MagicMock(spec=CostStorage)
    mock_storage.cost = mock_cost
    
    # 3. Setup GraphEngine
    engine = GraphEngine(graph, storage=mock_storage)
    
    # 4. Mock execution to return token usage
    async def mock_execute(node, state):
        await asyncio.sleep(0)
        return {
            "output": "hello world",
            "tokens_used": 100,
            "cost_usd": 0.05
        }
    
    engine._execute_node = mock_execute
    
    # 5. Execute
    await engine.execute()
    
    # 6. Verify CostEvent saved
    mock_cost.save_cost_event.assert_called_once()
    event = mock_cost.save_cost_event.call_args[0][0]
    
    assert isinstance(event, CostEvent)
    assert event.workflow_id == "cost_test_graph"
    assert event.node_id == "node_a"
    assert event.total_tokens == 100
    assert event.cost_usd == 0.05
    assert event.model == "gpt-4"
    assert event.task_type == "generation"

@pytest.mark.asyncio
async def test_graph_engine_infers_provider():
    # 1. Setup Graph with model that implies provider
    nodes = [
        WorkflowNode(
            id="claude_node", 
            type="llm_call", 
            config={"model": "claude-3-opus", "task_type": "analysis"}
        )
    ]
    graph = WorkflowGraph(id="provider_test", nodes=nodes, edges=[])
    
    # 2. Setup Mock Storage
    mock_storage = MagicMock(spec=StorageService)
    mock_cost = MagicMock(spec=CostStorage)
    mock_storage.cost = mock_cost
    
    # 3. Setup GraphEngine
    engine = GraphEngine(graph, storage=mock_storage)
    
    # 4. Mock execution
    async def mock_execute(node, state):
        await asyncio.sleep(0)
        return {"tokens_used": 50, "cost_usd": 0.01}
    
    engine._execute_node = mock_execute
    
    # 5. Execute
    await engine.execute()
    
    # 6. Verify Provider Inference
    mock_cost.save_cost_event.assert_called_once()
    event = mock_cost.save_cost_event.call_args[0][0]
    
    assert event.provider == "anthropic"
