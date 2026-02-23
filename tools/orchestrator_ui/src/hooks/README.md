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
