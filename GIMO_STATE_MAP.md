# GIMO - Mapa de Estado Real
> Generado 2026-02-23 por lectura exhaustiva de cada archivo del repositorio.
> Cada afirmacion tiene referencia al archivo y linea donde se verifico.

---

## RESUMEN EJECUTIVO

| Metrica | Valor |
|---------|-------|
| Archivos de servicio | 45 |
| Endpoints REST | ~95 |
| MCP Tools | 14 de ~95 posibles |
| Hooks frontend | 14 |
| Hooks con backend real | 10 |
| Hooks llamando al vacio | 4 (13+ endpoints fantasma) |
| Bugs bloqueantes encontrados | 3 |
| Servicios legacy sin uso | 4 |

---

## BUG 1 - CRITICO: gimo_run_task() nunca genera plan

**Archivo**: `tools/gimo_server/mcp_server.py:389-396`

Cuando un IDE llama `gimo_run_task("escribe hello world")`:
1. Crea draft con `content=None` (vacio)
2. Lo aprueba inmediatamente (sigue vacio)
3. Crea run con status "pending"
4. RunWorker (5s despues) lo ejecuta con prompt vago:
   ```
   Execute the following approved operation:
   --- PROMPT ---
   escribe hello world
   --- CONTENT ---
   (vacio)
   ```
5. El LLM recibe un prompt sin plan, sin contexto, sin instrucciones

**Existe** `gimo_propose_structured_plan()` en linea 288 que SI genera planes con LLM, pero `gimo_run_task()` NO lo llama.

**Impacto**: El flujo principal de ejecucion via MCP esta roto. Un agente externo no puede ejecutar tareas reales.

---

## BUG 2 - CRITICO: gics_service.py no importa uuid ni os

**Archivo**: `tools/gimo_server/services/gics_service.py`

- Linea 164: `uuid.uuid4()` usado pero `import uuid` no existe
- Linea 41+: `os.environ`, `os.name` usado pero `import os` no existe

**Impacto**: `send_command()` crashea con `NameError` al primer uso. `start_daemon()` tambien crashea. **GICS no puede funcionar.**

---

## BUG 3 - MENOR: custom_plan_router.py sin import asyncio

**Archivo**: `tools/gimo_server/routers/ops/custom_plan_router.py:94`

`asyncio.create_task()` se llama sin `import asyncio`.

**Impacto**: Ejecutar custom plans via REST crashea.

---

## CAPA 0: STORAGE

### Situacion Real
SQLite es la UNICA fuente de verdad funcional. GICS es secundario ("best effort").

| Storage | Metodos SQLite | Metodos GICS | Patron |
|---------|---------------|--------------|--------|
| cost_storage | 15 (todas las queries) | 1 (solo write) | GICS es write-only, nunca se lee |
| trust_storage | 8 | 5 | GICS fallback en reads, pero SQLite es primario |
| eval_storage | 6 | 6 | GICS fallback en reads |
| workflow_storage | 4 | 4 | GICS primero en reads, fallback SQLite |
| config_storage | 3 | 2 | GICS primero en reads |

**DB Path**: `.orch_data/ops/gimo_ops.db` (SQLite WAL mode)
**GICS Daemon**: `vendor/gics/dist/src/daemon/server.js` (Node.js)
**GICS Socket**: `.orch_data/ops/gics.sock` (Unix) o `\\.\pipe\gics_sock` (Windows)

### Decision Pendiente del Usuario
El usuario quiere eliminar SQLite y usar solo GICS. Esto requiere:
1. Arreglar los bugs de import en gics_service.py
2. Migrar las 15 queries de agregacion de cost_storage a GICS (getInsight, getInsights, getForecast, etc.)
3. Validar que el daemon GICS soporta todas las operaciones necesarias

---

## CAPA 1: SERVICIOS (45 archivos)

### Nucleo Funcional (FUNCIONAN)
| Servicio | Lineas | Funcion | Storage |
|----------|--------|---------|---------|
| graph_engine.py | ~1380 | Ejecucion de workflows con budget/cascade/retry | StorageService |
| ops_service.py | ~400 | CRUD de drafts/approved/runs + config | Filesystem JSON + GICS |
| provider_service.py | ~430 | Gestion de proveedores + generacion LLM | Filesystem JSON |
| run_worker.py | ~334 | Background worker que ejecuta runs | OpsService |
| cost_service.py | ~150 | Pricing registry + calculo de costos | model_pricing.json |
| trust_engine.py | ~250 | Scoring de confianza + circuit breaker | StorageService |
| storage_service.py | ~100 | Facade de 5 sub-storages | SQLite + GICS |
| model_router_service.py | ~300 | Seleccion inteligente de modelo (ROI/eco/budget) | StorageService |
| cascade_service.py | ~150 | Escalado de modelo por calidad | ProviderService |
| notification_service.py | ~50 | Broker SSE para eventos real-time | In-memory |

