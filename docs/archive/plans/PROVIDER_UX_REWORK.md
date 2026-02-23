# PROVIDER UX REWORK — Contrato final (Fase 4)

> **DEPRECATED 2026-02-23** — Secciones UX superseded by `docs/UI_IMPROVEMENT_PLAN_2026-02-23.md`

## Objetivo

Consolidar **Providers** como dominio explícito y dejar una sola verdad operativa en OPS para:

- tipo de provider
- catálogo de modelos (instalados/disponibles/recomendados)
- instalación/activación desde UI
- validación de credenciales y health
- estado efectivo (provider/modelo/rol/error accionable)

---

## Endpoints OPS (canónicos)

### 1) Catálogo

`GET /ops/connectors/{provider_type}/models`

Retorna:

- `provider_type`
- `installed_models[]`
- `available_models[]`
- `recommended_models[]`
- `can_install`
- `install_method` (`api|command|manual`)
- `auth_modes_supported[]`
- `warnings[]`

Modelo normalizado por item:

- `id`, `label`, `context_window?`, `size?`, `installed`, `downloadable`, `quality_tier?`

### 2) Instalación / activación

`POST /ops/connectors/{provider_type}/models/install` con body `{ "model_id": "..." }`

Retorna:

- `status` (`queued|running|done|error`)
- `message`
- `progress?`
- `job_id?`

`GET /ops/connectors/{provider_type}/models/install/{job_id}`

Retorna estado de instalación para polling desde UI:

- `status` (`queued|running|done|error`)
- `message`
- `progress?`
- `job_id`

### 3) Validación de conexión / credenciales

`POST /ops/connectors/{provider_type}/validate`

Body según modo:

- `api_key` (+ `base_url` / `org` opcional)
- `account` (solo cuando el entorno lo soporta oficialmente)

Retorna:

- `valid`
- `health`
- `effective_model?`
- `warnings[]`
- `error_actionable?`

### 4) Provider activo

`PUT /ops/provider`

Persistencia v2:

- `schema_version`
- `provider_type`
- `model_id`
- `auth_mode`
- `auth_ref` (nunca secreto plano)
- `last_validated_at`
- `effective_state`
- `capabilities_snapshot`

`effective_state` mantiene snapshot no sensible y estado efectivo de runtime:

- `active`, `provider_type`, `model_id`, `auth_mode`, `auth_ref`, `base_url`, `display_name`
- `valid`, `health`, `effective_model`, `last_error_actionable`, `warnings[]`

---

## Capability Matrix (runtime)

Taxonomía canónica:

- `ollama_local`
- `openai`
- `codex`
- `groq`
- `openrouter`
- `custom_openai_compatible`

Notas de contrato:

- `supports_account_mode` en `openai/codex` queda **feature-gated por entorno**.
- Flags soportadas:
  - `ORCH_OPENAI_ACCOUNT_MODE_ENABLED=true`
  - `ORCH_CODEX_ACCOUNT_MODE_ENABLED=true`
- Si no están activadas, UI debe mostrar fallback explícito a `api_key`.
- Normalización UX: `api_key_optional` se presenta como `api_key` en UI para evitar ambigüedad.

---

## Seguridad y compliance

- Nunca retornar secretos (`api_key` redactado siempre).
- `auth_ref` referencia segura (`env:*`, vault, etc.), no secreto en claro.
- No loggear secretos.
- Auditoría requerida en:
  - cambio de provider
  - validación credenciales
  - instalación de modelo (start/success/fail)

---

## UX final en Provider Settings

La UI debe permitir:

1. Seleccionar `Provider Type`.
2. Cargar catálogo dinámico por tipo.
3. Elegir modelo agrupado en:
   - Installed
   - Available to download
   - Recommended
4. Ejecutar `Download & Use` cuando aplique.
5. Elegir autenticación dinámica (`none|api_key|account`, según capabilities).
6. Ejecutar `Test connection`.
7. Guardar con `Save as active provider`.
8. Ver estado efectivo continuo:
   - provider activo
   - modelo efectivo
   - role
   - health
   - error accionable

---

## Compatibilidad legacy

- `/ui/providers` se mantiene solo como puente (`deprecated`) leyendo/escribiendo contra OPS.
- Runtime y configuración efectiva deben depender únicamente de OPS.
