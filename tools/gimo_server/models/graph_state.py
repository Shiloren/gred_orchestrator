from __future__ import annotations
from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

class IntentClass(str, Enum):
    feature = "feature"
    bugfix = "bugfix"
    refactor = "refactor"
    chore = "chore"

class DelegationStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"

class QaVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"

class RepoSnapshot(BaseModel):
    provider: str
    repo: str
    base_ref: str
    worktree_id: Optional[str] = None

class RepoContext(BaseModel):
    stack: List[str] = Field(default_factory=list)
    commands: List[str] = Field(default_factory=list)
    paths_of_interest: List[str] = Field(default_factory=list)
    env_notes: Optional[str] = None

class ContractExecution(BaseModel):
    intent_class: IntentClass
    path_scope: List[str] = Field(default_factory=list)

class StrictContract(BaseModel):
    objective: str = Field(min_length=10)
    constraints: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(min_length=1)
    execution: ContractExecution
    out_of_scope: List[str] = Field(default_factory=list)

    @field_validator("acceptance_criteria")
    @classmethod
    def validate_actionable_criteria(cls, v: List[str]) -> List[str]:
        for c in v:
            if not c.strip():
                raise ValueError("Acceptance criteria cannot be empty strings.")
        return v

class Delegation(BaseModel):
    role: str
    prompt: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    expected_outputs: Dict[str, Any] = Field(default_factory=dict)
    status: DelegationStatus = DelegationStatus.pending
    artifacts: List[str] = Field(default_factory=list)

class CommandRun(BaseModel):
    cmd: str
    cwd: str
    exit_code: int
    stdout_tail: str
    stderr_tail: str
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TestRun(BaseModel):
    name: str
    status: Literal["passed", "failed", "skipped"]
    duration_ms: int

class DiffRef(BaseModel):
    path: str
    sha: Optional[str] = None
    summary: str

class Evidence(BaseModel):
    commands_run: List[CommandRun] = Field(default_factory=list)
    test_results: List[TestRun] = Field(default_factory=list)
    diffs: List[DiffRef] = Field(default_factory=list)

class Failure(BaseModel):
    criterion: str
    reason: str
    evidence_ref: Optional[str] = None
    suggested_fix: Optional[str] = None

class QaState(BaseModel):
    verdict: Optional[QaVerdict] = None
    failures: List[Failure] = Field(default_factory=list)

class GraphState(BaseModel):
    state_version: Literal["0.1"] = "0.1"
    user_request_raw: str
    repo_snapshot: Optional[RepoSnapshot] = None
    repo_context: RepoContext = Field(default_factory=RepoContext)
    contract: Optional[StrictContract] = None
    delegations: Dict[str, Delegation] = Field(default_factory=dict)
    evidence: Evidence = Field(default_factory=Evidence)
    qa: QaState = Field(default_factory=QaState)
