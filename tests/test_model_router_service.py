from __future__ import annotations

from tools.gimo_server.ops_models import WorkflowNode
from tools.gimo_server.services.model_router_service import ModelRouterService


def test_model_router_policy_by_task_type():
    router = ModelRouterService()
    node = WorkflowNode(id="n1", type="llm_call", config={"task_type": "security_review"})

    decision = router.choose_model(node, state={})

    assert decision.model == "opus"
    assert decision.reason.startswith("policy:")


def test_model_router_degrades_on_low_budget():
    router = ModelRouterService()
    node = WorkflowNode(id="n2", type="llm_call", config={"task_type": "code_generation"})

    decision = router.choose_model(
        node,
        state={
            "budget": {"max_cost_usd": 10.0},
            "budget_counters": {"cost_usd": 9.0},
        },
    )

    assert decision.model == "haiku"
    assert "low_budget" in decision.reason
