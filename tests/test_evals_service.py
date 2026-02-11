from __future__ import annotations

import pytest

from tools.gimo_server.ops_models import (
    EvalDataset,
    EvalGateConfig,
    EvalGoldenCase,
    EvalJudgeConfig,
    WorkflowGraph,
    WorkflowNode,
)
from tools.gimo_server.services.evals_service import EvalsService


@pytest.mark.asyncio
async def test_evals_service_regression_passes_all_cases():
    workflow = WorkflowGraph(
        id="wf_eval_ok",
        nodes=[WorkflowNode(id="A", type="transform", config={"result": "ok"})],
        edges=[],
    )
    dataset = EvalDataset(
        workflow_id="wf_eval_ok",
        cases=[
            EvalGoldenCase(
                case_id="c1",
                input_state={},
                expected_state={"status": "ok"},
                threshold=1.0,
            )
        ],
    )

    report = await EvalsService.run_regression(
        workflow=workflow,
        dataset=dataset,
        judge=EvalJudgeConfig(enabled=False),
        gate=EvalGateConfig(min_pass_rate=1.0, min_avg_score=1.0),
    )

    assert report.workflow_id == "wf_eval_ok"
    assert report.total_cases == 1
    assert report.passed_cases == 1
    assert report.failed_cases == 0
    assert report.pass_rate == 1.0
    assert report.avg_score == 1.0
    assert report.gate_passed is True


@pytest.mark.asyncio
async def test_evals_service_regression_fails_gate_on_mismatch():
    workflow = WorkflowGraph(
        id="wf_eval_fail",
        nodes=[WorkflowNode(id="A", type="transform", config={"result": "actual"})],
        edges=[],
    )
    dataset = EvalDataset(
        workflow_id="wf_eval_fail",
        cases=[
            EvalGoldenCase(
                case_id="c1",
                input_state={},
                expected_state={"status": "expected"},
                threshold=1.0,
            )
        ],
    )

    report = await EvalsService.run_regression(
        workflow=workflow,
        dataset=dataset,
        judge=EvalJudgeConfig(enabled=True, mode="heuristic", output_key="result"),
        gate=EvalGateConfig(min_pass_rate=1.0, min_avg_score=1.0),
    )

    assert report.total_cases == 1
    assert report.passed_cases == 0
    assert report.failed_cases == 1
    assert report.gate_passed is False
    assert report.results[0].passed is False
    assert report.results[0].score < 1.0
    assert report.results[0].reason is not None
