import hashlib
import hmac
import logging
import secrets
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, Optional

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from tools.gimo_server.config import ORCH_ACTIONS_TOKEN, ORCH_OPERATOR_TOKEN, TOKENS

logger = logging.getLogger("orchestrator.auth")

security = HTTPBearer(auto_error=False)

INVALID_TOKEN_ERROR = "Invalid token"
SESSION_COOKIE_NAME = "gimo_session"
SESSION_TTL_SECONDS = 86400  # 24 hours


# ---------------------------------------------------------------------------
# Session store (in-memory, survives as long as the process runs)
# ---------------------------------------------------------------------------
@dataclass
class _Session:
    session_id: str
    role: str
    created_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)


class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, _Session] = {}
        self._lock = Lock()
        # Derive a signing key from the set of valid tokens for HMAC
        self._signing_key = hashlib.sha256(
            "|".join(sorted(TOKENS)).encode()
        ).digest()

    def create(self, role: str) -> str:
        session_id = secrets.token_urlsafe(32)
        sig = hmac.new(self._signing_key, session_id.encode(), hashlib.sha256).hexdigest()[:16]
        cookie_value = f"{session_id}.{sig}"
        with self._lock:
            self._sessions[session_id] = _Session(session_id=session_id, role=role)
        return cookie_value

    def validate(self, cookie_value: str) -> Optional[_Session]:
        parts = cookie_value.split(".", 1)
        if len(parts) != 2:
            return None
        session_id, sig = parts
        expected_sig = hmac.new(self._signing_key, session_id.encode(), hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected_sig):
            return None
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            if time.time() - session.created_at > SESSION_TTL_SECONDS:
                del self._sessions[session_id]
                return None
            session.last_seen = time.time()
            return session

    def revoke(self, cookie_value: str) -> None:
        parts = cookie_value.split(".", 1)
        if len(parts) == 2:
            with self._lock:
                self._sessions.pop(parts[0], None)

    def cleanup_expired(self) -> int:
        now = time.time()
        with self._lock:
            expired = [sid for sid, s in self._sessions.items() if now - s.created_at > SESSION_TTL_SECONDS]
            for sid in expired:
                del self._sessions[sid]
            return len(expired)


session_store = SessionStore()


# ---------------------------------------------------------------------------
# Auth context
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AuthContext:
    token: str
    role: str


def _resolve_role(token: str) -> str:
    if token == ORCH_ACTIONS_TOKEN:
        return "actions"
    elif token == ORCH_OPERATOR_TOKEN:
        return "operator"
    return "admin"


# ---------------------------------------------------------------------------
# Unified verify: Bearer header OR session cookie
# ---------------------------------------------------------------------------
def verify_token(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Security(security)
) -> AuthContext:
    # 1. Try Bearer header first (API/CLI callers)
    if credentials and credentials.credentials:
        token = credentials.credentials.strip()
        if token and len(token) >= 16 and token in TOKENS:
            return AuthContext(token=token, role=_resolve_role(token))
        if token:
            _report_auth_failure(request, token)
            raise HTTPException(status_code=401, detail=INVALID_TOKEN_ERROR)

    # 2. Try session cookie (browser/UI callers)
    cookie_value = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_value:
        session = session_store.validate(cookie_value)
        if session:
            return AuthContext(token="session", role=session.role)
        # Invalid/expired cookie — don't escalate threat, just reject
        raise HTTPException(status_code=401, detail="Session expired")

    raise HTTPException(status_code=401, detail="Token missing")


def _report_auth_failure(request: Request, token: str) -> None:
    from tools.gimo_server.security import threat_engine

    token_hash = hashlib.sha256(token.encode("utf-8", errors="ignore")).hexdigest()
    client_ip = request.client.host if request.client else "unknown"

    threat_engine.record_auth_failure(
        source=client_ip,
        detail=f"Invalid token hash: {token_hash[:16]}..."
    )
