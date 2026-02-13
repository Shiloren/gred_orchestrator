import time
import os
from pathlib import Path
from typing import Optional, Dict, List
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from tools.repo_orchestrator.config import (
    REPO_ROOT_DIR,
    ALLOWLIST_REQUIRE,
    MAX_LINES,
)
from tools.repo_orchestrator.security import (
    verify_token,
    validate_path,
    audit_log,
    check_rate_limit,
    load_security_db,
    save_security_db,
    load_repo_registry,
    save_repo_registry,
    get_active_repo_dir,
    get_allowed_paths,
    serialize_allowlist,
)
from tools.repo_orchestrator.services.system_service import SystemService
from tools.repo_orchestrator.services.repo_service import RepoService
from tools.repo_orchestrator.services.file_service import FileService
from tools.repo_orchestrator.models import (
    GraphResponse,
    GraphNode,
    GraphEdge,
    RepoEntry,
    VitaminizeResponse,
    StatusResponse,
    UiStatusResponse,
    NodeData,
    Plan,
    PlanCreateRequest,
    PlanUpdateRequest,
    AgentMessage,
    SubAgent,
    DelegationRequest,
)
from tools.repo_orchestrator.services.sub_agent_manager import SubAgentManager


# Constants for error messages
ERR_REPO_NOT_FOUND = "Repo no encontrado"
ERR_REPO_OUT_OF_BASE = "Repo fuera de la base permitida"
ERR_PLAN_NOT_FOUND = "Plan not found"

# Route Handlers

