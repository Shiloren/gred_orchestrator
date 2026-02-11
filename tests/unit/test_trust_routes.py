from __future__ import annotations

import time
from unittest.mock import patch

from fastapi.testclient import TestClient

from tools.gimo_server.main import app
from tools.gimo_server.security import verify_token
from tools.gimo_server.security.auth import AuthContext


def _auth(role: str):
    def _override():
        return AuthContext(token=f"{role}-test-token-1234567890", role=role)

    return _override


def test_trust_query_requires_dimension_key():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post("/ops/trust/query", json={})
            assert response.status_code == 400
            assert "dimension_key" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_trust_query_returns_record_for_operator():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with patch("tools.gimo_server.ops_routes.TrustEngine.query_dimension") as mock_query:
            mock_query.return_value = {
                "dimension_key": "shell_exec|*|claude|agent_task",
                "score": 0.93,
                "policy": "auto_approve",
            }
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/ops/trust/query",
                    json={"dimension_key": "shell_exec|*|claude|agent_task"},
                )
                assert response.status_code == 200
                payload = response.json()
                assert payload["policy"] == "auto_approve"
                assert payload["score"] == 0.93
    finally:
        app.dependency_overrides.clear()


def test_trust_dashboard_returns_items_for_operator():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with patch("tools.gimo_server.ops_routes.TrustEngine.dashboard") as mock_dashboard:
            mock_dashboard.return_value = [
                {"dimension_key": "a|*|m|t", "score": 0.8, "policy": "require_review"}
            ]
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/ops/trust/dashboard?limit=10")
                assert response.status_code == 200
                data = response.json()
                assert data["count"] == 1
                assert data["items"][0]["dimension_key"] == "a|*|m|t"
    finally:
        app.dependency_overrides.clear()


def test_trust_query_forbidden_for_actions_role():
    app.dependency_overrides[verify_token] = _auth("actions")
    app.state.start_time = time.time()
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/ops/trust/query",
                json={"dimension_key": "shell_exec|*|claude|agent_task"},
            )
            assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_get_circuit_breaker_config_returns_default_for_operator():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with patch("tools.gimo_server.services.storage_service.StorageService.get_circuit_breaker_config") as mock_get:
            mock_get.return_value = None
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/ops/trust/circuit-breaker/shell_exec|*|claude|agent_task")
                assert response.status_code == 200
                payload = response.json()
                assert payload["dimension_key"] == "shell_exec|*|claude|agent_task"
                assert payload["window"] == 20
                assert payload["failure_threshold"] == 5
    finally:
        app.dependency_overrides.clear()


def test_set_circuit_breaker_config_requires_admin():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.put(
                "/ops/trust/circuit-breaker/shell_exec|*|claude|agent_task",
                json={
                    "window": 10,
                    "failure_threshold": 3,
                    "recovery_probes": 2,
                    "cooldown_seconds": 60,
                },
            )
            assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_set_circuit_breaker_config_as_admin():
    app.dependency_overrides[verify_token] = _auth("admin")
    app.state.start_time = time.time()
    try:
        with patch(
            "tools.gimo_server.services.storage_service.StorageService.upsert_circuit_breaker_config"
        ) as mock_upsert:
            mock_upsert.return_value = {
                "dimension_key": "shell_exec|*|claude|agent_task",
                "window": 10,
                "failure_threshold": 3,
                "recovery_probes": 2,
                "cooldown_seconds": 60,
            }
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.put(
                    "/ops/trust/circuit-breaker/shell_exec|*|claude|agent_task",
                    json={
                        "window": 10,
                        "failure_threshold": 3,
                        "recovery_probes": 2,
                        "cooldown_seconds": 60,
                    },
                )
                assert response.status_code == 200
                payload = response.json()
                assert payload["failure_threshold"] == 3
                assert payload["cooldown_seconds"] == 60
    finally:
        app.dependency_overrides.clear()


def test_tool_registry_list_for_operator():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with patch("tools.gimo_server.ops_routes.ToolRegistryService.list_tools") as mock_list:
            mock_list.return_value = []
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/ops/tool-registry")
                assert response.status_code == 200
                payload = response.json()
                assert payload["count"] == 0
                assert payload["items"] == []
    finally:
        app.dependency_overrides.clear()