### Servicios Operativos (FUNCIONAN pero poco usados)
| Servicio | Funcion | Storage |
|----------|---------|---------|
| conversation_service.py | Threads de conversacion | Filesystem JSON |
| custom_plan_service.py | Planes custom con grafos | Filesystem JSON |
| skills_service.py | Templates de skills predefinidos | Filesystem JSON |
| policy_service.py | Reglas allow/deny/review por tool | Filesystem JSON |
| budget_forecast_service.py | Prediccion de gasto | StorageService (SQLite) |
| cost_predictor.py | Estimacion de costo pre-ejecucion | StorageService + CostService |
| evals_service.py | Regression testing de workflows | GraphEngine |
| quality_service.py | Scoring heuristico de output LLM | In-memory |
| confidence_service.py | Trust + LLM para detectar riesgo | TrustEngine + ProviderService |
| observability_service.py | OpenTelemetry tracing + metrics | In-memory spans |
| institutional_memory_service.py | Sugerencias de politica por historial | StorageService |
| tool_registry_service.py | Allowlist fail-closed de tools + MCP sync | Filesystem JSON |
| provider_catalog_service.py | ~770 lineas, catalogo de modelos/install | In-memory cache |
| sub_agent_manager.py | Spawn de sub-agentes con worktrees git | In-memory + Git |
| file_service.py | Lectura/escritura segura con snapshots | Filesystem |
| repo_service.py | Discovery de repos + file tree + search | Filesystem |
| git_service.py | Diff, worktrees, list repos | Git CLI |

### Servicios Legacy (REEMPLAZADOS, candidatos a eliminar)
| Servicio | Reemplazado por |
|----------|-----------------|
| model_router.py | model_router_service.py |
| model_service.py | provider_service.py |
| plan_service.py | ops_service.py |
| registry_service.py | repo_service.py + ops_service.py |
| provider_registry.py | provider_service.py |
| comms_service.py | conversation_service.py + notification_service.py |

---

## CAPA 2: ENDPOINTS REST (~95 total)

### Auth (3 endpoints) - FUNCIONAN
```
POST /auth/login          → session_store.create()
POST /auth/logout         → session_store.revoke()
GET  /auth/check          → session_store.validate()
```

### Core UI (25+ endpoints) - FUNCIONAN
```
GET  /status              → version + uptime
GET  /tree                → RepoService.walk_tree()
GET  /file                → FileService.get_file_content()
GET  /search              → RepoService.perform_search()
GET  /diff                → GitService.get_diff()
GET  /ui/status           → FileService.tail_audit_lines()
GET  /ui/audit            → FileService.tail_audit_lines()
GET  /ui/repos            → RepoService.list_repos()
POST /ui/repos/select     → save_repo_registry()
GET  /ui/graph            → build_graph_from_ops_plan()
POST /ui/plan/create      → ProviderService + OpsService
GET  /ui/security/events  → threat_engine.snapshot()
POST /ui/security/resolve → threat_engine.clear_all()
GET  /ui/service/status   → SystemService.get_status()
POST /ui/service/restart  → SystemService.restart()
POST /ui/service/stop     → SystemService.stop()
```

### OPS Plans & Drafts (8 endpoints) - FUNCIONAN
```
GET  /ops/plan                         → OpsService.get_plan()
PUT  /ops/plan                         → OpsService.set_plan()
GET  /ops/drafts                       → OpsService.list_drafts()
POST /ops/drafts                       → OpsService.create_draft()
GET  /ops/drafts/{id}                  → OpsService.get_draft()
PUT  /ops/drafts/{id}                  → OpsService.update_draft()
POST /ops/drafts/{id}/reject           → OpsService.reject_draft()
POST /ops/generate?prompt=             → CognitiveService + ProviderService
```

### OPS Runs & Workflows (10 endpoints) - FUNCIONAN
```
POST /ops/drafts/{id}/approve          → OpsService.approve_draft()
GET  /ops/approved                     → OpsService.list_approved()
POST /ops/runs                         → OpsService.create_run()
GET  /ops/runs                         → OpsService.list_runs()
GET  /ops/runs/{id}                    → OpsService.get_run()
POST /ops/runs/{id}/cancel             → OpsService.update_run_status()
POST /ops/workflows/execute            → GraphEngine()
GET  /ops/workflows/{id}/checkpoints   → StorageService.list_checkpoints()
POST /ops/workflows/{id}/resume        → GraphEngine.resume_from_checkpoint()
```

