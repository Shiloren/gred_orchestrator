# Arquitectura GIMO

## Capas
0. GICS Daemon (Node.js) - Storage distribuido propietario
1. Services (Python) - 30+ servicios, GraphEngine es el nucleo
2. REST API (FastAPI) - ~95 endpoints en /ops/*, /ui/*, /auth/*
3. MCP Server (FastMCP) - 14 tools para IDEs via stdio/SSE
4. Frontend (React+Vite) - Dashboard en puerto 5173

## Autenticacion y Seguridad
- **Sistema de Auth**: Utiliza Bearer token + cookie session para las peticiones de la API REST.
- Las integraciones LLM (Codex, etc.) utilizan Device Code Flow (Codex Account Mode).
- Un guardián cognitivo (`SecurityGuard`) evalúa riesgos y sanitiza intenciones antes de su ejecución.

## Sistema de Storage
- **Actual**: SQLite predominante en varios storages (`cost_storage`, `trust_storage`, `eval_storage`, etc.).
- **GICS (Global Information Control System)**: Daemon Node.js para almacenamiento. Tiene conectividad via socket y tiers de storage (hot/warm/cold).
- **Pendiente**: Migrar todo el almacenamiento de SQLite a GICS para tener a GICS como único origen de datos.

## Flujo Principal Detallado
1. **Draft**: Se recibe un prompt o intenct y se genera un borrador (`ExecutionPlanDraft`).
2. **Approved**: El usuario (o regla automática) aprueba el plan.
3. **Run**: El draft se convierte en un plan de ejecución en el `GraphEngine`.
4. **RunWorker**: El worker asíncrono toma los nodos del grafo y delega el trabajo real.
5. **ProviderService / LLM**: Se solicita inferencia al proveedor (ej. Qwen vía Ollama, Groq, Codex).
IDE → MCP tool → OpsService → RunWorker → ProviderService → LLM

## Rutas de Datos Runtime
Todos los datos dinámicos durante la ejecución se guardan en `.orch_data/ops/`:
- Drafts, configuraciones, estados de ejecución, y bases de datos locales.

## Servicios Legacy vs. Activos
**Legacy (en proceso de eliminación)**:
- `model_service.py`, `plan_service.py`, `registry_service.py`, `comms_service.py`, `provider_registry.py`
**Activos**:
- `ops_service.py`, `provider_service.py`, `notification_service.py`, `repo_service.py`

## Directorios Clave
tools/gimo_server/services/     → Logica de negocio
tools/gimo_server/routers/ops/  → Endpoints REST
tools/gimo_server/mcp_server.py → MCP tools
tools/orchestrator_ui/src/      → Frontend React
vendor/gics/                    → Daemon GICS (Node.js)
.orch_data/ops/                 → Datos runtime (drafts, runs, config)
