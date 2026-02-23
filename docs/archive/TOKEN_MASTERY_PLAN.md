 El Token Mastery actual esta implementado al ~60%: la fontaneria existe (CostService, ModelRouterService, budget
 counters en GraphEngine) pero los datos del dashboard son hardcodeados (total_savings_usd: 12.45 en
 mastery_router.py:29), no hay persistencia historica de costes, y el eco-mode es binario/agresivo (fuerza todo a
 local).

 Problema central del plan anterior: Todo era automatico. GIMO decidia por el usuario. El usuario necesita control
 total sobre que se enciende, que se apaga, y dentro de que limites opera cada feature. Las optimizaciones deben estar
 acotadas a los providers, APIs y presupuestos que el usuario configura.

 Resultado: Un sistema donde el usuario elige su nivel de autonomia, configura sus limites, y GIMO opera estrictamente
 dentro de esas reglas. Datos reales, no hardcodeados. Ingenieria solida, no magia.

 ---
 Analisis Competitivo (Feb 2026)

 Que hace cada competidor

 Feature: Cost tracking
 LangChain: LangSmith (SaaS)
 CrewAI: Externo
 AutoGen: Built-in/agente
 OpenRouter: Per-request
 Portkey: Dashboard real-time
 LiteLLM: Built-in + UI
 GIMO (actual): CostService (in-memory)
 ────────────────────────────────────────
 Feature: Budget enforcement
 LangChain: Ninguno
 CrewAI: Quotas/plan
 AutoGen: Ninguno
 OpenRouter: Per-key caps
 Portkey: Per-team caps
 LiteLLM: Per-user/provider/windowed
 GIMO (actual): Per-workflow (steps/tokens/cost/duration)
 ────────────────────────────────────────
 Feature: Model routing por coste
 LangChain: DIY patterns
 CrewAI: Ninguno
 AutoGen: Ninguno
 OpenRouter: :floor + Auto Router
 Portkey: Cost-based
 LiteLLM: Provider budget routing
 GIMO (actual): ModelRouter con tier degradation
 ────────────────────────────────────────
 Feature: Cascading (calidad)
 LangChain: CascadeFlow (3rd party)
 CrewAI: No
 AutoGen: No
 OpenRouter: Error-based fallover
 Portkey: Error-based
 LiteLLM: Error-based
 GIMO (actual): No (solo budget-based)
 ────────────────────────────────────────
 Feature: Eco-mode
 LangChain: No
 CrewAI: No
 AutoGen: No
 OpenRouter: :floor variant
 Portkey: No
 LiteLLM: No
 GIMO (actual): Binario (force cheapest)
 ────────────────────────────────────────
 Feature: Trust/confidence scoring
 LangChain: No
 CrewAI: No
 AutoGen: No
 OpenRouter: No
 Portkey: No
 LiteLLM: No
 GIMO (actual): TrustEngine + ConfidenceService
 ────────────────────────────────────────
 Feature: Autonomia configurable
 LangChain: No
 CrewAI: No
 AutoGen: Binary HITL
 OpenRouter: No
 Portkey: No
 LiteLLM: No
 GIMO (actual): Policy-as-code + trust thresholds
 ────────────────────────────────────────
 Feature: Caching semantico
 LangChain: Externo
 CrewAI: No
 AutoGen: Response cache
 OpenRouter: No
 Portkey: OpenAI+Pinecone
 LiteLLM: Response cache
 GIMO (actual): No
 ────────────────────────────────────────
 Feature: OTel nativo
 LangChain: Via LangSmith
 CrewAI: Externo
 AutoGen: Externo
 OpenRouter: No
 Portkey: Propietario
 LiteLLM: No
 GIMO (actual): Built-in spans+counters

 Donde GIMO ya gana

 1. Budget enforcement per-workflow - Nadie mas lo tiene a nivel de orquestacion (max_tokens, max_cost_usd, max_steps,
 max_duration)
 2. Trust scoring que afecta decisiones - TrustEngine + ConfidenceService es unico
 3. Proactive confidence - LLM evalua su propia capacidad antes de ejecutar. Nadie mas tiene esto
 4. HITL completo - Approve/reject/edit/takeover/fork en nodos interactivos

 Donde tenemos gaps

 1. Persistencia de costes - Todos persisten, nosotros no (in-memory solo)
 2. Cascading por calidad - CascadeFlow lo hace para llamadas individuales; nosotros no
 3. Pricing database - 6 modelos vs 100-300+ en LiteLLM/Helicone
 4. Provider-scoped budgets - LiteLLM tiene $X/dia para OpenAI, $Y/mes para Azure
 5. Caching - Portkey tiene semantic cache; nosotros tenemos SHA256 exacto basico

 Lo que este plan agrega y nadie tiene

 1. Capas de autonomia configurables por el usuario para decisiones economicas
 2. Cascading a nivel de orquestacion (no solo llamadas individuales) acotado a los providers del usuario
 3. ROI tracking que retroalimenta routing, con override del usuario
 4. Budget scoping por provider, por workflow, y por periodo temporal
 5. Todo encendible/apagable - cada feature es un toggle independiente

 ---
 Principio de Diseno: User-First Control

 Regla fundamental: GIMO nunca actua fuera de lo que el usuario ha configurado.

 - Si el usuario no tiene key de OpenAI, GIMO no puede rutear a GPT-4o
 - Si el usuario no activa cascading, no hay cascading
 - Si el usuario fija "minimo sonnet", GIMO no degrada a haiku
 - Si el usuario no pone budget, no hay alertas de budget
 - Cada feature es opt-in, no opt-out

 ---
 Fase 0: Modelo de Autonomia (UserEconomyConfig)

 Lo primero que se implementa. Todo lo demas lo consulta.

 Modificar: tools/gimo_server/ops_models.py

 Agregar UserEconomyConfig como sub-modelo dentro de OpsConfig:

 class ProviderBudget(BaseModel):
     """Budget limit per provider, set by the user."""
     provider: str                          # "openai", "anthropic", "local", etc.
     max_cost_usd: Optional[float] = None   # None = sin limite
     period: Literal["daily", "weekly", "monthly", "total"] = "monthly"

 class CascadeConfig(BaseModel):
     """User-configured cascade behavior."""
     enabled: bool = False
     min_tier: str = "local"                # El tier mas bajo que el usuario permite
     max_tier: str = "opus"                 # El tier mas alto al que puede escalar
     quality_threshold: int = 65            # 0-100, umbral para escalar
     max_escalations: int = 2              # Max intentos de escalado

 class EcoModeConfig(BaseModel):
     """User-configured eco-mode behavior."""
     mode: Literal["off", "binary", "smart"] = "off"
     floor_tier: str = "local"              # El tier minimo que usa eco-mode
     # Solo para mode="smart":
     confidence_threshold_aggressive: float = 0.85  # Degrade agresivo si >= esto
     confidence_threshold_moderate: float = 0.70    # Degrade moderado si >= esto

 class UserEconomyConfig(BaseModel):
     """All token economy settings. User controls everything."""
     # -- Autonomia --
     autonomy_level: Literal["manual", "advisory", "guided", "autonomous"] = "manual"

     # -- Budget --
     global_budget_usd: Optional[float] = None      # None = sin limite global
     provider_budgets: list[ProviderBudget] = []     # Per-provider limits
     alert_thresholds: list[int] = [50, 25, 10]      # % remaining triggers

     # -- Routing --
     cascade: CascadeConfig = CascadeConfig()
     eco_mode: EcoModeConfig = EcoModeConfig()
     allow_roi_routing: bool = False                  # Permitir que GIMO rute por ROI aprendido
     model_floor: Optional[str] = None                # "sonnet" = nunca usar menos que sonnet
     model_ceiling: Optional[str] = None              # "sonnet" = nunca usar mas que sonnet

     # -- Cache --
     cache_enabled: bool = False
     cache_ttl_hours: int = 24

     # -- Predictions --
     show_cost_predictions: bool = False              # Mostrar estimacion antes de ejecutar

 Autonomia: 4 niveles claros

 Nivel: manual
 Que hace GIMO: Solo registra costes. No toca nada.
 Que decide el usuario: Todo: modelo, provider, budget
 ────────────────────────────────────────
 Nivel: advisory
 Que hace GIMO: Sugiere optimizaciones en el dashboard. No actua.
 Que decide el usuario: Acepta o ignora sugerencias
 ────────────────────────────────────────
 Nivel: guided
 Que hace GIMO: Aplica optimizaciones dentro de los limites configurados (floor/ceiling/budget).
 Que decide el usuario: Define las reglas: min tier, max tier, budget, thresholds
 ────────────────────────────────────────
 Nivel: autonomous
 Que hace GIMO: Cascading, eco-mode smart, ROI routing -- todo activo dentro de lo configurado
 Que decide el usuario: Configura y enciende features. GIMO opera dentro de esas reglas

 Clave: En manual y advisory, GIMO nunca cambia el modelo elegido por el usuario. En guided y autonomous, GIMO cambia
 modelo solo dentro de model_floor..model_ceiling y solo usando providers que el usuario tiene configurados.

 Modificar: tools/gimo_server/ops_models.py - OpsConfig

 Agregar campo economy: UserEconomyConfig = UserEconomyConfig() al OpsConfig existente. Eliminar los campos sueltos
 eco_mode y cascade_mode (migrar a economy.eco_mode y economy.cascade).

 Endpoint: POST /ops/config/economy y GET /ops/config/economy

 En mastery_router.py o en un nuevo economy_router.py -- CRUD para UserEconomyConfig.

 Test: tests/services/test_economy_config.py

 - Verificar serialization/deserialization
 - Verificar que autonomy_level="manual" bloquea todas las optimizaciones
 - Verificar que model_floor/ceiling se respetan

 ---
 Fase 1: Cost Persistence Layer

 Fundacion de datos reales. Sin esto, todo lo demas muestra ceros.

 Crear: tools/gimo_server/services/storage/cost_storage.py

 - CostStorage(BaseStorage) siguiendo el patron de TrustStorage
 - Tabla cost_events: id, workflow_id, node_id, model, provider, task_type, input_tokens, output_tokens, total_tokens,
 cost_usd, quality_score, cascade_level, cache_hit, duration_ms, timestamp
 - Indices en: workflow_id, model, task_type, timestamp, provider
 - Dual-write SQLite + GICS (key: ce:{workflow_id}:{node_id}:{timestamp})
 - Queries de agregacion:
   - aggregate_by_model(days) - SUM cost, tokens, COUNT por modelo
   - aggregate_by_task_type(days) - AVG cost, quality por task_type x model
   - aggregate_by_provider(days) - SUM cost por provider (para budget checks)
   - aggregate_daily(days) - series temporales dia a dia
   - get_roi_leaderboard(days) - ROI = AVG(quality) / AVG(cost) por model x task_type
   - get_spend_rate(hours) - tasa de gasto reciente
   - get_cascade_stats(days) - stats de cascading por task_type x level
   - get_cache_stats(days) - hit rate y ahorro del cache
   - get_provider_spend(provider, period) - gasto por provider en periodo (para ProviderBudget)

 Modificar: tools/gimo_server/services/storage_service.py

 - Agregar self.cost = CostStorage(...) al facade
 - Agregar CostStorage.ensure_tables() a _create_tables()

 Modificar: tools/gimo_server/ops_models.py

 - CostEvent(BaseModel) - schema del evento
 - CostAnalytics(BaseModel) - response de agregaciones
 - BudgetForecast(BaseModel) - current_spend, remaining, rate, alert_level
 - MasteryStatus(BaseModel) - status completo con datos reales

 Modificar: tools/gimo_server/services/graph_engine.py

 - En _append_step_log() (~linea 686, despues de record_node_span):
   - Emitir storage.save_cost_event() con datos extraidos del output del nodo
   - Solo si tokens_used > 0 or cost_usd > 0 (no generar eventos vacios)
   - Extraer model, task_type, provider del node.config y output dict

 Test: tests/services/test_cost_storage.py

 ---
 Fase 2: Provider Budget Enforcement

 El usuario define cuanto puede gastar por provider. GIMO lo respeta.

 Modificar: tools/gimo_server/services/model_router_service.py

 - Antes de seleccionar modelo, consultar cost_storage.get_provider_spend(provider, period)
 - Si el provider del modelo candidato ha excedido su ProviderBudget.max_cost_usd, excluirlo y elegir siguiente
 disponible
 - Si TODOS los providers estan agotados, retornar error claro: "Budget exhausted for all configured providers"
 - Solo aplica si el usuario ha configurado provider_budgets - si la lista esta vacia, no hay restriccion

 Modificar: tools/gimo_server/services/graph_engine.py

 - En _check_budget_before_step(): consultar tambien provider budgets si estan configurados
 - Proporcionar razon clara en el budget_exceeded: "Provider 'openai' exceeded monthly budget ($50.00/$50.00)"

 Test: tests/services/test_provider_budget.py

 ---
 Fase 3: Cascading Execution Engine

 Acotado a los tiers y providers que el usuario permite.

 Crear: tools/gimo_server/services/cascade_service.py

 - CascadeService con metodo execute_with_cascade(prompt, context, task_type, cascade_config, available_providers)
 - La cadena de cascading usa SOLO los tiers entre cascade_config.min_tier y cascade_config.max_tier
 - Filtra por providers que el usuario tiene configurados y con budget disponible
 - Respeta max_escalations del config del usuario
 - Evalua calidad con QualityService.analyze_output() vs cascade_config.quality_threshold
 - Retorna CascadeResult: output final, cascade_chain, total_cost, savings

 Modificar: tools/gimo_server/services/graph_engine.py

 - En _execute_llm_call(): consultar economy_config.cascade.enabled y economy_config.autonomy_level
   - manual o advisory: nunca cascade, ejecucion directa
   - guided o autonomous: cascade si cascade.enabled == True
 - Pasar cascade_config y lista de providers disponibles al CascadeService

 Mejorar: tools/gimo_server/services/quality_service.py

 - Agregar heuristicas adicionales (sin ML):
   - Respuesta vacia o solo whitespace
   - JSON invalido cuando context indica que se espera JSON
   - Output < 20 chars para task_types que esperan contenido largo
   - Deteccion de respuestas de error ("I cannot", "I'm sorry", "Error:")

 Test: tests/services/test_cascade_service.py

 ---
 Fase 4: Smart Eco-Mode (Confidence-Aware, User-Bounded)

 Modificar: tools/gimo_server/services/model_router_service.py

 - Consultar economy_config.eco_mode:
   - mode="off": no eco-mode
   - mode="binary": forzar eco_mode.floor_tier (lo que el usuario defina como piso, no siempre "local")
   - mode="smart": usar ConfidenceService con los thresholds del usuario
       - confidence >= confidence_threshold_aggressive + risk=low -> degradar a floor_tier
     - confidence >= confidence_threshold_moderate -> degradar un tier (sin bajar de floor_tier)
     - confidence < confidence_threshold_moderate -> mantener modelo
 - Siempre respetar model_floor y model_ceiling del UserEconomyConfig
 - Solo en autonomy_level guided o autonomous - en manual/advisory no aplica

 Test: tests/services/test_smart_eco_mode.py

 ---
 Fase 5: ROI Tracking & Routing Adaptativo (Opt-in)

 Modificar: tools/gimo_server/services/cost_service.py

 - Agregar calculate_roi(quality_score, cost_usd) -> float

 Modificar: tools/gimo_server/services/model_router_service.py

 - choose_model_with_roi(node, state, cost_storage):
   - Solo activo si economy_config.allow_roi_routing == True
   - Solo en autonomy_level guided o autonomous
   - Consulta ROI leaderboard del cost_storage para el task_type del nodo
   - Necesita >= 10 muestras para un combo model x task_type antes de usarlo
   - Respeta model_floor y model_ceiling siempre
   - En modo advisory: solo retorna la recomendacion, no la aplica

 Nuevo endpoint: GET /ops/mastery/recommendations

 - Retorna sugerencias de optimizacion basadas en ROI aprendido
 - Disponible en TODOS los niveles de autonomia (informativo)
 - "Para classification, haiku logra 92/100 calidad a $0.002 vs opus que logra 95/100 a $0.15"

 Test: tests/services/test_roi_routing.py

 ---
 Fase 6: Predictive Cost Estimation (Opt-in)

 Crear: tools/gimo_server/services/cost_predictor.py

 - predict_workflow_cost(nodes, state, economy_config):
   - Para cada nodo: consultar historico por task_type en cost_storage
   - Si hay datos (>= 5 muestras): usar media + stddev para intervalo
   - Si no hay datos: usar precios estaticos de CostService como fallback
   - Filtrar por providers que el usuario tiene configurados
   - Retornar: estimated_cost, confidence_interval, model_breakdown
 - Solo se muestra si economy_config.show_cost_predictions == True

 Endpoint: POST /ops/mastery/predict

 Test: tests/services/test_cost_predictor.py

 ---
 Fase 7: Normalized Cache (Opt-in)

 Modificar: tools/llm_security/cache.py

 - NormalizedLLMCache(LLMResponseCache) con normalize_prompt():
   - Strip whitespace, collapse multiple spaces/newlines
   - Lowercase, NFC unicode normalize
   - Remove markdown formatting artifacts
 - Override get_cache_key() para normalizar antes de SHA256
 - Hit/miss stats con get_hit_rate()
 - TTL configurable via economy_config.cache_ttl_hours

 Modificar: tools/gimo_server/services/provider_service.py

 - En generate(): consultar economy_config.cache_enabled
   - Si False: no cache, comportamiento actual
   - Si True: check cache antes de llamar adapter; cachear resultado despues
   - Retornar cache_hit: True/False en el output dict

 Test: tests/test_normalized_cache.py

 ---
 Fase 8: Budget Forecasting

 Crear: tools/gimo_server/services/budget_forecast_service.py

 - forecast(economy_config):
   - Solo si economy_config.global_budget_usd esta configurado
   - Consultar cost_storage.get_spend_rate(hours=24) para tasa actual
   - Calcular: remaining, remaining_pct, hours_to_exhaustion
   - Alert levels basados en economy_config.alert_thresholds (defaults: 50%, 25%, 10%)
   - Tambien forecast por provider si hay provider_budgets

 Endpoint: GET /ops/mastery/forecast

 - Retorna forecast global + per-provider

 Test: tests/services/test_budget_forecast.py

 ---
 Fase 9: Ampliar Pricing Database

 Modificar: tools/gimo_server/services/cost_service.py

 - Extraer PRICING_REGISTRY a archivo JSON: tools/gimo_server/data/model_pricing.json
 - Agregar modelos actuales (Feb 2026):
   - Claude 4.x (opus-4, sonnet-4.5, haiku-4.5)
   - GPT-4.1, GPT-4.1-mini, GPT-4.1-nano
   - Gemini 2.0 Flash, Gemini 2.5 Pro
   - DeepSeek V3, Qwen 2.5
   - Modelos locales (cost: 0)
 - CostService.get_pricing() lee el JSON al importar (una vez) con fallback a local si modelo desconocido
 - El usuario puede editar el JSON o se puede actualizar sin tocar codigo

 Crear: tools/gimo_server/data/model_pricing.json

 ---
 Fase 10: Dashboard Real + API Completa

 Backend: Reescribir tools/gimo_server/routers/ops/mastery_router.py

 Endpoints (todos autenticados):

 Metodo: GET
 Ruta: /mastery/status
 Funcion: Status completo con datos reales de cost_storage
 ────────────────────────────────────────
 Metodo: GET
 Ruta: /mastery/analytics?days=30
 Funcion: Agregaciones: daily, by_model, by_task_type, by_provider, roi_leaderboard, cascade_stats, cache_stats
 ────────────────────────────────────────
 Metodo: POST
 Ruta: /mastery/predict
 Funcion: Prediccion de coste de workflow
 ────────────────────────────────────────
 Metodo: GET
 Ruta: /mastery/forecast
 Funcion: Budget forecast global + per-provider
 ────────────────────────────────────────
 Metodo: GET
 Ruta: /mastery/recommendations
 Funcion: Sugerencias basadas en ROI aprendido
 ────────────────────────────────────────
 Metodo: GET
 Ruta: /config/economy
 Funcion: Leer UserEconomyConfig actual
 ────────────────────────────────────────
 Metodo: POST
 Ruta: /config/economy
 Funcion: Guardar UserEconomyConfig

 - /mastery/status genera tips dinamicos basados en datos reales:
   - "En los ultimos 30 dias, haiku logro 90% calidad en classification. Considera activar cascade."
   - "Tu budget de OpenAI tiene 23% restante este mes."
   - Solo si hay datos suficientes; si no, tips genericos informativos

 Frontend: Agregar recharts

 - npm install recharts en tools/orchestrator_ui/

 Agregar tipos: tools/orchestrator_ui/src/types.ts

 - UserEconomyConfig, MasteryStatus, BudgetForecast, CostAnalytics

 Crear: tools/orchestrator_ui/src/hooks/useMasteryService.ts

 - Hook que consume /mastery/status, /mastery/analytics, /mastery/forecast, /config/economy
 - Metodos: saveEconomyConfig, refresh

 Reescribir: tools/orchestrator_ui/src/components/TokenMastery.tsx

 Secciones del dashboard:

 1. Panel de Control del Usuario (siempre visible)
 - Selector de autonomia: manual / advisory / guided / autonomous (con descripcion de cada nivel)
 - Toggle eco-mode: off / binary / smart
 - Toggle cascade: on/off (con inputs para min_tier, max_tier, quality_threshold)
 - Toggle cache: on/off
 - Toggle cost predictions: on/off
 - Toggle ROI routing: on/off
 - Input de budget global (USD)
 - Lista de provider budgets (add/remove)
 - Inputs de model_floor / model_ceiling

 2. Metricas Clave (siempre visible, datos reales)
 - Total Cost USD | Total Tokens | Cache Hit Rate | Cascade Savings

 3. Coste Diario (recharts AreaChart)
 - Solo visible si hay datos (>= 2 dias de eventos)
 - Coste USD por dia + tokens por dia como overlay

 4. Desglose por Modelo (recharts BarChart)
 - Coste y calidad media por modelo

 5. ROI Leaderboard (tabla)
 - model, task_type, ROI score, avg quality, avg cost, sample count
 - Indicador visual de "recomendado" si ROI es alto y samples >= 10

 6. Budget Forecast (solo si budget configurado)
 - Progress bar con remaining %
 - "X horas restantes al ritmo actual"
 - Badges de alerta segun thresholds del usuario

 7. Recomendaciones (modo advisory y superiores)
 - Lista de sugerencias basadas en datos
 - El usuario puede aceptar o ignorar cada una

 ---
 Orden de Implementacion

 Fase 0  (UserEconomyConfig)     <- PRIMERO. Todo lo consulta.
 Fase 1  (Cost Storage)          <- SEGUNDO. Fundacion de datos.
 Fase 9  (Pricing Database)      <- Puede ir en paralelo con 1.
 Fase 2  (Provider Budgets)      <- Depende de 0 + 1.
 Fase 3  (Cascade)               <- Depende de 0 + 1.
 Fase 4  (Smart Eco-Mode)        <- Depende de 0.
 Fase 5  (ROI Routing)           <- Depende de 0 + 1.
 Fase 6  (Cost Predictor)        <- Depende de 1.
 Fase 7  (Cache)                 <- Depende de 0. Independiente del resto.
 Fase 8  (Budget Forecast)       <- Depende de 0 + 1.
 Fase 10 (Dashboard + API)       <- ULTIMO. Consume todo.

 Secuencia: 0 -> 1+9 (paralelo) -> 7 (independiente) -> 2 -> 3 -> 4 -> 5 -> 6 -> 8 -> 10

 ---
 Archivos a Crear (9)

 ┌───────────────────────────────────────────────────────┬─────────────────────────────────────────────────┐
 │                        Archivo                        │                   Descripcion                   │
 ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
 │ tools/gimo_server/services/storage/cost_storage.py    │ Persistencia de eventos de coste + agregaciones │
 ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
 │ tools/gimo_server/services/cascade_service.py         │ Motor de ejecucion en cascada                   │
 ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
 │ tools/gimo_server/services/cost_predictor.py          │ Prediccion estadistica de costes                │
 ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
 │ tools/gimo_server/services/budget_forecast_service.py │ Pronostico de agotamiento de presupuesto        │
 ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
 │ tools/gimo_server/data/model_pricing.json             │ Precios actualizados de 20+ modelos             │
 ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
 │ tools/orchestrator_ui/src/hooks/useMasteryService.ts  │ Hook React para datos de mastery                │
 ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
 │ tests/services/test_cost_storage.py                   │ Tests de persistencia + agregaciones            │
 ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
 │ tests/services/test_cascade_service.py                │ Tests de cascada                                │
 ├───────────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
 │ tests/services/test_economy_config.py                 │ Tests de autonomia + bounds                     │
 └───────────────────────────────────────────────────────┴─────────────────────────────────────────────────┘

 Archivos a Modificar (12)

 Archivo: tools/gimo_server/ops_models.py
 Cambio: UserEconomyConfig, ProviderBudget, CascadeConfig, EcoModeConfig, CostEvent, BudgetForecast, MasteryStatus;
   OpsConfig.economy
 ────────────────────────────────────────
 Archivo: tools/gimo_server/services/storage_service.py
 Cambio: Agregar CostStorage al facade
 ────────────────────────────────────────
 Archivo: tools/gimo_server/services/graph_engine.py
 Cambio: Emitir cost events; consultar economy_config para cascade; provider budget checks
 ────────────────────────────────────────
 Archivo: tools/gimo_server/services/model_router_service.py
 Cambio: Smart eco-mode con bounds; ROI routing opt-in; provider budget exclusion
 ────────────────────────────────────────
 Archivo: tools/gimo_server/services/cost_service.py
 Cambio: calculate_roi(); pricing desde JSON externo
 ────────────────────────────────────────
 Archivo: tools/gimo_server/services/quality_service.py
 Cambio: Heuristicas mejoradas (sin ML)
 ────────────────────────────────────────
 Archivo: tools/gimo_server/routers/ops/mastery_router.py
 Cambio: Endpoints reales con datos de cost_storage
 ────────────────────────────────────────
 Archivo: tools/llm_security/cache.py
 Cambio: NormalizedLLMCache con normalizacion
 ────────────────────────────────────────
 Archivo: tools/gimo_server/services/provider_service.py
 Cambio: Cache opt-in en generate()
 ────────────────────────────────────────
 Archivo: tools/orchestrator_ui/src/components/TokenMastery.tsx
 Cambio: Dashboard completo con controles + recharts
 ────────────────────────────────────────
 Archivo: tools/orchestrator_ui/src/types.ts
 Cambio: Tipos TS para economy config, analytics, forecast
 ────────────────────────────────────────
 Archivo: tools/orchestrator_ui/package.json
 Cambio: Agregar recharts

 ---
 Verificacion

 1. Autonomia manual: Configurar autonomy_level: "manual", ejecutar workflow. Verificar que GIMO NO cambia modelo, NO
 hace cascade, solo registra costes
 2. Autonomia advisory: Configurar "advisory", ejecutar. Verificar que /mastery/recommendations retorna sugerencias
 pero no se aplican
 3. Autonomia guided: Configurar "guided" con model_floor: "haiku", cascade.enabled: true. Verificar que cascade nunca
 baja de haiku
 4. Provider budget: Configurar OpenAI con max_cost_usd: 0.01. Ejecutar hasta agotar. Verificar que GIMO excluye OpenAI
  y usa alternativa o retorna error claro
 5. Cost persistence: Ejecutar workflow, luego sqlite3 .orch_data/ops/gimo_ops.db "SELECT * FROM cost_events" --
 verificar registros reales
 6. Dashboard datos reales: GET /ops/mastery/status debe retornar total_savings_usd calculado, no hardcodeado
 7. Cache: Activar cache, enviar mismo prompt 2 veces. Segunda vez debe retornar cache_hit=True, cost_usd=0
 8. Tests existentes: pytest tests/ completo debe seguir pasando (504+ tests)