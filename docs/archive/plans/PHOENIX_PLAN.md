# Plan PHOENIX — Rediseño UI Completo de GIMO

> **Codename**: PHOENIX
> **Status**: `COMPLETE`
> **Deprecates**: GIMO_UI_OVERHAUL_PLAN, GIMO_ROADMAP, TOKEN_MASTERY_PLAN
> **Created**: 2026-02-17
> **Target**: `tools/orchestrator_ui/src/`

---

## Contexto

Audit visual humano + análisis técnico del frontend (47 componentes, 15 hooks) y backend (73 endpoints, 57% cobertura UI) revelan que la interfaz está en estado alpha/prototipo, no diseñada para uso humano real.

### Problemas detectados (Audit Humano)
1. No hay punto central de interacción (chat/prompt) con el orquestador
2. Información aplastada en sidebar de 380px
3. Secciones sin propósito claro o explicación
4. Dropdown suelto en "Repo Orchestrator" — necesita barra de menú profesional
5. Indicador verde "Running" no aporta nada
6. Plans, Evaluations, Maintenance — sin contexto ni orientación
7. Observability — nombre difícil, info aplastada
8. Settings — una sola opción, nada de QoL
9. Token Mastery — botón que parece vacío
10. Audit Logs — mal diseñada

### Problemas detectados (Análisis Técnico)
1. Auth inconsistente: `GraphCanvas`, `LiveLogs`, `TrustSettings` usan `Bearer` token en headers en vez de `credentials: 'include'` (cookies)
2. Datos hardcodeados: `ObservabilityPanel` → "+12%", `MaintenanceIsland` → Uptime "—"
3. `ProviderSettings` usa tema `slate-*` (Tailwind genérico) — resto usa tema macOS dark
4. `TokenMastery` diseñada para fullscreen (`max-w-7xl`) pero renderizada en panel de 380px
5. `CommandPalette.tsx` y `WorkflowCanvas.tsx` existen pero no se usan
6. 43% de endpoints backend sin representación UI
7. Model field mismatches entre Python y TypeScript (EvalRunReport, MasteryRecommendation, CostAnalytics)

---

## Decisiones de Diseño

- **Navegación**: Sidebar de iconos (mejorado) + Menu bar tipo desktop arriba
- **Layout**: Cada sección se renderiza fullscreen en el área principal (no en panel de 380px)
- **Inspector**: Panel contextual retráctil que solo aparece al seleccionar nodos del grafo
- **Chat**: Panel split-view integrado en la vista Graph (60% grafo / 40% chat)

---

## Archivos Principales a Modificar/Crear

| Archivo | Acción |
|---------|--------|
| `App.tsx` | Reescribir layout: MenuBar + Sidebar + Main fullscreen |
| `components/MenuBar.tsx` | **NUEVO** - Barra de menú File/Edit/View/Tools/Help |
| `components/Sidebar.tsx` | Mejorar: labels visibles, mejor spacing, tooltips |
| `components/InspectPanel.tsx` | Convertir en drawer contextual (solo para nodos) |
| `components/OrchestratorChat.tsx` | **NUEVO** - Chat central split con graph |
| `components/WelcomeScreen.tsx` | **NUEVO** - Onboarding cuando grafo vacío |
| `components/GraphCanvas.tsx` | Fix auth + integrar chat split |
| `components/LiveLogs.tsx` | Fix auth |
| `components/TrustSettings.tsx` | Fix auth |
| `components/ObservabilityPanel.tsx` | Eliminar hardcode "+12%", renombrar a Metrics |
| `components/ProviderSettings.tsx` | Migrar tema slate → macOS dark |
| `islands/system/MaintenanceIsland.tsx` | Conectar uptime real |
| `components/TokenMastery.tsx` | Mover renderizado a fullscreen |

---

## Fases de Ejecución

