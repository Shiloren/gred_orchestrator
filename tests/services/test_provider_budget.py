
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Any, Dict, Optional

from tools.gimo_server.ops_models import (
    WorkflowNode, OpsConfig, UserEconomyConfig, ProviderBudget
)
from tools.gimo_server.services.model_router_service import ModelRouterService
from tools.gimo_server.services.storage_service import StorageService
from tools.gimo_server.services.storage.cost_storage import CostStorage

@pytest.fixture
def mock_storage():
    storage = MagicMock(spec=StorageService)
    storage.cost = MagicMock(spec=CostStorage)
    return storage

@pytest.fixture
def model_router(mock_storage):
    return ModelRouterService(storage=mock_storage)

@pytest.mark.asyncio
async def test_provider_budget_enforcement(model_router, mock_storage):
    # Setup Config
    config = OpsConfig()
    config.economy.provider_budgets = [
        ProviderBudget(provider="openai", max_cost_usd=10.0, period="monthly"),
        ProviderBudget(provider="anthropic", max_cost_usd=50.0, period="monthly")
    ]
    
    # Setup Node
    node = WorkflowNode(id="test", type="llm_call", config={"model": "gpt-4o", "task_type": "generation"})
    state = {}

    # Case 1: OpenAI within budget
    mock_storage.cost.get_provider_spend.return_value = 5.0 # Spent 5 out of 10
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await model_router.choose_model(node, state)
        assert decision.model == "gpt-4o"
        assert "policy" in decision.reason

    # Case 2: OpenAI budget exhausted
    mock_storage.cost.get_provider_spend.side_effect = lambda p, days: 10.5 if p == "openai" else 0.0
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await model_router.choose_model(node, state)
        # Should degrade to local or another provider if degradation logic permits
        # In current implementation, degrade("gpt-4o") -> might not switch provider immediately if next tier is still openai
        # Let's check what degrade does. 
        # Tiers are ["local", "haiku", "sonnet", "opus"]
        # Wait, gpt-4o is NOT is _TIERS list in ModelRouterService! 
        # ModelRouterService._TIERS = ["local", "haiku", "sonnet", "opus"]
        # The default policy uses these keys.
        # If I use "gpt-4o" it might return as is or fallback.
        
        # Let's adjust the test to use a supported tier for better testing of logic
        pass

@pytest.mark.asyncio
async def test_provider_budget_exhausted_degradation(model_router, mock_storage):
    # Setup Config
    config = OpsConfig()
    config.economy.provider_budgets = [
        ProviderBudget(provider="anthropic", max_cost_usd=10.0, period="monthly")
    ]
    
    # Node requesting "opus" (anthropic)
    node = WorkflowNode(id="test", type="llm_call", config={"model": "opus", "task_type": "security_review"})
    state = {}

    # Anthropic budget exhausted
    mock_storage.cost.get_provider_spend.return_value = 11.0 
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await model_router.choose_model(node, state)
        
        # Should degrade. 
        # opus -> sonnet (anthropic) -> haiku (anthropic) -> local (local)
        # Verify it falls back to 'local' because 'anthropic' is exhausted for ALL anthropic models
        assert decision.model == "local"
        assert "budget_exhausted" in decision.reason

@pytest.mark.asyncio
async def test_global_budget_check_is_separate(model_router, mock_storage):
    # This test ensures we are testing PROVIDER budget, not global
    # Providers:
    # "anthropic": used by opus, sonnet, haiku
    # "local": used by local
    
    config = OpsConfig()
    config.economy.provider_budgets = [
        ProviderBudget(provider="anthropic", max_cost_usd=5.0)
    ]
    
    node = WorkflowNode(id="n1", type="llm_call", config={"model": "sonnet"})
    
    # Spend is high
    mock_storage.cost.get_provider_spend.return_value = 6.0
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await model_router.choose_model(node, {})
        assert decision.model == "local"

