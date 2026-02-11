# STATUS (UNRELEASED)

**Status**: PHASE_2_VALIDATED_NEEDS_REVIEW

**Last verified**: 2026-02-11 07:36 CET
**Verified on commit**: 831d67babc54de34eea36f450cd91aa5f99e731b

## Executive summary

- The project is currently marked as **UNRELEASED** (intentionally; v1.0 must be explicitly declared by maintainer).
- **Quality gates** pass locally after portability fixes.
- Some verification steps are currently **blocked by missing local tooling** in this environment:
  - `pip-audit` is not installed.
  - `docker` CLI is not installed.

## Sprint 1 update (Fase 1 cierre roadmap v2)

Fase 1 del roadmap `docs/GIMO_ROADMAP_v2.md` se considera **cerrada a nivel backend/core** con evidencia local en la suite objetivo:

- Command:
  - `python -m pytest -q tests/test_adapters.py tests/test_graph_engine.py tests/test_trust_event_buffer.py tests/test_storage_service.py`
- Result:
  - **37 passed** in 3.60s

Cobertura funcional validada en este sprint:

- **1.1 Agent adapters**: contrato base + Claude/generic adapter round-trip.
- **1.2 Graph Engine MVP**: secuencia, branching, loops controlados, checkpoints y contracts.
- **1.3 SQLite layer**: workflows/checkpoints/trust_events/audit_entries y operaciones persistentes.
- **1.4 Trust Event schema + buffer**: buffer in-memory con flush por tamaño/intervalo.
- **1.5 Contracts pre/post**: checks ejecutables con rollback en fallos post.

### Sprint 1 review (revalidación solicitada)

Revisión adicional ejecutada para validar cierre más estricto de Fase 1 incluyendo piezas de gobernanza base asociadas al flujo de adapters/trust:

- Command:
  - `python -m pytest -q tests/test_adapters.py tests/test_graph_engine.py tests/test_trust_event_buffer.py tests/test_storage_service.py tests/test_trust_engine.py tests/unit/test_trust_routes.py`
- Result:
  - **60 passed** in 3.88s

Conclusión de revisión:

- **Sprint 1 confirmado en verde** para alcance backend/core de Fase 1.
- No se detectaron regresiones en adapters, grafo, persistencia SQLite, trust events/buffer, contratos ni rutas de trust asociadas.

## Sprint 2 update (Governance Core)

Validación ejecutada para los entregables clave de Sprint 2/Fase 2 (Trust Engine, Circuit Breaker, HITL avanzado en grafo, Durable Execution y Tool Registry):

- Command:
  - `python -m pytest -q tests/test_trust_engine.py tests/test_graph_engine.py tests/unit/test_trust_routes.py tests/test_ops_v2.py tests/test_adapters.py`
- Result:
  - **91 passed** in 7.07s

Cobertura validada para Sprint 2:

- **Trust Engine + Circuit Breaker**: cálculo de score/policy, thresholds y configuración por dimensión.
- **HITL avanzado (human_review node)**: pause/resume, approve/reject, timeout/default action, edición de estado y anotaciones.
- **Durable Execution**: execute/checkpoints/resume por API con persistencia SQLite.
- **Tool Registry**: endpoints y RBAC (operator/admin) verificados.
- **Integración OPS RBAC**: rutas de trust/governance con controles de acceso en verde.

### Sprint 2 deep review (detallada)

Tras revisión técnica adicional (código + tests) Sprint 2 queda **muy sólido pero no 100% roadmap literal**.

Verificación adicional ejecutada:

- `python -m pytest -q tests/test_model_router_service.py tests/test_observability_service.py tests/test_storage_service.py tests/test_trust_store.py tests/test_institutional_memory_service.py`
- Resultado: **12 passed** in 0.52s

Brechas reales detectadas vs roadmap Fase 2 (pendientes para “100%”):

1) **Idempotency keys para tool calls de escritura (2.4)**
   - No hay implementación explícita de `idempotency_key`/deduplicación por operación write.

2) **HITL fork en paralelo (2.3)**
   - Existe decisión `fork` en `human_review`, pero no ejecución real de ramas paralelas con selección posterior de resultado.

3) **Tool Registry dinámico (2.5)**
   - Registry estático JSON y enforcement correcto, pero falta capa de descubrimiento/registro dinámico reportado por adapters.

