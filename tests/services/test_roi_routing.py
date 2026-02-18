
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tools.gimo_server.ops_models import OpsConfig, UserEconomyConfig, WorkflowNode
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
    router = ModelRouterService(storage=mock_storage)
    router._TIERS = ["local", "haiku", "sonnet", "opus"]
    return router

@pytest.mark.asyncio
async def test_roi_routing_enabled(model_router, mock_storage):
    config = OpsConfig()
    config.economy.allow_roi_routing = True
    config.economy.autonomy_level = "autonomous"
    
    node = WorkflowNode(id="n1", type="llm_call", config={"model": "opus", "task_type": "generation"})
    
    # ROI Leaderboard suggests "haiku" is best
    mock_storage.cost.get_roi_leaderboard.return_value = [
        {"model": "haiku", "task_type": "generation", "sample_count": 20, "roi_score": 100},
        {"model": "opus", "task_type": "generation", "sample_count": 20, "roi_score": 50}
    ]
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await model_router.choose_model(node, {})
        assert decision.model == "haiku"
        assert "roi_routing" in decision.reason

@pytest.mark.asyncio
async def test_roi_routing_insufficient_samples(model_router, mock_storage):
    config = OpsConfig()
    config.economy.allow_roi_routing = True
    config.economy.autonomy_level = "autonomous"
    
    node = WorkflowNode(id="n1", type="llm_call", config={"model": "opus", "task_type": "generation"})
    
    # ROI Leaderboard suggests "haiku" but only 5 samples
    mock_storage.cost.get_roi_leaderboard.return_value = [
        {"model": "haiku", "task_type": "generation", "sample_count": 5, "roi_score": 100}
    ]
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await model_router.choose_model(node, {})
        # Should stick to original model "opus" because samples < 10
        assert decision.model == "opus"

@pytest.mark.asyncio
async def test_roi_routing_respects_floor(model_router, mock_storage):
    config = OpsConfig()
    config.economy.allow_roi_routing = True
    config.economy.autonomy_level = "autonomous"
    config.economy.model_floor = "sonnet"
    
    node = WorkflowNode(id="n1", type="llm_call", config={"model": "opus", "task_type": "generation"})
    
    # ROI suggests "haiku" (below floor)
    mock_storage.cost.get_roi_leaderboard.return_value = [
        {"model": "haiku", "task_type": "generation", "sample_count": 20, "roi_score": 100}
    ]
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await model_router.choose_model(node, {})
        # Should check ROI, reject haiku, fallback to original "opus" (or floor if original is below floor, but opus is ok)
        assert decision.model == "opus"

@pytest.mark.asyncio
async def test_roi_advisory_mode(model_router, mock_storage):
    config = OpsConfig()
    config.economy.allow_roi_routing = True
    config.economy.autonomy_level = "advisory" # Advisory only!
    
    node = WorkflowNode(id="n1", type="llm_call", config={"model": "opus", "task_type": "generation"})
    
    mock_storage.cost.get_roi_leaderboard.return_value = [
        {"model": "haiku", "task_type": "generation", "sample_count": 20, "roi_score": 100}
    ]
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await model_router.choose_model(node, {})
        # Should stick to "opus" but mention recommendation in reason
        assert decision.model == "opus"
        assert "ROI recommendation: haiku" in decision.reason
