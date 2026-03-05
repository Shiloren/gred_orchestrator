import pytest

from tools.gimo_server.services.codex_auth_service import CodexAuthService


@pytest.mark.asyncio
async def test_codex_auth_service_returns_actionable_error_when_cli_missing(monkeypatch):
    monkeypatch.setattr("tools.gimo_server.services.codex_auth_service.shutil.which", lambda _: None)

    result = await CodexAuthService.start_device_flow()

    assert result["status"] == "error"
    assert "Codex CLI no detectado" in result["message"]
    assert result["action"] == "npm install -g @openai/codex"