### OPS Config & Providers (21 endpoints) - FUNCIONAN
```
GET  /ops/config                       → OpsService.get_config()
PUT  /ops/config                       → OpsService.set_config()
GET  /ops/provider                     → ProviderService.get_public_config()
PUT  /ops/provider                     → ProviderService.set_config()
GET  /ops/provider/capabilities        → capabilities matrix
GET  /ops/connectors                   → list CLI + API connectors
GET  /ops/connectors/{type}/models     → catalog de modelos
POST /ops/connectors/{type}/models/install → instalar modelo
POST /ops/connectors/{type}/validate   → validar credenciales
GET  /ops/config/mcp                   → MCP servers configurados
POST /ops/config/mcp/sync             → descubrir tools de MCP server
GET  /ops/tool-registry               → tools registrados
PUT  /ops/tool-registry/{name}        → actualizar tool
DELETE /ops/tool-registry/{name}      → eliminar tool
GET  /ops/policy                      → reglas de politica
PUT  /ops/policy                      → actualizar reglas
POST /ops/policy/decide               → evaluar decision
POST /ops/model/recommend             → recomendacion de modelo
```

### OPS Mastery/Cost (8 endpoints) - FUNCIONAN (dependen de SQLite)
```
GET  /ops/mastery/status               → metricas de mastery
GET  /ops/mastery/analytics?days=      → costos diarios, por modelo, ROI
GET  /ops/mastery/forecast             → prediccion de gasto
GET  /ops/mastery/recommendations      → tips de optimizacion
POST /ops/mastery/predict              → predecir costo de workflow
GET  /ops/mastery/config/economy       → config de economia
POST /ops/mastery/config/economy       → actualizar economia
POST /ops/mastery/recommend            → best vs eco model
```

### OPS Trust (6 endpoints) - FUNCIONAN
```
POST /ops/trust/query                  → TrustEngine.query_dimension()
GET  /ops/trust/dashboard              → TrustEngine.dashboard()
GET  /ops/trust/suggestions            → InstitutionalMemoryService
GET  /ops/trust/circuit-breaker/{key}  → config circuit breaker
PUT  /ops/trust/circuit-breaker/{key}  → actualizar circuit breaker
POST /ops/trust/reset                  → reset threat levels
```

### OPS Evals (6 endpoints) - FUNCIONAN
```
POST /ops/evals/run                    → EvalsService.run_regression()
GET  /ops/evals/runs                   → list eval runs
GET  /ops/evals/runs/{id}             → detalle eval run
POST /ops/evals/datasets              → crear dataset
GET  /ops/evals/datasets              → listar datasets
GET  /ops/evals/datasets/{id}         → detalle dataset
```

### OPS Observability (3 endpoints) - FUNCIONAN
```
GET  /ops/observability/metrics        → ObservabilityService.get_metrics()
GET  /ops/observability/traces         → list traces
GET  /ops/observability/traces/{id}    → trace detail
```

### OPS Skills (6 endpoints) - FUNCIONAN
```
GET  /ops/skills                       → SkillsService.list_skills()
GET  /ops/skills/{id}                  → get skill
POST /ops/skills                       → create skill
PUT  /ops/skills/{id}                  → update skill
DELETE /ops/skills/{id}                → delete skill
POST /ops/skills/{id}/trigger          → trigger skill como draft
```

### OPS Custom Plans (6 endpoints) - BUG (missing import asyncio)
```
GET  /ops/custom-plans                 → CustomPlanService.list_plans()
GET  /ops/custom-plans/{id}            → get plan
POST /ops/custom-plans                 → create plan
PUT  /ops/custom-plans/{id}            → update plan
DELETE /ops/custom-plans/{id}          → delete plan
POST /ops/custom-plans/{id}/execute    → CRASHEA (missing import asyncio)
```

### OPS Conversations (8 endpoints) - FUNCIONAN
```
GET  /ops/threads                      → ConversationService.list_threads()
POST /ops/threads                      → create thread
GET  /ops/threads/{id}                 → get thread
POST /ops/threads/{id}/turns           → add turn
POST /ops/threads/{id}/turns/{tid}/items → add item
PATCH /ops/threads/{id}/turns/{tid}/items/{iid} → update item
POST /ops/threads/{id}/fork            → fork thread
POST /ops/threads/{id}/messages        → post message
```

