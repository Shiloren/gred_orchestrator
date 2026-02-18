import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tools.gimo_server.ops_models import OpsConfig, UserEconomyConfig, EcoModeConfig, WorkflowNode
from tools.gimo_server.services.model_router_service import ModelRouterService
from tools.gimo_server.services.confidence_service import ConfidenceService

@pytest.fixture
def mock_confidence_service():
    return MagicMock(spec=ConfidenceService)

@pytest.fixture
def model_router(mock_confidence_service):
    router = ModelRouterService(confidence_service=mock_confidence_service)
    # Expose _TIERS
    router._TIERS = ["local", "haiku", "sonnet", "opus"]
    return router

@pytest.mark.asyncio
async def test_eco_mode_off(model_router):
    config = OpsConfig()
    config.economy.eco_mode = EcoModeConfig(mode="off")
    config.economy.autonomy_level = "guided"
    
    node = WorkflowNode(id="n1", type="llm_call", config={"model": "opus", "task_type": "generation"})
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await model_router.choose_model(node, {})
        assert decision.model == "opus"

@pytest.mark.asyncio
async def test_eco_mode_binary(model_router):
    config = OpsConfig()
    config.economy.eco_mode = EcoModeConfig(mode="binary", floor_tier="haiku")
    config.economy.autonomy_level = "guided"
    
    node = WorkflowNode(id="n1", type="llm_call", config={"model": "opus", "task_type": "generation"})
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await model_router.choose_model(node, {})
        assert decision.model == "haiku"
        assert "eco_mode:binary" in decision.reason

@pytest.mark.asyncio
async def test_eco_mode_smart_aggressive(model_router, mock_confidence_service):
    config = OpsConfig()
    config.economy.eco_mode = EcoModeConfig(
        mode="smart", 
        floor_tier="haiku",
        confidence_threshold_aggressive=0.8,
        confidence_threshold_moderate=0.6
    )
    config.economy.autonomy_level = "autonomous"
    node = WorkflowNode(
        id="n1", 
        type="llm_call", 
        config={"model": "opus", "task_type": "generation", "description": "task"}
    )
    
    # Mock confidence projection
    mock_confidence_service.project_confidence = AsyncMock(return_value={
        "score": 0.85, 
        "risk_level": "low"
    })
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await model_router.choose_model(node, {})
        assert decision.model == "haiku"

@pytest.mark.asyncio
async def test_eco_mode_smart_moderate(model_router, mock_confidence_service):
    config = OpsConfig()
    config.economy.eco_mode = EcoModeConfig(
        mode="smart", 
        floor_tier="local",
        confidence_threshold_aggressive=0.9,
        confidence_threshold_moderate=0.7
    )
    config.economy.autonomy_level = "autonomous"
    node = WorkflowNode(
        id="n1", 
        type="llm_call", 
        config={"model": "opus", "task_type": "generation", "description": "task"}
    )
    
    mock_confidence_service.project_confidence = AsyncMock(return_value={
        "score": 0.75, 
        "risk_level": "medium"
    })
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await model_router.choose_model(node, {})
        assert decision.model == "sonnet" 

@pytest.mark.asyncio
async def test_respects_floor_in_smart_mode(model_router, mock_confidence_service):
    config = OpsConfig()
    config.economy.eco_mode = EcoModeConfig(
        mode="smart", 
        floor_tier="sonnet", 
        confidence_threshold_moderate=0.5
    )
    config.economy.autonomy_level = "autonomous"
    node = WorkflowNode(
        id="n1", 
        type="llm_call", 
        config={"model": "opus", "task_type": "generation", "description": "task"}
    )
    
    mock_confidence_service.project_confidence = AsyncMock(return_value={
        "score": 0.9, 
        "risk_level": "low"
    })
    
    with patch("tools.gimo_server.services.ops_service.OpsService.get_config", return_value=config):
        decision = await model_router.choose_model(node, {})
        assert decision.model == "sonnet"
