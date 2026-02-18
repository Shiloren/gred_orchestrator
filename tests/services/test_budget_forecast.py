import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from tools.gimo_server.ops_models import UserEconomyConfig, ProviderBudget, BudgetForecast
from tools.gimo_server.services.budget_forecast_service import BudgetForecastService

@pytest.fixture
def mock_storage():
    storage = MagicMock()
    storage.cost = MagicMock()
    return storage

def test_forecast_no_budget(mock_storage):
    service = BudgetForecastService(mock_storage)
    config = UserEconomyConfig(global_budget_usd=None)

    forecasts = service.forecast(config)
    assert len(forecasts) == 0

def test_forecast_global_budget(mock_storage):
    # Setup mock data
    mock_storage.cost.get_total_spend.return_value = 50.0  # Spend so far
    mock_storage.cost.get_spend_rate.return_value = 1.0    # 1.0 USD/hour

    service = BudgetForecastService(mock_storage)
    config = UserEconomyConfig(
        global_budget_usd=100.0,
        alert_thresholds=[50, 25, 10] # % remaining
    )

    forecasts = service.forecast(config)
    assert len(forecasts) == 1

    f = forecasts[0]
    assert f.scope == "global"
    assert f.current_spend == pytest.approx(50.0)
    assert f.limit == pytest.approx(100.0)
    assert f.remaining == pytest.approx(50.0)
    assert f.remaining_pct == pytest.approx(50.0)
    assert f.burn_rate_hourly == pytest.approx(1.0)
    assert f.hours_to_exhaustion == pytest.approx(50.0, rel=0.1)
    assert f.alert_level == "none"

def test_forecast_zero_budget(mock_storage):
    # Budget is 0, spend is 1.0 -> 0% remaining
    mock_storage.cost.get_total_spend.return_value = 1.0
    mock_storage.cost.get_spend_rate.return_value = 0.0

    service = BudgetForecastService(mock_storage)
    config = UserEconomyConfig(global_budget_usd=0.0)

    forecasts = service.forecast(config)
    assert forecasts[0].alert_level == "critical"
    assert forecasts[0].remaining == 0.0

def test_forecast_alert_warning(mock_storage):
    # 80 spent of 100 -> 20 remaining (20%)
    mock_storage.cost.get_total_spend.return_value = 80.0
    mock_storage.cost.get_spend_rate.return_value = 0.5 # 0.5 USD/hour

    service = BudgetForecastService(mock_storage)
    config = UserEconomyConfig(
        global_budget_usd=100.0,
        alert_thresholds=[50, 25, 10]
    )

    forecasts = service.forecast(config)
    # 20% remaining is <= 25% threshold -> warning
    assert forecasts[0].alert_level == "warning"

def test_forecast_alert_critical(mock_storage):
    # 95 spent of 100 -> 5 remaining (5%)
    mock_storage.cost.get_total_spend.return_value = 95.0
    mock_storage.cost.get_spend_rate.return_value = 0.5

    service = BudgetForecastService(mock_storage)
    config = UserEconomyConfig(
        global_budget_usd=100.0,
        alert_thresholds=[50, 25, 10]
    )

    forecasts = service.forecast(config)
    # 5% remaining is <= 10% threshold -> critical
    assert forecasts[0].alert_level == "critical"

def test_forecast_provider_budget(mock_storage):
    mock_storage.cost.get_provider_spend.return_value = 5.0
    mock_storage.cost.get_spend_rate.return_value = 0.1 # 0.1 USD/hour

    service = BudgetForecastService(mock_storage)
    config = UserEconomyConfig(
        global_budget_usd=None, # Disable global
        provider_budgets=[
            ProviderBudget(provider="openai", max_cost_usd=10.0, period="monthly")
        ]
    )

    forecasts = service.forecast(config)
    assert len(forecasts) == 1
    assert forecasts[0].scope == "openai"
    assert forecasts[0].remaining == pytest.approx(5.0)
    assert forecasts[0].limit == pytest.approx(10.0)
    assert forecasts[0].alert_level == "none"

def test_forecast_provider_budget_weekly(mock_storage):
    mock_storage.cost.get_provider_spend.return_value = 0.0
    mock_storage.cost.get_spend_rate.return_value = 0.0

    service = BudgetForecastService(mock_storage)
    config = UserEconomyConfig(
        provider_budgets=[
            ProviderBudget(provider="anthropic", max_cost_usd=100.0, period="weekly")
        ]
    )

    forecasts = service.forecast(config)
    # Verify that get_provider_spend was called with days=7
    mock_storage.cost.get_provider_spend.assert_called_with("anthropic", days=7)
    assert forecasts[0].scope == "anthropic"