### Fase 0 — Bugs Críticos
- [x] 0.1 `GraphCanvas.tsx:37-39` — Cambiar `Bearer ${ORCH_TOKEN}` → `credentials: 'include'`
- [x] 0.2 `LiveLogs.tsx:12-14` — Mismo fix auth
- [x] 0.3 `TrustSettings.tsx:54-57` — Mismo fix auth + usar cookies no Bearer
- [x] 0.4 `ObservabilityPanel.tsx:37` — Eliminar `change="+12%"` hardcodeado
- [x] 0.5 `MaintenanceIsland.tsx:233` — Conectar uptime al dato real de `/ui/status`
- [x] 0.6 `ProviderSettings.tsx` — Migrar clases `slate-*` al tema macOS dark (`bg-[#1c1c1e]`, `border-[#2c2c2e]`, `text-[#f5f5f7]`)

### Fase 1 — Reestructuración Layout
- [x] 1.1 Crear `components/MenuBar.tsx` con dropdowns: File, Edit, View, Tools, Help
  - File: Nuevo Plan, Abrir Repo, Exportar Logs, Cerrar Sesión
  - Edit: Config Economía, Config Providers, Políticas
  - View: Graph, Plans, Evaluations, Metrics, Security, Maintenance
  - Tools: Command Palette (Ctrl+K), MCP Sync, Run Evaluation
  - Help: Documentación, Acerca de
- [x] 1.2 Mejorar `Sidebar.tsx`: labels visibles bajo iconos, padding adecuado, separadores de grupo
- [x] 1.3 Reescribir `App.tsx`: MenuBar(40px) + Sidebar(64px) + Main(fullscreen) + Footer(32px)
- [x] 1.4 Cada tab renderiza su componente en area principal fullscreen (no en InspectPanel)
- [x] 1.5 `InspectPanel.tsx` → drawer contextual retráctil, solo aparece al seleccionar nodo del grafo
- [x] 1.6 Eliminar indicador verde "Running" — reemplazar por info sutil en footer

### Fase 2 — Chat Central + Onboarding
- [x] 2.1 Crear `components/OrchestratorChat.tsx` — chat global conectado a `POST /ops/generate` y `POST /ops/drafts`
- [x] 2.2 Integrar chat como split-view inferior en vista Graph (60% grafo / 40% chat)
- [x] 2.3 Crear `components/WelcomeScreen.tsx` — pantalla cuando no hay nodos: explicación + quick actions
  - Quick actions: "Nuevo Plan", "Conectar Provider", "Abrir Repo"
  - Acceso directo a Command Palette
- [x] 2.4 Permitir aprobar/rechazar drafts directamente desde el chat

### Fase 3 — Mejoras por Sección
- [x] 3.1 **Plans**: Añadir lista de historial (drafts + approved + runs), timeline visual. Endpoints: `GET /ops/drafts`, `GET /ops/approved`, `GET /ops/runs`
- [x] 3.2 **Evaluations**: Añadir texto explicativo en header: "Test regression de workflows contra datasets golden". Ya funcional
- [x] 3.3 **Observability → Metrics**: Renombrar en Sidebar, código y títulos. Agregar avg_latency_ms al grid
- [x] 3.4 **Security**: Añadir tooltips explicativos a cada sección (Threat Level, Circuit Breakers, Trust Dimensions), más padding fullscreen
- [x] 3.5 **Maintenance**: Conectar datos reales de `/ui/status`. Explicar visualmente que status y security level son métricas independientes
- [x] 3.6 **Audit Logs**: Unificar con la versión completa de MaintenanceIsland (filtros + búsqueda + export). Eliminar LiveLogs simplificado o redirigir
- [x] 3.7 **Settings**: Expandir con secciones:
  - General: Tema, idioma, auto_run, TTLs, concurrencia
  - Providers: (ya existe ProviderSettings)
  - Economy: (mover settings tab de TokenMastery)
  - Security: Políticas, circuit breaker defaults
  - About: Versión, uptime, endpoints disponibles
- [x] 3.8 **Token Mastery**: Renderizar en main area fullscreen (ya diseñada para esto con `max-w-7xl mx-auto`)

