from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from tools.gimo_server.security import verify_token
from tools.gimo_server.security.auth import AuthContext
from .routers.ops import (
    plan_router, run_router, eval_router, trust_router, config_router, observability_router, mastery_router
)
from .routers.ops.common import _ROLE_LEVEL, _ACTIONS_SAFE_PATHS, _ACTIONS_SAFE_PATH_PREFIXES

router = APIRouter(prefix="/ops", tags=["ops"])

# Mount sub-routers
router.include_router(plan_router.router)
router.include_router(run_router.router)
router.include_router(eval_router.router)
router.include_router(trust_router.router)
router.include_router(config_router.router)
router.include_router(observability_router.router)
router.include_router(mastery_router.router)

@router.get("/openapi.json")
async def get_filtered_openapi(
    request: Request,
    auth: AuthContext = Depends(verify_token),
):
    """Return a filtered OpenAPI spec with only actions-safe endpoints.

    Useful for ChatGPT Actions import — excludes admin-only endpoints
    like /ops/provider, /ops/generate, PUT /ops/plan, etc.
    """
    import copy
    import yaml
    from pathlib import Path as P

    spec_path = P(__file__).parent / "openapi.yaml"
    if not spec_path.exists():
        raise HTTPException(status_code=404, detail="OpenAPI spec not found")
    full_spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    filtered = copy.deepcopy(full_spec)

    new_paths = {}
    for path, methods in filtered.get("paths", {}).items():
        is_safe = path in _ACTIONS_SAFE_PATHS or any(
            path.startswith(p) for p in _ACTIONS_SAFE_PATH_PREFIXES
        )
        if is_safe:
            # Keep only GET methods for actions-safe paths
            safe_methods = {m: v for m, v in methods.items() if m == "get"}
            if safe_methods:
                new_paths[path] = safe_methods

    # Also include the approve and runs POST for operator-level spec
    if _ROLE_LEVEL.get(auth.role, 0) >= _ROLE_LEVEL["operator"]:
        for path in ("/ops/drafts/{draft_id}/approve", "/ops/runs"):
            if path in filtered.get("paths", {}):
                entry = new_paths.setdefault(path, {})
                if "post" in filtered["paths"][path]:
                    entry["post"] = filtered["paths"][path]["post"]

    filtered["paths"] = new_paths
    filtered["info"]["title"] = "Repo Orchestrator API (Actions)"
    filtered["info"]["description"] = "Filtered spec for external integrations. Admin-only endpoints excluded."
    return filtered
