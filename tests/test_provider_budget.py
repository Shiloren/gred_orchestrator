from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from tools.gimo_server.ops_models import (
    WorkflowGraph, 
    WorkflowNode, 
    UserEconomyConfig,
    ProviderBudget,
    OpsConfig
)
from tools.gimo_server.services.graph_engine import GraphEngine

@pytest.mark.asyncio
async def test_provider_budget_enforcement_nested_nodes():
    """
    Test that provider budget enforcement works for nested nodes.
    By mocking check_provider_budget, we verify that GraphEngine properly calls it
    and reacts to the 'exhausted' signal even for child nodes.
    """
    # 1. Setup a graph with a supervisor-worker pattern
    nodes = [
        WorkflowNode(
            id="supervisor",
            type="agent_task",
            config={
                "pattern": "supervisor_workers",
                "workers": [
                    {"id": "worker1", "task": "do something"}
                ]
            }
        )
    ]
    graph = WorkflowGraph(id="nested_budget_test", nodes=nodes, edges=[])
    
    # 2. Setup GraphEngine
    mock_storage = MagicMock()
    mock_storage.cost = MagicMock()
    mock_storage.cost.get_total_spend.return_value = 0.0
    mock_storage.cost.get_provider_spend.return_value = 0.0

    engine = GraphEngine(graph, storage=mock_storage)
    engine._execute_node = AsyncMock(return_value={"status": "ok"})

    # 3. Mocks
    with patch("tools.gimo_server.services.graph_engine.ConfidenceService") as mock_conf_cls:
        mock_conf_instance = mock_conf_cls.return_value
        mock_conf_instance.get_confidence_score.return_value = {"score": 0.9, "reasoning": "test"}

        with patch.object(engine._model_router, "check_provider_budget", new_callable=AsyncMock) as mock_check:
            mock_check.side_effect = [
                None, # supervisor OK
                "provider_budget_exhausted: anthropic" # worker1 BLOCKED
            ]
            
            with patch.object(engine._model_router, "choose_model", new_callable=AsyncMock) as mock_choose:
                from tools.gimo_server.services.model_router_service import RoutingDecision
                mock_choose.return_value = RoutingDecision(model="claude-3-sonnet", reason="test")

                # Execute
                try:
                    state = await engine.execute()
                    print(f"DEBUG: execute() returned. Pause reason: {state.data.get('pause_reason')}, Aborted reason: {state.data.get('aborted_reason')}")
                except Exception as e:
                    print(f"DEBUG: execute() raised {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
                
                # If the fix works, it should have been blocked at the worker level
                assert state.data.get("pause_reason") or state.data.get("aborted_reason"), "Budget check was skipped for nested node!"
                reason = str(state.data.get("pause_reason") or state.data.get("aborted_reason"))
                print(f"Captured reason: {reason}")
                assert "provider_budget_exhausted" in reason.lower()
                assert "anthropic" in reason.lower()

if __name__ == "__main__":
    asyncio.run(test_provider_budget_enforcement_nested_nodes())
