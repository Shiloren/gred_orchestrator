
import pytest
from tools.gimo_server.ops_models import (
    OpsConfig, 
    UserEconomyConfig, 
    ProviderBudget, 
    CascadeConfig, 
    EcoModeConfig
)

def test_user_economy_config_defaults():
    config = UserEconomyConfig()
    assert config.autonomy_level == "manual"
    assert config.global_budget_usd is None
    assert config.provider_budgets == []
    assert config.cascade.enabled is False
    assert config.eco_mode.mode == "off"
    assert config.allow_roi_routing is False
    assert config.cache_enabled is False

def test_user_economy_config_serialization():
    config = UserEconomyConfig(
        autonomy_level="guided",
        global_budget_usd=100.0,
        provider_budgets=[
            ProviderBudget(provider="openai", max_cost_usd=50.0, period="monthly")
        ],
        cascade=CascadeConfig(enabled=True, min_tier="haiku"),
        eco_mode=EcoModeConfig(mode="smart")
    )
    
    json_data = config.model_dump()
    assert json_data["autonomy_level"] == "guided"
    assert json_data["global_budget_usd"] == pytest.approx(100.0)
    assert json_data["provider_budgets"][0]["provider"] == "openai"
    assert json_data["cascade"]["enabled"] is True
    assert json_data["eco_mode"]["mode"] == "smart"

    # Deserialization
    loaded = UserEconomyConfig(**json_data)
    assert loaded.autonomy_level == "guided"
    assert loaded.provider_budgets[0].max_cost_usd == pytest.approx(50.0)

def test_boundary_values():
    """Verify boundary values for validation logic."""
    # Quality threshold boundaries
    config = CascadeConfig(quality_threshold=0)
    assert config.quality_threshold == 0
    config = CascadeConfig(quality_threshold=100)
    assert config.quality_threshold == 100

    # Confidence threshold boundaries
    eco = EcoModeConfig(confidence_threshold_aggressive=0.0, confidence_threshold_moderate=1.0)
    assert eco.confidence_threshold_aggressive == pytest.approx(0.0)
    assert eco.confidence_threshold_moderate == pytest.approx(1.0)

    # Budget boundaries
    econ = UserEconomyConfig(global_budget_usd=0.0)
    assert econ.global_budget_usd == pytest.approx(0.0)

def test_ops_config_integration():
    ops_config = OpsConfig()
    assert ops_config.economy.autonomy_level == "manual"
    
    ops_config.economy.autonomy_level = "autonomous"
    assert ops_config.economy.autonomy_level == "autonomous"
    
    # Verify legacy eco_mode is gone (it should raise AttributeError if accessed dynamically, 
    # but Pydantic might allow it if extra='ignore'. However, it shouldn't be in model_fields)
    assert "eco_mode" not in OpsConfig.model_fields
    
    # OpsConfig default initialization should include economy
    json_data = ops_config.model_dump()
    assert "economy" in json_data

def test_ops_config_migration():
    """Verify that loading a config with legacy fields doesn't crash."""
    legacy_json = """
    {
        "default_auto_run": true,
        "eco_mode": true
    }
    """
    # Should load without error, ignoring eco_mode
    config = OpsConfig.model_validate_json(legacy_json)
    assert config.default_auto_run is True
    # And economy should be initialized with defaults
    assert config.economy.eco_mode.mode == "off"

from pydantic import ValidationError

def test_invalid_global_budget():
    """Verify negative budget raises error."""
    with pytest.raises(ValidationError) as excinfo:
        UserEconomyConfig(global_budget_usd=-10.0)
    assert "global_budget_usd must be >= 0" in str(excinfo.value)

def test_invalid_alert_thresholds():
    """Verify out-of-range thresholds raise error."""
    with pytest.raises(ValidationError) as excinfo:
        UserEconomyConfig(alert_thresholds=[120, 50])
    assert "Alert thresholds must be percentages between 0 and 100" in str(excinfo.value)
    
    # Should resolve duplicates and sort
    config = UserEconomyConfig(alert_thresholds=[10, 50, 50, 25])
    assert config.alert_thresholds == [50, 25, 10]

def test_invalid_cache_ttl():
    """Verify negative TTL raises error."""
    with pytest.raises(ValidationError) as excinfo:
        UserEconomyConfig(cache_ttl_hours=-1)
    assert "cache_ttl_hours must be >= 0" in str(excinfo.value)

def test_invalid_cascade_config():
    """Verify invalid quality threshold or max escalations."""
    with pytest.raises(ValidationError):
        CascadeConfig(quality_threshold=101)
    
    with pytest.raises(ValidationError):
        CascadeConfig(max_escalations=-1)

def test_invalid_eco_mode_config():
    """Verify invalid confidence thresholds."""
    with pytest.raises(ValidationError):
        EcoModeConfig(confidence_threshold_aggressive=1.5)

def test_invalid_provider_budget():
    """Verify negative max cost."""
    with pytest.raises(ValidationError):
        ProviderBudget(provider="test", max_cost_usd=-5.0)

