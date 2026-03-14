# P2 Runbook — Lifecycle Incident Response (stuck-runs, lock contention, rerun)

## Objetivo
Responder de forma determinista a incidentes del lifecycle `draft -> approved -> run`, con foco en:

- `STUCK_RUN_DETECTED`
- conflictos `RUN_ALREADY_ACTIVE:*`
- contención de merge lock (`MERGE_LOCKED`)

## Señales operativas (fuente de verdad)

1. `GET /ops/observability/metrics`
   - `stuck_runs`
   - `stuck_run_ids`
   - `active_runs`
   - `run_completion_ratio`
2. `GET /ops/observability/alerts`
   - código `STUCK_RUN_DETECTED`
3. `GET /ops/runs/{run_id}`
   - `status`, `stage`, `heartbeat_at`, `log`

## SLI/SLO operativos recomendados

- **SLI stuck-run ratio** = `stuck_runs / max(active_runs,1)`
- **SLO**: stuck-run ratio <= 5% por ventana de 15 min
- **SLI completion ratio** = `run_completion_ratio`
- **SLO**: completion ratio >= 95% por ventana diaria

## Procedimiento A — Stuck run detectado

1. Identificar `run_id` en `stuck_run_ids`.
2. Consultar `GET /ops/runs/{run_id}` y revisar:
   - último `stage`
   - `heartbeat_at`
   - mensajes terminales en `log`
3. Si sigue activo sin progreso:
   - `POST /ops/runs/{run_id}/cancel`
4. Relanzar de forma formal:
   - `POST /ops/runs/{run_id}/rerun`
5. Verificar nueva instancia:
   - nuevo `run_id`
   - `rerun_of=<run_id_original>`
   - `attempt` incrementado

## Procedimiento B — Conflicto RUN_ALREADY_ACTIVE

Síntoma: `409 RUN_ALREADY_ACTIVE:*` en `POST /ops/runs` o `POST /ops/runs/{id}/rerun`.

1. Consultar el run activo reportado.
2. Si está sano, no relanzar (evitar duplicación).
3. Si está degradado/stuck:
   - cancelar activo (`/cancel`)
   - ejecutar rerun del run origen (`/rerun`)

## Procedimiento C — Merge lock contention

Síntoma: `MERGE_LOCKED` o bloqueo persistente en etapa de merge.

1. Verificar que no haya otro run activo legítimo para el mismo repo.
2. Si el lock corresponde a run huérfano/stuck:
   - cancelar run huérfano
   - reintentar con `rerun`
3. Confirmar transición desde `MERGE_LOCKED` a ejecución normal en la nueva instancia.

## Criterios de cierre de incidente

- `stuck_runs == 0`
- alerta `STUCK_RUN_DETECTED` ausente
- run de recuperación en estado terminal esperado (`done` o error diagnosticado)
- evidencia de trazabilidad (`rerun_of`, `attempt`) preservada

## Postmortem mínimo

Registrar:

- `run_id` original y `run_id` de recuperación
- `stage` donde ocurrió degradación
- causa probable (worker, lock, policy, infraestructura)
- acción aplicada (cancel/rerun)
- tiempo total de recuperación (MTTR)
