import pytest
from tools.gimo_server.services.quality_service import QualityService

def test_analyze_output_good():
    text = "This is a high quality output with no repetition and sufficient length for reasoning."
    result = QualityService.analyze_output(text)
    assert result.score == 100
    assert result.alerts == []

def test_analyze_output_repetition():
    text = "Repeating a long phrase multiple times here. Repeating a long phrase multiple times here. Repeating a long phrase multiple times here. Repeating a long phrase multiple times here. Repeating a long phrase multiple times here."
    result = QualityService.analyze_output(text)
    assert "high_repetition_rate" in result.alerts
    assert result.score < 100

def test_analyze_output_empty():
    result = QualityService.analyze_output("")
    assert result.score == 0
    assert "empty_output" in result.alerts

def test_analyze_output_error_phrase():
    text = "I'm sorry, I cannot fulfill this request due to content policy."
    result = QualityService.analyze_output(text)
    assert result.score < 50
    assert result.heuristics["has_error_phrase"] is True

def test_analyze_output_invalid_json():
    text = "Here is your data: {broken json"
    result = QualityService.analyze_output(text, expected_format="json")
    assert "invalid_json_format" in result.alerts
    assert result.heuristics["invalid_json"] is True

def test_analyze_output_valid_json():
    text = '{"key": "value", "count": 42}'
    result = QualityService.analyze_output(text, expected_format="json")
    assert "invalid_json_format" not in result.alerts
