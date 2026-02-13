import uuid
from typing import List, Dict, Optional
from tools.repo_orchestrator.models import Plan, PlanTask, AgentAssignment, PlanUpdateRequest

class PlanService:
    _plans: Dict[str, Plan] = {}

    @classmethod
    def create_plan(cls, title: str, task_description: str) -> Plan:
        # Mocking plan generation
        plan_id = str(uuid.uuid4())
        tasks = [
            PlanTask(
                id="task-1",
                title="Analyze Requirements",
                description=f"Analyze: {task_description}",
                status="pending",
                dependencies=[]
            ),
            PlanTask(
                id="task-2",
                title="Implementation",
                description="Implement the logic",
                status="pending",
                dependencies=["task-1"]
            )
        ]
        assignments = [
            AgentAssignment(agentId="api", taskIds=["task-1", "task-2"])
        ]
        plan = Plan(
            id=plan_id,
            title=title,
            status="review",
            tasks=tasks,
            assignments=assignments
        )
        cls._plans[plan_id] = plan
        return plan

    @classmethod
    def get_plan(cls, plan_id: str) -> Optional[Plan]:
        return cls._plans.get(plan_id)

    @classmethod
    def approve_plan(cls, plan_id: str) -> bool:
        if plan_id in cls._plans:
            cls._plans[plan_id].status = "approved"
            return True
        return False

    @classmethod
    def update_plan(cls, plan_id: str, updates: PlanUpdateRequest) -> Optional[Plan]:
        if plan_id in cls._plans:
            plan = cls._plans[plan_id]
            # Simple update logic
            if updates.status is not None:
                plan.status = updates.status
            if updates.title is not None:
                plan.title = updates.title
            return plan
        return None
