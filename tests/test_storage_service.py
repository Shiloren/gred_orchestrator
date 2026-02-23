from __future__ import annotations

from tools.gimo_server.ops_models import EvalGateConfig, EvalRunReport, TrustEvent
from tools.gimo_server.services.storage_service import StorageService

class MockGics:
    def __init__(self):
        self.data = {}
    
    def put(self, key, value):
        self.data[key] = value
        
    def get(self, key):
        if key in self.data:
            return {"key": key, "fields": self.data[key], "timestamp": "2026-01-01T00:00:00Z"}
        return None
        
    def scan(self, prefix="", include_fields=False):
        results = []
        for k, v in self.data.items():
            if k.startswith(prefix):
                if include_fields:
                    results.append({"key": k, "fields": v, "timestamp": "2026-01-01T00:00:00Z"})
                else:
                    results.append({"key": k, "timestamp": "2026-01-01T00:00:00Z"})
        return results




def test_storage_service_workflow_and_checkpoints_roundtrip(tmp_path):

    storage = StorageService(gics=MockGics())

    workflow_payload = {
        "id": "wf1",
        "nodes": [{"id": "A", "type": "transform"}],
        "edges": [],
        "state_schema": {},
    }
    storage.save_workflow("wf1", workflow_payload)

    stored_workflow = storage.get_workflow("wf1")
    assert stored_workflow is not None
    assert stored_workflow["id"] == "wf1"
    assert stored_workflow["data"]["nodes"][0]["id"] == "A"

    storage.save_checkpoint(
        workflow_id="wf1",
        node_id="A",
        state={"value": 1},
        output={"status": "ok"},
        status="completed",
    )
    storage.save_checkpoint(
        workflow_id="wf1",
        node_id="B",
        state={"value": 2},
        output=None,
        status="failed",
    )

    checkpoints = storage.list_checkpoints("wf1")
    assert len(checkpoints) == 2
    assert checkpoints[0]["node_id"] == "A"
    assert checkpoints[0]["state"]["value"] == 1
    assert checkpoints[0]["output"]["status"] == "ok"
    assert checkpoints[1]["node_id"] == "B"
    assert checkpoints[1]["output"] is None
    assert checkpoints[1]["status"] == "failed"

    storage.close()


def test_storage_service_trust_events_roundtrip(tmp_path):

    storage = StorageService(gics=MockGics())

    event = TrustEvent(
        dimension_key="shell_exec|*|claude-code|agent_task",
        tool="shell_exec",
        context="*",
        model="claude-code",
        task_type="agent_task",
        outcome="approved",
        actor="agent:claude_code",
        post_check_passed=True,
        duration_ms=120,
        tokens_used=55,
        cost_usd=0.01,
    )

    storage.save_trust_event(event)
    storage.save_trust_events(
        [
            {
                "dimension_key": "file_write|*|generic-cli|agent_task",
                "tool": "file_write",
                "context": "src/a.py",
                "model": "generic-cli",
                "task_type": "agent_task",
                "outcome": "rejected",
                "actor": "agent:generic_cli",
                "post_check_passed": False,
                "duration_ms": 200,
                "tokens_used": 0,
                "cost_usd": 0.0,
            }
        ]
    )

    events = storage.list_trust_events(limit=10)
    assert len(events) == 2
    # Newest first
    assert events[0]["tool"] == "file_write"
    assert events[0]["outcome"] == "rejected"
    assert events[0]["post_check_passed"] is False
    assert events[1]["tool"] == "shell_exec"
    assert events[1]["tokens_used"] == 55

    storage.close()


def test_storage_service_list_trust_records(tmp_path):

    storage = StorageService(gics=MockGics())

    storage.upsert_trust_record(
        {
            "dimension_key": "shell_exec|*|claude|agent_task",
            "approvals": 12,
            "rejections": 1,
            "failures": 0,
            "auto_approvals": 4,
            "streak": 5,
            "score": 0.91,
            "policy": "auto_approve",
            "circuit_state": "closed",
            "circuit_opened_at": None,
            "last_updated": "2026-01-01T00:00:00Z",
        }
    )

    rows = storage.list_trust_records(limit=10)
    assert len(rows) == 1
    assert rows[0]["dimension_key"] == "shell_exec|*|claude|agent_task"
    assert rows[0]["approvals"] == 12
    assert rows[0]["policy"] == "auto_approve"

    storage.close()


def test_storage_service_eval_reports_roundtrip(tmp_path):

    storage = StorageService(gics=MockGics())

    report = EvalRunReport(
        workflow_id="wf_eval_hist",
        total_cases=2,
        passed_cases=1,
        failed_cases=1,
        pass_rate=0.5,
        avg_score=0.75,
        gate_passed=False,
        gate=EvalGateConfig(min_pass_rate=0.8, min_avg_score=0.8),
        results=[],
    )

    run_id = storage.save_eval_report(report)
    assert run_id >= 1

    rows = storage.list_eval_reports(workflow_id="wf_eval_hist", limit=10)
    assert len(rows) == 1
    assert rows[0]["run_id"] == run_id
    assert rows[0]["workflow_id"] == "wf_eval_hist"
    assert rows[0]["gate_passed"] is False

    detail = storage.get_eval_report(run_id)
    assert detail is not None
    assert detail["run_id"] == run_id
    assert detail["workflow_id"] == "wf_eval_hist"
    assert detail["report"]["pass_rate"] == 0.5

    storage.close()


def test_storage_service_eval_datasets_roundtrip(tmp_path):

    storage = StorageService(gics=MockGics())

    dataset = {
        "workflow_id": "wf_eval_ds",
        "cases": [
            {
                "case_id": "c1",
                "input_state": {"x": 1},
                "expected_state": {"status": "ok"},
                "threshold": 1.0,
            }
        ],
    }

    dataset_id = storage.save_eval_dataset(dataset, version_tag="v1")
    assert dataset_id >= 1

    rows = storage.list_eval_datasets(workflow_id="wf_eval_ds", limit=10)
    assert len(rows) == 1
    assert rows[0]["dataset_id"] == dataset_id
    assert rows[0]["workflow_id"] == "wf_eval_ds"
    assert rows[0]["version_tag"] == "v1"

    detail = storage.get_eval_dataset(dataset_id)
    assert detail is not None
    assert detail["dataset_id"] == dataset_id
    assert detail["workflow_id"] == "wf_eval_ds"
    assert detail["dataset"]["cases"][0]["case_id"] == "c1"

    storage.close()


def test_storage_service_tool_call_idempotency_key_roundtrip(tmp_path):

    storage = StorageService(gics=MockGics())

    first = storage.register_tool_call_idempotency_key(
        idempotency_key="idem-123",
        tool="file_write",
        context="src/a.py",
    )
    second = storage.register_tool_call_idempotency_key(
        idempotency_key="idem-123",
        tool="file_write",
        context="src/a.py",
    )

    assert first is True
    assert second is False

    storage.close()
