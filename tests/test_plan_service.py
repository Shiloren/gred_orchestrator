from tools.repo_orchestrator.services.plan_service import PlanService
from tools.repo_orchestrator.models import PlanUpdateRequest

def test_create_plan():
    title = "Test Plan"
    desc = "Test Description"
    plan = PlanService.create_plan(title, desc)
    
    assert plan.title == title
    assert plan.status == "review"
    assert len(plan.tasks) == 2
    assert plan.assignments[0].agentId == "api"

def test_get_plan():
    title = "Fetch Plan"
    desc = "Fetch Description"
    plan = PlanService.create_plan(title, desc)
    
    fetched = PlanService.get_plan(plan.id)
    assert fetched is not None
    assert fetched.id == plan.id

def test_approve_plan():
    plan = PlanService.create_plan("Approve", "Approve Desc")
    success = PlanService.approve_plan(plan.id)
    
    assert success is True
    assert PlanService.get_plan(plan.id).status == "approved"

def test_update_plan():
    plan = PlanService.create_plan("Update", "Update Desc")
    updates = PlanUpdateRequest(title="New Title", status="executing")
    updated = PlanService.update_plan(plan.id, updates)
    
    assert updated is not None
    assert updated.title == "New Title"
    assert updated.status == "executing"
