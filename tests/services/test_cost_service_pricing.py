import pytest
from unittest.mock import patch
import json
from tools.gimo_server.services.cost_service import CostService

# Mock data for testing
MOCK_PRICING = {
    "test-model": {"input": 1.0, "output": 2.0},
    "local": {"input": 0.0, "output": 0.0}
}

@pytest.fixture(autouse=True)
def reset_cost_service():
    """Reset CostService state before and after each test."""
    CostService._PRICING_LOADED = False
    CostService.PRICING_REGISTRY = {}
    yield
    CostService._PRICING_LOADED = False
    CostService.PRICING_REGISTRY = {}

class CustomMockFile:
    def __init__(self, data):
        self.data = data
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    def read(self):
        return self.data

def test_load_pricing_success():
    # Use custom mock class
    mock_file = CustomMockFile(json.dumps(MOCK_PRICING))
    
    with patch("builtins.open", return_value=mock_file):
        with patch("os.path.exists", return_value=True):
            CostService.load_pricing()
            
            assert CostService._PRICING_LOADED is True
            assert "test-model" in CostService.PRICING_REGISTRY
            assert CostService.PRICING_REGISTRY["test-model"]["input"] == pytest.approx(1.0)

def test_get_pricing_direct_match():
    CostService.PRICING_REGISTRY = MOCK_PRICING.copy()
    CostService._PRICING_LOADED = True
    
    price = CostService.get_pricing("test-model")
    assert price["input"] == pytest.approx(1.0)
    assert price["output"] == pytest.approx(2.0)

def test_get_pricing_alias_match():
    CostService.PRICING_REGISTRY = MOCK_PRICING.copy()
    CostService._PRICING_LOADED = True
    
    original_mapping = CostService.MODEL_MAPPING.copy()
    CostService.MODEL_MAPPING["test-alias"] = "test-model"
    try:
        price = CostService.get_pricing("my-test-alias-v1")
        assert price["input"] == pytest.approx(1.0)
    finally:
        CostService.MODEL_MAPPING = original_mapping

def test_get_pricing_fallback():
    CostService.PRICING_REGISTRY = {"local": {"input": 0.0, "output": 0.0}}
    CostService._PRICING_LOADED = True
    
    price = CostService.get_pricing("unknown-model")
    assert price["input"] == pytest.approx(0.0)
    assert price["output"] == pytest.approx(0.0)

def test_calculate_cost():
    CostService.PRICING_REGISTRY = MOCK_PRICING.copy()
    CostService._PRICING_LOADED = True
    
    cost = CostService.calculate_cost("test-model", 1_000_000, 0)
    assert cost == pytest.approx(1.0)
    
    cost = CostService.calculate_cost("test-model", 500_000, 500_000)
    assert cost == pytest.approx(1.5)

def test_calculate_roi():
    # ROI = Quality / Cost
    # Quality=90, Cost=0.01 -> ROI=9000
    roi = CostService.calculate_roi(90.0, 0.01)
    assert roi == pytest.approx(9000.0, rel=1e-3)
    
    # Usage of epsilon
    # Quality=100, Cost=0.0
    # Expected: 100 / 1e-6 = 100,000,000
    roi_zero = CostService.calculate_roi(100.0, 0.0)
    assert roi_zero == pytest.approx(100_000_000.0, rel=1e-3)

def test_get_provider_fuzzy_match():
    # Regression test for get_provider consistency
    # "super-fast-flash" contains "flash" -> maps to gymini-1.5-flash -> google
    
    # We don't need to load pricing for get_provider, but we need the mapping
    # The mapping is class-level constant, so it's always there.
    
    provider = CostService.get_provider("super-fast-flash")
    assert provider == "google"
    
    provider_sonnet = CostService.get_provider("my-sonnet-wrapper")
    assert provider_sonnet == "anthropic"
    
    # Ensure standard ones still work
    assert CostService.get_provider("gpt-4o") == "openai"
