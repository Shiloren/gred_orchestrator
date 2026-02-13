from __future__ import annotations

from tools.gimo_server.services.trust_engine import CircuitBreakerConfig, TrustEngine, TrustThresholds



class StubTrustStore:
    def __init__(self, storage):
        self.storage = storage
        self.saved_records = {}

    def save_dimension(self, dimension_key, data):
        self.storage.upsert_trust_record(data)
        self.saved_records[dimension_key] = data

class StubStorage:
    def __init__(self, events):
        self._events = list(events)
        self._records = {}
        self._cb_cfg = {}

    def list_trust_events(self, limit: int = 100):
        return self._events[:limit]

    def get_trust_record(self, dimension_key: str):
        return self._records.get(dimension_key)

    def upsert_trust_record(self, record):
        self._records[record["dimension_key"]] = dict(record)

    def get_circuit_breaker_config(self, dimension_key: str):
        return self._cb_cfg.get(dimension_key)


def test_trust_engine_query_dimension_auto_approve_policy():
    events = [
        {
            "dimension_key": "shell_exec|*|claude|agent_task",
            "outcome": "approved",
            "post_check_passed": True,
            "timestamp": f"2026-01-01T00:00:{i:02d}Z",
        }
        for i in range(25)
    ]
    store = StubTrustStore(StubStorage(events))
    engine = TrustEngine(store)

    record = engine.query_dimension("shell_exec|*|claude|agent_task")
    assert record["approvals"] == 25
    assert record["policy"] == "auto_approve"
    assert record["score"] >= 0.9


def test_trust_engine_dashboard_and_blocked_policy():
    events = [
        {
            "dimension_key": "file_write|*|generic|agent_task",
            "outcome": "error",
            "post_check_passed": False,
            "timestamp": f"2026-01-01T00:00:{i:02d}Z",
        }
        for i in range(6)
    ] + [
        {
            "dimension_key": "shell_exec|*|claude|agent_task",
            "outcome": "approved",
            "post_check_passed": True,
            "timestamp": "2026-01-02T00:00:00Z",
        }
    ]

    store = StubTrustStore(StubStorage(events))
    engine = TrustEngine(store, thresholds=TrustThresholds(blocked_failures=5))
    rows = engine.dashboard(limit=10)

    blocked = next(r for r in rows if r["dimension_key"].startswith("file_write"))
    assert blocked["policy"] == "blocked"
    assert blocked["failures"] >= 6


def test_trust_engine_circuit_breaker_opens_on_failure_threshold():
    dimension = "file_write|*|generic|agent_task"
    events = [
        {
            "dimension_key": dimension,
            "outcome": "error",
            "post_check_passed": False,
            "timestamp": f"2026-01-01T00:00:{i:02d}Z",
        }
        for i in range(5)
    ]
    store = StubTrustStore(StubStorage(events))
    engine = TrustEngine(
        store,
        circuit_breaker=CircuitBreakerConfig(window=5, failure_threshold=5, recovery_probes=2, cooldown_seconds=60),
    )

    record = engine.query_dimension(dimension)
    assert record["circuit_state"] == "open"
    assert record["policy"] == "blocked"


def test_trust_engine_uses_dimension_specific_circuit_breaker_config():
    dimension = "shell_exec|*|claude|agent_task"
    events = [
        {
            "dimension_key": dimension,
            "outcome": "error",
            "post_check_passed": False,
            "timestamp": f"2026-01-01T00:00:{i:02d}Z",
        }
        for i in range(2)
    ]
    storage = StubStorage(events)
    storage._cb_cfg[dimension] = {
        "dimension_key": dimension,
        "window": 3,
        "failure_threshold": 2,
        "recovery_probes": 1,
        "cooldown_seconds": 0,
    }
    store = StubTrustStore(storage)
    engine = TrustEngine(
        store,
        circuit_breaker=CircuitBreakerConfig(window=20, failure_threshold=10, recovery_probes=3, cooldown_seconds=300),
    )

    record = engine.query_dimension(dimension)
    assert record["circuit_state"] == "open"
