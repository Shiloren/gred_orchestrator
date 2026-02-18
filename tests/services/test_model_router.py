"""Tests for ModelRouter -- task classification and routing logic."""
import pytest
from unittest.mock import AsyncMock

from tools.repo_orchestrator.services.model_router import ModelRouter, NodeManager
from tools.repo_orchestrator.services.provider_registry import ProviderRegistry


@pytest.fixture(autouse=True)
def clean_state():
    ProviderRegistry.clear()
    NodeManager.clear()
    yield
    ProviderRegistry.clear()
    NodeManager.clear()


class TestTaskClassification:
    def test_code_monkey_task(self):
        result = ModelRouter.classify_task("generate test for the utils module")
        assert result == "code_monkey"

    def test_architect_task(self):
        result = ModelRouter.classify_task("refactor the entire authentication module")
        assert result == "architect"

    def test_complex_keyword_architect(self):
        result = ModelRouter.classify_task("debug race condition in the WebSocket handler")
        assert result == "architect"

    def test_simple_keyword_code_monkey(self):
        result = ModelRouter.classify_task("write regex for email validation")
        assert result == "code_monkey"

    def test_long_description_defaults_to_code_monkey(self):
        long_desc = "do something with " + "x " * 200
        result = ModelRouter.classify_task(long_desc)
        # No architect keywords → defaults to code_monkey
        assert result == "code_monkey"

    def test_ambiguous_defaults_to_code_monkey(self):
        result = ModelRouter.classify_task("do this thing")
        assert result == "code_monkey"


class TestNodeManager:
    def test_default_nodes_exist(self):
        status = NodeManager.get_nodes_status()
        assert "ally_x" in status
        assert "desktop" in status

    def test_node_concurrency_limits(self):
        status = NodeManager.get_nodes_status()
        assert status["ally_x"]["max_concurrency"] == 2
        assert status["desktop"]["max_concurrency"] == 4

    @pytest.mark.asyncio
    async def test_acquire_and_release_slot(self):
        await NodeManager.acquire_slot("ally_x")
        status = NodeManager.get_nodes_status()
        assert status["ally_x"]["current_load"] == 1

        NodeManager.release_slot("ally_x")
        status = NodeManager.get_nodes_status()
        assert status["ally_x"]["current_load"] == 0

    def test_clear_resets_state(self):
        NodeManager.clear()
        status = NodeManager.get_nodes_status()
        assert status["ally_x"]["current_load"] == 0
        assert status["desktop"]["current_load"] == 0


class TestModelRouting:
    def test_route_no_providers(self):
        provider, model = ModelRouter.select_provider("generate test")
        assert provider is None
        assert model == ""

    def test_route_with_ollama(self):
        config = ProviderRegistry.create_from_template("ollama")
        # select_provider iterates over ProviderConfig objects (not instances)
        provider, model = ModelRouter.select_provider("generate test for utils")
        assert provider is not None
        assert provider.type == "ollama"

    def test_route_prefers_cloud_for_architect(self):
        ProviderRegistry.create_from_template("ollama")
        ProviderRegistry.create_from_template("groq", api_key="test")

        provider, model = ModelRouter.select_provider("refactor the entire auth system")
        # Should prefer cloud (groq) for architect tasks
        assert provider is not None
        assert provider.type == "groq"

    def test_route_with_preferred_type(self):
        ProviderRegistry.create_from_template("ollama")

        provider, model = ModelRouter.select_provider("do task", "ollama")
        assert provider is not None
        assert provider.type == "ollama"
