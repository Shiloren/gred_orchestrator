from __future__ import annotations

import os
from typing import Any, Dict, Optional


class ProviderCapabilityService:
    """Single-responsibility service for provider taxonomy and capability matrix."""

    _PROVIDER_TYPE_ALIASES = {
        "ollama": "ollama_local",
        "local_ollama": "ollama_local",
        "ollama_local": "ollama_local",
        "openai_compat": "custom_openai_compatible",
        "custom": "custom_openai_compatible",
        "openai": "openai",
        "codex": "codex",
        "groq": "groq",
        "openrouter": "openrouter",
        "custom_openai_compatible": "custom_openai_compatible",
    }

    _CAPABILITY_MATRIX: Dict[str, Dict[str, Any]] = {
        "ollama_local": {
            "auth_modes_supported": ["none", "api_key_optional"],
            "can_install": True,
            "install_method": "local_runtime",
            "supports_account_mode": False,
            "supports_recommended_models": True,
            "requires_remote_api": False,
        },
        "openai": {
            "auth_modes_supported": ["api_key"],
            "can_install": False,
            "install_method": "none",
            "supports_account_mode": False,
            "supports_recommended_models": True,
            "requires_remote_api": True,
        },
        "codex": {
            "auth_modes_supported": ["api_key"],
            "can_install": True,
            "install_method": "cli",
            "supports_account_mode": False,
            "supports_recommended_models": True,
            "requires_remote_api": True,
        },
        "groq": {
            "auth_modes_supported": ["api_key"],
            "can_install": False,
            "install_method": "none",
            "supports_account_mode": False,
            "supports_recommended_models": True,
            "requires_remote_api": True,
        },
        "openrouter": {
            "auth_modes_supported": ["api_key"],
            "can_install": False,
            "install_method": "none",
            "supports_account_mode": False,
            "supports_recommended_models": True,
            "requires_remote_api": True,
        },
        "custom_openai_compatible": {
            "auth_modes_supported": ["none", "api_key"],
            "can_install": False,
            "install_method": "none",
            "supports_account_mode": False,
            "supports_recommended_models": False,
            "requires_remote_api": True,
        },
    }

    @classmethod
    def normalize_provider_type(cls, raw_type: Optional[str]) -> str:
        key = (raw_type or "custom_openai_compatible").strip().lower()
        return cls._PROVIDER_TYPE_ALIASES.get(key, "custom_openai_compatible")

    @classmethod
    def _is_account_mode_enabled(cls, provider_type: str) -> bool:
        canonical = cls.normalize_provider_type(provider_type)
        if canonical == "openai":
            return str(os.environ.get("ORCH_OPENAI_ACCOUNT_MODE_ENABLED", "")).strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        if canonical == "codex":
            return str(os.environ.get("ORCH_CODEX_ACCOUNT_MODE_ENABLED", "")).strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        return False

    @classmethod
    def capabilities_for(cls, provider_type: Optional[str]) -> Dict[str, Any]:
        canonical = cls.normalize_provider_type(provider_type)
        caps = dict(cls._CAPABILITY_MATRIX.get(canonical, cls._CAPABILITY_MATRIX["custom_openai_compatible"]))
        if canonical in {"openai", "codex"}:
            supports_account = cls._is_account_mode_enabled(canonical)
            caps["supports_account_mode"] = supports_account
            auth_modes = list(caps.get("auth_modes_supported") or [])
            if supports_account and "account" not in auth_modes:
                auth_modes.append("account")
            if not supports_account:
                auth_modes = [m for m in auth_modes if m != "account"]
            caps["auth_modes_supported"] = auth_modes
        return caps

    @classmethod
    def get_capability_matrix(cls) -> Dict[str, Dict[str, Any]]:
        return {k: cls.capabilities_for(k) for k in cls._CAPABILITY_MATRIX.keys()}
