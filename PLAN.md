# GIMO MCP Bridge: Mejora Disruptiva

## Diagnostico del MCP Actual

### Estado actual: 14 tools hardcoded de 80+ endpoints
- Solo expone: status, agents, drafts, runs, handover, spawn
- **NO expone**: Cost/Mastery, Trust/Security, Evaluations, Observability, Providers, Repos, Skills, Custom Plans, Threads, Workflows, Policy, Tool Registry, Config, Audit
- Sin MCP Resources (datos read-only)
- Sin MCP Prompts (templates de workflow)
- Solo 5 IDEs soportados (falta Claude Desktop, Windsurf, Cline, Continue, JetBrains)
- Logica de negocio duplicada (importa servicios directamente en vez de usar la REST API)
- Tools devuelven strings planos, sin manejo de errores estructurado

### Problema Arquitectural Critico
El MCP server actual importa servicios Python directamente. Cuando corre como subprocess (stdio para IDEs), tiene su propio proceso Python con instancias separadas de servicios. Esto es fragil e inconsistente con el estado del servidor principal.

---

## Arquitectura Propuesta: API Bridge Pattern

```
IDE (Claude Desktop, VS Code, Cursor, Windsurf, etc.)
    | stdio (JSON-RPC)
    v
GIMO MCP Bridge (mcp_bridge/server.py)
    | httpx (HTTP async)
    v
GIMO REST API (localhost:9325)
    -> Auth, Validation, Audit, Business Logic
```

**Concepto clave**: Un manifiesto declarativo define 67 tools. Una funcion bridge generica traduce cada llamada MCP a una peticion HTTP contra la REST API de GIMO. No se duplica logica de negocio.

---

## Archivos a CREAR

### 1. `tools/gimo_server/mcp_bridge/__init__.py`
- Package init, exporta `create_bridge_mcp()`

### 2. `tools/gimo_server/mcp_bridge/manifest.py`
- Dataclasses: `ParamMapping`, `ToolSpec`
- 67 ToolSpec definitions organizados en 12 dominios:
  - **System** (5): status, server_info, service_status, restart, stop
  - **Repository** (7): list_repos, active_repo, select_repo, tree, read_file, search, diff
  - **Plans** (8): get_plan, list/get/create/generate/approve/reject drafts, plan_graph
  - **Runs** (8): list/get/create/cancel runs, execute/checkpoint/resume workflows, list_approved
  - **Mastery** (7): status, analytics, forecast, recommendations, predict, get/set economy_config
  - **Trust** (7): dashboard, query, suggestions, circuit_breaker get/set, reset, security_events
  - **Evals** (6): run, list/get runs, create/list/get datasets
  - **Observability** (3): metrics, list/get traces
  - **Providers** (7): config, capabilities, connectors, catalog, install, validate, recommend
  - **Skills** (6): list/get/create/update/delete/trigger
  - **Custom Plans** (6): list/get/create/update/delete/execute
  - **Conversations** (6): list/create/get threads, add_turn, fork, post_message
  - **Config** (7): ops config get/set, mcp servers, sync tools, tool registry list/get/delete
  - **Policy** (3): get/set policy, decide
  - **Audit** (2): audit_log, resolve_security

### 3. `tools/gimo_server/mcp_bridge/bridge.py`
- Funcion generica `call_api(spec, arguments, base_url, token) -> str`
- Resuelve path params (`{draft_id}` -> valor)
- Separa query params y body fields segun ParamMapping.source
- Envia peticion HTTP via httpx con Bearer token
- Retorna JSON con errores estructurados (`{"error": true, "detail": "..."}`)
- Connection pooling con httpx.AsyncClient reutilizable

### 4. `tools/gimo_server/mcp_bridge/registrar.py`
- `register_all_tools(mcp, base_url, token)` - Itera manifiesto y registra cada tool
- Usa patron closure para capturar cada spec correctamente
- Genera JSON Schema desde ParamMapping para cada tool

### 5. `tools/gimo_server/mcp_bridge/resources.py`
- 8 MCP Resources read-only:
  - `gimo://config/ops` - Config OPS runtime
  - `gimo://config/provider` - Config proveedores
  - `gimo://config/economy` - Config economia de tokens
  - `gimo://config/policy` - Reglas de politica
  - `gimo://observability/metrics` - Metricas sistema
  - `gimo://mastery/status` - Estado token mastery
  - `gimo://audit/recent` - Ultimas 50 entradas audit
  - `gimo://security/events` - Eventos de seguridad

