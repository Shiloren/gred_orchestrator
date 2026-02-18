# Plan Maestro GIMO: Sprint de Excelencia Técnica y Operativa

Este documento consolida todas las acciones necesarias para alcanzar la excelencia en los 7 gates de madurez identificados en la auditoría técnica.

**Objetivo:** Llevar a GIMO de "Backend Functional" a "Excelente en todas las dimensiones" (Arquitectura, Observabilidad, Seguridad, Quality Gates, Core Engine, UI/DX, Ecosistema).

---

## Fase 1: Refactorización Arquitectónica (Cimientos)

### Paso 1.1: Atomización de Rutas (`ops_routes.py`) [COMPLETADO]
**Problema:** Archivo monolítico de 946 líneas (Blast Radius alto).
**Acción:** Dividir en routers por dominio en `tools/gimo_server/routers/ops/`.

- [x] Crear paquete `tools/gimo_server/routers/ops/`.
- [x] Implementar sub-routers:
    - [x] `plan_router.py`: Endpoints de `Plan` y `Draft`.
    - [x] `run_router.py`: Endpoints de `Approved` y `Run`.
    - [x] `eval_router.py`: Endpoints de Evaluations, Datasets, Reports.
    - [x] `trust_router.py`: Endpoints de `TrustEngine` y CircuitBreakers.
    - [x] `config_router.py`: Endpoints de `Provider`, Connectors, `Policy`, `ToolRegistry`.
    - [x] `observability_router.py`: Endpoints de Metrics y Traces.
- [x] Refactorizar `ops_routes.py` para importar y montar estos routers.

```python
# CHECKPOINT: VERIFICACIÓN DE RUTAS
# Ejecutar obligatoriamente:
# pytest tests/test_ops_v2.py
# CRITERIO DE ÉXITO: 100% de tests pasando. Si falla uno solo, REVERTIR y corregir.
```

### Paso 1.2: Atomización de Almacenamiento (`storage_service.py`) [COMPLETADO]
**Problema:** Servicio monolítico de 718 líneas mezclando dominios.
**Acción:** Separar responsabilidades en `tools/gimo_server/services/storage/`.

- [x] Crear paquete `tools/gimo_server/services/storage/`.
- [x] Extraer lógica a:
    - [x] `workflow_storage.py`: CRUD Workflows/Checkpoints.
    - [x] `eval_storage.py`: CRUD Datasets/Reports.
    - [x] `trust_storage.py`: CRUD TrustEvents (fusionar con lógica de `trust_store.py`).
    - [x] `config_storage.py`: CRUD CircuitBreakers/ToolRegistry.
- [x] Mantener `StorageService` como Facade para compatibilidad.

```python
# CHECKPOINT: VERIFICACIÓN DE ALMACENAMIENTO
# Ejecutar obligatoriamente:
# pytest tests/test_storage_service.py
# CRITERIO DE ÉXITO: 100% de tests pasando.
```

### [x] 1.3 GICS como Single Source of Truth <!-- id: gics_integration -->
- **Objetivo**: GICS debe ser la persistencia primaria para GIMO, eliminando la duplicidad.
- **Estatus**: [x] COMPLETADO
- **Cambios Realizados**:
    - Escaneo cross-tier (Hot/Warm/Cold) habilitado en GICS Daemon.
    - Todos los servicios de storage (`Workflow`, `Trust`, `Eval`, `Config`) migrados para priorizar GICS.
    - Preservada compatibilidad con SQLite como fallback.

```python
# CHECKPOINT: PERSISTENCIA GICS
# 1. Iniciar servidor.
# 2. Crear un Draft vía API.
# 3. Verificar que el dato existe usando la CLI de GICS o query directa.
# 4. Reiniciar servidor y verificar que el dato persiste.
```

---

## Fase 2: Excelencia y Calidad (Operaciones)

### Paso 2.1: Observabilidad Industrial (OpenTelemetry) [COMPLETADO]
**Problema:** MVP in-memory volátil.
**Acción:** Implementar OpenTelemetry (OTel).

- [x] Instalar `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp`.
- [x] Actualizar `ObservabilityService` para usar `TracerProvider`.
- [x] Reemplazar `deque` in-memory por spans OTel reales.
- [x] Configurar exportador (console por defecto, variable de entorno para OTLP).

