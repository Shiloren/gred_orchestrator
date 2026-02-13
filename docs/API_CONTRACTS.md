# GIMO API Contracts

> **Version**: 1.0.0
> **Last Updated**: 2026-02-13
> **Auth**: All endpoints require `Authorization: <ORCH_TOKEN>` header.

---

## Core Endpoints

### `GET /status`
**Response**: `StatusResponse`
```json
{ "version": "1.0.0", "uptime_seconds": 123.45 }
```

### `GET /ui/status`
**Response**: `UiStatusResponse`
```json
{
  "version": "1.0.0",
  "uptime_seconds": 123.45,
  "allowlist_count": 42,
  "last_audit_line": "2026-02-13 ...",
  "service_status": "RUNNING (Dashboard)"
}
```

### `GET /ui/audit?limit=200`
**Query**: `limit` (int, 10-500, default 200)
**Response**:
```json
{ "lines": ["log line 1", "log line 2"] }
```

### `GET /ui/allowlist`
**Response**:
```json
{ "paths": [{ "path": "src/main.py", "type": "file" }] }
```

---

## Repository Management

### `GET /ui/repos`
**Response**:
```json
{
  "root": "C:/repos",
  "active_repo": "C:/repos/my-project",
  "repos": [{ "name": "my-project", "path": "C:/repos/my-project" }]
}
```

### `GET /ui/repos/active`
**Response**:
```json
{ "active_repo": "C:/repos/my-project" }
```

### `POST /ui/repos/open?path=<path>`
**Query**: `path` (string, required)
**Response**:
```json
{ "status": "success", "message": "Repo signaled for opening (server-agnostic)" }
```

### `POST /ui/repos/select?path=<path>`
**Query**: `path` (string, required)
**Response**:
```json
{ "status": "success", "active_repo": "C:/repos/my-project" }
```

### `POST /ui/repos/vitaminize?path=<path>`
**Query**: `path` (string, required)
**Response**: `VitaminizeResponse`
```json
{ "status": "success", "created_files": ["file1", "file2"], "active_repo": "C:/repos/my-project" }
```

---

## Graph & Visualization

### `GET /ui/graph`
**Response**: `GraphResponse`
```json
{
  "nodes": [
    { "id": "api", "type": "orchestrator", "data": { "label": "API Orchestrator", "status": "RUNNING", "trustLevel": "autonomous", "quality": { "score": 98, "alerts": [], "lastCheck": "..." } }, "position": { "x": 400, "y": 200 } }
  ],
  "edges": [
    { "id": "e-tunnel-api", "source": "tunnel", "target": "api", "animated": true }
  ]
}
```

**Node types**: `bridge`, `orchestrator`, `repo`, `cluster`

---

## Security

### `GET /ui/security/events`
**Response**:
```json
{ "panic_mode": false, "events": [] }
```

### `POST /ui/security/resolve?action=clear_panic`
**Query**: `action` (string, only `clear_panic`)
**Response**:
```json
{ "status": "panic cleared" }
```

---

## Service Control

### `GET /ui/service/status`
**Response**: `{ "status": "running" }`

### `POST /ui/service/restart`
**Response**: `{ "status": "restarting" }`

### `POST /ui/service/stop`
**Response**: `{ "status": "stopping" }`

---

## File & Search

### `GET /tree?path=.&max_depth=3`
**Query**: `path` (string, default "."), `max_depth` (int, 1-6, default 3)
**Response**:
```json
{ "files": ["src/main.py", "src/config.py"], "truncated": false }
```

### `GET /file?path=<path>&start_line=1&end_line=500`
**Response**: Plain text file content.

### `GET /search?q=<query>&ext=<ext>`
**Query**: `q` (string, 3-128 chars), `ext` (optional file extension)
**Response**:
```json
{ "results": [{ "file": "src/main.py", "line": 42, "content": "..." }], "truncated": false }
```

### `GET /diff?base=main&head=HEAD`
**Response**: Plain text git diff output.

---

## Quality Monitoring (Phase 4)

### `GET /ui/agent/{agent_id}/quality`
**Response**: `AgentQuality`
```json
{ "score": 98, "alerts": [], "lastCheck": "2026-02-13T..." }
```

---

## Plan System (Phase 5)