def test_tool_registry_upsert_requires_admin():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.put(
                "/ops/tool-registry/file_write",
                json={
                    "name": "file_write",
                    "description": "writes files",
                    "inputs": {},
                    "outputs": {},
                    "risk": "write",
                    "estimated_cost": 0.0,
                    "requires_hitl": False,
                    "allowed_roles": ["operator", "admin"],
                },
            )
            assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_tool_registry_upsert_and_delete_as_admin():
    app.dependency_overrides[verify_token] = _auth("admin")
    app.state.start_time = time.time()
    try:
        with patch("tools.gimo_server.ops_routes.ToolRegistryService.upsert_tool") as mock_upsert:
            mock_upsert.return_value = type(
                "Entry",
                (),
                {
                    "model_dump": lambda self: {
                        "name": "file_write",
                        "description": "writes files",
                        "inputs": {},
                        "outputs": {},
                        "risk": "write",
                        "estimated_cost": 0.0,
                        "requires_hitl": False,
                        "allowed_roles": ["operator", "admin"],
                    }
                },
            )()
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.put(
                    "/ops/tool-registry/file_write",
                    json={
                        "name": "ignored",
                        "description": "writes files",
                        "inputs": {},
                        "outputs": {},
                        "risk": "write",
                        "estimated_cost": 0.0,
                        "requires_hitl": False,
                        "allowed_roles": ["operator", "admin"],
                    },
                )
                assert response.status_code == 200
                payload = response.json()
                assert payload["name"] == "file_write"

        with patch("tools.gimo_server.ops_routes.ToolRegistryService.delete_tool") as mock_delete:
            mock_delete.return_value = True
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.delete("/ops/tool-registry/file_write")
                assert response.status_code == 200
                payload = response.json()
                assert payload["deleted"] == "file_write"
    finally:
        app.dependency_overrides.clear()


def test_get_policy_config_for_operator():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with patch("tools.gimo_server.ops_routes.PolicyService.get_config") as mock_get:
            mock_get.return_value = {"rules": []}
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/ops/policy")
                assert response.status_code == 200
                payload = response.json()
                assert "rules" in payload
    finally:
        app.dependency_overrides.clear()


def test_set_policy_config_requires_admin():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.put(
                "/ops/policy",
                json={"rules": []},
            )
            assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_set_policy_config_as_admin():
    app.dependency_overrides[verify_token] = _auth("admin")
    app.state.start_time = time.time()
    try:
        with patch("tools.gimo_server.ops_routes.PolicyService.set_config") as mock_set:
            mock_set.return_value = {
                "rules": [
                    {
                        "match": {"tool": "file_delete", "context": "*"},
                        "action": "require_review",
                        "override": "never_auto_approve",
                        "min_trust_score": None,
                    }
                ]
            }
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.put(
                    "/ops/policy",
                    json={
                        "rules": [
                            {
                                "match": {"tool": "file_delete", "context": "*"},
                                "action": "require_review",
                                "override": "never_auto_approve",
                            }
                        ]
                    },
                )
                assert response.status_code == 200
                payload = response.json()
                assert len(payload["rules"]) == 1
                assert payload["rules"][0]["action"] == "require_review"
    finally:
        app.dependency_overrides.clear()


def test_policy_decide_requires_tool():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/ops/policy/decide",
                json={"context": "src/**", "trust_score": 0.8},
            )
            assert response.status_code == 400
            assert "tool" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_policy_decide_returns_decision_for_operator():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with patch("tools.gimo_server.ops_routes.PolicyService.decide") as mock_decide:
            mock_decide.return_value = {
                "decision": "require_review",
                "rule_index": 0,
                "matched": {"tool": "file_delete", "context": "*"},
                "override": "never_auto_approve",
                "min_trust_score": 0.95,
            }
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/ops/policy/decide",
                    json={"tool": "file_delete", "context": "src/payments/a.py", "trust_score": 0.93},
                )
                assert response.status_code == 200
                payload = response.json()
                assert payload["decision"] == "require_review"
                assert payload["rule_index"] == 0
    finally:
        app.dependency_overrides.clear()


def test_execute_workflow_for_operator():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/ops/workflows/execute",
                json={
                    "workflow": {
                        "id": "wf_api_exec",
                        "nodes": [{"id": "A", "type": "transform", "config": {"ok": True}}],
                        "edges": [],
                        "state_schema": {},
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
    finally:
        app.dependency_overrides.clear()


def test_execute_workflow_forbidden_for_actions():
    app.dependency_overrides[verify_token] = _auth("actions")
    app.state.start_time = time.time()
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/ops/workflows/execute",
                json={
                    "workflow": {
                        "id": "wf_api_exec_forbidden",
                        "nodes": [{"id": "A", "type": "transform", "config": {}}],
                        "edges": [],
                        "state_schema": {},
                    }
                },
            )
            assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_workflow_checkpoints_for_operator():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with patch("tools.gimo_server.ops_routes.StorageService.list_checkpoints") as mock_list:
            mock_list.return_value = [{"workflow_id": "wf1", "node_id": "A", "state": {}, "output": {}, "status": "completed"}]
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/ops/workflows/wf1/checkpoints")
                assert response.status_code == 200
                payload = response.json()
                assert payload["count"] == 1
                assert payload["items"][0]["node_id"] == "A"
    finally:
        app.dependency_overrides.clear()


def test_resume_workflow_not_found_when_no_runtime_or_persisted_data():
    app.dependency_overrides[verify_token] = _auth("operator")
    app.state.start_time = time.time()
    try:
        with patch("tools.gimo_server.ops_routes.StorageService.get_workflow") as mock_get:
            mock_get.return_value = None
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post("/ops/workflows/wf_missing/resume")
                assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
