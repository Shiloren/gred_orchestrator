import pytest
from unittest.mock import AsyncMock, patch
from tools.gimo_server.services.provider_service import ProviderService

@pytest.mark.asyncio
async def test_provider_service_returns_metrics():
    # Mock adapter response
    mock_response = {
        "content": "Hello world",
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50
        }
    }

    with patch("tools.gimo_server.services.provider_service.ProviderService._build_adapter") as mock_build:
        adapter = AsyncMock()
        adapter.generate.return_value = mock_response
        adapter.model = "claude-3-5-sonnet-20241022"
        mock_build.return_value = adapter

        # Mock config
        mock_cfg = AsyncMock()
        mock_cfg.active = "test_provider"
        mock_cfg.providers = {"test_provider": AsyncMock(model="claude-3-5-sonnet-20241022")}

        with patch("tools.gimo_server.services.provider_service.ProviderService.get_config", return_value=mock_cfg):
            result = await ProviderService.static_generate("test prompt", {})

            assert result["content"] == "Hello world"
            assert result["tokens_used"] == 150
            assert result["prompt_tokens"] == 100
            assert result["completion_tokens"] == 50
            # Sonnet pricing: $3/1M input, $15/1M output
            # 100 * 3/1M + 50 * 15/1M = 0.0003 + 0.00075 = 0.00105
            assert result["cost_usd"] == 0.00105
            assert result["provider"] == "test_provider"

@pytest.mark.asyncio
async def test_provider_service_handles_missing_usage_gracefully():
    # Mock adapter response without usage
    mock_response = {
        "content": "Hello world"
    }

    with patch("tools.gimo_server.services.provider_service.ProviderService._build_adapter") as mock_build:
        adapter = AsyncMock()
        adapter.generate.return_value = mock_response
        adapter.model = "local"
        mock_build.return_value = adapter

        mock_cfg = AsyncMock()
        mock_cfg.active = "local"
        mock_cfg.providers = {"local": AsyncMock(model="local")}

        with patch("tools.gimo_server.services.provider_service.ProviderService.get_config", return_value=mock_cfg):
            result = await ProviderService.static_generate("test prompt", {})

            assert result["content"] == "Hello world"
            assert result["tokens_used"] == 0
            assert result["cost_usd"] == 0.0
