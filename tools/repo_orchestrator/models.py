from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel
from dataclasses import dataclass

class AgentQuality(BaseModel):
    score: int
    alerts: List[str]
    lastCheck: str

class AgentPlan(BaseModel):
    id: str
    steps: List[Dict[str, str]]
    status: str

class NodeData(BaseModel):
    label: str
    status: Optional[str] = "active"
    path: Optional[str] = None
    plan: Optional[AgentPlan] = None
    trustLevel: Optional[str] = None
    quality: Optional[AgentQuality] = None
    subAgents: Optional[List[SubAgent]] = None

class GraphNode(BaseModel):
    id: str
    type: str
    data: NodeData
    position: Dict[str, float]

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    animated: bool = False

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
class RepoEntry(BaseModel):
    name: str
    path: str

class VitaminizeResponse(BaseModel):
    status: str
    created_files: List[str]
    active_repo: Optional[str] = None

class StatusResponse(BaseModel):
    version: str
    uptime_seconds: float

class UiStatusResponse(BaseModel):
    version: str
    uptime_seconds: float
    allowlist_count: int
    last_audit_line: Optional[str] = None
    service_status: str

class FileWriteRequest(BaseModel):
    path: str
    content: str

class PlanTask(BaseModel):
    id: str
    title: str
    description: str
    status: Literal['pending', 'running', 'done', 'failed']
    dependencies: List[str]

class AgentAssignment(BaseModel):
    agentId: str
    taskIds: List[str]

class Plan(BaseModel):
    id: str
    title: str
    status: Literal['draft', 'review', 'approved', 'executing', 'completed', 'failed']
    tasks: List[PlanTask]
    assignments: List[AgentAssignment]

class PlanCreateRequest(BaseModel):
    title: str
    task_description: str

class PlanUpdateRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[Literal['draft', 'review', 'approved', 'executing', 'completed', 'failed']] = None

class AgentMessage(BaseModel):
    id: str
    from_role: Literal['agent', 'orchestrator', 'user']
    agentId: str
    type: Literal['question', 'instruction', 'report', 'reassignment']
    content: str
    timestamp: str

class SubAgentConfig(BaseModel):
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048

class SubAgent(BaseModel):
    id: str
    parentId: str
    name: str
    model: str
    status: Literal['starting', 'working', 'idle', 'terminated', 'failed']
    currentTask: Optional[str] = None
    config: SubAgentConfig

class DelegationRequest(BaseModel):
    subTaskDescription: str
    modelPreference: str = "llama3"
    constraints: Dict[str, Any] = {}

