from __future__ import annotations
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tools.gimo_server.services.confidence_service import ConfidenceService

@pytest.mark.asyncio
async def test_project_confidence_calls_llm_correctly():
    trust_engine = MagicMock()
    service = ConfidenceService(trust_engine=trust_engine)

    # Mock LLM response as valid JSON
    mock_data = {
        "confidence": 0.65,
        "analysis": "The task is clear but the provided context is missing authentication tokens.",
        "questions": [
            "Where should I find the auth token?",
            "Is there a specific API version?"
        ],
        "risk_level": "medium"
    }
    mock_llm_content = json.dumps(mock_data)

    with patch("tools.gimo_server.services.provider_service.ProviderService.static_generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"content": mock_llm_content, "tokens_used": 100, "cost_usd": 0.001}

        result = await service.project_confidence("Analyze API logs", {"data": "debug"})

        # Check if score is close to 0.65 (float precision)
        assert abs(result["score"] - 0.65) < 0.001
        assert "authentication tokens" in result["analysis"].lower()
        assert len(result["questions"]) == 2
        assert result["risk_level"] == "medium"
        assert result["type"] == "proactive"

@pytest.mark.asyncio
async def test_project_confidence_handles_failed_llm_gracefully():
    trust_engine = MagicMock()
    service = ConfidenceService(trust_engine=trust_engine)

    with patch("tools.gimo_server.services.provider_service.ProviderService.static_generate", side_effect=Exception("LLM Down")):
        result = await service.project_confidence("Some task", {})

        # Fallback to 0.5 (safe/doubt)
        assert abs(result["score"] - 0.5) < 0.001
        assert "evaluación fallida" in result["analysis"].lower()
