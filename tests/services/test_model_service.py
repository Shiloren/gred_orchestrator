import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from tools.repo_orchestrator.services.model_service import ModelService
from tools.repo_orchestrator.services.provider_registry import ProviderRegistry


@pytest.fixture(autouse=True)
def reset_model_service():
    ModelService._legacy_default = None
    ProviderRegistry.clear()
    yield
    ModelService._legacy_default = None
    ProviderRegistry.clear()


def test_initialize_ollama():
    ModelService.initialize("ollama", base_url="http://localhost:11434")
    assert ModelService._legacy_default is not None


def test_initialize_custom_url():
    ModelService.initialize("ollama", base_url="http://gpu-server:11434")
    assert ModelService._legacy_default is not None
    assert ModelService._legacy_default.config["base_url"] == "http://gpu-server:11434"


def test_initialize_default():
    ModelService.initialize("ollama")
    assert ModelService._legacy_default is not None


@pytest.mark.asyncio
async def test_generate_no_providers_no_legacy():
    with pytest.raises(RuntimeError, match="No available AI providers"):
        await ModelService.generate("prompt", "model")


@pytest.mark.asyncio
async def test_generate_with_legacy_fallback():
    mock_provider = AsyncMock()
    mock_provider.generate.return_value = "Generated text"
    ModelService._legacy_default = mock_provider

    result = await ModelService.generate("prompt", "model", temperature=0.5)
    assert result == "Generated text"


@pytest.mark.asyncio
async def test_is_backend_ready_not_initialized():
    result = await ModelService.is_backend_ready()
    assert result is False


@pytest.mark.asyncio
async def test_is_backend_ready_with_provider():
    mock_provider = AsyncMock()
    mock_provider.check_availability.return_value = True
    ModelService._legacy_default = mock_provider

    result = await ModelService.is_backend_ready()
    assert result is True


@pytest.mark.asyncio
async def test_is_backend_ready_unavailable():
    mock_provider = AsyncMock()
    mock_provider.check_availability.return_value = False
    ModelService._legacy_default = mock_provider

    result = await ModelService.is_backend_ready()
    assert result is False
