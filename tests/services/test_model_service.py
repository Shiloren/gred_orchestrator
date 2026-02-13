import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from tools.repo_orchestrator.services.model_service import ModelService
from tools.repo_orchestrator.services.providers.ollama_provider import OllamaProvider
from tools.repo_orchestrator.services.provider_registry import ProviderRegistry


@pytest.fixture(autouse=True)
def reset_model_service():
    ModelService._legacy_provider = None
    ProviderRegistry.clear()
    yield
    ModelService._legacy_provider = None
    ProviderRegistry.clear()


def test_initialize_ollama():
    ModelService.initialize("ollama", base_url="http://localhost:11434")
    assert ModelService._legacy_provider is not None
    assert isinstance(ModelService._legacy_provider, OllamaProvider)


def test_initialize_custom_url():
    ModelService.initialize("ollama", base_url="http://gpu-server:11434")
    assert ModelService._legacy_provider.base_url == "http://gpu-server:11434"


def test_initialize_via_registry():
    ModelService.initialize("groq", api_key="gsk_test")
    # Should have created via registry
    assert len(ProviderRegistry.list_providers()) == 1


@pytest.mark.asyncio
async def test_generate_not_initialized():
    with pytest.raises(RuntimeError, match="not initialized"):
        await ModelService.generate("prompt", "llama3")


@pytest.mark.asyncio
async def test_generate_success():
    mock_provider = AsyncMock()
    mock_provider.generate.return_value = "Generated text"
    ModelService._legacy_provider = mock_provider

    result = await ModelService.generate("prompt", "llama3", temperature=0.5)

    assert result == "Generated text"
    mock_provider.generate.assert_called_once_with("prompt", "llama3", temperature=0.5)


@pytest.mark.asyncio
async def test_is_backend_ready_not_initialized():
    result = await ModelService.is_backend_ready()
    assert result is False


@pytest.mark.asyncio
async def test_is_backend_ready_available():
    mock_provider = AsyncMock()
    mock_provider.check_availability.return_value = True
    ModelService._legacy_provider = mock_provider

    result = await ModelService.is_backend_ready()
    assert result is True


@pytest.mark.asyncio
async def test_is_backend_ready_unavailable():
    mock_provider = AsyncMock()
    mock_provider.check_availability.return_value = False
    ModelService._legacy_provider = mock_provider

    result = await ModelService.is_backend_ready()
    assert result is False
