"""
Test suite exhaustivo para validación de autenticación.
Diseñado para detectar y prevenir bypasses de autenticación.
"""

import os
from pathlib import Path

import pytest

# Set environment variables for testing BEFORE importing the app
os.environ.setdefault("ORCH_REPO_ROOT", str(Path(__file__).parent.parent.resolve()))

from tools.gimo_server.main import app
from tools.gimo_server.security import load_security_db, save_security_db

# Populated by the autouse fixture below from the session-scoped test_client
_shared_client = None


@pytest.fixture(autouse=True)
def _use_session_client(test_client):
    """Inject the session-scoped test_client into the module-level _shared_client."""
    global _shared_client
    _shared_client = test_client


class TestAuthenticationBypass:
    """Tests para prevenir bypasses de autenticación."""

    def setup_method(self):
        import time
        app.state.start_time = time.time()
        self.client = _shared_client

    def test_empty_token_rejected(self):
        """CRITICAL: Verify empty token is rejected."""
        response = self.client.get("/status", headers={"Authorization": "Bearer "})
        assert response.status_code == 401
        assert (
            "Invalid token" in response.json()["detail"]
            or "Token missing" in response.json()["detail"]
        )

    def test_whitespace_only_token_rejected(self):
        """Verify token with only whitespace is rejected."""
        response = self.client.get("/status", headers={"Authorization": "Bearer    "})
        assert response.status_code == 401
        detail = response.json()["detail"]
        assert "Invalid token" in detail or "Token missing" in detail or "Session expired" in detail

    def test_short_token_rejected(self):
        """Verify tokens shorter than minimum length are rejected."""
        short_tokens = ["a", "ab", "abc", "short", "123456789"]
        for token in short_tokens:
            response = self.client.get("/status", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 401, f"Short token '{token}' should be rejected"
            assert "Invalid token" in response.json()["detail"]

    def test_missing_authorization_header(self):
        """Verify requests without Authorization header are rejected."""
        response = self.client.get("/status")
        assert response.status_code == 401
        assert "Token missing" in response.json()["detail"]

    def test_invalid_token_triggers_lockdown(self):
        """Verify enough invalid auth events trigger LOCKDOWN via ThreatEngine."""
        from tools.gimo_server.security import threat_engine
        from tools.gimo_server.security.threat_level import ThreatLevel, AUTH_FAILURE_LOCKDOWN_THRESHOLD

        # Confirm invalid tokens are rejected
        for _ in range(5):
            response = self.client.get(
                "/status", headers={"Authorization": "Bearer invalid-token-1234567890"}
            )
            assert response.status_code == 401

        # TestClient source is whitelisted, so simulate external attacker directly
        for _ in range(AUTH_FAILURE_LOCKDOWN_THRESHOLD):
            threat_engine.record_auth_failure("external-attacker-1.2.3.4")

        assert threat_engine.level >= ThreatLevel.LOCKDOWN

    def test_malformed_bearer_scheme(self):
        """Verify malformed Authorization schemes are rejected."""
        malformed_headers = [
            "basic token123456789012345678",  # Wrong scheme
            "token123456789012345678",  # No scheme
            "Bearer",  # No token
            "BearerToken123456789012345678",  # No space
        ]
        for header in malformed_headers:
            response = self.client.get("/status", headers={"Authorization": header})
            assert response.status_code == 401, f"Malformed header '{header}' should be rejected"

    def test_case_sensitive_token(self):
        """Verify token validation is case-sensitive."""
        from tools.gimo_server.config import TOKENS

        valid_token = list(TOKENS)[0]

        # Try uppercase version
        response = self.client.get(
            "/status", headers={"Authorization": f"Bearer {valid_token.upper()}"}
        )
        if valid_token != valid_token.upper():
            assert response.status_code == 401


class TestEndpointProtection:
    """Verify all endpoints require authentication."""

    def setup_method(self):
        self.client = _shared_client

    @pytest.mark.parametrize(
        "endpoint,method",
        [
            ("/status", "get"),
            ("/ui/status", "get"),
            ("/ui/audit", "get"),
            ("/ui/allowlist", "get"),
            ("/ui/repos", "get"),
            ("/ui/repos/active", "get"),
            ("/ui/security/events", "get"),
            ("/ui/service/status", "get"),
            ("/tree", "get"),
        ],
    )
    def test_endpoint_requires_auth(self, endpoint, method):
        """Verify critical endpoints reject unauthenticated requests."""
        response = getattr(self.client, method)(endpoint)
        assert response.status_code == 401, f"{endpoint} should require authentication"

    @pytest.mark.parametrize(
        "endpoint,method",
        [
            ("/ui/repos/open?path=.", "post"),
            ("/ui/repos/select?path=.", "post"),
            ("/ui/service/restart", "post"),
            ("/ui/service/stop", "post"),
        ],
    )
    def test_sensitive_endpoints_require_auth(self, endpoint, method):
        """Verify sensitive operations require authentication."""
        response = getattr(self.client, method)(endpoint)
        assert response.status_code == 401, f"{endpoint} should require authentication"


class TestTokenInjection:
    """Tests para prevenir inyecciones de token."""

    def setup_method(self):
        self.client = _shared_client

    def test_null_byte_injection(self):
        """Verify null byte injection in token is rejected."""
        response = self.client.get("/status", headers={"Authorization": "Bearer token123\x00admin"})
        assert response.status_code == 401

    def test_newline_injection(self):
        """Verify newline injection in token is rejected."""
        response = self.client.get(
            "/status", headers={"Authorization": "Bearer token123\nX-Admin: true"}
        )
        assert response.status_code == 401

    def test_sql_injection_patterns(self):
        """Verify SQL injection patterns in tokens are rejected."""
        sql_patterns = [
            "' OR '1'='1",
            "admin'--",
            "1234567890123456'; DROP TABLE users--",
        ]
        for pattern in sql_patterns:
            response = self.client.get("/status", headers={"Authorization": f"Bearer {pattern}"})
            assert response.status_code == 401


class TestLockdownIsolation:
    """Test threat engine lockdown behavior."""

    def setup_method(self):
        import time
        app.state.start_time = time.time()
        self.client = _shared_client

    def test_lockdown_blocks_all_except_resolution(self, valid_token):
        """Verify LOCKDOWN blocks unauthenticated requests; resolution clears it."""
        from tools.gimo_server.security import threat_engine
        from tools.gimo_server.security.threat_level import ThreatLevel, AUTH_FAILURE_LOCKDOWN_THRESHOLD

        # Escalate to LOCKDOWN via external attacker failures
        for _ in range(AUTH_FAILURE_LOCKDOWN_THRESHOLD):
            threat_engine.record_auth_failure("attacker-1.2.3.4")
        assert threat_engine.level >= ThreatLevel.LOCKDOWN

        # Unauthenticated / invalid token request should be blocked
        response = self.client.get(
            "/status", headers={"Authorization": "Bearer invalid-token-1234567890"}
        )
        assert response.status_code == 503
        assert "LOCKDOWN" in response.text

        # Resolution endpoint with valid token should work
        response = self.client.post(
            "/ui/security/resolve?action=clear_all",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200

        # Verify lockdown was cleared
        assert threat_engine.level == ThreatLevel.NOMINAL


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