```python
# CHECKPOINT: TRAZABILIDAD
# Ejecutar un workflow y verificar en logs que se emiten trazas con:
# - Trace ID y Span ID únicos.
# - Atributos correctos (inputs, outputs, latency).
```

### Paso 2.2: Validación de Seguridad API [COMPLETADO]
**Problema:** Seguridad de filtrado OpenAPI ("Filtered OpenAPI") sin validar.
**Acción:** Crear test de penetración de endpoints.

- [x] Crear `tests/test_api_security.py`.
- [x] Intentar acceder a endpoints administrativos (`/ops/config`, `/trust/reset`) con token de operador/action.
- [x] Validar que `/openapi.json` con token de operador NO muestra endpoints privados.
- [x] Implementar `/ops/trust/reset` como alias funcional.

```python
# CHECKPOINT: AUDITORÍA DE SEGURIDAD
# pytest tests/test_api_security.py
# CRITERIO: Debe pasar (bloquear accesos no autorizados).
```

### Paso 2.3: Quality Gates Estrictos
**Problema:** Estándares laxos ("Aceptable").
**Acción:** Elevar a "Excelente".

- [x] **Cobertura:** Medir coverage actual. Refactorizar para alcanzar >90% en core (`graph_engine`, `security`).
- [x] **Rendimiento:** Añadir test de latencia para `TrustEngine` (<10ms overhead).
- [x] **Claridad:** Renombrar `LocalLLMAdapter` a `OpenAICompatibleAdapter` y actualizar docs para mencionar Ollama/LM Studio explícitamente.

```python
# CHECKPOINT: CALIDAD TOTAL
# 1. Ejecutar suite completa: pytest tests/
# 2. Verificar reporte de cobertura > 90%.
# 3. Verificar benchmark de latencia.
```

---

## Fase 3: Interfaz y Experiencia de Desarrollador (UI/DX)

### Paso 3.1: Panel de Evaluaciones (Eval Dashboard) [COMPLETADO]
**Problema:** Backend de evals completo pero sin interfaz visual.
**Acción:** Crear componentes React para gestionar datasets y reportes.

- [x] Crear `EvalDashboard.tsx`: Vista principal con lista de datasets y reportes.
- [x] Crear `EvalDatasetEditor.tsx`: Editor para crear/editar golden cases.
- [x] Crear `EvalRunViewer.tsx`: Visualización de resultados (pass/fail, scores).
- [x] Crear hook `useEvalsService.ts` conectando con `/ops/evals/*`.
- [x] Añadir tab `evals` en `Sidebar.tsx` y montar en `InspectPanel.tsx`.

```python
# CHECKPOINT: EVAL UI
# 1. Abrir la app en el navegador.
# 2. Navegar a la tab "Evaluations".
# 3. Crear un dataset de prueba desde la UI.
# 4. Verificar que aparece en la lista y se puede ver su detalle.
```

### Paso 3.2: Panel de Observabilidad (Traces & Metrics) [COMPLETADO]
**Problema:** Las trazas OTel (Fase 2.1) no tienen visualización.
**Acción:** Crear panel de monitoreo en la UI.

- [x] Crear `ObservabilityPanel.tsx`: Métricas en tiempo real (workflows, tokens, cost).
- [x] Crear `TraceViewer.tsx`: Lista de trazas con filtros y detalle de spans.
- [x] Conectar con hook existente o nuevo `useObservabilityService.ts`.
- [x] Añadir tab `observability` en `Sidebar.tsx`.

```python
# CHECKPOINT: OBSERVABILITY UI
# 1. Ejecutar un workflow.
# 2. Abrir tab Observability.
# 3. Verificar que aparece la traza con sus spans.
```

### Paso 3.3: Visualización de Seguridad (Security Panel) [COMPLETADO]
**Problema:** `TrustEngine` y `ThreatEngine` potentes pero invisibles para el usuario.
**Acción:** Mejorar componentes existentes (`TrustSettings.tsx`, `TrustBadge.tsx`).

