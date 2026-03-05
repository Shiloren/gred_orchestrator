from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from ..config import OPS_DATA_DIR

logger = logging.getLogger("orchestrator.skills")

SKILLS_DIR = OPS_DATA_DIR / "skills"
COMMAND_RE = re.compile(r"^/[a-z0-9_-]{2,32}$")
SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9._-]{1,80}$")


class DuplicateCommandError(ValueError):
    """Raised when a skill command is already taken by another skill."""


class SkillDefinition(BaseModel):
    id: str
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=5000)
    command: str
    replace_graph: bool = False
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("command")
    @classmethod
    def _validate_command(cls, value: str) -> str:
        if not COMMAND_RE.fullmatch(value or ""):
            raise ValueError("command must match ^/[a-z0-9_-]{2,32}$")
        return value


class SkillCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=5000)
    command: str
    replace_graph: bool = False
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)

class SkillDescriptionRequest(BaseModel):
    name: str = Field(default="", max_length=120)
    command: Optional[str] = None
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)


class SkillExecuteRequest(BaseModel):
    replace_graph: bool = False
    context: Dict[str, Any] = Field(default_factory=dict)


class SkillExecuteResponse(BaseModel):
    skill_run_id: str
    skill_id: str
    replace_graph: bool
    status: str


@dataclass(frozen=True)
class _GraphEdge:
    source: str
    target: str


