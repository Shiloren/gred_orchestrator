import pytest
from unittest.mock import MagicMock, patch
from tools.gimo_server.services.cost_predictor import CostPredictor
from tools.gimo_server.ops_models import WorkflowNode, UserEconomyConfig, ProviderBudget, ProviderConfig, ProviderEntry

@pytest.fixture
def mock_storage():
    storage = MagicMock()
    # Mock CostStorage behavior
    storage.cost.get_avg_cost_by_task_type.return_value = {
        "avg_cost": 0.05,
        "avg_tokens": 1500,
        "sample_count": 10
    }
    return storage

@pytest.fixture
def mock_provider_config():
    return ProviderConfig(
        active="openai",
        providers={
            "openai": ProviderEntry(type="openai_compat", model="gpt-4o", base_url="http://test", api_key="sk-test"),
            "local": ProviderEntry(type="openai_compat", model="local-model", base_url="http://localhost", api_key=None)
        }
    )

def test_predict_workflow_cost_with_history(mock_storage):
    predictor = CostPredictor(storage=mock_storage)
    
    nodes = [
        WorkflowNode(id="n1", type="llm_call", config={"task_type": "coding", "model": "sonnet"}),
        WorkflowNode(id="n2", type="llm_call", config={"task_type": "coding", "model": "sonnet"}),
        WorkflowNode(id="n3", type="tool_call", config={}) # Should be ignored
    ]
    
    prediction = predictor.predict_workflow_cost(nodes, {}, UserEconomyConfig())
    
    assert prediction["estimated_cost"] == pytest.approx(0.1)
    assert prediction["samples_found"] == 2
    assert prediction["total_llm_nodes"] == 2
    assert prediction["confidence_score"] == pytest.approx(1.0)
    assert prediction["model_breakdown"]["sonnet"] == pytest.approx(0.1)

def test_predict_workflow_cost_fallback(mock_storage):
    # Mock no history
    mock_storage.cost.get_avg_cost_by_task_type.return_value = {
        "sample_count": 0
    }
    
    predictor = CostPredictor(storage=mock_storage)
    
    nodes = [
        WorkflowNode(id="n1", type="llm_call", config={"task_type": "new_task", "model": "local"})
    ]
    
    prediction = predictor.predict_workflow_cost(nodes, {}, UserEconomyConfig())
    
    # local pricing is 0.0
    assert prediction["estimated_cost"] == pytest.approx(0.0)
    assert prediction["samples_found"] == 0
    assert prediction["total_llm_nodes"] == 1

def test_predict_empty_workflow(mock_storage):
    predictor = CostPredictor(storage=mock_storage)
    prediction = predictor.predict_workflow_cost([], {}, UserEconomyConfig())
    
    assert prediction["estimated_cost"] == pytest.approx(0.0)
    assert prediction["total_llm_nodes"] == 0

def test_predict_defaults_to_active_provider(mock_storage, mock_provider_config):
    # Mock ProviderService.get_config to return our mock config
    with patch("tools.gimo_server.services.provider_service.ProviderService.get_config", return_value=mock_provider_config):
        
        # Mock no history to force static pricing check (which depends on model name)
        mock_storage.cost.get_avg_cost_by_task_type.return_value = {"sample_count": 0}
        
        predictor = CostPredictor(storage=mock_storage)
        
        # Node WITHOUT explicit model
        nodes = [
            WorkflowNode(id="n1", type="llm_call", config={"task_type": "generic"})
        ]
        
        prediction = predictor.predict_workflow_cost(nodes, {}, UserEconomyConfig())
        
        # Should populate breakdown with 'gpt-4o' (active in mock_provider_config)
        assert "gpt-4o" in prediction["model_breakdown"]
        assert prediction["model_breakdown"]["gpt-4o"] > 0 # gpt-4o has cost
        
        # Verify it did NOT use 'haiku'
        assert "haiku" not in prediction["model_breakdown"]

def test_predict_defaults_fallback_if_no_config(mock_storage):
    # Mock ProviderService.get_config to return None
    with patch("tools.gimo_server.services.provider_service.ProviderService.get_config", return_value=None):
        mock_storage.cost.get_avg_cost_by_task_type.return_value = {"sample_count": 0}

        predictor = CostPredictor(storage=mock_storage)
        nodes = [WorkflowNode(id="n1", type="llm_call", config={"task_type": "generic"})]

        prediction = predictor.predict_workflow_cost(nodes, {}, UserEconomyConfig())

        # Should fallback to haiku
        assert "haiku" in prediction["model_breakdown"]


def test_predict_filters_by_configured_providers(mock_storage):
    """Models whose provider is not in provider_budgets are replaced with 'local'."""
    mock_storage.cost.get_avg_cost_by_task_type.return_value = {"sample_count": 0}

    predictor = CostPredictor(storage=mock_storage)

    # User only configured anthropic provider
    config = UserEconomyConfig(
        provider_budgets=[ProviderBudget(provider="anthropic", max_cost_usd=50.0)]
    )

    # Node explicitly requests gpt-4o (openai provider) — not in allowed list
    nodes = [
        WorkflowNode(id="n1", type="llm_call", config={"task_type": "coding", "model": "gpt-4o"})
    ]

    prediction = predictor.predict_workflow_cost(nodes, {}, config)

    # gpt-4o should be filtered out, replaced with local
    assert "gpt-4o" not in prediction["model_breakdown"]
    assert "local" in prediction["model_breakdown"]
    assert prediction["estimated_cost"] == pytest.approx(0.0)  # local cost is 0


def test_predict_allows_configured_providers(mock_storage):
    """Models whose provider IS in provider_budgets are kept."""
    mock_storage.cost.get_avg_cost_by_task_type.return_value = {"sample_count": 0}

    predictor = CostPredictor(storage=mock_storage)

    config = UserEconomyConfig(
        provider_budgets=[ProviderBudget(provider="openai", max_cost_usd=50.0)]
    )

    nodes = [
        WorkflowNode(id="n1", type="llm_call", config={"task_type": "coding", "model": "gpt-4o"})
    ]

    prediction = predictor.predict_workflow_cost(nodes, {}, config)

    # gpt-4o is allowed (openai is configured)
    assert "gpt-4o" in prediction["model_breakdown"]


def test_predict_no_provider_budgets_allows_all(mock_storage):
    """When provider_budgets is empty, all models are allowed."""
    mock_storage.cost.get_avg_cost_by_task_type.return_value = {"sample_count": 0}

    predictor = CostPredictor(storage=mock_storage)

    # Empty provider_budgets — no restriction
    config = UserEconomyConfig(provider_budgets=[])

    nodes = [
        WorkflowNode(id="n1", type="llm_call", config={"task_type": "coding", "model": "gpt-4o"})
    ]

    prediction = predictor.predict_workflow_cost(nodes, {}, config)

    assert "gpt-4o" in prediction["model_breakdown"]
