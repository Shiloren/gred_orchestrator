import pytest
from tools.repo_orchestrator.services.quality_service import QualityService

def test_get_agent_quality_orchestrator():
    result = QualityService.get_agent_quality("api")
    assert result.score == 98
    assert result.alerts == []
    assert result.lastCheck is not None

def test_get_agent_quality_bridge():
    result = QualityService.get_agent_quality("tunnel-bridge")
    assert result.score == 65
    assert "repetition" in result.alerts

def test_analyze_output_good():
    text = "This is a high quality output with no repetition and sufficient length for reasoning."
    result = QualityService.analyze_output(text)
    assert result.score == 100
    assert result.alerts == []

def test_analyze_output_repetition():
    text = "Repeating a long phrase multiple times. Repeating a long phrase multiple times. Repeating a long phrase multiple times. Repeating a long phrase multiple times. Repeating a long phrase multiple times."
    result = QualityService.analyze_output(text)
    assert "repetition" in result.alerts
    assert result.score < 100

def test_analyze_output_short():
    text = "Too short."
    result = QualityService.analyze_output(text)
    assert "coherence" in result.alerts
    assert result.score < 100
