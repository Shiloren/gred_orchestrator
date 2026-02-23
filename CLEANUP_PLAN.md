# Plan de Orden - GIMO

## Objetivo
Dejar el proyecto en un estado donde cualquier IA (incluso modelos baratos) pueda entenderlo y operar sobre el sin perderse. Reducir ruido, documentar lo real, eliminar lo muerto.

---

## FASE 1: Eliminar Ruido (30 min)

### 1.1 Borrar servicios legacy muertos
Estos archivos tienen reemplazos modernos y no se usan en ningun router:

| Archivo a borrar | Reemplazado por |
|-----------------|-----------------|
| services/model_router.py | model_router_service.py |
| services/model_service.py | provider_service.py |
| services/plan_service.py | ops_service.py |
| services/registry_service.py | repo_service.py + ops_service.py |
| services/provider_registry.py | provider_service.py |
| services/comms_service.py | conversation_service.py + notification_service.py |

**Validacion**: Buscar imports de estos en routers/. Si algun router los importa, NO borrar ese.

### 1.2 Arreglar el ultimo bug conocido
- `routers/ops/custom_plan_router.py` linea 1: agregar `import asyncio`

### 1.3 Limpiar flush() en gics_service.py
El comentario de 10 lineas sobre flush puede ser un simple docstring:
```python
def flush(self) -> Any:
    """No-op: GICS daemon auto-flushes. Manual flush not exposed via JSON-RPC."""
    pass
```

---

## FASE 2: Arquitectura Self-Documenting (1 hora)

### 2.1 Crear ARCHITECTURE.md en la raiz
Un solo documento que cualquier IA pueda leer para entender todo GIMO:

```
# Arquitectura GIMO

## Capas
0. GICS Daemon (Node.js) - Storage distribuido propietario
1. Services (Python) - 30+ servicios, GraphEngine es el nucleo
2. REST API (FastAPI) - ~95 endpoints en /ops/*, /ui/*, /auth/*
3. MCP Server (FastMCP) - 14 tools para IDEs via stdio/SSE
4. Frontend (React+Vite) - Dashboard en puerto 5173

## Flujo Principal
IDE → MCP tool → OpsService → RunWorker → ProviderService → LLM

## Directorios Clave
tools/gimo_server/services/     → Logica de negocio
tools/gimo_server/routers/ops/  → Endpoints REST
tools/gimo_server/mcp_server.py → MCP tools
tools/orchestrator_ui/src/      → Frontend React
vendor/gics/                    → Daemon GICS (Node.js)
.orch_data/ops/                 → Datos runtime (drafts, runs, config)
```

### 2.2 Agregar docstrings de 1 linea a cada servicio que no lo tenga
No prosa - solo una linea que diga que hace:
```python
class GraphEngine:
    """Ejecuta workflows multi-nodo con budget, cascade, retry y checkpointing."""
```

### 2.3 Crear indice de hooks en el frontend
Archivo `tools/orchestrator_ui/src/hooks/README.md`:
```
# Hooks

## Conectados (backend existe)
- useOpsService: drafts, runs, config
- useMasteryService: costos, economia
- useProviders: proveedores, modelos, connectors
- useEvalsService: evaluaciones
- useSecurityService: trust, circuit breaker
- useObservabilityService: metrics, traces
- useAuditLog: audit log
- useRepoService: repos
- useSystemService: servicio Windows
- useRealtimeChannel: WebSocket SSE

## Sin Backend (NO USAR hasta implementar)
- useAgentComms: chat con agentes (endpoints no existen)
- useAgentControl: control de agentes (endpoints no existen)
- useAgentQuality: metricas de agente (endpoints no existen)
- useSubAgents: delegacion (endpoints no existen)

## Path Mismatch (necesita arreglo)
- usePlanEngine: usa /ui/plan/* pero backend tiene /ops/drafts/*
```

---

## FASE 3: Hacer el MCP Completo (2-3 horas)

### 3.1 Crear el MCP Bridge (paquete nuevo)
En vez de agregar 80 funciones a mcp_server.py, crear:
```
tools/gimo_server/mcp_bridge/
    __init__.py
    manifest.py     → Lista declarativa de tools (nombre, metodo, path, params)
    bridge.py       → Funcion generica que traduce MCP → HTTP via httpx
    registrar.py    → Loop que registra tools en FastMCP desde manifest
    resources.py    → 8 MCP Resources (config, metrics, audit)
    prompts.py      → 5 MCP Prompts (workflows guiados)
    server.py       → Entry point
```

**Resultado**: ~67 tools MCP cubriendo TODOS los endpoints, sin duplicar logica.