### 6. `tools/gimo_server/mcp_bridge/prompts.py`
- 5 MCP Prompts (templates de workflow):
  - `plan_and_execute` - Planificar y ejecutar tarea multi-agente
  - `cost_optimization_review` - Revisar gasto y optimizar
  - `security_audit` - Auditoria de seguridad completa
  - `run_regression_eval` - Ejecutar evaluaciones de regresion
  - `setup_new_provider` - Configurar nuevo proveedor LLM

### 7. `tools/gimo_server/mcp_bridge/server.py`
- Entry point principal
- `create_bridge_mcp()` factory: crea FastMCP, registra tools+resources+prompts
- 3 tools LOCAL-ONLY (no via HTTP): gimo_start_engine, gimo_wake_ollama, gimo_reload_worker
- Lee token de env var ORCH_TOKEN o archivo .orch_token
- Soporta GIMO_API_URL para conexiones remotas
- `if __name__ == "__main__"`: modo stdio

---

## Archivos a MODIFICAR

### 8. `tools/gimo_mcp/server.py`
- Actualizar proxy para importar desde `mcp_bridge.server` en vez de `mcp_server`

### 9. `tools/gimo_server/main.py`
- Montar bridge MCP en `/mcp/v2` junto al legacy `/mcp`
- Mantener backward compatibility durante transicion

### 10. `scripts/setup_mcp.py`
- Ampliar soporte a 9+ IDEs:
  - Claude Desktop (Windows: %APPDATA%/Claude/, Mac: ~/Library/Application Support/Claude/)
  - VS Code (~/.vscode/mcp.json)
  - Cursor (~/.cursor/mcp.json)
  - Windsurf (~/.windsurf/mcp.json)
  - Cline (globalStorage path)
  - Continue (~/.continue/config.json)
  - JetBrains (~/.config/JetBrains/mcp.json)
  - Antigravity (existente)
  - Gemini (existente)
- Flags: `--all`, `--ide=<name>`, `--check`, `--remove`, `--remote=<url>`
- Usar `sys.executable` para Python correcto

### 11. `tools/gimo_server/mcp_server.py`
- Agregar deprecation warning
- Mantener funcional para backward compat

---

## Tests a CREAR

### 12. `tests/test_mcp_manifest.py`
- Validar nombres unicos, prefijo gimo_, paths validos
- Verificar que path params coinciden con ParamMapping
- Verificar que params required no tienen default
- Verificar count >= 60 tools

### 13. `tests/test_mcp_bridge.py`
- Test bridge con httpx mockeado
- Test sustitucion de path params
- Test errores de conexion
- Test query params y body fields

---

## Orden de Implementacion

1. `mcp_bridge/__init__.py` + `manifest.py` (estructura + 67 tools)
2. `mcp_bridge/bridge.py` (funcion bridge generica)
3. `mcp_bridge/registrar.py` (auto-registro de tools)
4. `mcp_bridge/resources.py` (8 resources)
5. `mcp_bridge/prompts.py` (5 prompts)
6. `mcp_bridge/server.py` (entry point + 3 tools locales)
7. `tools/gimo_mcp/server.py` (actualizar proxy)
8. `tools/gimo_server/main.py` (montar /mcp/v2)
9. `scripts/setup_mcp.py` (9+ IDEs)
10. `tools/gimo_server/mcp_server.py` (deprecation warning)
11. `tests/test_mcp_manifest.py`
12. `tests/test_mcp_bridge.py`

---

## Beneficios

| Aspecto | Antes | Despues |
|---------|-------|---------|
| Tools MCP | 14 | 70 (67 bridge + 3 local) |
| Resources | 0 | 8 |
| Prompts | 0 | 5 |
| IDEs soportados | 5 | 9+ |
| Agregar nuevo tool | Escribir funcion async completa | 1 entrada en manifiesto |
| Logica duplicada | Si (imports directos) | No (todo via REST API) |
| Soporte remoto | No | Si (GIMO_API_URL) |
| Auth consistente | No | Si (Bearer token via HTTP) |
| Audit logging | Parcial | Completo (todo pasa por REST) |
