from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from tools.gimo_server.ops_models import NormalizedModelInfo, ProviderConfig, ProviderEntry, ProviderValidateRequest
from tools.gimo_server.services.provider_catalog_service import ProviderCatalogService
from tools.gimo_server.services.provider_service import ProviderService


def _provider_cfg_with_inline_key() -> ProviderConfig:
    return ProviderConfig(
        active="openai_main",
        providers={
            "openai_main": ProviderEntry(
                type="openai_compat",
                provider_type="openai",
                base_url="https://api.openai.com/v1",
                model="gpt-4o-mini",
                api_key="sk-test-inline",
            )
        },
    )


def test_provider_config_v2_persists_without_api_key(tmp_path: Path):
    cfg_file = tmp_path / "provider.json"
    with patch.object(ProviderService, "CONFIG_FILE", cfg_file):
        saved = ProviderService.set_config(_provider_cfg_with_inline_key())

        assert saved.schema_version == 2
        entry = saved.providers["openai_main"]
        assert entry.api_key is None
        assert entry.auth_mode == "api_key"
        assert entry.auth_ref and entry.auth_ref.startswith("env:")

        raw = json.loads(cfg_file.read_text(encoding="utf-8"))
        raw_entry = raw["providers"]["openai_main"]
        assert raw["schema_version"] == 2
        assert raw_entry.get("api_key") is None
        assert raw_entry.get("auth_ref", "").startswith("env:")
        assert "sk-test-inline" not in cfg_file.read_text(encoding="utf-8")


def test_provider_public_config_redacts_sensitive_fields(tmp_path: Path):
    cfg_file = tmp_path / "provider.json"
    with patch.object(ProviderService, "CONFIG_FILE", cfg_file):
        ProviderService.set_config(_provider_cfg_with_inline_key())
        public_cfg = ProviderService.get_public_config()

        assert public_cfg is not None
        assert public_cfg.schema_version == 2
        pub_entry = public_cfg.providers["openai_main"]
        assert pub_entry.api_key is None
        assert pub_entry.auth_ref and pub_entry.auth_ref.startswith("env:")


@pytest.mark.asyncio
async def test_catalog_cache_ttl_and_invalidation():
    ProviderCatalogService._CATALOG_CACHE.clear()

    first_installed = []
    first_available = []
    with patch.object(ProviderCatalogService, "list_installed_models", AsyncMock(return_value=first_installed)) as m_installed, \
         patch.object(ProviderCatalogService, "list_available_models", AsyncMock(return_value=(first_available, []))) as m_available:
        _ = await ProviderCatalogService.get_catalog("openai")
        _ = await ProviderCatalogService.get_catalog("openai")

        assert m_installed.await_count == 1
        assert m_available.await_count == 1

    invalidated = ProviderCatalogService.invalidate_cache(provider_type="openai", reason="credentials_changed")
    assert invalidated >= 1

    with patch.object(ProviderCatalogService, "list_installed_models", AsyncMock(return_value=[])) as m_installed2, \
         patch.object(ProviderCatalogService, "list_available_models", AsyncMock(return_value=([], []))) as m_available2:
        _ = await ProviderCatalogService.get_catalog("openai")
        assert m_installed2.await_count == 1
        assert m_available2.await_count == 1