def get_status_handler(request: Request, token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    return {
        "version": "1.0.0",
        "uptime_seconds": time.time() - request.app.state.start_time
    }

def get_ui_status_handler(request: Request, token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    audit_lines = FileService.tail_audit_lines(limit=1)
    base_dir = get_active_repo_dir()
    allowed_paths = get_allowed_paths(base_dir) if ALLOWLIST_REQUIRE else {}
    
    is_healthy = base_dir.exists() and os.access(base_dir, os.R_OK)
    status_str = "RUNNING" if is_healthy else "DEGRADED"
    
    user_agent = request.headers.get("User-Agent", "").lower()
    agent_label = "ChatGPT" if "openai" in user_agent or "gpt" in user_agent else "Dashboard"
    
    return {
        "version": "1.0.0",
        "uptime_seconds": time.time() - request.app.state.start_time,
        "allowlist_count": len(allowed_paths),
        "last_audit_line": audit_lines[-1] if audit_lines else None,
        "service_status": f"{status_str} ({agent_label})",
    }

def get_ui_audit_handler(limit: int = Query(200, ge=10, le=500), token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    return {
        "lines": FileService.tail_audit_lines(limit=limit),
    }

def get_ui_allowlist_handler(token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    base_dir = get_active_repo_dir()
    allowed_paths = get_allowed_paths(base_dir)
    items = serialize_allowlist(allowed_paths)
    for item in items:
        try:
            item["path"] = str(Path(item["path"]).relative_to(base_dir))
        except Exception:
            continue
    return {"paths": items}

def list_repos_handler(token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    repos = RepoService.list_repos()
    registry = RepoService.ensure_repo_registry(repos)
    active_repo = registry.get("active_repo")
    return {
        "root": str(REPO_ROOT_DIR),
        "active_repo": active_repo,
        "repos": [r.__dict__ for r in repos],
    }

def get_active_repo_handler(token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    registry = load_repo_registry()
    return {"active_repo": registry.get("active_repo")}

def open_repo_handler(path: str = Query(...), token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    repo_path = Path(path).resolve()
    if not str(repo_path).startswith(str(REPO_ROOT_DIR)):
        raise HTTPException(status_code=400, detail=ERR_REPO_OUT_OF_BASE)
    if not repo_path.exists():
        raise HTTPException(status_code=404, detail=ERR_REPO_NOT_FOUND)
    
    audit_log("UI", "OPEN_REPO", str(repo_path), actor=token)
    return {"status": "success", "message": "Repo signaled for opening (server-agnostic)"}

def select_repo_handler(path: str = Query(...), token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    repo_path = Path(path).resolve()
    if not str(repo_path).startswith(str(REPO_ROOT_DIR)):
        raise HTTPException(status_code=400, detail=ERR_REPO_OUT_OF_BASE)
    if not repo_path.exists():
        raise HTTPException(status_code=404, detail=ERR_REPO_NOT_FOUND)
        
    registry = load_repo_registry()
    registry["active_repo"] = str(repo_path)
    save_repo_registry(registry)
    
    audit_log("REPO", "SELECT", str(repo_path), actor=token)
    return {"status": "success", "active_repo": str(repo_path)}

def get_security_events_handler(token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    db = load_security_db()
    return {
        "panic_mode": db.get("panic_mode", False),
        "events": db.get("recent_events", [])
    }

def resolve_security_handler(action: str = Query(...), token: str = Depends(verify_token)):
    if action != "clear_panic":
        raise HTTPException(status_code=400, detail="Invalid action")
    
    db = load_security_db()
    db["panic_mode"] = False
    for event in db.get("recent_events", []):
        event["resolved"] = True
    save_security_db(db)
    
    audit_log("SECURITY", "PANIC_CLEARED", "SUCCESS", actor=token)
    return {"status": "panic cleared"}

def get_service_status_handler(token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    return {"status": SystemService.get_status()}

def restart_service_handler(token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    success = SystemService.restart(actor=token)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to restart service")
    return {"status": "restarting"}

def stop_service_handler(token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    success = SystemService.stop(actor=token)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to stop service")
    return {"status": "stopping"}

def vitaminize_repo_handler(path: str = Query(...), token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    repo_path = Path(path).resolve()
    if not str(repo_path).startswith(str(REPO_ROOT_DIR)):
        raise HTTPException(status_code=400, detail=ERR_REPO_OUT_OF_BASE)
    if not repo_path.exists():
        raise HTTPException(status_code=404, detail=ERR_REPO_NOT_FOUND)
        
    created = RepoService.vitaminize_repo(repo_path)
    
    registry = load_repo_registry()
    registry["active_repo"] = str(repo_path)
    save_repo_registry(registry)
    
    audit_log("REPO", "VITAMINIZE", str(repo_path), actor=token)
    return {
        "status": "success",
        "created_files": created,
        "active_repo": str(repo_path)
    }

def get_ui_graph_handler(token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    """Generate the graph structure for the UI."""
    from tools.repo_orchestrator.security import load_repo_registry
    from tools.repo_orchestrator.services.quality_service import QualityService
    registry = load_repo_registry()
    active_repo_path = registry.get("active_repo")
    
    from tools.repo_orchestrator.services.sub_agent_manager import SubAgentManager
    api_sub_agents = SubAgentManager.get_sub_agents("api")
    api_node_type = "cluster" if api_sub_agents else "orchestrator"
    
    # Base nodes
    nodes = [
        GraphNode(
            id="tunnel", 
            type="bridge", 
            data=NodeData(
                label="Cloudflare Tunnel", 
                status="ACTIVE",
                quality=QualityService.get_agent_quality("tunnel")
            ), 
            position={"x": 100, "y": 200}
        ),
        GraphNode(
            id="api", 
            type=api_node_type,
            data=NodeData(
                label="API Orchestrator", 
                status="RUNNING",
                trustLevel="autonomous",
                quality=QualityService.get_agent_quality("api"),
                subAgents=api_sub_agents
            ), 
            position={"x": 400, "y": 200}
        ),
    ]
    edges = [
        GraphEdge(id="e-tunnel-api", source="tunnel", target="api", animated=True)
    ]
    
    if active_repo_path:
        repo_name = Path(active_repo_path).name
        nodes.append(GraphNode(
            id="active-repo", 
            type="repo", 
            data=NodeData(label=repo_name, path=active_repo_path), 
            position={"x": 700, "y": 200}
        ))
        edges.append(GraphEdge(id="e-api-repo", source="api", target="active-repo", animated=True))
    
    return {"nodes": nodes, "edges": edges}

async def get_tree_handler(path: str = ".", max_depth: int = Query(3, le=6), token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    base_dir = get_active_repo_dir()
    target = validate_path(path, base_dir)
    if not target.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory.")

    if ALLOWLIST_REQUIRE:
        allowed_paths = get_allowed_paths(base_dir)
        files = [str(p.relative_to(target)) for p in allowed_paths if str(p).startswith(str(target))]
        return {"files": sorted(set(files)), "truncated": False}
    
    import asyncio
    loop = asyncio.get_running_loop()
    files = await loop.run_in_executor(None, RepoService.walk_tree, target, max_depth)
    return {"files": files, "truncated": len(files) >= 2000}

def get_file_handler(path: str, start_line: int = Query(1, ge=1), end_line: int = Query(MAX_LINES, ge=1), token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    base_dir = get_active_repo_dir()
    target = validate_path(path, base_dir)
    if not target.is_file(): 
        raise HTTPException(status_code=400, detail="Path is not a file.")
    if target.stat().st_size > 5 * 1024 * 1024: 
        raise HTTPException(status_code=413, detail="File too large.")

    try:
        content, _ = FileService.get_file_content(target, start_line, end_line, token)
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def search_handler(q: str = Query(..., min_length=3, max_length=128), ext: Optional[str] = None, token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    base_dir = get_active_repo_dir()
    import asyncio
    loop = asyncio.get_running_loop()
    hits = await loop.run_in_executor(None, RepoService.perform_search, base_dir, q, ext)
    return {"results": hits, "truncated": len(hits) >= 50}

def get_diff_handler(base: str = "main", head: str = "HEAD", token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    from tools.repo_orchestrator.services.git_service import GitService
    from tools.repo_orchestrator.security import redact_sensitive_data
    from tools.repo_orchestrator.config import MAX_BYTES
    base_dir = get_active_repo_dir()
    try:
        stdout = GitService.get_diff(base_dir, base, head)
        content = redact_sensitive_data(stdout)
        if len(content.encode('utf-8')) > MAX_BYTES: 
            content = content[:MAX_BYTES] + "\n# ... [TRUNCATED] ...\n"
        return content
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def get_agent_quality_handler(agent_id: str, token: str = Depends(verify_token), rl: None = Depends(check_rate_limit)):
    from tools.repo_orchestrator.services.quality_service import QualityService
    return QualityService.get_agent_quality(agent_id)

def create_plan_handler(req: PlanCreateRequest, token: str = Depends(verify_token)):
    from tools.repo_orchestrator.services.plan_service import PlanService
    plan = PlanService.create_plan(req.title, req.task_description)
    audit_log("PLAN", "CREATE", plan.id, actor=token)
    return plan

def get_plan_handler(plan_id: str, token: str = Depends(verify_token)):
    from tools.repo_orchestrator.services.plan_service import PlanService
    plan = PlanService.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=ERR_PLAN_NOT_FOUND)
    return plan

def approve_plan_handler(plan_id: str, token: str = Depends(verify_token)):
    from tools.repo_orchestrator.services.plan_service import PlanService
    if not PlanService.approve_plan(plan_id):
        raise HTTPException(status_code=404, detail=ERR_PLAN_NOT_FOUND)
    audit_log("PLAN", "APPROVE", plan_id, actor=token)
    return {"status": "approved"}

def update_plan_handler(plan_id: str, updates: PlanUpdateRequest, token: str = Depends(verify_token)):
    from tools.repo_orchestrator.services.plan_service import PlanService
    plan = PlanService.update_plan(plan_id, updates)
    if not plan:
        raise HTTPException(status_code=404, detail=ERR_PLAN_NOT_FOUND)
    audit_log("PLAN", "UPDATE", plan_id, actor=token)
    return plan

def send_agent_message_handler(agent_id: str, content: str = Query(...), type: str = Query("instruction"), token: str = Depends(verify_token)):
    from tools.repo_orchestrator.services.comms_service import CommsService
    # When sending via UI, the user acts as the 'orchestrator'
    msg = CommsService.send_message(agent_id, from_role="orchestrator", msg_type=type, content=content)
    audit_log("COMMS", "SEND_MESSAGE", f"{agent_id}: {content[:20]}...", actor=token)
    return msg

def get_agent_messages_handler(agent_id: str, token: str = Depends(verify_token)):
    from tools.repo_orchestrator.services.comms_service import CommsService
    return CommsService.get_messages(agent_id)

def create_sub_agent_handler(agent_id: str, req: DelegationRequest, token: str = Depends(verify_token)):
    agent = SubAgentManager.create_sub_agent(agent_id, req)
    audit_log("SUB_AGENT", "CREATE", f"{agent_id} -> {agent.id}", actor=token)
    return agent

def get_sub_agents_handler(agent_id: str, token: str = Depends(verify_token)):
    return SubAgentManager.get_sub_agents(agent_id)

def terminate_sub_agent_handler(sub_agent_id: str, token: str = Depends(verify_token)):
    SubAgentManager.terminate_sub_agent(sub_agent_id)
    audit_log("SUB_AGENT", "TERMINATE", sub_agent_id, actor=token)
    return {"status": "terminated"}

def register_routes(app: FastAPI):
    app.get("/status", response_model=StatusResponse)(get_status_handler)
    app.get("/ui/status", response_model=UiStatusResponse)(get_ui_status_handler)
    app.get("/ui/audit")(get_ui_audit_handler)
    app.get("/ui/allowlist")(get_ui_allowlist_handler)
    app.get("/ui/repos")(list_repos_handler)
    app.get("/ui/repos/active")(get_active_repo_handler)
    app.post("/ui/repos/open")(open_repo_handler)
    app.post("/ui/repos/select")(select_repo_handler)
    app.get("/ui/security/events")(get_security_events_handler)
    app.post("/ui/security/resolve")(resolve_security_handler)
    app.get("/ui/service/status")(get_service_status_handler)
    app.post("/ui/service/restart")(restart_service_handler)
    app.post("/ui/service/stop")(stop_service_handler)
    app.post("/ui/repos/vitaminize", response_model=VitaminizeResponse)(vitaminize_repo_handler)
    app.get("/ui/graph", response_model=GraphResponse)(get_ui_graph_handler)
    app.get("/ui/agent/{agent_id}/quality")(get_agent_quality_handler)
    app.post("/ui/plan/create", response_model=Plan)(create_plan_handler)
    app.get("/ui/plan/{plan_id}", response_model=Plan)(get_plan_handler)
    app.post("/ui/plan/{plan_id}/approve")(approve_plan_handler)
    app.patch("/ui/plan/{plan_id}", response_model=Plan)(update_plan_handler)
    app.post("/ui/agent/{agent_id}/message", response_model=AgentMessage)(send_agent_message_handler)
    app.get("/ui/agent/{agent_id}/messages", response_model=List[AgentMessage])(get_agent_messages_handler)
    app.post("/ui/agent/{agent_id}/delegate", response_model=SubAgent)(create_sub_agent_handler)
    app.get("/ui/agent/{agent_id}/sub_agents", response_model=List[SubAgent])(get_sub_agents_handler)
    app.post("/ui/sub_agent/{sub_agent_id}/terminate")(terminate_sub_agent_handler)
    app.get("/tree")(get_tree_handler)

    app.get("/file", response_class=PlainTextResponse)(get_file_handler)
    app.get("/search")(search_handler)
    app.get("/diff", response_class=PlainTextResponse)(get_diff_handler)
