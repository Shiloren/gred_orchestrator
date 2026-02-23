import pytest
from datetime import datetime, timezone, timedelta

from tools.gimo_server.ops_models import CostEvent
from tools.gimo_server.services.storage.cost_storage import CostStorage

class MockGics:
    def __init__(self):
        self.data = {}
    
    def put(self, key, value):
        self.data[key] = value
        
    def get(self, key):
        if key in self.data:
            return {"key": key, "fields": self.data[key], "timestamp": 1234567890}
        return None
        
    def scan(self, prefix="", include_fields=False):
        results = []
        for k, v in self.data.items():
            if k.startswith(prefix):
                if include_fields:
                    results.append({"key": k, "fields": v, "timestamp": 1234567890})
                else:
                    results.append({"key": k, "timestamp": 1234567890})
        return results

@pytest.fixture
def mock_gics():
    return MockGics()

@pytest.fixture
def cost_storage(mock_gics):
    storage = CostStorage(conn=None, gics=mock_gics)
    storage.ensure_tables()
    return storage

def _make_event(id, model="gpt-4", provider="openai", task_type="generation",
                cost_usd=0.1, total_tokens=1000, quality_score=0.0,
                cascade_level=0, cache_hit=False, timestamp=None,
                input_tokens=500, output_tokens=500, duration_ms=200):
    return CostEvent(
        id=id, workflow_id="w1", node_id="n1",
        model=model, provider=provider, task_type=task_type,
        input_tokens=input_tokens, output_tokens=output_tokens,
        total_tokens=total_tokens, cost_usd=cost_usd,
        quality_score=quality_score, cascade_level=cascade_level,
        cache_hit=cache_hit, duration_ms=duration_ms,
        timestamp=timestamp or datetime.now(timezone.utc),
    )

# --- Basic Save & GICS Sync ---

def test_save_cost_event(cost_storage, mock_gics):
    event = _make_event("evt_1", cost_usd=0.015)
    cost_storage.save_cost_event(event)

    saved_items = [v for k, v in mock_gics.data.items() if k.startswith("ce:w1:n1:")]
    assert len(saved_items) == 1
    assert saved_items[0]["id"] == "evt_1"
    assert saved_items[0]["cost_usd"] == 0.015

# --- Provider Spend & Time Filtering ---

