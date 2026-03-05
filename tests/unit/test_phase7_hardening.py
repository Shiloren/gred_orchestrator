from __future__ import annotations
import asyncio
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from tools.gimo_server.main import app
from tools.gimo_server.security import verify_token
from tools.gimo_server.security.auth import AuthContext
from tools.gimo_server.services import skills_service, notification_service, custom_plan_service

def _override_auth() -> AuthContext:
    return AuthContext(token="test-token", role="admin")

@pytest.fixture
def client():
    app.dependency_overrides[verify_token] = _override_auth
    yield TestClient(app)
    app.dependency_overrides.clear()

def _valid_skill_payload(command: str = "/hardened") -> dict:
    return {
        "name": "Hardened Skill",
        "description": "Verification skill",
        "command": command,
        "replace_graph": False,
        "nodes": [
            {"id": "orch", "type": "orchestrator"},
            {"id": "worker_1", "type": "worker", "data": {"label": "Worker 1", "prompt": "Test"}},
        ],
        "edges": [
            {"source": "orch", "target": "worker_1"},
        ],
    }

@pytest.mark.asyncio
async def test_skill_execution_sse_events(tmp_path, monkeypatch, client):
    """
    Verify that executing a skill triggers NotificationService.publish 
    with correct event types.
    """
    monkeypatch.setattr(skills_service, "SKILLS_DIR", tmp_path / "skills")
    
    # Mock NotificationService.publish to track events
    mock_publish = AsyncMock()
    monkeypatch.setattr(notification_service.NotificationService, "publish", mock_publish)
    
    # Mock CustomPlanService.execute_plan to avoid real LLM calls
    mock_plan = custom_plan_service.CustomPlan(
        id="test_plan",
        name="Test Plan",
        status="done",
        nodes=[],
        edges=[]
    )
    monkeypatch.setattr(custom_plan_service.CustomPlanService, "execute_plan", AsyncMock(return_value=mock_plan))
    
    # 1. Create skill
    create_res = client.post("/ops/skills", json=_valid_skill_payload())
    assert create_res.status_code == 201
    skill_id = create_res.json()["id"]
    
    # 2. Execute skill
    exec_res = client.post(f"/ops/skills/{skill_id}/execute", json={"replace_graph": False})
    assert exec_res.status_code == 201
    
    # Wait for background task
    await asyncio.sleep(0.5) 
    
    # Check if events were "published"
    event_types = [call.args[0] for call in mock_publish.call_args_list]
    assert "skill_execution_started" in event_types
    assert "skill_execution_finished" in event_types

@pytest.mark.asyncio
async def test_skill_execution_error_propagation(tmp_path, monkeypatch, client):
    """
    Verify that an error in execution emits a finished event with error status.
    """
    monkeypatch.setattr(skills_service, "SKILLS_DIR", tmp_path / "skills")
    
    mock_publish = AsyncMock()
    monkeypatch.setattr(notification_service.NotificationService, "publish", mock_publish)
    
    # Force an error in execute_plan
    monkeypatch.setattr(custom_plan_service.CustomPlanService, "execute_plan", AsyncMock(side_effect=Exception("Simulated Failure")))
    
    create_res = client.post("/ops/skills", json=_valid_skill_payload("/fail"))
    assert create_res.status_code == 201
    skill_id = create_res.json()["id"]
    
    client.post(f"/ops/skills/{skill_id}/execute", json={"replace_graph": False})
    await asyncio.sleep(0.5)
    
    # Check for error status in finished event
    finished_call = next((c for c in mock_publish.call_args_list if c.args[0] == "skill_execution_finished"), None)
    assert finished_call is not None
    assert finished_call.args[1]["status"] == "error"
    assert "Simulated Failure" in finished_call.args[1]["message"]

def test_slugify_uniqueness_under_load():
    """
    Fast check that slugify generates unique IDs even when called 
    rapidly.
    """
    ids = set()
    for _ in range(1000): # Increased load
        ids.add(skills_service.SkillsService._slugify_id("Test Name"))
    assert len(ids) == 1000
