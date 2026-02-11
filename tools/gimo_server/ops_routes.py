from __future__ import annotations

import hashlib
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from tools.gimo_server.security import audit_log, check_rate_limit, verify_token
from tools.gimo_server.security.auth import AuthContext

from .ops_models import (
    CircuitBreakerConfigModel,
    EvalRunDetail,
    EvalRunReport,
    EvalRunRequest,
    EvalRunSummary,
    EvalDataset,
    OpsApproved,
    OpsApproveResponse,
    OpsConfig,
    OpsCreateDraftRequest,
    OpsCreateRunRequest,
    OpsDraft,
    OpsPlan,
    OpsRun,
    PolicyConfig,
    WorkflowCheckpoint,
    WorkflowExecuteRequest,
    WorkflowGraph,
    ToolEntry,
    OpsUpdateDraftRequest,
    ProviderConfig,
)
from .services.graph_engine import GraphEngine
from .services.ops_service import OpsService
from .services.institutional_memory_service import InstitutionalMemoryService
from .services.observability_service import ObservabilityService
from .services.evals_service import EvalsService
from .services.provider_service import ProviderService
from .services.policy_service import PolicyService
from .services.storage_service import StorageService
from .services.tool_registry_service import ToolRegistryService
from .services.trust_engine import TrustEngine


router = APIRouter(prefix="/ops", tags=["ops"])
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


