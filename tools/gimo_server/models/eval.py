from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from .workflow import WorkflowGraph

class EvalGoldenCase(BaseModel):
    case_id: str
    input_state: Dict[str, Any] = Field(default_factory=dict)
    expected_state: Dict[str, Any] = Field(default_factory=dict)
    threshold: float = Field(default=1.0, ge=0.0, le=1.0)

class EvalDataset(BaseModel):
    workflow_id: str
    name: str
    description: Optional[str] = None
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
    input_state: Dict[str, Any] = Field(default_factory=dict)
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
