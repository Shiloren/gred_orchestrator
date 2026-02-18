from __future__ import annotations
import hashlib
from typing import Literal, Dict, Any
from fastapi import HTTPException
from tools.gimo_server.security.auth import AuthContext
from tools.gimo_server.services.graph_engine import GraphEngine

# Shared state for workflow engines
_WORKFLOW_ENGINES: dict[str, GraphEngine] = {}

# Role hierarchy: actions < operator < admin
_ROLE_LEVEL = {"actions": 0, "operator": 1, "admin": 2}

def _require_role(auth: AuthContext, minimum: Literal["operator", "admin"]) -> None:
    if _ROLE_LEVEL.get(auth.role, 0) < _ROLE_LEVEL[minimum]:
        raise HTTPException(status_code=403, detail=f"{minimum} role or higher required")

def _actor_label(auth: AuthContext) -> str:
    """Return a safe label for audit/storage — never the raw token."""
    short_hash = hashlib.sha256(auth.token.encode()).hexdigest()[:12]
    return f"{auth.role}:{short_hash}"

# Paths safe for actions/operator tokens (GET-only read endpoints).
_ACTIONS_SAFE_PATHS = {
    "/ops/plan", "/ops/drafts", "/ops/approved", "/ops/runs",
    "/ops/config", "/status", "/tree", "/file", "/search", "/diff",
    "/ui/status",
}
_ACTIONS_SAFE_PATH_PREFIXES = (
    "/ops/drafts/", "/ops/approved/", "/ops/runs/",
)