@router.get("/plan", response_model=OpsPlan)
async def get_plan(
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    plan = OpsService.get_plan()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not set")
    return plan


@router.put("/plan")
async def set_plan(
    request: Request,
    plan: OpsPlan,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "admin")
    OpsService.set_plan(plan)
    audit_log("OPS", "/ops/plan", plan.id, operation="WRITE", actor=_actor_label(auth))
    return {"status": "ok"}


@router.get("/drafts", response_model=List[OpsDraft])
async def list_drafts(
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    return OpsService.list_drafts()


@router.post("/drafts", response_model=OpsDraft, status_code=201)
async def create_draft(
    request: Request,
    body: OpsCreateDraftRequest,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "admin")
    draft = OpsService.create_draft(body.prompt, context=body.context)
    audit_log("OPS", "/ops/drafts", draft.id, operation="WRITE", actor=_actor_label(auth))
    return draft


@router.get("/drafts/{draft_id}", response_model=OpsDraft)
async def get_draft(
    draft_id: str,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    draft = OpsService.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.put("/drafts/{draft_id}", response_model=OpsDraft)
async def update_draft(
    request: Request,
    draft_id: str,
    body: OpsUpdateDraftRequest,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "admin")
    try:
        updated = OpsService.update_draft(
            draft_id, prompt=body.prompt, content=body.content, context=body.context
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    audit_log("OPS", f"/ops/drafts/{draft_id}", updated.id, operation="WRITE", actor=_actor_label(auth))
    return updated


@router.post("/drafts/{draft_id}/reject", response_model=OpsDraft)
async def reject_draft(
    request: Request,
    draft_id: str,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "admin")
    try:
        updated = OpsService.reject_draft(draft_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    audit_log("OPS", f"/ops/drafts/{draft_id}/reject", updated.id, operation="WRITE", actor=_actor_label(auth))
    return updated


@router.post("/drafts/{draft_id}/approve", response_model=OpsApproveResponse)
async def approve_draft(
    request: Request,
    draft_id: str,
    auto_run: Optional[bool] = Query(None, description="Override default_auto_run from config"),
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    actor = _actor_label(auth)
    try:
        approved = OpsService.approve_draft(draft_id, approved_by=actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    audit_log("OPS", f"/ops/drafts/{draft_id}/approve", approved.id, operation="WRITE", actor=actor)

    # Resolve auto_run: explicit param > config default
    should_run = auto_run if auto_run is not None else OpsService.get_config().default_auto_run
    run = None
    if should_run:
        try:
            run = OpsService.create_run(approved.id)
            audit_log("OPS", "/ops/runs", run.id, operation="WRITE_AUTO", actor=actor)
        except (PermissionError, ValueError):
            pass  # Non-fatal: approved was created, run creation failed silently
    return OpsApproveResponse(approved=approved, run=run)


@router.get("/approved", response_model=List[OpsApproved])
async def list_approved(
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    return OpsService.list_approved()


@router.get("/approved/{approved_id}", response_model=OpsApproved)
async def get_approved(
    approved_id: str,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    approved = OpsService.get_approved(approved_id)
    if not approved:
        raise HTTPException(status_code=404, detail="Approved entry not found")
    return approved


@router.post("/runs", response_model=OpsRun, status_code=201)
async def create_run(
    request: Request,
    body: OpsCreateRunRequest,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    try:
        run = OpsService.create_run(body.approved_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    audit_log("OPS", "/ops/runs", run.id, operation="WRITE", actor=_actor_label(auth))
    return run


@router.get("/runs", response_model=List[OpsRun])
async def list_runs(
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    return OpsService.list_runs()


@router.get("/runs/{run_id}", response_model=OpsRun)
async def get_run(
    run_id: str,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    run = OpsService.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/runs/{run_id}/cancel", response_model=OpsRun)
async def cancel_run(
    request: Request,
    run_id: str,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    actor = _actor_label(auth)
    run = OpsService.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status in ("done", "error", "cancelled"):
        raise HTTPException(status_code=409, detail=f"Run already in terminal state: {run.status}")
    try:
        run = OpsService.update_run_status(run_id, "cancelled", msg=f"Cancelled by {actor}")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    audit_log("OPS", f"/ops/runs/{run_id}/cancel", run.id, operation="WRITE", actor=actor)
    return run


@router.get("/provider", response_model=ProviderConfig)
async def get_provider(
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "admin")
    cfg = ProviderService.get_public_config()
    if not cfg:
        raise HTTPException(status_code=404, detail="Provider not configured")
    return cfg


@router.put("/provider", response_model=ProviderConfig)
async def set_provider(
    request: Request,
    config: ProviderConfig,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "admin")
    cfg = ProviderService.set_config(config)
    audit_log("OPS", "/ops/provider", "set", operation="WRITE", actor=_actor_label(auth))
    # return redacted version
    return ProviderService.get_public_config() or cfg


@router.get("/connectors")
async def list_connectors(
    request: Request,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    data = ProviderService.list_connectors()
    audit_log("OPS", "/ops/connectors", str(data.get("count", 0)), operation="READ", actor=_actor_label(auth))
    return data


@router.get("/connectors/{connector_id}/health")
async def connector_health(
    request: Request,
    connector_id: str,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    try:
        data = await ProviderService.connector_health(connector_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    audit_log("OPS", f"/ops/connectors/{connector_id}/health", connector_id, operation="READ", actor=_actor_label(auth))
    return data


@router.post("/generate", response_model=OpsDraft, status_code=201)
async def generate_draft(
    request: Request,
    prompt: str = Query(..., min_length=1, max_length=8000),
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    # Generate requires admin, or operator if config allows it
    config = OpsService.get_config()
    if config.operator_can_generate:
        _require_role(auth, "operator")
    else:
        _require_role(auth, "admin")
    try:
        provider_name, content = await ProviderService.generate(prompt, context={})
        draft = OpsService.create_draft(
            prompt,
            provider=provider_name,
            content=content,
            status="draft",
        )
    except Exception as exc:
        draft = OpsService.create_draft(
            prompt,
            provider=None,
            content=None,
            status="error",
            error=str(exc)[:200],
        )
    audit_log("OPS", "/ops/generate", draft.id, operation="WRITE", actor=_actor_label(auth))
    return draft


# ----- OPS Config -----


@router.get("/config", response_model=OpsConfig)
async def get_config(
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    return OpsService.get_config()


@router.put("/config", response_model=OpsConfig)
async def set_config(
    request: Request,
    config: OpsConfig,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "admin")
    result = OpsService.set_config(config)
    audit_log("OPS", "/ops/config", "set", operation="WRITE", actor=_actor_label(auth))
    return result


# ----- Trust Engine (Fase 2.1 MVP) -----


@router.post("/trust/query")
async def trust_query(
    request: Request,
    body: dict,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    dimension_key = str(body.get("dimension_key", "")).strip()
    if not dimension_key:
        raise HTTPException(status_code=400, detail="dimension_key is required")

    engine = TrustEngine(StorageService())
    result = engine.query_dimension(dimension_key)
    audit_log("OPS", "/ops/trust/query", dimension_key, operation="READ", actor=_actor_label(auth))
    return result


@router.get("/trust/dashboard")
async def trust_dashboard(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    engine = TrustEngine(StorageService())
    result = engine.dashboard(limit=limit)
    audit_log("OPS", "/ops/trust/dashboard", str(limit), operation="READ", actor=_actor_label(auth))
    return {"items": result, "count": len(result)}


@router.get("/trust/suggestions")
async def trust_suggestions(
    request: Request,
    limit: int = Query(20, ge=1, le=200),
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    service = InstitutionalMemoryService(StorageService())
    items = service.generate_suggestions(limit=limit)
    audit_log("OPS", "/ops/trust/suggestions", str(limit), operation="READ", actor=_actor_label(auth))
    return {"items": items, "count": len(items)}


@router.get("/observability/metrics")
async def observability_metrics(
    request: Request,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    data = ObservabilityService.get_metrics()
    audit_log("OPS", "/ops/observability/metrics", "read", operation="READ", actor=_actor_label(auth))
    return data


@router.get("/observability/traces")
async def observability_traces(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    items = ObservabilityService.list_traces(limit=limit)
    audit_log("OPS", "/ops/observability/traces", str(limit), operation="READ", actor=_actor_label(auth))
    return {"items": items, "count": len(items)}


@router.post("/evals/run", response_model=EvalRunReport)
async def evals_run(
    request: Request,
    body: EvalRunRequest,
    fail_on_gate: bool = Query(False, description="If true and gate fails, returns HTTP 412"),
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")

    if body.dataset.workflow_id != body.workflow.id:
        raise HTTPException(status_code=400, detail="dataset.workflow_id must match workflow.id")

    report = await EvalsService.run_regression(
        workflow=body.workflow,
        dataset=body.dataset,
        judge=body.judge,
        gate=body.gate,
        case_limit=body.case_limit,
    )
    storage = StorageService()
    report_id = storage.save_eval_report(report)
    report.eval_run_id = report_id

    audit_log(
        "OPS",
        "/ops/evals/run",
        f"{report.workflow_id}:{report.passed_cases}/{report.total_cases}",
        operation="WRITE",
        actor=_actor_label(auth),
    )

    if fail_on_gate and not report.gate_passed:
        raise HTTPException(status_code=412, detail=report.model_dump())

    return report


@router.get("/evals/runs", response_model=List[EvalRunSummary])
async def list_eval_runs(
    request: Request,
    workflow_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    storage = StorageService()
    rows = storage.list_eval_reports(workflow_id=workflow_id, limit=limit)
    audit_log("OPS", "/ops/evals/runs", str(len(rows)), operation="READ", actor=_actor_label(auth))
    return rows


@router.get("/evals/runs/{run_id}", response_model=EvalRunDetail)
async def get_eval_run(
    request: Request,
    run_id: int,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    storage = StorageService()
    item = storage.get_eval_report(run_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Eval run not found")

    report = item.get("report") if isinstance(item, dict) else None
    if isinstance(report, dict):
        report.setdefault("eval_run_id", item.get("run_id"))

    payload = {
        "run_id": item.get("run_id"),
        "workflow_id": item.get("workflow_id"),
        "created_at": item.get("created_at"),
        "report": report,
    }
    audit_log("OPS", f"/ops/evals/runs/{run_id}", str(run_id), operation="READ", actor=_actor_label(auth))
    return payload


@router.post("/evals/datasets")
async def create_eval_dataset(
    request: Request,
    dataset: EvalDataset,
    version_tag: Optional[str] = Query(None, max_length=128),
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    storage = StorageService()
    dataset_id = storage.save_eval_dataset(dataset, version_tag=version_tag)
    audit_log(
        "OPS",
        "/ops/evals/datasets",
        f"{dataset.workflow_id}:{dataset_id}",
        operation="WRITE",
        actor=_actor_label(auth),
    )
    return {"dataset_id": dataset_id, "workflow_id": dataset.workflow_id, "version_tag": version_tag}


@router.get("/evals/datasets")
async def list_eval_datasets(
    request: Request,
    workflow_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    storage = StorageService()
    items = storage.list_eval_datasets(workflow_id=workflow_id, limit=limit)
    audit_log("OPS", "/ops/evals/datasets", str(len(items)), operation="READ", actor=_actor_label(auth))
    return {"items": items, "count": len(items)}


@router.get("/evals/datasets/{dataset_id}")
async def get_eval_dataset(
    request: Request,
    dataset_id: int,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    storage = StorageService()
    item = storage.get_eval_dataset(dataset_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Eval dataset not found")
    audit_log("OPS", f"/ops/evals/datasets/{dataset_id}", str(dataset_id), operation="READ", actor=_actor_label(auth))
    return item


@router.get("/trust/circuit-breaker/{dimension_key}")
async def get_circuit_breaker_config(
    request: Request,
    dimension_key: str,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    storage = StorageService()
    result = storage.get_circuit_breaker_config(dimension_key)
    if result is None:
        engine = TrustEngine(storage)
        cfg = engine.circuit_breaker
        result = {
            "dimension_key": dimension_key,
            "window": cfg.window,
            "failure_threshold": cfg.failure_threshold,
            "recovery_probes": cfg.recovery_probes,
            "cooldown_seconds": cfg.cooldown_seconds,
        }
    audit_log(
        "OPS",
        f"/ops/trust/circuit-breaker/{dimension_key}",
        dimension_key,
        operation="READ",
        actor=_actor_label(auth),
    )
    return result


@router.put("/trust/circuit-breaker/{dimension_key}")
async def set_circuit_breaker_config(
    request: Request,
    dimension_key: str,
    body: CircuitBreakerConfigModel,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "admin")
    storage = StorageService()
    result = storage.upsert_circuit_breaker_config(dimension_key, body.model_dump())
    audit_log(
        "OPS",
        f"/ops/trust/circuit-breaker/{dimension_key}",
        f"{dimension_key}:updated",
        operation="WRITE",
        actor=_actor_label(auth),
    )
    return result


# ----- Tool Registry (Fase 2.5 MVP) -----


@router.get("/tool-registry")
async def list_tool_registry(
    request: Request,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    items = ToolRegistryService.list_tools()
    audit_log("OPS", "/ops/tool-registry", str(len(items)), operation="READ", actor=_actor_label(auth))
    return {"items": [item.model_dump() for item in items], "count": len(items)}


@router.get("/tool-registry/{tool_name}")
async def get_tool_registry_entry(
    request: Request,
    tool_name: str,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    item = ToolRegistryService.get_tool(tool_name)
    if item is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    audit_log("OPS", f"/ops/tool-registry/{tool_name}", tool_name, operation="READ", actor=_actor_label(auth))
    return item.model_dump()


@router.put("/tool-registry/{tool_name}")
async def upsert_tool_registry_entry(
    request: Request,
    tool_name: str,
    body: ToolEntry,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "admin")
    payload = body.model_copy(update={"name": tool_name})
    item = ToolRegistryService.upsert_tool(payload)
    audit_log("OPS", f"/ops/tool-registry/{tool_name}", tool_name, operation="WRITE", actor=_actor_label(auth))
    return item.model_dump()


@router.delete("/tool-registry/{tool_name}")
async def delete_tool_registry_entry(
    request: Request,
    tool_name: str,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "admin")
    deleted = ToolRegistryService.delete_tool(tool_name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tool not found")
    audit_log("OPS", f"/ops/tool-registry/{tool_name}", tool_name, operation="WRITE", actor=_actor_label(auth))
    return {"status": "ok", "deleted": tool_name}


# ----- Policy-as-Code (Fase 5.1 MVP) -----


@router.get("/policy", response_model=PolicyConfig)
async def get_policy_config(
    request: Request,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    cfg = PolicyService.get_config()
    audit_log("OPS", "/ops/policy", "read", operation="READ", actor=_actor_label(auth))
    return cfg


@router.put("/policy", response_model=PolicyConfig)
async def set_policy_config(
    request: Request,
    body: PolicyConfig,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "admin")
    cfg = PolicyService.set_config(body)
    audit_log("OPS", "/ops/policy", "updated", operation="WRITE", actor=_actor_label(auth))
    return cfg


@router.post("/policy/decide")
async def policy_decide(
    request: Request,
    body: dict,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")

    tool = str(body.get("tool", "")).strip()
    context = str(body.get("context", "*")).strip() or "*"
    if not tool:
        raise HTTPException(status_code=400, detail="tool is required")

    try:
        trust_score = float(body.get("trust_score", 0.0) or 0.0)
    except Exception:
        raise HTTPException(status_code=400, detail="trust_score must be numeric")

    decision = PolicyService.decide(tool=tool, context=context, trust_score=trust_score)
    audit_log(
        "OPS",
        "/ops/policy/decide",
        f"{tool}:{decision.get('decision')}",
        operation="READ",
        actor=_actor_label(auth),
    )
    return {
        "tool": tool,
        "context": context,
        "trust_score": trust_score,
        **decision,
    }


# ----- Durable Execution API slice (Roadmap v2 / Fase 2.4) -----


@router.post("/workflows/execute")
async def execute_workflow(
    request: Request,
    body: WorkflowExecuteRequest,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")

    storage = StorageService()
    engine = GraphEngine(
        body.workflow,
        storage=storage,
        persist_checkpoints=bool(body.persist_checkpoints),
        workflow_timeout_seconds=body.workflow_timeout_seconds,
    )
    _WORKFLOW_ENGINES[body.workflow.id] = engine

    state = await engine.execute(initial_state=body.initial_state)
    audit_log(
        "OPS",
        "/ops/workflows/execute",
        body.workflow.id,
        operation="WRITE",
        actor=_actor_label(auth),
    )
    return {
        "workflow_id": body.workflow.id,
        "checkpoint_count": len(state.checkpoints),
        "paused": bool(state.data.get("execution_paused", False)),
        "aborted_reason": state.data.get("aborted_reason"),
        "state": state.model_dump(),
    }


@router.get("/workflows/{workflow_id}/checkpoints")
async def list_workflow_checkpoints(
    request: Request,
    workflow_id: str,
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")
    storage = StorageService()
    items = storage.list_checkpoints(workflow_id)
    audit_log(
        "OPS",
        f"/ops/workflows/{workflow_id}/checkpoints",
        str(len(items)),
        operation="READ",
        actor=_actor_label(auth),
    )
    return {"items": items, "count": len(items)}


@router.post("/workflows/{workflow_id}/resume")
async def resume_workflow(
    request: Request,
    workflow_id: str,
    from_checkpoint: int = Query(-1, description="Checkpoint index to resume from (default: last)"),
    auth: AuthContext = Depends(verify_token),
    rl: None = Depends(check_rate_limit),
):
    _require_role(auth, "operator")

    storage = StorageService()
    engine = _WORKFLOW_ENGINES.get(workflow_id)

    if engine is None:
        persisted = storage.get_workflow(workflow_id)
        if not persisted or not isinstance(persisted.get("data"), dict):
            raise HTTPException(status_code=404, detail="Workflow not found")

        try:
            workflow = WorkflowGraph.model_validate(persisted["data"])
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Invalid persisted workflow: {exc}")

        engine = GraphEngine(workflow, storage=storage, persist_checkpoints=True)
        raw_checkpoints = storage.list_checkpoints(workflow_id)
        engine.state.checkpoints = [WorkflowCheckpoint.model_validate(item) for item in raw_checkpoints]
        if engine.state.checkpoints:
            engine.state.data = dict(engine.state.checkpoints[-1].state)
        _WORKFLOW_ENGINES[workflow_id] = engine

    if not engine.state.checkpoints:
        raise HTTPException(status_code=409, detail="No checkpoints available to resume")

    try:
        next_node = engine.resume_from_checkpoint(from_checkpoint)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    state = await engine.execute()
    audit_log(
        "OPS",
        f"/ops/workflows/{workflow_id}/resume",
        f"checkpoint={from_checkpoint}",
        operation="WRITE",
        actor=_actor_label(auth),
    )
    return {
        "workflow_id": workflow_id,
        "resumed_from_checkpoint": from_checkpoint,
        "next_node": next_node,
        "checkpoint_count": len(state.checkpoints),
        "state": state.model_dump(),
    }


# ----- Filtered OpenAPI for external integrations -----

# Paths safe for actions/operator tokens (GET-only read endpoints).
_ACTIONS_SAFE_PATHS = {
    "/ops/plan", "/ops/drafts", "/ops/approved", "/ops/runs",
    "/ops/config", "/status", "/tree", "/file", "/search", "/diff",
    "/ui/status",
}
_ACTIONS_SAFE_PATH_PREFIXES = (
    "/ops/drafts/", "/ops/approved/", "/ops/runs/",
)


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
