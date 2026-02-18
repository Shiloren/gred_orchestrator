import asyncio
import uuid
import sys
import os

sys.path.append(os.getcwd())

from tools.gimo_server.services.observability_service import ObservabilityService

async def main():
    print("--- Inciando prueba de Observabilidad ---")
    trace_id = uuid.uuid4().hex
    wf_id = "test_workflow_otel"
    
    print(f"Workflow ID: {wf_id}, Trace ID: {trace_id}")
    
    ObservabilityService.record_workflow_start(wf_id, trace_id)
    
    await asyncio.sleep(0.5)
    
    ObservabilityService.record_node_span(
        workflow_id=wf_id,
        trace_id=trace_id,
        step_id="step_1",
        node_id="llm_node",
        node_type="llm_call",
        status="completed",
        duration_ms=450,
        tokens_used=120,
        cost_usd=0.0024
    )
    
    await asyncio.sleep(0.2)
    
    ObservabilityService.record_node_span(
        workflow_id=wf_id,
        trace_id=trace_id,
        step_id="step_2",
        node_id="tool_node",
        node_type="tool_call",
        status="completed",
        duration_ms=150,
        tokens_used=0,
        cost_usd=0.0
    )
    
    print(f"\nActive spans before end: {len(ObservabilityService._active_spans)}")
    ObservabilityService.record_workflow_end(wf_id, trace_id, status="completed")
    print(f"Active spans after end: {len(ObservabilityService._active_spans)}")

    print("\n--- Métricas Finales (UI Compatibility) ---")
    print(ObservabilityService.get_metrics())
    
    print("\n--- Traces (UI Compatibility) ---")
    for trace in ObservabilityService.list_traces():
        print(f"[{trace['kind']}] {trace.get('node_id', '')} - {trace['status'] if 'status' in trace else ''}")

if __name__ == "__main__":
    asyncio.run(main())