### 3.2 Actualizar setup_mcp.py
Agregar soporte para:
- Claude Desktop (Windows + Mac)
- Windsurf
- Cline
- Continue
- JetBrains

---

## FASE 4: Frontend Honesto (2-3 horas) - COMPLETED

### 4.1 Desactivar hooks sin backend - DONE
En cada hook sin backend, agregar al inicio:
```typescript
console.warn('useAgentComms: backend endpoints not implemented yet');
return { messages: [], sendMessage: async () => {} };
```
Esto evita errores 404 silenciosos y deja claro que no funciona.

### 4.2 Arreglar usePlanEngine - DONE
Cambiar paths para usar los endpoints reales:
- GET /ui/plan/{id} → GET /ops/drafts/{id}
- POST /ui/plan/{id}/approve → POST /ops/drafts/{id}/approve
- PATCH /ui/plan/{id} → PUT /ops/drafts/{id}

### 4.3 Arreglar useRepoService - DONE
- POST /ui/repos/bootstrap → POST /ui/repos/vitaminize

---

## FASE 5: GICS como Unico Storage (3-4 horas) - COMPLETED

### 5.1 Mapear queries SQLite → GICS
Las 15 queries de agregacion de cost_storage.py necesitan equivalentes GICS:

| Query SQLite | Metodo GICS |
|-------------|-------------|
| SUM(cost_usd) WHERE timestamp > X | scan("ce:") + sum en Python |
| GROUP BY model | scan("ce:") + groupby en Python |
| GROUP BY date | scan("ce:") + groupby por dia |
| GROUP BY provider | scan("ce:") + groupby |
| GROUP BY task_type | scan("ce:") + groupby |
| ROI leaderboard | getInsights() o scan + calculo |
| Cascade stats | scan("ce:") + filter cascade_level |
| Cache stats | scan("ce:") + filter cache_hit |
| Budget alerts | get_total_spend + thresholds |
| Spend rate | scan con rango temporal |
| Avg cost by task | getInsight("cost_avg:{task}:{model}") |

**Alternativa mas eficiente**: Usar getInsight/getForecast de GICS para las queries que GICS ya sabe hacer internamente, y scan+groupby para el resto.

### 5.2 Migrar trust_storage, eval_storage, workflow_storage, config_storage
Mismo patron: reemplazar cursor.execute() por gics.scan()/gics.get().

### 5.3 Eliminar SQLite
- Borrar BaseStorage y su DB_PATH
- Borrar import sqlite3 de todos los storages
- Actualizar StorageService para no crear conexion SQLite

---

## FASE 6: Verificacion (1 hora)

### 6.1 Test del flujo principal via MCP
```
1. python -m tools.gimo_mcp.server  (arrancar MCP stdio)
2. Enviar: gimo_start_engine        (arrancar backend + frontend)
3. Enviar: gimo_run_task("crea un archivo hello.py con print hello world")
4. Verificar: draft tiene content != None
5. Verificar: run llega a status "done"
6. Verificar: archivo hello.py existe
```

### 6.2 Test del frontend
```
1. Abrir http://127.0.0.1:5173
2. No debe haber errores 404 en consola
3. Token Mastery debe mostrar datos reales
4. Trust Dashboard debe mostrar datos reales
5. Crear draft desde chat debe funcionar
```

### 6.3 Test de GICS
```
1. Verificar que gics daemon arranca (node vendor/gics/dist/src/daemon/server.js)
2. gics.put("test:1", {"value": 42})
3. gics.get("test:1") debe devolver {"value": 42}
4. gics.scan("test:") debe devolver [{"key": "test:1", ...}]
```

---

## Tiempo Estimado Total
| Fase | Tiempo | Dependencia |
|------|--------|-------------|
| 1. Eliminar ruido | 30 min | Ninguna |
| 2. Documentacion | 1 hora | Ninguna |
| 3. MCP Bridge | 2-3 horas | Fase 1 |
| 4. Frontend honesto | 2-3 horas | ✅ |
| 5. Migrar a GICS | 3-4 horas | Fase 1 |
| 6. Verificacion | 1 hora | Fases 1-5 |
| **Total** | **~10-12 horas** | |

## Orden Recomendado
Fases 1 y 2 primero (ponen orden). Luego Fases 3 y 4 en paralelo (MCP + Frontend). Fase 5 al final (migracion de storage). Fase 6 cierra todo.

Las fases 1, 2, 4 las puede hacer cualquier IA barata (Haiku, GPT-4o-mini). Las fases 3 y 5 necesitan algo mas capaz pero no necesariamente Opus.
