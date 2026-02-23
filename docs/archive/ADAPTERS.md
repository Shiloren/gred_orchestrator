# GIMO Adapter Configuration Guide

This guide details how to configure and use the various LLM adapters available in GIMO.

## Compatibility Matrix

| Adapter | Supported Models | Protocol | Streaming | Tools | Metrics |
|---------|------------------|----------|-----------|-------|---------|
| `OpenAICompatibleAdapter` | Ollama, LM Studio, vLLM, DeepSeek, OpenAI | HTTP/JSON | Yes | Yes (Limited) | Yes |
| `ClaudeCodeAdapter` | Claude Code CLI | Stdio/MCP | Yes | Yes | Yes |
| `GeminiAdapter` | Gemini CLI | Stdio/JSON | Yes | Yes | Yes |
| `CodexAdapter` | Custom Codex CLI | Stdio/JSON | Yes | Yes | Yes |
| `GenericCLIAdapter` | Any CLI | Stdio/Text | Yes | No | No |

## Configuration (`provider.json`)

Adapters are configured in `provider.json` under the `models` section.

### Ollama (Recommended for Local Dev)
```json
{
  "ollama-llama3": {
    "provider": "openai_compatible",
    "base_url": "http://localhost:11434/v1",
    "model_name": "llama3",
    "context_window": 8192
  }
}
```

### LM Studio
```json
{
  "lmstudio-mistral": {
    "provider": "openai_compatible",
    "base_url": "http://localhost:1234/v1",
    "model_name": "mistral-instruct",
    "context_window": 32768
  }
}
```

### vLLM / DeepSeek
```json
{
  "vllm-deepseek-coder": {
    "provider": "openai_compatible",
    "base_url": "http://vllm-server:8000/v1",
    "model_name": "deepseek-coder",
    "api_key": "EMPTY"
  }
}
```

## Usage Examples

### Python Usage
```python
from tools.gimo_server.adapters.openai_compatible import OpenAICompatibleAdapter

adapter = OpenAICompatibleAdapter(
    base_url="http://localhost:11434/v1",
    model_name="llama3"
)

session = await adapter.spawn(task="Refactor this code")
# ... interact with session
```

---

## Providers (OPS canónico)

Desde esta fase, la **fuente única de verdad** para providers es OPS:

- `GET /ops/provider`
- `PUT /ops/provider`
- `GET /ops/provider/capabilities`
- `GET /ops/connectors`
- `GET /ops/connectors/{connector_id}/health`

Los endpoints legacy `/ui/providers` se mantienen en **fase puente** y devuelven payload marcado como `deprecated`.

### Taxonomía canónica `provider_type`

- `ollama_local`
- `openai`
- `codex`
- `groq`
- `openrouter`
- `custom_openai_compatible`

### Aliases legacy (compatibilidad gradual)

- `ollama` -> `ollama_local`
- `local_ollama` -> `ollama_local`
- `openai_compat` -> `custom_openai_compatible`
- `custom` -> `custom_openai_compatible`

### Capability Matrix (por `provider_type`)

Cada provider declara:

- `auth_modes_supported`
- `can_install`
- `install_method`
- `supports_account_mode`
- `supports_recommended_models`
- `requires_remote_api`

Matriz actual de referencia:

| provider_type | auth_modes_supported | can_install | install_method | supports_account_mode | supports_recommended_models | requires_remote_api |
|---|---|---:|---|---:|---:|---:|
| `ollama_local` | `none`, `api_key_optional` | ✅ | `local_runtime` | ❌ | ✅ | ❌ |
| `openai` | `api_key` (+ `account` con feature flag de entorno) | ❌ | `none` | feature-gated | ✅ | ✅ |
| `codex` | `api_key` (+ `account` con feature flag de entorno) | ✅ | `cli` | feature-gated | ✅ | ✅ |
| `groq` | `api_key` | ❌ | `none` | ❌ | ✅ | ✅ |
| `openrouter` | `api_key` | ❌ | `none` | ❌ | ✅ | ✅ |
| `custom_openai_compatible` | `none`, `api_key` | ❌ | `none` | ❌ | ❌ | ✅ |

### Seguridad por defecto

- Las respuestas públicas de providers redaccionan secretos (`api_key` nunca se expone).
- El puente legacy mantiene la misma redacción.
- Auditoría de operaciones sin exponer token crudo.
