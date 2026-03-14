from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tools.gimo_server.engine.contracts import StageOutput
from tools.gimo_server.services.engine_service import EngineService

import tools.gimo_server.engine as engine_pkg
import tools.gimo_server.engine.stages as stages_pkg

# Ensure dotted patch path resolution works consistently in all environments.
setattr(engine_pkg, "stages", stages_pkg)


@pytest.mark.asyncio
async def test_engine_service_routes_known_compositions() -> None:
    """EngineService must route supported compositions into Pipeline.run."""
    with patch("tools.gimo_server.engine.pipeline.Pipeline.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = []

        await EngineService.run_composition("merge_gate", "test_run_1", {"k": "v"})
        await EngineService.run_composition("custom_plan", "test_run_2", {"k": "v"})

        assert mock_run.await_count == 2


@pytest.mark.asyncio
async def test_engine_service_rejects_unknown_composition() -> None:
    with pytest.raises(ValueError, match="Unknown composition"):
        await EngineService.run_composition("not_valid", "test_run", {})


@pytest.mark.asyncio
async def test_pipeline_execution_flow() -> None:
    """Pipeline should execute stage with StageInput carrying initial context."""
    mock_stage = AsyncMock()
    mock_stage.name = "test_stage"
    mock_stage.execute.return_value = StageOutput(status="continue", artifacts={"ok": True})

    from tools.gimo_server.engine.pipeline import Pipeline

    pipeline = Pipeline(run_id="r_test", stages=[mock_stage])
    outputs = await pipeline.run({"input": "hello"})

    assert len(outputs) == 1
    assert outputs[0].status == "continue"
    args, _kwargs = mock_stage.execute.call_args
    assert args[0].context["input"] == "hello"


@pytest.mark.asyncio
async def test_policy_gate_integration_happy_path() -> None:
    """PolicyGate should propagate policy+intent artifacts and continue on allow."""
    from tools.gimo_server.engine.contracts import StageInput
    from tools.gimo_server.engine.stages.policy_gate import PolicyGate

    fake_policy = MagicMock()
    fake_policy.decision = "allow"
    fake_policy.status_code = "POLICY_ALLOW"
    fake_policy.model_dump.return_value = {"decision": "allow", "status_code": "POLICY_ALLOW"}

    fake_intent = MagicMock()
    fake_intent.execution_decision = "AUTO_RUN_ELIGIBLE"
    fake_intent.model_dump.return_value = {
        "intent_effective": "SAFE_REFACTOR",
        "execution_decision": "AUTO_RUN_ELIGIBLE",
    }

    with patch(
        "tools.gimo_server.engine.stages.policy_gate.RuntimePolicyService.evaluate_draft_policy",
        return_value=fake_policy,
    ), patch(
        "tools.gimo_server.engine.stages.policy_gate.IntentClassificationService.evaluate",
        return_value=fake_intent,
    ):
        stage = PolicyGate()
        output = await stage.execute(StageInput(run_id="r_policy", context={}))

    assert output.status == "continue"
    assert output.artifacts["execution_decision"] == "AUTO_RUN_ELIGIBLE"
