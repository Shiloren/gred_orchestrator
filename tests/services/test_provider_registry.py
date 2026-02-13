"""Tests for ProviderRegistry -- CRUD, templates, and health checks."""
import pytest
from unittest.mock import AsyncMock, patch

from tools.repo_orchestrator.services.provider_registry import ProviderRegistry, PROVIDER_TEMPLATES
from tools.repo_orchestrator.models import ProviderConfig


@pytest.fixture(autouse=True)
def clean_registry():
    ProviderRegistry.clear()
    yield
    ProviderRegistry.clear()


class TestProviderTemplates:
    def test_create_ollama_from_template(self):
        config = ProviderRegistry.create_from_template("ollama")
        assert config.type == "ollama"
        assert config.is_local is True
        assert config.cost_per_1k_tokens == 0.0
        assert "qwen2.5-coder:7b" in config.models
        assert config.enabled is True

    def test_create_groq_from_template(self):
        config = ProviderRegistry.create_from_template("groq", api_key="gsk_test123")
        assert config.type == "groq"
        assert config.is_local is False
        assert config.api_key == "gsk_test123"
        assert "llama-3.3-70b-versatile" in config.models

    def test_create_codex_from_template(self):
        config = ProviderRegistry.create_from_template("codex", api_key="sk-test")
        assert config.type == "codex"
        assert "gpt-4o" in config.models

    def test_create_openrouter_from_template(self):
        config = ProviderRegistry.create_from_template("openrouter", api_key="or-test")
        assert config.type == "openrouter"

    def test_unknown_template_raises(self):
        with pytest.raises(ValueError, match="Unknown provider type"):
            ProviderRegistry.create_from_template("nonexistent")

    def test_all_known_templates_exist(self):
        for ptype in ["ollama", "groq", "openrouter", "codex"]:
            assert ptype in PROVIDER_TEMPLATES


class TestProviderCRUD:
    def test_add_and_list(self):
        ProviderRegistry.create_from_template("ollama")
        providers = ProviderRegistry.list_providers()
        assert len(providers) == 1
        assert providers[0].type == "ollama"

    def test_remove_provider(self):
        config = ProviderRegistry.create_from_template("ollama")
        assert ProviderRegistry.remove_provider(config.id)
        assert len(ProviderRegistry.list_providers()) == 0

    def test_remove_nonexistent(self):
        assert ProviderRegistry.remove_provider("no-such-id") is False

    def test_get_provider(self):
        config = ProviderRegistry.create_from_template("ollama")
        fetched = ProviderRegistry.get_provider(config.id)
        assert fetched is not None
        assert fetched.id == config.id

    def test_get_enabled_providers(self):
        c1 = ProviderRegistry.create_from_template("ollama")
        c2 = ProviderRegistry.create_from_template("groq", api_key="k")
        c2.enabled = False
        enabled = ProviderRegistry.get_enabled_providers()
        assert len(enabled) == 1
        assert enabled[0].id == c1.id

    def test_multiple_providers(self):
        ProviderRegistry.create_from_template("ollama")
        ProviderRegistry.create_from_template("groq", api_key="k")
        ProviderRegistry.create_from_template("codex", api_key="k")
        assert len(ProviderRegistry.list_providers()) == 3


class TestProviderInstances:
    def test_get_ollama_instance(self):
        config = ProviderRegistry.create_from_template("ollama")
        instance = ProviderRegistry.get_instance(config.id)
        assert instance is not None
        assert instance.provider_type == "ollama"

    def test_groq_without_key_returns_none(self):
        config = ProviderRegistry.create_from_template("groq")
        # No API key, should return None
        instance = ProviderRegistry.get_instance(config.id)
        assert instance is None

    def test_groq_with_key_returns_instance(self):
        config = ProviderRegistry.create_from_template("groq", api_key="gsk_test")
        instance = ProviderRegistry.get_instance(config.id)
        assert instance is not None
        assert instance.provider_type == "groq"


class TestProviderHealth:
    @pytest.mark.asyncio
    async def test_health_check_unavailable(self):
        config = ProviderRegistry.create_from_template("groq")
        health = await ProviderRegistry.check_health(config.id)
        assert health.available is False
        assert health.error is not None

    @pytest.mark.asyncio
    async def test_health_check_with_mock(self):
        config = ProviderRegistry.create_from_template("groq", api_key="test")
        # Mock the instance
        mock_instance = AsyncMock()
        mock_instance.measure_latency = AsyncMock(return_value=42.5)
        ProviderRegistry._instances[config.id] = mock_instance

        health = await ProviderRegistry.check_health(config.id)
        assert health.available is True
        assert health.latency_ms == 42.5
