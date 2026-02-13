"""Tests for ModelRouter -- task classification and routing logic."""
import pytest
from unittest.mock import AsyncMock

from tools.repo_orchestrator.services.model_router import ModelRouter, NodeManager
from tools.repo_orchestrator.services.provider_registry import ProviderRegistry
from tools.repo_orchestrator.models import ComputeNode


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
        assert result.task_type == "code_monkey"
        assert result.preferred_provider_type == "local"

    def test_architect_task(self):
        result = ModelRouter.classify_task("refactor the entire authentication module")
        assert result.task_type == "architect"
        assert result.preferred_provider_type == "cloud"

    def test_complex_keyword_architect(self):
        result = ModelRouter.classify_task("debug race condition in the WebSocket handler")
        assert result.task_type == "architect"

    def test_simple_keyword_code_monkey(self):
        result = ModelRouter.classify_task("write regex for email validation")
        assert result.task_type == "code_monkey"

    def test_long_description_defaults_to_architect(self):
        long_desc = "Please analyze the entire codebase structure and " + "x " * 200
        result = ModelRouter.classify_task(long_desc)
        assert result.task_type == "architect"

    def test_ambiguous_defaults_to_code_monkey(self):
        result = ModelRouter.classify_task("do this thing")
        assert result.task_type == "code_monkey"
        assert result.complexity == "low"


class TestNodeManager:
    def test_register_and_list_nodes(self):
        NodeManager.setup_default_nodes()
        nodes = NodeManager.get_nodes()
        assert len(nodes) == 2
        assert nodes[0].name == "The Handheld (ROG Ally X)"
        assert nodes[1].name == "The Workstation (Desktop)"

    def test_node_capacity(self):
        NodeManager.register_node(ComputeNode(
            id="test-node",
            name="Test",
            role="Test",
            max_concurrent_agents=2,
        ))
        assert NodeManager.has_capacity("test-node")
        assert NodeManager.acquire_slot("test-node")
        assert NodeManager.acquire_slot("test-node")
        assert not NodeManager.has_capacity("test-node")
        assert not NodeManager.acquire_slot("test-node")

    def test_release_slot(self):
        NodeManager.register_node(ComputeNode(
            id="test-node",
            name="Test",
            role="Test",
            max_concurrent_agents=1,
        ))
        NodeManager.acquire_slot("test-node")
        assert not NodeManager.has_capacity("test-node")
        NodeManager.release_slot("test-node")
        assert NodeManager.has_capacity("test-node")

    def test_default_nodes_constraints(self):
        NodeManager.setup_default_nodes()
        ally = NodeManager.get_node("node-a")
        desktop = NodeManager.get_node("node-b")
        assert ally.max_concurrent_agents == 2
        assert desktop.max_concurrent_agents == 4
        assert "qwen2.5-coder:1.5b" in ally.preferred_models
        assert "qwen2.5-coder:7b" in desktop.preferred_models


class TestModelRouting:
    @pytest.mark.asyncio
    async def test_route_no_providers(self):
        provider, model = await ModelRouter.route("generate test")
        assert provider is None
        assert model == ""

    @pytest.mark.asyncio
    async def test_route_with_ollama(self):
        config = ProviderRegistry.create_from_template("ollama")
        # Mock the instance
        mock_instance = AsyncMock()
        mock_instance.provider_type = "ollama"
        ProviderRegistry._instances[config.id] = mock_instance

        provider, model = await ModelRouter.route("generate test for utils")
        assert provider is not None
        assert model == "qwen2.5-coder:7b"

    @pytest.mark.asyncio
    async def test_route_prefers_cloud_for_architect(self):
        ollama = ProviderRegistry.create_from_template("ollama")
        groq = ProviderRegistry.create_from_template("groq", api_key="test")

        mock_ollama = AsyncMock()
        mock_ollama.provider_type = "ollama"
        mock_groq = AsyncMock()
        mock_groq.provider_type = "groq"

        ProviderRegistry._instances[ollama.id] = mock_ollama
        ProviderRegistry._instances[groq.id] = mock_groq

        provider, model = await ModelRouter.route("refactor the entire auth system")
        # Should prefer cloud (groq) for architect tasks
        assert provider == mock_groq

    @pytest.mark.asyncio
    async def test_route_with_model_preference(self):
        config = ProviderRegistry.create_from_template("ollama")
        mock_instance = AsyncMock()
        mock_instance.provider_type = "ollama"
        ProviderRegistry._instances[config.id] = mock_instance

        provider, model = await ModelRouter.route("do task", "llama3.2:3b")
        assert provider is not None
        assert model == "llama3.2:3b"