def test_openai_account_mode_is_feature_gated(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ORCH_OPENAI_ACCOUNT_MODE_ENABLED", raising=False)
    caps_default = ProviderService.capabilities_for("openai")
    assert caps_default.get("supports_account_mode") is False
    assert "account" not in (caps_default.get("auth_modes_supported") or [])

    monkeypatch.setenv("ORCH_OPENAI_ACCOUNT_MODE_ENABLED", "true")
    caps_enabled = ProviderService.capabilities_for("openai")
    assert caps_enabled.get("supports_account_mode") is True
    assert "account" in (caps_enabled.get("auth_modes_supported") or [])


def test_codex_account_mode_is_feature_gated(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ORCH_CODEX_ACCOUNT_MODE_ENABLED", raising=False)
    caps_default = ProviderService.capabilities_for("codex")
    assert caps_default.get("supports_account_mode") is False
    assert "account" not in (caps_default.get("auth_modes_supported") or [])

    monkeypatch.setenv("ORCH_CODEX_ACCOUNT_MODE_ENABLED", "true")
    caps_enabled = ProviderService.capabilities_for("codex")
    assert caps_enabled.get("supports_account_mode") is True
    assert "account" in (caps_enabled.get("auth_modes_supported") or [])


def test_localhost_11434_entry_normalizes_to_ollama_local(tmp_path: Path):
    cfg_file = tmp_path / "provider.json"
    cfg = ProviderConfig(
        active="local_ollama",
        providers={
            "local_ollama": ProviderEntry(
                type="openai_compat",
                provider_type="custom_openai_compatible",
                base_url="http://localhost:11434/v1",
                model="qwen2.5-coder:7b",
            )
        },
    )
    with patch.object(ProviderService, "CONFIG_FILE", cfg_file):
        saved = ProviderService.set_config(cfg)
        entry = saved.providers["local_ollama"]
        assert entry.provider_type == "ollama_local"
        assert entry.capabilities.get("requires_remote_api") is False


@pytest.mark.asyncio
async def test_validate_updates_effective_state_snapshot(tmp_path: Path):
    cfg_file = tmp_path / "provider.json"
    with patch.object(ProviderService, "CONFIG_FILE", cfg_file):
        ProviderService.set_config(_provider_cfg_with_inline_key())

        with patch.object(
            ProviderCatalogService,
            "_fetch_remote_models",
            AsyncMock(return_value=[NormalizedModelInfo(id="gpt-4o-mini", label="gpt-4o-mini")]),
        ):
            result = await ProviderCatalogService.validate_credentials(
                "openai",
                ProviderValidateRequest(api_key="sk-any"),
            )

        assert result.valid is True
        saved = ProviderService.get_config()
        assert saved is not None
        assert saved.effective_state.get("health") == "ok"
        assert saved.effective_state.get("valid") is True
        assert saved.effective_state.get("effective_model") == "gpt-4o-mini"


def test_account_mode_storage_uses_env_auth_ref(tmp_path: Path):
    cfg_file = tmp_path / "provider.json"
    cfg = ProviderConfig(
        active="openai_main",
        providers={
            "openai_main": ProviderEntry(
                type="openai_compat",
                provider_type="openai",
                base_url="https://api.openai.com/v1",
                model="gpt-4o-mini",
                auth_mode="account",
                auth_ref="acct-inline-token",
            )
        },
    )

    with patch.object(ProviderService, "CONFIG_FILE", cfg_file):
        saved = ProviderService.set_config(cfg)
        entry = saved.providers["openai_main"]
        assert entry.auth_mode == "account"
        assert entry.auth_ref and entry.auth_ref.startswith("env:")
        assert "acct-inline-token" not in cfg_file.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_catalog_can_resolve_saved_api_key_for_remote_provider(tmp_path: Path):
    cfg_file = tmp_path / "provider.json"
    with patch.object(ProviderService, "CONFIG_FILE", cfg_file):
        ProviderService.set_config(_provider_cfg_with_inline_key())
        payload = ProviderCatalogService._resolve_payload_from_provider_config("openai")
        assert payload is not None
        assert payload.api_key == "sk-test-inline"


@pytest.mark.asyncio
async def test_validate_account_env_ref_resolves_before_remote_call(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ORCH_OPENAI_ACCOUNT_MODE_ENABLED", "true")
    monkeypatch.setenv("ORCH_TEST_ACCOUNT_TOKEN", "acct-real-token")

    captured: dict[str, str | None] = {}

    async def _fake_fetch(provider_type: str, payload: ProviderValidateRequest):
        captured["provider_type"] = provider_type
        captured["account"] = payload.account
        return [NormalizedModelInfo(id="gpt-4o-mini", label="gpt-4o-mini")]

    with patch.object(ProviderCatalogService, "_fetch_remote_models", side_effect=_fake_fetch):
        result = await ProviderCatalogService.validate_credentials(
            "openai",
            ProviderValidateRequest(account="env:ORCH_TEST_ACCOUNT_TOKEN"),
        )

    assert result.valid is True
    assert captured.get("provider_type") == "openai"
    assert captured.get("account") == "acct-real-token"