Conclusión: Sprint 2 está **validado funcionalmente** para MVP de gobernanza, pero para declarar “100% fase 2” faltan esos tres cierres.

## Reality check (docs vs code)

Recent fixes applied in this repo (still pending a fresh evidence run under `docs/evidence/`):

1) **Ports / entrypoints aligned**
   - Canonical service port: **9325**.
   - `tools/gimo_server/main.py` defaults to 9325 (override via `ORCH_PORT`).
   - UI fallback uses 9325 if `VITE_API_URL` is unset.
   - `scripts/ops/launch_orchestrator.ps1` launches `tools.gimo_server.main:app` on 9325.

2) **OpenAPI expanded**
   - `tools/gimo_server/openapi.yaml` now covers the implemented `/ui/*` routes and core read-only endpoints.

3) **Allowlist parser made backward-compatible**
   - `get_allowed_paths()` accepts both legacy `{timestamp, paths:[str]}` and new `{paths:[{path, expires_at}]}` formats.

4) **Policy-as-Code MVP integrated (GIMO roadmap v2, Phase 5.1 slice)**
   - New models in `tools/gimo_server/ops_models.py`: `PolicyConfig`, `PolicyRule`, `PolicyRuleMatch`.
   - New service `tools/gimo_server/services/policy_service.py`:
     - JSON-backed policy rules (`.orch_data/ops/policy_rules.json`)
     - `decide(tool, context, trust_score)` with glob matching (`tool`, `context`),
       optional `min_trust_score`, and `never_auto_approve` override.
   - `GenericCLISession.allow()` now enforces policy decisions before allowing tool execution
     (deny / require_review / override paths are fail-closed via `PermissionError`).
   - New OPS endpoints in `tools/gimo_server/ops_routes.py`:
     - `GET /ops/policy` (operator+)
     - `PUT /ops/policy` (admin)
     - `POST /ops/policy/decide` (operator+)
   - Test coverage added in `tests/unit/test_trust_routes.py` for policy routes and roles.
   - Regression subset verified:
     - `python -m pytest -q tests/test_adapters.py tests/unit/test_trust_routes.py tests/test_ops_v2.py`
     - **62 passed**.

5) **Durable Execution API slice integrated (GIMO roadmap v2, Phase 2.4 slice)**
   - New request model in `tools/gimo_server/ops_models.py`:
     - `WorkflowExecuteRequest` (`workflow`, `initial_state`, `persist_checkpoints`, `workflow_timeout_seconds`).
   - New OPS runtime endpoints in `tools/gimo_server/ops_routes.py`:
     - `POST /ops/workflows/execute`
     - `GET /ops/workflows/{workflow_id}/checkpoints`
     - `POST /ops/workflows/{workflow_id}/resume?from_checkpoint=...`
   - Added in-memory engine registry for active workflow resumes and persisted fallback reconstruction
     from SQLite (`workflows` + `checkpoints`).
   - Role and audit integrated (operator+ for execute/read/resume, full audit entries).
   - Test coverage expanded in `tests/unit/test_trust_routes.py` for:
     - execute RBAC,
     - checkpoints listing,
     - resume not-found fallback case.
   - Regression subset verified:
     - `python -m pytest -q tests/unit/test_trust_routes.py tests/test_graph_engine.py tests/test_ops_v2.py`
     - **78 passed**.

## Current blockers for “professional release readiness”

1) Documentation rebuild is in progress (all previous docs archived as legacy).
2) Evidence pack not yet completed (needs: pytest run logs + security audit + docker build + UI checks).
3) Qwen/LM Studio dependent suites must be executed last, once everything else is green.

## Next actions (recommended)

1) Produce/refresh evidence pack (pytest + quality gates + UI checks + security scans).
2) Confirm OpenAPI coverage is complete and kept in sync with `routes.py`.
3) Continue roadmap v2 pending phases/slices:
   - durable execution endpoints (`resume` API surface),
   - policy versioning/audit diff,
   - sandboxing for destructive tools,
   - graph/timeline UX and enterprise compliance exports.
4) Decide 1.0 version bump (still `UNRELEASED`).
   - `python scripts\\ci\\quality_gates.py`
   - `python scripts\quality_gates.py`
   - `python -m pytest -q`
   - `pip-audit`, `bandit`
   - UI lint/build/test
   - Docker build
