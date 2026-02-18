"""TrustEngine latency benchmark.

Verifies that TrustEngine operations complete within 10ms overhead budget.
Part of Paso 2.3 Quality Gates in the GIMO Master Plan.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from tools.gimo_server.services.trust_engine import TrustEngine, TrustThresholds


def _build_mock_store(events: list) -> MagicMock:
    store = MagicMock()
    store.list_trust_events = MagicMock(return_value=events)
    store.get_circuit_breaker_config = MagicMock(return_value=None)
    return store


def _make_events(n: int, *, dimension: str = "tool|git_diff|model-a|refactor") -> list:
    now = datetime.now(timezone.utc)
    return [
        {
            "timestamp": now.isoformat(),
            "dimension_key": dimension,
            "tool": "git_diff",
            "context": "/repo",
            "model": "model-a",
            "task_type": "refactor",
            "outcome": "approved" if i % 5 != 0 else "rejected",
            "actor": "operator",
            "post_check_passed": True,
            "duration_ms": 10,
            "tokens_used": 100,
            "cost_usd": 0.001,
        }
        for i in range(n)
    ]


class TestTrustEngineLatency:
    """Ensure TrustEngine overhead stays under 10ms."""

    def test_query_dimension_latency(self):
        events = _make_events(200)
        store = _build_mock_store(events)
        engine = TrustEngine(trust_store=store)

        start = time.perf_counter()
        for _ in range(100):
            engine.query_dimension("tool|git_diff|model-a|refactor")
        elapsed_ms = (time.perf_counter() - start) / 100 * 1000

        assert elapsed_ms < 10, f"query_dimension avg {elapsed_ms:.2f}ms exceeds 10ms budget"

    def test_dashboard_latency(self):
        events = _make_events(500)
        store = _build_mock_store(events)
        engine = TrustEngine(trust_store=store)

        start = time.perf_counter()
        for _ in range(20):
            engine.dashboard(limit=50)
        elapsed_ms = (time.perf_counter() - start) / 20 * 1000

        assert elapsed_ms < 10, f"dashboard avg {elapsed_ms:.2f}ms exceeds 10ms budget"

    def test_circuit_breaker_latency(self):
        events = _make_events(100)
        store = _build_mock_store(events)
        engine = TrustEngine(trust_store=store)

        record = engine.query_dimension("tool|git_diff|model-a|refactor")

        start = time.perf_counter()
        for _ in range(1000):
            engine._apply_circuit_breaker(dict(record))
        elapsed_ms = (time.perf_counter() - start) / 1000 * 1000

        assert elapsed_ms < 10, f"circuit_breaker avg {elapsed_ms:.2f}ms exceeds 10ms budget"
