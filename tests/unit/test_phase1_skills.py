from __future__ import annotations

from fastapi.testclient import TestClient

from tools.gimo_server.main import app
from tools.gimo_server.security import verify_token
from tools.gimo_server.security.auth import AuthContext
from tools.gimo_server.services import skills_service


def _override_auth() -> AuthContext:
    return AuthContext(token="test-token", role="admin")


def _valid_skill_payload(command: str = "/explorar") -> dict:
    return {
        "name": "Exploración de repo",
        "description": "Recorre módulos principales",
        "command": command,
        "replace_graph": False,
        "nodes": [
            {"id": "orch", "type": "orchestrator"},
            {"id": "worker_1", "type": "worker"},
        ],
        "edges": [
            {"source": "orch", "target": "worker_1"},
        ],
    }


def test_phase1_skills_crud_and_validations(tmp_path, monkeypatch):
    app.dependency_overrides[verify_token] = _override_auth
    monkeypatch.setattr(skills_service, "SKILLS_DIR", tmp_path / "skills")

    try:
        client = TestClient(app)
        # create valid
        create_res = client.post("/ops/skills", json=_valid_skill_payload())
        assert create_res.status_code == 201
        created = create_res.json()
        assert created["command"] == "/explorar"

        # duplicate command
        dup_res = client.post("/ops/skills", json=_valid_skill_payload("/explorar"))
        assert dup_res.status_code == 409

        # invalid graph (cycle)
        cycle_payload = _valid_skill_payload("/ciclo")
        cycle_payload["edges"] = [
            {"source": "orch", "target": "worker_1"},
            {"source": "worker_1", "target": "orch"},
        ]
        cycle_res = client.post("/ops/skills", json=cycle_payload)
        assert cycle_res.status_code == 400

        # list
        list_res = client.get("/ops/skills")
        assert list_res.status_code == 200
        listed = list_res.json()
        assert isinstance(listed, list)
        assert len(listed) == 1
        assert listed[0]["command"] == "/explorar"

        # delete
        delete_res = client.delete(f"/ops/skills/{created['id']}")
        assert delete_res.status_code == 204

        list_after_delete = client.get("/ops/skills")
        assert list_after_delete.status_code == 200
        assert list_after_delete.json() == []
    finally:
        app.dependency_overrides.clear()


def test_phase1_skills_generate_description(tmp_path, monkeypatch):
    app.dependency_overrides[verify_token] = _override_auth
    monkeypatch.setattr(skills_service, "SKILLS_DIR", tmp_path / "skills")

    try:
        client = TestClient(app)
        res = client.post(
            "/ops/skills/generate-description",
            json={
                "name": "Análisis",
                "command": "/analizar",
                "nodes": [{"id": "orch", "type": "orchestrator"}],
                "edges": [],
            },
        )
        assert res.status_code == 200
        assert "description" in res.json()
        assert "/analizar" in res.json()["description"]
    finally:
        app.dependency_overrides.clear()


def test_phase1_skills_execute_returns_run_id(tmp_path, monkeypatch):
    app.dependency_overrides[verify_token] = _override_auth
    monkeypatch.setattr(skills_service, "SKILLS_DIR", tmp_path / "skills")

    async def _fake_execute_skill(skill_id: str, req):
        import asyncio
        await asyncio.sleep(0)
        return skills_service.SkillExecuteResponse(
            skill_run_id="skill_run_test_1234",
            skill_id=skill_id,
            replace_graph=req.replace_graph,
            status="queued",
        )

    monkeypatch.setattr(skills_service.SkillsService, "execute_skill", _fake_execute_skill)

    try:
        client = TestClient(app)
        create_res = client.post("/ops/skills", json=_valid_skill_payload("/ejecutar"))
        assert create_res.status_code == 201
        created = create_res.json()

        exec_res = client.post(
            f"/ops/skills/{created['id']}/execute",
            json={"replace_graph": False, "context": {}},
        )
        assert exec_res.status_code == 201
        body = exec_res.json()
        assert body["skill_run_id"] == "skill_run_test_1234"
        assert body["skill_id"] == created["id"]
        assert body["status"] == "queued"
    finally:
        app.dependency_overrides.clear()