def test_provider_spend(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", provider="openai", cost_usd=0.10, timestamp=now))
    cost_storage.save_cost_event(_make_event("2", provider="openai", cost_usd=0.20, timestamp=now))
    cost_storage.save_cost_event(_make_event("3", provider="anthropic", cost_usd=0.05, timestamp=now))
    cost_storage.save_cost_event(_make_event("4", provider="openai", cost_usd=0.10, timestamp=now - timedelta(days=40)))

    assert cost_storage.get_provider_spend("openai", days=30) == pytest.approx(0.3)
    assert cost_storage.get_provider_spend("anthropic", days=30) == pytest.approx(0.05)
    assert cost_storage.get_provider_spend("openai", days=60) == pytest.approx(0.4)
    assert cost_storage.get_provider_spend("nonexistent", days=30) == pytest.approx(0.0)

def test_total_spend(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", cost_usd=0.10, timestamp=now))
    cost_storage.save_cost_event(_make_event("2", cost_usd=0.25, timestamp=now))
    cost_storage.save_cost_event(_make_event("3", cost_usd=0.05, timestamp=now - timedelta(days=40)))

    assert cost_storage.get_total_spend(days=30) == pytest.approx(0.35)
    assert cost_storage.get_total_spend(days=60) == pytest.approx(0.40)

# --- Aggregations ---

def test_aggregate_by_model(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", model="gpt-4", cost_usd=0.10, total_tokens=1000, timestamp=now))
    cost_storage.save_cost_event(_make_event("2", model="gpt-4", cost_usd=0.20, total_tokens=2000, timestamp=now))
    cost_storage.save_cost_event(_make_event("3", model="claude-3", cost_usd=0.05, total_tokens=500, timestamp=now))

    stats = cost_storage.aggregate_by_model(days=30)
    assert len(stats) == 2
    gpt4 = next(s for s in stats if s["model"] == "gpt-4")
    assert gpt4["cost"] == pytest.approx(0.3)
    assert gpt4["count"] == 2

    claude = next(s for s in stats if s["model"] == "claude-3")
    assert claude["cost"] == pytest.approx(0.05)

def test_aggregate_by_task_type(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", task_type="coding", cost_usd=0.10, quality_score=85, timestamp=now))
    cost_storage.save_cost_event(_make_event("2", task_type="coding", cost_usd=0.20, quality_score=90, timestamp=now))
    cost_storage.save_cost_event(_make_event("3", task_type="classification", cost_usd=0.01, quality_score=95, timestamp=now))

    stats = cost_storage.aggregate_by_task_type(days=30)
    assert len(stats) == 2
    coding = next(s for s in stats if s["task_type"] == "coding")
    assert coding["cost"] == pytest.approx(0.3)
    assert coding["quality"] == pytest.approx(87.5)
    assert coding["count"] == 2

def test_aggregate_by_provider(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", provider="openai", cost_usd=0.10, total_tokens=1000, timestamp=now))
    cost_storage.save_cost_event(_make_event("2", provider="openai", cost_usd=0.05, total_tokens=500, timestamp=now))
    cost_storage.save_cost_event(_make_event("3", provider="anthropic", cost_usd=0.20, total_tokens=2000, timestamp=now))

    stats = cost_storage.aggregate_by_provider(days=30)
    assert len(stats) == 2
    anthropic = next(s for s in stats if s["provider"] == "anthropic")
    assert anthropic["cost"] == pytest.approx(0.20)
    assert anthropic["total_tokens"] == 2000

# --- Daily Costs Timeseries ---

def test_daily_costs(cost_storage):
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    cost_storage.save_cost_event(_make_event("1", cost_usd=0.10, total_tokens=1000, timestamp=now))
    cost_storage.save_cost_event(_make_event("2", cost_usd=0.05, total_tokens=500, timestamp=now))
    cost_storage.save_cost_event(_make_event("3", cost_usd=0.20, total_tokens=2000, timestamp=yesterday))

    daily = cost_storage.get_daily_costs(days=30)
    assert len(daily) == 2
    assert daily[0]["cost"] == pytest.approx(0.20)  # yesterday first (ASC)
    assert daily[1]["cost"] == pytest.approx(0.15)

# --- ROI Leaderboard ---

def test_roi_leaderboard(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", model="haiku", task_type="classification", cost_usd=0.001, quality_score=90, timestamp=now))
    cost_storage.save_cost_event(_make_event("2", model="haiku", task_type="classification", cost_usd=0.002, quality_score=88, timestamp=now))
    cost_storage.save_cost_event(_make_event("3", model="opus", task_type="classification", cost_usd=0.15, quality_score=95, timestamp=now))

    leaderboard = cost_storage.get_roi_leaderboard(days=30)
    assert len(leaderboard) == 2
    assert leaderboard[0]["model"] == "haiku"
    assert leaderboard[0]["roi_score"] > leaderboard[1]["roi_score"]
    assert leaderboard[0]["sample_count"] == 2
    assert leaderboard[0]["avg_quality"] == pytest.approx(89.0)

def test_roi_leaderboard_excludes_zero_quality(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", model="gpt-4", quality_score=0, cost_usd=0.1, timestamp=now))
    cost_storage.save_cost_event(_make_event("2", model="haiku", quality_score=80, cost_usd=0.01, timestamp=now))

    leaderboard = cost_storage.get_roi_leaderboard(days=30)
    assert len(leaderboard) == 1
    assert leaderboard[0]["model"] == "haiku"

# --- Cascade Stats ---

def test_cascade_stats(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", task_type="coding", cascade_level=0, cost_usd=0.01, timestamp=now))
    cost_storage.save_cost_event(_make_event("2", task_type="coding", cascade_level=1, cost_usd=0.05, timestamp=now))
    cost_storage.save_cost_event(_make_event("3", task_type="coding", cascade_level=2, cost_usd=0.15, timestamp=now))
    cost_storage.save_cost_event(_make_event("4", task_type="qa", cascade_level=0, cost_usd=0.02, timestamp=now))

    stats = cost_storage.get_cascade_stats(days=30)
    assert len(stats) == 2
    coding = next(s for s in stats if s["task_type"] == "coding")
    assert coding["total_calls"] == 3
    assert coding["cascaded_calls"] == 2
    assert coding["avg_cascade_depth"] == pytest.approx(1.0)
    assert coding["total_spent"] == pytest.approx(0.21)

# --- Cache Stats ---

def test_cache_stats(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", cache_hit=False, cost_usd=0.10, timestamp=now))
    cost_storage.save_cost_event(_make_event("2", cache_hit=False, cost_usd=0.20, timestamp=now))
    cost_storage.save_cost_event(_make_event("3", cache_hit=True, cost_usd=0.00, timestamp=now))

    stats = cost_storage.get_cache_stats(days=30)
    assert stats["total_calls"] == 3
    assert stats["cache_hits"] == 1
    assert stats["hit_rate"] == pytest.approx(1 / 3, abs=0.01)
    assert stats["estimated_savings_usd"] > 0

def test_cache_stats_empty(cost_storage):
    stats = cost_storage.get_cache_stats(days=30)
    assert stats["total_calls"] == 0
    assert stats["hit_rate"] == 0.0

# --- Spend Rate ---

def test_spend_rate(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", cost_usd=0.24, timestamp=now))
    cost_storage.save_cost_event(_make_event("2", cost_usd=0.24, timestamp=now))

    rate = cost_storage.get_spend_rate(hours=24)
    assert rate == pytest.approx(0.48 / 24)

def test_spend_rate_empty(cost_storage):
    rate = cost_storage.get_spend_rate(hours=24)
    assert rate == pytest.approx(0.0)

# --- Budget Alerts ---

def test_budget_alerts_none_triggered(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", cost_usd=0.05, timestamp=now))

    alerts = cost_storage.check_budget_alerts(global_budget=100.0, thresholds=[50, 25, 10])
    assert len(alerts) == 0

def test_budget_alerts_triggered(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", cost_usd=80.0, timestamp=now))

    alerts = cost_storage.check_budget_alerts(global_budget=100.0, thresholds=[50, 25, 10])
    assert len(alerts) >= 1
    assert alerts[0]["percentage"] == pytest.approx(80.0)

def test_budget_alerts_no_budget(cost_storage):
    alerts = cost_storage.check_budget_alerts(global_budget=0, thresholds=[50, 25, 10])
    assert len(alerts) == 0

# --- Total Savings ---

def test_total_savings(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", cache_hit=True, cost_usd=0.0, timestamp=now))
    cost_storage.save_cost_event(_make_event("2", cache_hit=False, cost_usd=0.10, timestamp=now))
    cost_storage.save_cost_event(_make_event("3", cascade_level=0, quality_score=85, cost_usd=0.005, timestamp=now))

    savings = cost_storage.get_total_savings(days=30)
    assert savings >= 0.0

def test_total_savings_empty(cost_storage):
    savings = cost_storage.get_total_savings(days=30)
    assert savings == pytest.approx(0.0)

# --- Avg Cost by Task Type ---

def test_avg_cost_by_task_type(cost_storage):
    now = datetime.now(timezone.utc)
    cost_storage.save_cost_event(_make_event("1", task_type="coding", model="sonnet", cost_usd=0.10, timestamp=now))
    cost_storage.save_cost_event(_make_event("2", task_type="coding", model="sonnet", cost_usd=0.20, timestamp=now))
    cost_storage.save_cost_event(_make_event("3", task_type="coding", model="haiku", cost_usd=0.01, timestamp=now))

    result = cost_storage.get_avg_cost_by_task_type("coding")
    assert result["sample_count"] == 3
    assert result["avg_cost"] == pytest.approx((0.10 + 0.20 + 0.01) / 3, abs=0.001)

    result = cost_storage.get_avg_cost_by_task_type("coding", model="sonnet")
    assert result["sample_count"] == 2
    assert result["avg_cost"] == pytest.approx(0.15)

def test_avg_cost_by_task_type_no_data(cost_storage):
    result = cost_storage.get_avg_cost_by_task_type("nonexistent")
    assert result["sample_count"] == 0
    assert result["avg_cost"] == pytest.approx(0.0)
