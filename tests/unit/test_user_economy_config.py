
import pytest
from pydantic import ValidationError
from tools.gimo_server.ops_models import (
    UserEconomyConfig,
    CascadeConfig,
    EcoModeConfig,
    ProviderBudget
)

class TestUserEconomyConfig:
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = UserEconomyConfig()
        assert config.autonomy_level == "manual"
        assert config.global_budget_usd is None
        assert config.provider_budgets == []
        assert config.alert_thresholds == [50, 25, 10]
        assert config.cascade.enabled is False
        assert config.eco_mode.mode == "off"
        assert config.allow_roi_routing is False
        assert config.model_floor is None
        assert config.model_ceiling is None
        assert config.cache_enabled is False
        assert config.cache_ttl_hours == 24
        assert config.show_cost_predictions is False

    def test_global_budget_validation(self):
        """Test validation for global_budget_usd."""
        # Valid values
        config = UserEconomyConfig(global_budget_usd=100.0)
        assert config.global_budget_usd == 100.0
        
        config = UserEconomyConfig(global_budget_usd=0.0)
        assert config.global_budget_usd == 0.0

        # Invalid values
        with pytest.raises(ValidationError) as excinfo:
            UserEconomyConfig(global_budget_usd=-1.0)
        assert "global_budget_usd must be >= 0" in str(excinfo.value)

    def test_alert_thresholds_validation(self):
        """Test validation for alert_thresholds."""
        # Valid values
        config = UserEconomyConfig(alert_thresholds=[10, 50, 90])
        assert config.alert_thresholds == [90, 50, 10]  # Should be sorted reverse
        
        config = UserEconomyConfig(alert_thresholds=[50, 50, 10])
        assert config.alert_thresholds == [50, 10]  # Should be unique and sorted

        # Invalid values
        with pytest.raises(ValidationError) as excinfo:
            UserEconomyConfig(alert_thresholds=[101])
        assert "Alert thresholds must be percentages between 0 and 100" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            UserEconomyConfig(alert_thresholds=[-1])
        assert "Alert thresholds must be percentages between 0 and 100" in str(excinfo.value)

    def test_cache_ttl_validation(self):
        """Test validation for cache_ttl_hours."""
        # Valid values
        config = UserEconomyConfig(cache_ttl_hours=0)
        assert config.cache_ttl_hours == 0
        
        config = UserEconomyConfig(cache_ttl_hours=100)
        assert config.cache_ttl_hours == 100

        # Invalid values
        with pytest.raises(ValidationError) as excinfo:
            UserEconomyConfig(cache_ttl_hours=-1)
        assert "cache_ttl_hours must be >= 0" in str(excinfo.value)


class TestCascadeConfig:
    def test_quality_threshold_validation(self):
        """Test validation for quality_threshold."""
        # Valid values
        config = CascadeConfig(quality_threshold=0)
        assert config.quality_threshold == 0
        
        config = CascadeConfig(quality_threshold=100)
        assert config.quality_threshold == 100

        # Invalid values
        with pytest.raises(ValidationError) as excinfo:
            CascadeConfig(quality_threshold=-1)
        assert "quality_threshold must be between 0 and 100" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            CascadeConfig(quality_threshold=101)
        assert "quality_threshold must be between 0 and 100" in str(excinfo.value)

    def test_max_escalations_validation(self):
        """Test validation for max_escalations."""
        # Valid values
        config = CascadeConfig(max_escalations=0)
        assert config.max_escalations == 0
        
        config = CascadeConfig(max_escalations=10)
        assert config.max_escalations == 10

        # Invalid values
        with pytest.raises(ValidationError) as excinfo:
            CascadeConfig(max_escalations=-1)
        assert "max_escalations must be >= 0" in str(excinfo.value)


class TestEcoModeConfig:
    def test_confidence_threshold_validation(self):
        """Test validation for confidence thresholds."""
        # Valid values
        config = EcoModeConfig(
            confidence_threshold_aggressive=0.5,
            confidence_threshold_moderate=0.8
        )
        assert config.confidence_threshold_aggressive == 0.5
        assert config.confidence_threshold_moderate == 0.8
        
        # Boundary values
        config = EcoModeConfig(
            confidence_threshold_aggressive=0.0,
            confidence_threshold_moderate=1.0
        )
        assert config.confidence_threshold_aggressive == 0.0
        assert config.confidence_threshold_moderate == 1.0

        # Invalid values - aggressive
        with pytest.raises(ValidationError) as excinfo:
            EcoModeConfig(confidence_threshold_aggressive=-0.1)
        assert "Confidence thresholds must be between 0.0 and 1.0" in str(excinfo.value)
        
        with pytest.raises(ValidationError) as excinfo:
            EcoModeConfig(confidence_threshold_aggressive=1.1)
        assert "Confidence thresholds must be between 0.0 and 1.0" in str(excinfo.value)

        # Invalid values - moderate
        with pytest.raises(ValidationError) as excinfo:
            EcoModeConfig(confidence_threshold_moderate=-0.1)
        assert "Confidence thresholds must be between 0.0 and 1.0" in str(excinfo.value)


class TestProviderBudget:
    def test_max_cost_validation(self):
        """Test validation for max_cost_usd."""
        # Valid values
        budget = ProviderBudget(provider="openai", max_cost_usd=100.0)
        assert budget.max_cost_usd == 100.0
        
        budget = ProviderBudget(provider="anthropic", max_cost_usd=0.0)
        assert budget.max_cost_usd == 0.0
        
        budget = ProviderBudget(provider="gemini", max_cost_usd=None)
        assert budget.max_cost_usd is None

        # Invalid values
        with pytest.raises(ValidationError) as excinfo:
            ProviderBudget(provider="openai", max_cost_usd=-0.01)
        assert "max_cost_usd must be >= 0" in str(excinfo.value)

