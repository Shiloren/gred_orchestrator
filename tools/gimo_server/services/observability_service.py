from __future__ import annotations

import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List


class ObservabilityService:
    """In-memory observability store (MVP).

    Provides lightweight traces and aggregate metrics without external dependencies.
    """

    _lock = threading.Lock()
    _spans: Deque[Dict[str, Any]] = deque(maxlen=5000)
    _metrics: Dict[str, Any] = {
        "workflows_total": 0,
        "nodes_total": 0,
        "nodes_failed": 0,
        "tokens_total": 0,
        "cost_total_usd": 0.0,
    }

    @classmethod
    def record_workflow_start(cls, workflow_id: str, trace_id: str) -> None:
        with cls._lock:
            cls._metrics["workflows_total"] = int(cls._metrics.get("workflows_total", 0)) + 1
            cls._spans.append(
                {
                    "kind": "workflow",
                    "event": "start",
                    "workflow_id": workflow_id,
                    "trace_id": trace_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    @classmethod
    def record_node_span(
        cls,
        *,
        workflow_id: str,
        trace_id: str,
        step_id: str,
        node_id: str,
        node_type: str,
        status: str,
        duration_ms: int,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        with cls._lock:
            cls._metrics["nodes_total"] = int(cls._metrics.get("nodes_total", 0)) + 1
            if status == "failed":
                cls._metrics["nodes_failed"] = int(cls._metrics.get("nodes_failed", 0)) + 1
            cls._metrics["tokens_total"] = int(cls._metrics.get("tokens_total", 0)) + int(tokens_used or 0)
            cls._metrics["cost_total_usd"] = float(cls._metrics.get("cost_total_usd", 0.0)) + float(cost_usd or 0.0)

            cls._spans.append(
                {
                    "kind": "node",
                    "workflow_id": workflow_id,
                    "trace_id": trace_id,
                    "step_id": step_id,
                    "node_id": node_id,
                    "node_type": node_type,
                    "status": status,
                    "duration_ms": int(duration_ms),
                    "tokens_used": int(tokens_used or 0),
                    "cost_usd": float(cost_usd or 0.0),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        with cls._lock:
            return dict(cls._metrics)

    @classmethod
    def list_traces(cls, *, limit: int = 100) -> List[Dict[str, Any]]:
        with cls._lock:
            items = list(cls._spans)
        return items[-max(1, int(limit)) :]

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._spans.clear()
            cls._metrics = {
                "workflows_total": 0,
                "nodes_total": 0,
                "nodes_failed": 0,
                "tokens_total": 0,
                "cost_total_usd": 0.0,
            }
