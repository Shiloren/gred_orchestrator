from __future__ import annotations

from tools.gimo_server.services.observability_service import ObservabilityService


def test_observability_service_records_metrics_and_traces():
    ObservabilityService.reset()

    ObservabilityService.record_workflow_start("wf1", "trace-1")
    ObservabilityService.record_node_span(
        workflow_id="wf1",
        trace_id="trace-1",
        step_id="step_1",
        node_id="A",
        node_type="llm_call",
        status="completed",
        duration_ms=12,
        tokens_used=15,
        cost_usd=0.02,
    )
    ObservabilityService.record_node_span(
        workflow_id="wf1",
        trace_id="trace-1",
        step_id="step_2",
        node_id="B",
        node_type="tool_call",
        status="failed",
        duration_ms=8,
        tokens_used=0,
        cost_usd=0.0,
    )

    metrics = ObservabilityService.get_metrics()
    assert metrics["workflows_total"] == 1
    assert metrics["nodes_total"] == 2
    assert metrics["nodes_failed"] == 1
    assert metrics["tokens_total"] == 15
    assert metrics["cost_total_usd"] == 0.02

    traces = ObservabilityService.list_traces(limit=10)
    assert len(traces) == 3
    assert any(item["kind"] == "workflow" for item in traces)
    assert any(item["kind"] == "node" for item in traces)