class SkillsService:
    """File-backed service for canonical visual Skills."""

    @classmethod
    def _ensure_dir(cls) -> None:
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _skill_path(cls, skill_id: str) -> Path:
        if not SAFE_ID_RE.fullmatch(skill_id):
            raise ValueError("Invalid skill_id")
        return SKILLS_DIR / f"{skill_id}.json"

    @classmethod
    def _atomic_write(cls, path: Path, payload: str) -> None:
        tmp = path.with_suffix(f".tmp.{os.urandom(4).hex()}")
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, path)

    @classmethod
    def _extract_edge(cls, edge: Dict[str, Any]) -> _GraphEdge:
        source = edge.get("source") or edge.get("from") or edge.get("from_node")
        target = edge.get("target") or edge.get("to") or edge.get("to_node")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("Each edge must include a non-empty source/from")
        if not isinstance(target, str) or not target.strip():
            raise ValueError("Each edge must include a non-empty target/to")
        return _GraphEdge(source=source, target=target)

    @classmethod
    def _validate_command(cls, command: str) -> None:
        if not COMMAND_RE.fullmatch(command or ""):
            raise ValueError("command must match ^/[a-z0-9_-]{2,32}$")

    @classmethod
    def _is_orchestrator_node(cls, node: Dict[str, Any]) -> bool:
        node_type = str(node.get("type") or node.get("node_type") or node.get("role") or "").lower()
        if node_type == "orchestrator":
            return True
        data = node.get("data") if isinstance(node.get("data"), dict) else {}
        data_type = str(data.get("type") or data.get("node_type") or data.get("role") or "").lower()
        return data_type == "orchestrator"

    @classmethod
    def _validate_graph(cls, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> None:
        if not nodes:
            raise ValueError("nodes must contain exactly one orchestrator node")

        node_ids = []
        for node in nodes:
            node_id = node.get("id")
            if not isinstance(node_id, str) or not node_id.strip():
                raise ValueError("Each node must include a non-empty id")
            node_ids.append(node_id)

        if len(set(node_ids)) != len(node_ids):
            raise ValueError("Duplicate node ids are not allowed")

        parsed_edges = [cls._extract_edge(e) for e in edges]
        known = set(node_ids)
        for edge in parsed_edges:
            if edge.source not in known or edge.target not in known:
                raise ValueError("Edge references unknown node id")

        orchestrator_count = sum(1 for n in nodes if cls._is_orchestrator_node(n))
        if orchestrator_count != 1:
            raise ValueError("Skill must have exactly one orchestrator node")

        graph: Dict[str, List[str]] = {nid: [] for nid in known}
        for edge in parsed_edges:
            graph[edge.source].append(edge.target)

        visited: set[str] = set()
        in_stack: set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            in_stack.add(node_id)
            for nxt in graph.get(node_id, []):
                if nxt not in visited:
                    if dfs(nxt):
                        return True
                elif nxt in in_stack:
                    return True
            in_stack.remove(node_id)
            return False

        for nid in graph:
            if nid not in visited and dfs(nid):
                raise ValueError("Skill graph must be a DAG")

    @classmethod
    def _slugify_id(cls, name: str) -> str:
        base = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip()).strip("-").lower() or "skill"
        return f"{base}-{int(time.time() * 1000)}-{os.urandom(2).hex()}"

    @classmethod
    def list_skills(cls) -> List[SkillDefinition]:
        cls._ensure_dir()
        out: List[SkillDefinition] = []
        for f in SKILLS_DIR.glob("*.json"):
            try:
                out.append(SkillDefinition.model_validate_json(f.read_text(encoding="utf-8")))
            except Exception as exc:
                logger.warning("Failed to parse skill '%s': %s", f.name, exc)
        return sorted(out, key=lambda s: s.updated_at, reverse=True)

    @classmethod
    def get_skill(cls, skill_id: str) -> Optional[SkillDefinition]:
        cls._ensure_dir()
        try:
            path = cls._skill_path(skill_id)
        except ValueError:
            return None
        if not path.exists():
            return None
        return SkillDefinition.model_validate_json(path.read_text(encoding="utf-8"))

    @classmethod
    def _assert_command_unique(cls, command: str, exclude_id: Optional[str] = None) -> None:
        for skill in cls.list_skills():
            if skill.command == command and skill.id != exclude_id:
                raise DuplicateCommandError(f"command '{command}' already exists")

    @classmethod
    def create_skill(cls, req: SkillCreateRequest) -> SkillDefinition:
        cls._ensure_dir()
        cls._validate_command(req.command)
        cls._validate_graph(req.nodes, req.edges)
        cls._assert_command_unique(req.command)

        skill = SkillDefinition(
            id=cls._slugify_id(req.name),
            name=req.name,
            description=req.description,
            command=req.command,
            replace_graph=req.replace_graph,
            nodes=req.nodes,
            edges=req.edges,
        )
        cls._atomic_write(cls._skill_path(skill.id), skill.model_dump_json(indent=2))
        logger.info("Skill created: %s (%s)", skill.name, skill.id)
        return skill

    @classmethod
    def delete_skill(cls, skill_id: str) -> bool:
        try:
            path = cls._skill_path(skill_id)
        except ValueError:
            return False
        if not path.exists():
            return False
        path.unlink()
        logger.info("Skill deleted: %s", skill_id)
        return True

    @classmethod
    def generate_description(cls, req: SkillDescriptionRequest) -> str:
        node_count = len(req.nodes)
        edge_count = len(req.edges)
        command = req.command or "/skill"
        name = req.name.strip() if req.name else "Skill"
        if node_count == 0:
            return f"{name} ({command}) prepara un flujo visual reutilizable para ejecutar una automatización concreta."
        return (
            f"{name} ({command}) ejecuta un flujo visual con {node_count} nodos y {edge_count} "
            f"conexiones para completar una tarea de orquestación de forma repetible."
        )

    @classmethod
    async def execute_skill(cls, skill_id: str, req: SkillExecuteRequest) -> SkillExecuteResponse:
        from .custom_plan_service import CustomPlanService, CreatePlanRequest, PlanNode, PlanEdge, PlanNodePosition

        skill = cls.get_skill(skill_id)
        if not skill:
            raise ValueError(f"Skill {skill_id} not found")

        skill_run_id = f"skill_run_{int(time.time())}_{os.urandom(2).hex()}"

        nodes = []
        for n in skill.nodes:
            # map ui node format to CustomPlan node format
            node_type = str(n.get("type", "worker"))
            data = n.get("data", {})
            nodes.append(PlanNode(
                id=n.get("id", ""),
                label=data.get("label", n.get("id", "")),
                prompt=data.get("prompt", ""),
                model=data.get("model", "auto"),
                provider=data.get("provider", "auto"),
                role=data.get("role", node_type),
                node_type=node_type,
                role_definition=data.get("system_prompt", ""),
                is_orchestrator=cls._is_orchestrator_node(n),
                position=PlanNodePosition(
                    x=n.get("position", {}).get("x", 0),
                    y=n.get("position", {}).get("y", 0),
                ),
                config=data,
            ))

        edges = []
        for e in skill.edges:
            parsed = cls._extract_edge(e)
            edges.append(PlanEdge(
                id=e.get("id", ""),
                source=parsed.source,
                target=parsed.target,
            ))

        plan_req = CreatePlanRequest(
            name=f"Run of {skill.name}",
            description=f"Automated execution for skill {skill.command}",
            nodes=nodes,
            edges=edges,
        )

        plan = CustomPlanService.create_plan(plan_req)

        # Trigger execution in background to not block
        import asyncio
        asyncio.create_task(cls._execute_plan_background(plan.id, skill.id, skill_run_id))

        return SkillExecuteResponse(
            skill_run_id=skill_run_id,
            skill_id=skill.id,
            replace_graph=req.replace_graph,
            status="queued"
        )
        
    @classmethod
    async def _execute_plan_background(cls, plan_id: str, skill_id: str, skill_run_id: str) -> None:
        from .custom_plan_service import CustomPlanService
        from .notification_service import NotificationService
        
        await NotificationService.publish(f"skill_execution_started", {
            "skill_run_id": skill_run_id,
            "skill_id": skill_id,
            "status": "running",
            "message": "Starting skill execution",
            "started_at": datetime.now(timezone.utc).isoformat(),
        })
        
        try:
            plan = await CustomPlanService.execute_plan(plan_id, skill_id=skill_id, skill_run_id=skill_run_id)
            if not plan:
                raise ValueError(f"Plan {plan_id} not found or failed to execute")
                
            status = "success" if plan.status == "done" else "error"
            await NotificationService.publish(f"skill_execution_finished", {
                "skill_run_id": skill_run_id,
                "skill_id": skill_id,
                "status": status,
                "message": f"Skill execution finished with status: {status}",
                "finished_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            logger.error(f"Error executing skill {skill_id} via plan {plan_id}: {e}")
            await NotificationService.publish(f"skill_execution_finished", {
                "skill_run_id": skill_run_id,
                "skill_id": skill_id,
                "status": "error",
                "message": f"Skill execution failed: {str(e)}",
                "finished_at": datetime.now(timezone.utc).isoformat(),
            })
