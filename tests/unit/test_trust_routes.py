from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from tools.gimo_server.main import app
from tools.gimo_server.security import verify_token
from tools.gimo_server.security.auth import AuthContext


def _auth(role: str):
    def _override():
        return AuthContext(token=f"{role}-test-token-1234567890", role=role)
    return _override


@pytest.fixture(autouse=True)
def _setup_app():
    app.state.start_time = time.time()
    yield
    app.dependency_overrides.clear()


# ── Trust Query ──────────────────────────────────────────

def test_trust_query_requires_dimension_key(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    response = test_client.post("/ops/trust/query", json={})
    assert response.status_code == 400
    assert "dimension_key" in response.json()["detail"]


def test_trust_query_returns_record_for_operator(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    with patch("tools.gimo_server.routers.ops.trust_router.TrustEngine.query_dimension") as mock_query:
        mock_query.return_value = {
            "dimension_key": "shell_exec|*|claude|agent_task",
            "score": 0.93,
            "policy": "auto_approve",
        }
        response = test_client.post(
            "/ops/trust/query",
            json={"dimension_key": "shell_exec|*|claude|agent_task"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["policy"] == "auto_approve"
        assert payload["score"] == 0.93


def test_trust_dashboard_returns_items_for_operator(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    with patch("tools.gimo_server.routers.ops.trust_router.TrustEngine.dashboard") as mock_dashboard:
        mock_dashboard.return_value = [
            {"dimension_key": "a|*|m|t", "score": 0.8, "policy": "require_review"}
        ]
        response = test_client.get("/ops/trust/dashboard?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["items"][0]["dimension_key"] == "a|*|m|t"


def test_trust_query_forbidden_for_actions_role(test_client):
    app.dependency_overrides[verify_token] = _auth("actions")
    response = test_client.post(
        "/ops/trust/query",
        json={"dimension_key": "shell_exec|*|claude|agent_task"},
    )
    assert response.status_code == 403


# ── Circuit Breaker ──────────────────────────────────────

def test_get_circuit_breaker_config_returns_default_for_operator(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    with patch("tools.gimo_server.services.storage_service.StorageService.get_circuit_breaker_config") as mock_get:
        mock_get.return_value = None
        response = test_client.get("/ops/trust/circuit-breaker/shell_exec|*|claude|agent_task")
        assert response.status_code == 200
        payload = response.json()
        assert payload["dimension_key"] == "shell_exec|*|claude|agent_task"
        assert payload["window"] == 20
        assert payload["failure_threshold"] == 5


def test_set_circuit_breaker_config_requires_admin(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    response = test_client.put(
        "/ops/trust/circuit-breaker/shell_exec|*|claude|agent_task",
        json={"window": 10, "failure_threshold": 3, "recovery_probes": 2, "cooldown_seconds": 60},
    )
    assert response.status_code == 403


def test_set_circuit_breaker_config_as_admin(test_client):
    app.dependency_overrides[verify_token] = _auth("admin")
    with patch("tools.gimo_server.services.storage_service.StorageService.upsert_circuit_breaker_config") as mock_upsert:
        mock_upsert.return_value = {
            "dimension_key": "shell_exec|*|claude|agent_task",
            "window": 10, "failure_threshold": 3, "recovery_probes": 2, "cooldown_seconds": 60,
        }
        response = test_client.put(
            "/ops/trust/circuit-breaker/shell_exec|*|claude|agent_task",
            json={"window": 10, "failure_threshold": 3, "recovery_probes": 2, "cooldown_seconds": 60},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["failure_threshold"] == 3
        assert payload["cooldown_seconds"] == 60


# ── Tool Registry ────────────────────────────────────────

def test_tool_registry_list_for_operator(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    with patch("tools.gimo_server.routers.ops.config_router.ToolRegistryService.list_tools") as mock_list:
        mock_list.return_value = []
        response = test_client.get("/ops/tool-registry")
        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 0
        assert payload["items"] == []


def test_tool_registry_upsert_requires_admin(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    response = test_client.put(
        "/ops/tool-registry/file_write",
        json={
            "name": "file_write", "description": "writes files",
            "inputs": {}, "outputs": {}, "risk": "write",
            "estimated_cost": 0.0, "requires_hitl": False,
            "allowed_roles": ["operator", "admin"],
        },
    )
    assert response.status_code == 403


def test_tool_registry_upsert_and_delete_as_admin(test_client):
    app.dependency_overrides[verify_token] = _auth("admin")
    with patch("tools.gimo_server.routers.ops.config_router.ToolRegistryService.upsert_tool") as mock_upsert:
        mock_upsert.return_value = type("Entry", (), {
            "model_dump": lambda self: {
                "name": "file_write", "description": "writes files",
                "inputs": {}, "outputs": {}, "risk": "write",
                "estimated_cost": 0.0, "requires_hitl": False,
                "allowed_roles": ["operator", "admin"],
            }
        })()
        response = test_client.put(
            "/ops/tool-registry/file_write",
            json={
                "name": "ignored", "description": "writes files",
                "inputs": {}, "outputs": {}, "risk": "write",
                "estimated_cost": 0.0, "requires_hitl": False,
                "allowed_roles": ["operator", "admin"],
            },
        )
        assert response.status_code == 200
        assert response.json()["name"] == "file_write"

    with patch("tools.gimo_server.routers.ops.config_router.ToolRegistryService.delete_tool") as mock_delete:
        mock_delete.return_value = True
        response = test_client.delete("/ops/tool-registry/file_write")
        assert response.status_code == 200
        assert response.json()["deleted"] == "file_write"


# ── Policy ───────────────────────────────────────────────

def test_get_policy_config_for_operator(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    with patch("tools.gimo_server.routers.ops.config_router.PolicyService.get_config") as mock_get:
        mock_get.return_value = {"rules": []}
        response = test_client.get("/ops/policy")
        assert response.status_code == 200
        assert "rules" in response.json()


def test_set_policy_config_requires_admin(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    response = test_client.put("/ops/policy", json={"rules": []})
    assert response.status_code == 403


def test_set_policy_config_as_admin(test_client):
    app.dependency_overrides[verify_token] = _auth("admin")
    with patch("tools.gimo_server.routers.ops.config_router.PolicyService.set_config") as mock_set:
        mock_set.return_value = {
            "rules": [{
                "match": {"tool": "file_delete", "context": "*"},
                "action": "require_review",
                "override": "never_auto_approve",
                "min_trust_score": None,
            }]
        }
        response = test_client.put(
            "/ops/policy",
            json={"rules": [{"match": {"tool": "file_delete", "context": "*"}, "action": "require_review", "override": "never_auto_approve"}]},
        )
        assert response.status_code == 200
        payload = response.json()
        assert len(payload["rules"]) == 1
        assert payload["rules"][0]["action"] == "require_review"


def test_policy_decide_requires_tool(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    response = test_client.post("/ops/policy/decide", json={"context": "src/**", "trust_score": 0.8})
    assert response.status_code == 400
    assert "tool" in response.json()["detail"]


def test_policy_decide_returns_decision_for_operator(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    with patch("tools.gimo_server.routers.ops.config_router.PolicyService.decide") as mock_decide:
        mock_decide.return_value = {
            "decision": "require_review", "rule_index": 0,
            "matched": {"tool": "file_delete", "context": "*"},
            "override": "never_auto_approve", "min_trust_score": 0.95,
        }
        response = test_client.post(
            "/ops/policy/decide",
            json={"tool": "file_delete", "context": "src/payments/a.py", "trust_score": 0.93},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["decision"] == "require_review"
        assert payload["rule_index"] == 0


# ── Workflow Execution ───────────────────────────────────

def test_execute_workflow_for_operator(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    response = test_client.post(
        "/ops/workflows/execute",
        json={
            "workflow": {
                "id": "wf_api_exec",
                "nodes": [{"id": "A", "type": "transform", "config": {"ok": True}}],
                "edges": [], "state_schema": {},
            },
            "initial_state": {"seed": 1},
            "persist_checkpoints": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_id"] == "wf_api_exec"
    assert payload["checkpoint_count"] == 1
    assert "state" in payload


def test_execute_workflow_forbidden_for_actions(test_client):
    app.dependency_overrides[verify_token] = _auth("actions")
    response = test_client.post(
        "/ops/workflows/execute",
        json={
            "workflow": {
                "id": "wf_api_exec_forbidden",
                "nodes": [{"id": "A", "type": "transform", "config": {}}],
                "edges": [], "state_schema": {},
            }
        },
    )
    assert response.status_code == 403


def test_workflow_checkpoints_for_operator(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    with patch("tools.gimo_server.routers.ops.run_router.StorageService.list_checkpoints") as mock_list:
        mock_list.return_value = [{"workflow_id": "wf1", "node_id": "A", "state": {}, "output": {}, "status": "completed"}]
        response = test_client.get("/ops/workflows/wf1/checkpoints")
        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["items"][0]["node_id"] == "A"


def test_resume_workflow_not_found_when_no_runtime_or_persisted_data(test_client):
    app.dependency_overrides[verify_token] = _auth("operator")
    with patch("tools.gimo_server.routers.ops.run_router.StorageService.get_workflow") as mock_get:
        mock_get.return_value = None
        response = test_client.post("/ops/workflows/wf_missing/resume")
        assert response.status_code == 404
