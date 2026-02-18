import pytest
from unittest.mock import MagicMock, patch
from tools.gimo_server.ops_models import OpsConfig, UserEconomyConfig, EcoModeConfig, WorkflowNode
from tools.gimo_server.services.model_router_service import ModelRouterService
from tools.gimo_server.services.storage_service import StorageService
from tools.gimo_server.services.storage.cost_storage import CostStorage

@pytest.mark.asyncio
async def test_roi_routing_opt_out():
    """Reproduction of Phase 4/5 bug: eco-mode should not apply if it's 'off'."""
    storage = MagicMock(spec=StorageService)
    storage.cost = MagicMock(spec=CostStorage)
    router = ModelRouterService(storage=storage)
    router._TIERS = ["local", "haiku", "sonnet", "opus"]

    # Config: ROI enabled, BUT Eco-Mode is OFF
    config = OpsConfig()
    config.economy.allow_roi_routing = True
    config.economy.autonomy_level = "autonomous"
    config.economy.eco_mode = EcoModeConfig(mode="off")
    
    node = WorkflowNode(id="n1", type="llm_call", config={"model": "opus", "task_type": "generation"})
    
    # ROI Leaderboard suggests "sonnet" is best
    storage.cost.get_roi_leaderboard.return_value = [
        {"model": "sonnet", "task_type": "generation", "sample_count": 20, "roi_score": 100},
        {"model": "opus", "task_type": "generation", "sample_count": 20, "roi_score": 50}
    ]
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await router.choose_model(node, {})
        # BUG: The user says it "degrades anyway". 
        # If it works correctly, it should be "sonnet" (from ROI).
        # If the bug exists, maybe it becomes "haiku" or "local" because of some other logic.
        assert decision.model == "sonnet", f"Expected 'sonnet' from ROI, got '{decision.model}'"
        assert "roi_routing" in decision.reason

@pytest.mark.asyncio
async def test_roi_routing_selection():
    """Reproduction: ROI routing should select model, and eco-mode should NOT override if 'off'."""
    # Similar to above but specifically checking the override
    storage = MagicMock(spec=StorageService)
    storage.cost = MagicMock(spec=CostStorage)
    router = ModelRouterService(storage=storage)
    router._TIERS = ["local", "haiku", "sonnet", "opus"]

    config = OpsConfig()
    config.economy.allow_roi_routing = True
    config.economy.autonomy_level = "guided"
    config.economy.eco_mode = EcoModeConfig(mode="off", floor_tier="haiku")
    
    node = WorkflowNode(id="n1", type="llm_call", config={"model": "opus", "task_type": "generation"})
    
    # ROI suggests "opus" (no change)
    storage.cost.get_roi_leaderboard.return_value = [
        {"model": "opus", "task_type": "generation", "sample_count": 20, "roi_score": 100}
    ]
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await router.choose_model(node, {})
        # If binary eco-mode was incorrectly active, it would force haiku.
        assert decision.model == "opus", f"Expected 'opus', got '{decision.model}'"
