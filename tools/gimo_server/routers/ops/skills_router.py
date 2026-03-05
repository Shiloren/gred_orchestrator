from __future__ import annotations

from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException

from tools.gimo_server.security import audit_log, check_rate_limit, verify_token
from tools.gimo_server.security.auth import AuthContext
from tools.gimo_server.services.skills_service import (
    DuplicateCommandError,
    SkillDefinition,
    SkillCreateRequest,
    SkillDescriptionRequest,
    SkillExecuteRequest,
    SkillExecuteResponse,
    SkillsService,
)
from .common import _actor_label, _require_role

router = APIRouter()


@router.get("/skills", response_model=List[SkillDefinition])
async def list_skills(
    auth: Annotated[AuthContext, Depends(verify_token)],
    rl: Annotated[None, Depends(check_rate_limit)],
):
    """List all available skill templates."""
    return SkillsService.list_skills()


@router.get(
    "/skills/{skill_id}",
    response_model=SkillDefinition,
    responses={
        404: {"description": "Skill not found"}
    }
)
async def get_skill(
    skill_id: str,
    auth: Annotated[AuthContext, Depends(verify_token)],
    rl: Annotated[None, Depends(check_rate_limit)],
):
    """Get a single skill template by ID."""
    skill = SkillsService.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("/skills", response_model=SkillDefinition, status_code=201)
async def create_skill(
    body: SkillCreateRequest,
    auth: Annotated[AuthContext, Depends(verify_token)],
    rl: Annotated[None, Depends(check_rate_limit)],
):
    """Create a new skill template."""
    _require_role(auth, "operator")
    try:
        skill = SkillsService.create_skill(body)
    except DuplicateCommandError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    audit_log("SKILLS", "/ops/skills", skill.id, operation="CREATE", actor=_actor_label(auth))
    return skill


@router.delete("/skills/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: str,
    auth: Annotated[AuthContext, Depends(verify_token)],
    rl: Annotated[None, Depends(check_rate_limit)],
):
    """Delete a skill template."""
    _require_role(auth, "admin")
    deleted = SkillsService.delete_skill(skill_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Skill not found")
    audit_log("SKILLS", f"/ops/skills/{skill_id}", skill_id, operation="DELETE", actor=_actor_label(auth))


@router.post("/skills/generate-description")
async def generate_description(
    body: SkillDescriptionRequest,
    auth: Annotated[AuthContext, Depends(verify_token)],
    rl: Annotated[None, Depends(check_rate_limit)],
):
    """Generate a baseline description for a visual Skill payload."""
    _require_role(auth, "operator")
    description = SkillsService.generate_description(body)
    return {"description": description}


@router.post(
    "/skills/{skill_id}/execute",
    response_model=SkillExecuteResponse,
    status_code=201,
    responses={
        404: {"description": "Skill not found"},
        500: {"description": "Execution error"}
    }
)
async def execute_skill(
    skill_id: str,
    body: SkillExecuteRequest,
    auth: Annotated[AuthContext, Depends(verify_token)],
    rl: Annotated[None, Depends(check_rate_limit)],
):
    """Execute a skill."""
    _require_role(auth, "operator")
    try:
        response = await SkillsService.execute_skill(skill_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
        
    audit_log("SKILLS", f"/ops/skills/{skill_id}/execute", response.skill_run_id, operation="EXECUTE", actor=_actor_label(auth))
    return response