- [x] Ampliar `TrustSettings.tsx` para mostrar dashboard de trust scores por dimensión.
- [x] Crear `CircuitBreakerPanel.tsx`: Estado actual de circuit breakers (open/closed/half-open).
- [x] Crear `ThreatLevelIndicator.tsx`: Indicador visual del nivel de amenaza activo.
- [x] Conectar con hook existente `useSecurityService.ts`.

```python
# CHECKPOINT: SECURITY UI
# 1. Verificar que el panel muestra trust scores reales.
# 2. Simular un circuit breaker abierto y verificar que se refleja en la UI.
```

---

## Fase 4: Ecosistema y Extensibilidad

### Paso 4.1: Cliente MCP (Model Context Protocol) [COMPLETADO]
**Problema:** Catálogo de conectores limitado.
**Acción:** Implementar cliente MCP para heredar conectores del ecosistema.

- [x] Crear `tools/gimo_server/adapters/mcp_client.py`: Cliente MCP básico.
- [x] Implementar descubrimiento de herramientas vía MCP (`tools/list`, `tools/call`).
- [x] Registrar herramientas MCP automáticamente en `ToolRegistryService`.
- [x] Añadir configuración de servidores MCP en `provider.json`.

```python
# CHECKPOINT: MCP CLIENT
# 1. Configurar un servidor MCP de ejemplo (filesystem o similar).
# 2. Verificar que GIMO descubre y lista las herramientas del servidor MCP.
# 3. Ejecutar una herramienta MCP desde un workflow.
```

### Paso 4.2: Implementación de `_execute_node` Funcional [COMPLETADO]
**Problema:** Único placeholder real del sistema, impide ejecución real de workflows.
**Acción:** Implementar dispatch real a adaptadores y servicios.

- [x] Modificar `GraphEngine._execute_node` para despachar según `node.type`:
    - `llm_call` → `ModelRouterService` + adaptador seleccionado.
    - `tool_call` → `ToolRegistryService` + ejecución real.
    - `human_review` → ya implementado en `_run_human_review`.
    - `eval` → `EvalsService`.
    - `transform` → función de transformación configurable.
    - `sub_graph` → recursión de `GraphEngine`.
    - `agent_task` → ya implementado en `_run_agent_task`.
    - `contract_check` → ya implementado en `_run_contract_check`.
- [x] Crear ejemplo funcional `examples/hello_workflow.py` que ejecute un flujo completo.

```python
# CHECKPOINT: EJECUCIÓN REAL
# 1. Ejecutar `examples/hello_workflow.py`.
# 2. Verificar que cada nodo produce output real (no {"status": "ok"}).
# 3. Verificar que las trazas de observabilidad registran la ejecución.
```

### Paso 4.3: Expansión de Adaptadores
**Problema:** Adaptadores existentes buenos pero sin documentación clara.
**Acción:** Documentar y estandarizar.

- [x] Renombrar `LocalLLMAdapter` → `OpenAICompatibleAdapter`.
- [x] Actualizar docstrings en todos los adaptadores (`gemini.py`, `claude_code.py`, `codex.py`, `generic_cli.py`).
- [x] Crear `docs/ADAPTERS.md` con tabla de compatibilidad y ejemplos de configuración.
- [x] Añadir ejemplos en `provider.json` para Ollama, LM Studio, vLLM, DeepSeek.

```python
# CHECKPOINT: ADAPTADORES
# 1. Verificar que `pytest tests/test_adapters.py` pasa.
# 2. Verificar que la documentación es clara y completa.
```

---

## Instrucciones para Agentes Ejecutores

1. **SECUENCIALIDAD:** Fase 1 → Fase 2 → Fase 3 → Fase 4. No saltar fases.
2. **CHECKPOINTS:** Son obligatorios. Copia y pega el output del test en tu reporte de paso.
3. **ROLLBACK:** Si un refactor rompe tests y no se arregla en 2 intentos, revertir y pedir ayuda humana.
4. **UI:** Los componentes de Fase 3 dependen de la refactorización de Fase 1 (routers limpios) y de Fase 2 (OTel activo).
5. **ECOSISTEMA:** Fase 4 depende de que `_execute_node` funcione para probar MCP end-to-end.