### `POST /ui/plan/create`
**Body**: `PlanCreateRequest`
```json
{ "title": "Refactor auth", "task_description": "Extract auth logic into middleware" }
```
**Response**: `Plan`
```json
{
  "id": "uuid",
  "title": "Refactor auth",
  "status": "review",
  "tasks": [
    { "id": "task-1", "title": "Analyze Requirements", "description": "...", "status": "pending", "dependencies": [] },
    { "id": "task-2", "title": "Implementation", "description": "...", "status": "pending", "dependencies": ["task-1"] }
  ],
  "assignments": [{ "agentId": "api", "taskIds": ["task-1", "task-2"] }]
}
```

### `GET /ui/plan/{plan_id}`
**Response**: `Plan`

### `POST /ui/plan/{plan_id}/approve`
**Response**: `{ "status": "approved" }`

### `PATCH /ui/plan/{plan_id}`
**Body**: `PlanUpdateRequest`
```json
{ "title": "New Title", "status": "executing" }
```
**Response**: `Plan`

### `POST /ui/plan/{plan_id}/execute` *(Phase 10 - Parallel Orchestration)*
**Response**: `{ "status": "executing", "parallel_groups": [...] }`

---

## Agent Communication (Phase 6)

### `POST /ui/agent/{agent_id}/message?content=<text>&type=instruction`
**Query**: `content` (string, required), `type` (string, default "instruction")
**Response**: `AgentMessage`
```json
{
  "id": "uuid",
  "from": "orchestrator",
  "agentId": "api",
  "type": "instruction",
  "content": "Hello agent",
  "timestamp": "2026-02-13T..."
}
```

### `GET /ui/agent/{agent_id}/messages`
**Response**: `AgentMessage[]`

---

## Sub-Agent Delegation (Phase 7)

### `POST /ui/agent/{agent_id}/delegate`
**Body**: `DelegationRequest`
```json
{
  "subTaskDescription": "Analyze this module",
  "modelPreference": "llama3",
  "constraints": { "temperature": 0.5, "maxTokens": 1024 }
}
```
**Response**: `SubAgent`
```json
{
  "id": "uuid",
  "parentId": "api",
  "name": "Sub-Agent abc12345",
  "model": "llama3",
  "status": "starting",
  "currentTask": null,
  "config": { "model": "llama3", "temperature": 0.5, "max_tokens": 1024 },
  "result": null
}
```

### `GET /ui/agent/{agent_id}/sub_agents`
**Response**: `SubAgent[]`

### `POST /ui/sub_agent/{sub_agent_id}/terminate`
**Response**: `{ "status": "terminated" }`

### `POST /ui/agent/{agent_id}/delegate_batch` *(Phase 10 - Parallel Orchestration)*
**Body**: `BatchDelegationRequest`
```json
{
  "tasks": [
    { "subTaskDescription": "Task A", "modelPreference": "llama3" },
    { "subTaskDescription": "Task B", "modelPreference": "codellama" }
  ]
}
```
**Response**: `SubAgent[]`

---

## Agent Control (Phase 2)

### `POST /ui/agent/{agent_id}/control?action=<action>&plan_id=<id>`
**Query**: `action` (pause|resume|cancel), `plan_id` (optional)
**Response**: `{ "status": "paused|resumed|cancelled" }`

---

## Trust Management (Phase 3)

### `POST /ui/agent/{agent_id}/trust?trust_level=<level>`
**Query**: `trust_level` (autonomous|supervised|restricted)
**Response**: `{ "status": "updated", "trust_level": "supervised" }`

---

## WebSocket (Phase 8)

### `WS /ws`

**Connection**: `ws://localhost:9325/ws`

**Event types** (server → client):
```json
{ "type": "plan_update", "plan_id": "uuid", "payload": { ... } }
{ "type": "chat_message", "agent_id": "api", "payload": { ... } }
{ "type": "sub_agent_update", "agent_id": "uuid", "parent_id": "api", "payload": { ... } }
{ "type": "quality_alert", "agent_id": "api", "payload": { "score": 45, "alerts": ["repetition"] } }
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200  | Success |
| 400  | Bad request / invalid params |
| 401  | Unauthorized (missing/invalid token) |
| 404  | Resource not found |
| 413  | File too large (>5MB) |
| 429  | Rate limited |
| 500  | Server error |

---

## Models Reference

See `tools/repo_orchestrator/models.py` for Pydantic model definitions.
See `tools/orchestrator_ui/src/types.ts` for TypeScript interface definitions.