### SSE Stream (1 endpoint) - FUNCIONA
```
GET  /ops/stream                       → NotificationService.subscribe()
```

---

## CAPA 3: MCP (14 tools de ~95 posibles)

### Tools Expuestos
```
gimo_get_status            → health check (import directo, no REST)
gimo_wake_ollama           → arrancar Ollama
gimo_start_engine          → arrancar backend + frontend
gimo_get_server_info       → diagnosticos
gimo_reload_worker         → hot-reload RunWorker
gimo_list_agents           → listar sub-agentes
gimo_propose_structured_plan → generar plan via LLM
gimo_get_plan_graph        → Mermaid graph
gimo_create_draft          → crear draft (no genera contenido)
gimo_get_draft             → obtener draft
gimo_approve_draft         → aprobar + crear run
gimo_run_task              → ROTO (draft vacio)
gimo_get_task_status       → estado de run
gimo_resolve_handover      → resolver review humano
gimo_spawn_subagent        → crear sub-agente
```

### Tools que FALTAN (los 81 endpoints no expuestos)
Todo lo de Mastery, Trust, Evals, Observability, Providers, Config, Skills, Custom Plans, Conversations, Policy, Tool Registry, Repos/Files, Audit.

### Problema Arquitectural
Los 14 tools importan servicios directamente en vez de llamar la REST API. Cuando corre como subprocess (stdio para IDEs), tiene su propio proceso Python con instancias separadas = estado inconsistente.

---

## CAPA 4: FRONTEND

### Hooks que FUNCIONAN (backend existe)
| Hook | Endpoints | Estado |
|------|-----------|--------|
| useAuditLog | GET /ui/audit | OK |
| useEvalsService | 5 endpoints /ops/evals/* | OK |
| useMasteryService | 6 endpoints /ops/mastery/* | OK |
| useObservabilityService | 3 endpoints /ops/observability/* | OK |
| useOpsService | 15 endpoints /ops/* | OK |
| useProviders | 10+ endpoints /ops/provider, /ops/connectors/* | OK |
| useRealtimeChannel | ws://hostname:9325/ws | OK |
| useRepoService | 3 endpoints /ui/repos/* | OK (1 path mismatch: bootstrap vs vitaminize) |
| useSecurityService | 4 endpoints /ui/security/*, /ops/trust/* | OK |
| useSystemService | 3 endpoints /ui/service/* | OK |

### Hooks que LLAMAN AL VACIO (backend NO existe)
| Hook | Endpoints Fantasma | Impacto |
|------|-------------------|---------|
| useAgentComms | GET/POST /ui/agent/{id}/messages, /message | No hay chat con agentes |
| useAgentControl | POST /ui/agent/{id}/control?action=pause/resume/cancel | No se pueden controlar agentes |
| useAgentQuality | GET /ui/agent/{id}/quality | No hay metricas de agente |
| useSubAgents | GET/POST /ui/agent/{id}/sub_agents, /delegate, /terminate | No hay delegacion |

### Hook con Path Mismatch
| Hook | Espera | Backend Tiene |
|------|--------|---------------|
| usePlanEngine | GET /ui/plan/{id} | No existe (usar /ops/drafts/{id}) |
| usePlanEngine | POST /ui/plan/{id}/approve | No existe (usar /ops/drafts/{id}/approve) |
| usePlanEngine | PATCH /ui/plan/{id} | No existe (usar PUT /ops/drafts/{id}) |

---

## PRIORIDADES SUGERIDAS

### P0 - Sin esto nada funciona
1. **Arreglar gics_service.py** - Agregar `import uuid` e `import os`
2. **Arreglar gimo_run_task()** - Conectar generacion de plan antes de aprobar
3. **Arreglar custom_plan_router.py** - Agregar `import asyncio`

### P1 - Hacer el MCP usable
4. Exponer los ~80 endpoints faltantes via MCP bridge (httpx → REST API)
5. Arreglar los 4 hooks frontend que llaman al vacio (o eliminarlos si no son MVP)
6. Arreglar path mismatch de usePlanEngine

### P2 - Migrar a GICS
7. Migrar las 15 queries de agregacion de cost_storage de SQLite a GICS
8. Hacer lo mismo para trust, eval, workflow, config storages
9. Eliminar dependencia de SQLite

### P3 - Limpieza
10. Eliminar servicios legacy (model_router.py, model_service.py, plan_service.py, registry_service.py, provider_registry.py, comms_service.py)
11. Actualizar setup_mcp.py para soportar Claude Desktop, Windsurf, Cline, Continue, JetBrains