### Fase 4 — CommandPalette + Polish
- [x] 4.1 Integrar `Shell/CommandPalette.tsx` existente con Ctrl+K / Cmd+K
- [x] 4.2 Conectar CommandPalette a acciones: cambiar vista, nuevo plan, buscar repo
- [x] 4.3 Verificación final: cero `Bearer` en frontend, cero `slate-*`, cero hardcodes

#### Providers (Plan Maestro transversal)

- [x] Migración de `ProviderSettings` a UX dinámica por capacidades OPS (`/ops/provider/capabilities`)
- [x] Integración de catálogo dinámico por `provider_type` (`GET /ops/connectors/{provider_type}/models`)
- [x] Flujo `Download & Use` en UI (`POST /ops/connectors/{provider_type}/models/install`)
- [x] Flujo `Test connection` en UI (`POST /ops/connectors/{provider_type}/validate`)
- [x] Guardado de provider activo v2 (`PUT /ops/provider`) con `provider_type`, `model_id`, `auth_mode`, `auth_ref`
- [x] Estado efectivo siempre visible en UI (`effective_state` + `health` + error accionable)
- [x] Documentación de contrato final en `docs/PROVIDER_UX_REWORK.md`

---

## Backend API Reference (para conectar UI)

### Endpoints sin UI (prioridad para fases futuras)
| Endpoint | Propósito |
|----------|-----------|
| `PUT /ops/plan` | Editor de plan |
| `PUT /ops/drafts/{id}` | Editar draft |
| `POST /ops/drafts/{id}/reject` | Rechazar draft |
| `POST /ops/generate` | Generación AI de drafts |
| `POST /ops/workflows/execute` | Ejecución directa |
| `GET /ops/workflows/{id}/checkpoints` | Visualización de checkpoints |
| `POST /ops/workflows/{id}/resume` | Resume desde checkpoint |
| `GET /ops/connectors` | Lista de conectores LLM |
| `POST /ops/config/mcp/sync` | Sync herramientas MCP |
| `GET/PUT/DELETE /ops/tool-registry/*` | CRUD de herramientas |
| `PUT /ops/policy` | Editor de políticas |
| `POST /ops/mastery/predict` | Predicción de costes |
| `GET /ops/mastery/recommendations` | Sugerencias ML |

### Model Field Mismatches (corregir en frontend)
| Backend (Python) | Frontend (TS) | Fix |
|-----------------|---------------|-----|
| `avg_score` | `average_score` | Alinear TS al backend |
| `recommendations` wrapper | Array directo | Unwrap en hook |
| `cascade_stats` list | dict expected | Adaptar TS type |

---

## Verificación

1. `grep -r "Bearer" tools/orchestrator_ui/src/` → debe dar 0 resultados
2. `grep -r "slate-" tools/orchestrator_ui/src/components/` → debe dar 0 resultados
3. `npm run build` en `tools/orchestrator_ui/` → sin errores TS
4. Navegación manual: todas las tabs cargan fullscreen con espacio adecuado
5. Seleccionar nodo en grafo → inspector se abre como drawer lateral
6. Ctrl+K → CommandPalette aparece
7. Chat del orquestador funcional con endpoint `/ops/generate`
8. Todos los datos mostrados son reales (no hardcodeados)

---

## Notas para el Agente Ejecutor

- El tema visual macOS dark usa: `bg-[#0a0a0a]` (fondo), `bg-[#1c1c1e]` (cards), `border-[#2c2c2e]`, `text-[#f5f5f7]` (texto), `text-[#86868b]` (muted), `#0a84ff` (accent)
- Toda auth frontend debe usar `credentials: 'include'`, NUNCA Bearer headers
- Los hooks existentes (`useMasteryService`, `useEvalsService`, `useObservabilityService`, etc.) ya implementan los fetch correctamente con cookies — reutilizar siempre que sea posible
- `ErrorBoundary` y `ToastProvider` ya envuelven la app en `main.tsx`
- El `useToast()` hook existe para notificaciones — usarlo en lugar de `alert()`
