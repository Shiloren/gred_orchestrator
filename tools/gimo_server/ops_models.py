from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class OpsTask(BaseModel):
    id: str
    title: str
    scope: str
    depends: List[str] = []
    status: Literal["pending", "in_progress", "done", "blocked"] = "pending"
    description: str


class OpsPlan(BaseModel):
    id: str
    title: str
    workspace: str
    created: str
    objective: str
    tasks: List[OpsTask]
    constraints: List[str] = []


class OpsDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    prompt: str
    context: Dict[str, Any] = Field(default_factory=dict)
    provider: Optional[str] = None
    content: Optional[str] = None
    status: Literal["draft", "rejected", "approved", "error"] = "draft"
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OpsApproved(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    draft_id: str
    prompt: str
    provider: Optional[str] = None
    content: str
    approved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by: Optional[str] = None


class OpsRun(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    approved_id: str
    status: Literal["pending", "running", "done", "error", "cancelled"] = "pending"
    log: List[Dict[str, Any]] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProviderEntry(BaseModel):
    type: Literal["openai_compat", "anthropic", "gemini"]
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: str


class ProviderConfig(BaseModel):
    """Provider config persisted to disk.

    Matches the schema described in docs/OPS_RUNTIME_PLAN_v2.md.
    """

    active: str
    providers: Dict[str, ProviderEntry]


class OpsCreateDraftRequest(BaseModel):
    prompt: str
    context: Dict[str, Any] = Field(default_factory=dict)


class OpsUpdateDraftRequest(BaseModel):
    prompt: Optional[str] = None
    content: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class OpsConfig(BaseModel):
    """Global OPS runtime configuration persisted to .orch_data/ops/config.json."""

    default_auto_run: bool = False
    draft_cleanup_ttl_days: int = 7
    max_concurrent_runs: int = 3
    operator_can_generate: bool = False


class OpsApproveResponse(BaseModel):
    """Response for approve endpoint — includes optional auto-created run."""

    approved: OpsApproved
    run: Optional[OpsRun] = None


class OpsCreateRunRequest(BaseModel):
    approved_id: str


class WorkflowNode(BaseModel):
    id: str
    type: Literal[
        "llm_call",
        "tool_call",
        "human_review",
        "eval",
        "transform",
        "sub_graph",
        "agent_task",
        "contract_check",
    ]
    config: Dict[str, Any] = Field(default_factory=dict)
    agent: Optional[str] = None
    timeout: Optional[int] = None
    retries: int = 0


class WorkflowEdge(BaseModel):
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    condition: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class WorkflowGraph(BaseModel):
    id: str
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    state_schema: Dict[str, Any] = Field(default_factory=dict)


class WorkflowCheckpoint(BaseModel):
    node_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    state: Dict[str, Any]
    output: Any
    status: Literal["completed", "failed"]


class WorkflowState(BaseModel):
    version: int = 1
    data: Dict[str, Any] = Field(default_factory=dict)
    checkpoints: List[WorkflowCheckpoint] = Field(default_factory=list)


class WorkflowExecuteRequest(BaseModel):
    workflow: WorkflowGraph
    initial_state: Dict[str, Any] = Field(default_factory=dict)
    persist_checkpoints: bool = True
    workflow_timeout_seconds: Optional[int] = None


class TrustEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dimension_key: str  # "tool|path|model|task_type"
    tool: str
    context: str
    model: str
    task_type: Optional[str] = None
    outcome: Literal["approved", "rejected", "error", "timeout", "auto_approved"]
    actor: str
    post_check_passed: bool = True
    duration_ms: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0


class ContractCheck(BaseModel):
    type: Literal["file_exists", "tests_pass", "function_exists", "no_new_vulnerabilities", "custom"]
    params: Dict[str, Any] = Field(default_factory=dict)


class WorkflowContract(BaseModel):
    pre_conditions: List[ContractCheck] = Field(default_factory=list)
    post_conditions: List[ContractCheck] = Field(default_factory=list)
    rollback: List[Dict[str, Any]] = Field(default_factory=list)
    blast_radius: Literal["low", "medium", "high", "critical"] = "low"


class CircuitBreakerConfigModel(BaseModel):
    window: int = Field(default=20, ge=1)
    failure_threshold: int = Field(default=5, ge=1)
    recovery_probes: int = Field(default=3, ge=1)
    cooldown_seconds: int = Field(default=300, ge=0)


class ToolEntry(BaseModel):
    name: str
    description: str = ""
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    risk: Literal["read", "write", "destructive"] = "read"
    estimated_cost: float = 0.0
    requires_hitl: bool = False
    allowed_roles: List[str] = Field(default_factory=lambda: ["operator", "admin"])


class PolicyRuleMatch(BaseModel):
    tool: str = "*"
    context: str = "*"


class PolicyRule(BaseModel):
    match: PolicyRuleMatch = Field(default_factory=PolicyRuleMatch)
    action: Literal["allow", "deny", "require_review"] = "allow"
    override: Optional[Literal["never_auto_approve"]] = None
    min_trust_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class PolicyConfig(BaseModel):
    rules: List[PolicyRule] = Field(default_factory=list)


class EvalGoldenCase(BaseModel):
    case_id: str
    input_state: Dict[str, Any] = Field(default_factory=dict)
    expected_state: Dict[str, Any] = Field(default_factory=dict)
    threshold: float = Field(default=1.0, ge=0.0, le=1.0)


class EvalDataset(BaseModel):
    workflow_id: str
    cases: List[EvalGoldenCase] = Field(default_factory=list)


class EvalJudgeConfig(BaseModel):
    enabled: bool = False
    mode: Literal["heuristic"] = "heuristic"
    output_key: Optional[str] = None


class EvalGateConfig(BaseModel):
    min_pass_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    min_avg_score: float = Field(default=1.0, ge=0.0, le=1.0)


class EvalRunRequest(BaseModel):
    workflow: WorkflowGraph
    dataset: EvalDataset
    judge: EvalJudgeConfig = Field(default_factory=EvalJudgeConfig)
    gate: EvalGateConfig = Field(default_factory=EvalGateConfig)
    case_limit: Optional[int] = Field(default=None, ge=1)


class EvalCaseResult(BaseModel):
    case_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    expected_state: Dict[str, Any] = Field(default_factory=dict)
    actual_state: Dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None


class EvalRunReport(BaseModel):
    eval_run_id: Optional[int] = None
    workflow_id: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float = Field(ge=0.0, le=1.0)
    avg_score: float = Field(ge=0.0, le=1.0)
    gate_passed: bool
    gate: EvalGateConfig
    results: List[EvalCaseResult] = Field(default_factory=list)


class EvalRunSummary(BaseModel):
    run_id: int
    workflow_id: str
    gate_passed: bool
    pass_rate: float = Field(ge=0.0, le=1.0)
    avg_score: float = Field(ge=0.0, le=1.0)
    total_cases: int
    passed_cases: int
    failed_cases: int
    created_at: str


class EvalRunDetail(BaseModel):
    run_id: int
    workflow_id: str
    created_at: str
    report: Optional[EvalRunReport] = None
