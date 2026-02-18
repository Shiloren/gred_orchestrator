"""ProviderRegistry — CRUD, templates, instances, and health checks.

Manages the lifecycle of LLM provider connections.  Providers are created
from predefined templates or custom configs and stored as ``ProviderConfig``
objects.  Adapter *instances* are lazily created when first requested via
``get_instance``.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .providers.base_provider import BaseProvider
from .providers.ollama_provider import OllamaProvider
from .providers.groq_provider import GroqProvider
from .providers.codex_provider import CodexProvider
from .providers.openrouter_provider import OpenRouterProvider

logger = logging.getLogger("orchestrator.provider_registry")

# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------

PROVIDER_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "ollama": {
        "type": "ollama",
        "name": "Ollama (local)",
        "is_local": True,
        "base_url": "http://localhost:11434",
        "cost_per_1k_tokens": 0.0,
        "models": [
            "qwen2.5-coder:7b",
            "qwen2.5-coder:1.5b",
            "llama3.2:3b",
            "deepseek-coder:6.7b",
        ],
    },
    "groq": {
        "type": "groq",
        "name": "Groq Cloud",
        "is_local": False,
        "base_url": "https://api.groq.com/openai/v1",
        "cost_per_1k_tokens": 0.0003,
        "max_context": 32768,
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ],
    },
    "codex": {
        "type": "codex",
        "name": "OpenAI / Codex",
        "is_local": False,
        "base_url": "https://api.openai.com/v1",
        "cost_per_1k_tokens": 0.01,
        "max_context": 128000,
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "codex-mini-latest",
        ],
    },
    "openrouter": {
        "type": "openrouter",
        "name": "OpenRouter",
        "is_local": False,
        "base_url": "https://openrouter.ai/api/v1",
        "cost_per_1k_tokens": 0.001,
        "models": [
            "meta-llama/llama-3.1-8b-instruct:free",
            "google/gemma-2-9b-it:free",
        ],
    },
}

_PROVIDER_FACTORY = {
    "ollama": OllamaProvider,
    "groq": GroqProvider,
    "codex": CodexProvider,
    "openrouter": OpenRouterProvider,
}


class ProviderRegistry:
    """Central registry for LLM provider configurations and instances."""

    # Stores ProviderConfig objects keyed by id
    _providers: Dict[str, Any] = {}
    # Stores live adapter instances keyed by provider id
    _instances: Dict[str, BaseProvider] = {}

    # ------------------------------------------------------------------
    # Template helpers
    # ------------------------------------------------------------------

    @classmethod
    def create_from_template(cls, template: str, **overrides) -> Any:
        """Create and register a provider from a predefined template.

        Returns the ``ProviderConfig`` object (from models.py).
        """
        if template not in PROVIDER_TEMPLATES:
            raise ValueError(f"Unknown provider type: {template}")

        # Lazy import to avoid circular deps
        from tools.repo_orchestrator.models import ProviderConfig

        base = PROVIDER_TEMPLATES[template].copy()
        provider_id = overrides.pop("id", f"{template}_{uuid.uuid4().hex[:8]}")
        base["id"] = provider_id

        # Merge overrides
        for k, v in overrides.items():
            base[k] = v

        config = ProviderConfig(**base)
        cls._providers[config.id] = config
        logger.info(f"Registered provider from template: {config.id} ({template})")
        return config

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @classmethod
    def register_provider(cls, config) -> str:
        """Register a provider from a dict or ProviderConfig.

        Returns provider_id.
        """
        if isinstance(config, dict):
            p_type = config.get("type")
            p_id = config.get("id")

            if not p_type or not p_id:
                raise ValueError("Provider config must have 'type' and 'id'")

            if p_id in cls._providers:
                logger.warning(f"Provider {p_id} already exists. Overwriting.")

            provider: Optional[BaseProvider] = None
            factory = _PROVIDER_FACTORY.get(p_type)
            if factory:
                provider = factory(p_id, config)
            else:
                raise ValueError(f"Unknown provider type: {p_type}")

            cls._providers[p_id] = config
            cls._instances[p_id] = provider
            logger.info(f"Registered provider: {p_id} ({p_type})")
            return p_id
        else:
            # Assume ProviderConfig-like object
            cls._providers[config.id] = config
            logger.info(f"Registered provider: {config.id}")
            return config.id

    @classmethod
    def get_provider(cls, p_id: str) -> Optional[Any]:
        return cls._providers.get(p_id)

    @classmethod
    def list_providers(cls) -> List[Any]:
        """Return list of ProviderConfig objects (or raw dicts for legacy callers)."""
        return list(cls._providers.values())

    @classmethod
    def get_enabled_providers(cls) -> List[Any]:
        """Return only providers with ``enabled=True``."""
        results = []
        for p in cls._providers.values():
            enabled = getattr(p, "enabled", True)
            if enabled:
                results.append(p)
        return results

    @classmethod
    def remove_provider(cls, p_id: str) -> bool:
        if p_id in cls._providers:
            del cls._providers[p_id]
            cls._instances.pop(p_id, None)
            logger.info(f"Removed provider: {p_id}")
            return True
        return False

    @classmethod
    def get_all(cls) -> List[Any]:
        return list(cls._providers.values())

    # ------------------------------------------------------------------
    # Instance management
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls, p_id: str) -> Optional[BaseProvider]:
        """Return a live adapter instance for the given provider id.

        Lazily creates the instance if it doesn't exist yet.  Returns
        ``None`` if the provider requires an API key that is missing.
        """
        if p_id in cls._instances:
            return cls._instances[p_id]

        config = cls._providers.get(p_id)
        if config is None:
            return None

        p_type = getattr(config, "type", None)
        api_key = getattr(config, "api_key", None)

        # Cloud providers need an API key
        if p_type in ("groq", "codex", "openrouter") and not api_key:
            return None

        factory = _PROVIDER_FACTORY.get(p_type)
        if factory is None:
            return None

        cfg_dict = config.model_dump() if hasattr(config, "model_dump") else dict(config)
        instance = factory(p_id, cfg_dict)
        cls._instances[p_id] = instance
        return instance

    # ------------------------------------------------------------------
    # Health checks
    # ------------------------------------------------------------------

    @classmethod
    async def check_health(cls, p_id: str) -> Any:
        """Check availability and latency of a provider."""
        from tools.repo_orchestrator.models import ProviderHealth

        instance = cls.get_instance(p_id)
        now = datetime.now(timezone.utc).isoformat()

        if instance is None:
            return ProviderHealth(
                provider_id=p_id,
                available=False,
                error="No instance available (missing API key or unknown provider)",
                last_check=now,
            )

        try:
            latency = await instance.measure_latency()
            return ProviderHealth(
                provider_id=p_id,
                available=True,
                latency_ms=latency,
                last_check=now,
            )
        except Exception as exc:
            return ProviderHealth(
                provider_id=p_id,
                available=False,
                error=str(exc),
                last_check=now,
            )

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    @classmethod
    def clear(cls) -> None:
        """Reset all providers and instances.  Used in tests."""
        cls._providers.clear()
        cls._instances.clear()
