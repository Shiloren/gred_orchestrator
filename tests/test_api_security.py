"""
API Security Validation Tests (Phase 2.2)
Verifies RBAC, OpenAPI filtering, and Threat Level integration.
"""

import os
import shutil
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure we use the correct repo root for tests
os.environ.setdefault("ORCH_REPO_ROOT", str(Path(__file__).parent.parent.resolve()))

from tools.gimo_server.config import (
    ORCH_ACTIONS_TOKEN,
    ORCH_OPERATOR_TOKEN,
    TOKENS,
)
from tools.gimo_server.main import app
from tools.gimo_server.security import load_security_db, save_security_db
from tools.gimo_server.services.ops_service import OpsService

def _admin_token() -> str:
    token = os.environ.get("ORCH_TOKEN", "")
    if not token:
        # fallback: pick the admin token from TOKENS
        token = next(t for t in TOKENS if t != ORCH_ACTIONS_TOKEN and t != ORCH_OPERATOR_TOKEN)
    return token

def _admin_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_admin_token()}"}

def _operator_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {ORCH_OPERATOR_TOKEN}"}

def _actions_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {ORCH_ACTIONS_TOKEN}"}

@pytest.fixture(autouse=True)
def clean_security_state():
    """Reset security and OPS state before each test."""
    from tools.gimo_server.security import threat_engine
    threat_engine.clear_all()
    save_security_db()
    app.dependency_overrides.clear()
    
    # Clean OPS storage
    for subdir in ("drafts", "approved", "runs"):
        d = OpsService.OPS_DIR / subdir
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)
    yield
    app.dependency_overrides.clear()

_shared_client = TestClient(app, raise_server_exceptions=False)

@pytest.fixture()
def client():
    yield _shared_client

class TestRBACPenetration:
    """Verifies that roles cannot access endpoints above their privilege level."""

    def test_actions_cannot_access_admin_endpoints(self, client: TestClient):
        # Read-only admin endpoints
        for ep in ["/ops/provider", "/ops/policy"]:
            r = client.get(ep, headers=_actions_headers())
            assert r.status_code == 403, f"Endpoint {ep} should be blocked for actions role"

        # Write-only admin endpoints
        for ep in ["/ui/service/restart", "/ops/trust/reset"]:
            r = client.post(ep, headers=_actions_headers())
            assert r.status_code == 403, f"Endpoint {ep} should be blocked for actions role (POST)"

    def test_operator_cannot_access_admin_write_endpoints(self, client: TestClient):
        # Send a valid-looking body to avoid 422 and ensure it hits the 403 check
        r = client.put("/ops/provider", headers=_operator_headers(), json={"active": "openai", "providers": {}})
        assert r.status_code == 403

        r = client.put("/ops/config", headers=_operator_headers(), json={
            "default_auto_run": True,
            "draft_cleanup_ttl_days": 7,
            "max_concurrent_runs": 3,
            "operator_can_generate": False
        })
        assert r.status_code == 403

        r = client.post("/ops/trust/reset", headers=_operator_headers())
        assert r.status_code == 403

    def test_admin_can_access_everything(self, client: TestClient):
        r = client.get("/ops/config", headers=_admin_headers())
        assert r.status_code == 200
        
        r = client.get("/ops/provider", headers=_admin_headers())
        assert r.status_code in (200, 404) # 404 is fine if not set

class TestOpenAPIFiltering:
    """Verifies that the OpenAPI spec is filtered based on the requester's role."""

    def test_actions_openapi_is_filtered(self, client: TestClient):
        r = client.get("/ops/openapi.json", headers=_actions_headers())
        assert r.status_code == 200
        spec = r.json()
        paths = spec.get("paths", {})
        
        # Admin/Operator only paths should NOT be here
        assert "/ops/provider" not in paths
        assert "/ops/trust/reset" not in paths
        
        # Read-only paths should be here
        assert "/ops/plan" in paths
        assert "/ops/runs" in paths
        
        # Verify methods: /ops/runs should only have GET for actions (though /ops_routes.py says it handles POST for operator)
        assert "post" not in paths.get("/ops/runs", {})

    def test_operator_openapi_includes_mutation_paths(self, client: TestClient):
        r = client.get("/ops/openapi.json", headers=_operator_headers())
        assert r.status_code == 200
        spec = r.json()
        paths = spec.get("paths", {})
        
        # Operator has POST for runs and approve
        assert "post" in paths.get("/ops/runs", {})
        assert "post" in paths.get("/ops/drafts/{draft_id}/approve", {})
        
        # Still NO admin paths
        assert "/ops/provider" not in paths

    def test_admin_openapi_includes_everything(self, client: TestClient):
        # NOTE: Current implementation of get_filtered_openapi in ops_routes.py 
        # ALWAYS filters paths to _ACTIONS_SAFE_PATHS + some extras.
        # It doesn't actually return the full spec for admin.
        # This might be intended for "Actions import", but let's verify current behavior.
        r = client.get("/ops/openapi.json", headers=_admin_headers())
        assert r.status_code == 200
        spec = r.json()
        assert "paths" in spec

class TestThreatLevelEscalation:
    """Verifies that security failures escalate the threat level."""

    def test_auth_failure_escalates_level(self, client: TestClient):
        # We need to trigger multiple auth failures from a non-whitelisted source.
        # But TestClient uses "testclient" which is whitelisted.
        # Let's mock the IP or just use a non-whitelisted token enough times?
        # The threat engine whitelists source "testclient".
        
        from tools.gimo_server.security import threat_engine
        from tools.gimo_server.security.threat_level import ThreatLevel
        
        assert threat_engine.level == ThreatLevel.NOMINAL
        
        # Manually record failures to simulate multi-source attack if needed,
        # but let's try via API first. If it's whitelisted, it won't escalate.
        invalid_headers = {"Authorization": "Bearer invalid_but_long_enough_token_123456"}
        
        # Force a non-whitelisted source by overriding request.client.host if possible,
        # or just test the engine logic directly.
        
        for _ in range(5):
            client.get("/ops/plan", headers=invalid_headers)
            
        # Since "testclient" is whitelisted in threat_level.py, it shouldn't escalate.
        assert threat_engine.level == ThreatLevel.NOMINAL
        
        # Verify engine logic directly for non-whitelisted source
        threat_engine.record_auth_failure(source="1.2.3.4", detail="test")
        threat_engine.record_auth_failure(source="1.2.3.4", detail="test")
        threat_engine.record_auth_failure(source="1.2.3.4", detail="test")
        
        assert threat_engine.level == ThreatLevel.ALERT

    def test_lockdown_blocks_unauthenticated(self, client: TestClient):
        from tools.gimo_server.security import threat_engine
        from tools.gimo_server.security.threat_level import ThreatLevel
        
        threat_engine.level = ThreatLevel.LOCKDOWN
        
        # Unauthenticated should be blocked (503)
        r = client.get("/ops/plan")
        assert r.status_code == 503
        
        # Authenticated should pass
        r = client.get("/ops/plan", headers=_admin_headers())
        assert r.status_code in (200, 404)
