"""Lazy stage exports.

Avoid importing provider-heavy modules at package import time.
"""

from importlib import import_module
from typing import Any

_STAGE_MAP = {
    "PolicyGate": ("tools.gimo_server.engine.stages.policy_gate", "PolicyGate"),
    "RiskGate": ("tools.gimo_server.engine.stages.risk_gate", "RiskGate"),
    "LlmExecute": ("tools.gimo_server.engine.stages.llm_execute", "LlmExecute"),
    "PlanStage": ("tools.gimo_server.engine.stages.plan_stage", "PlanStage"),
    "FileWrite": ("tools.gimo_server.engine.stages.file_write", "FileWrite"),
    "GitPipeline": ("tools.gimo_server.engine.stages.git_pipeline", "GitPipeline"),
    "QaGate": ("tools.gimo_server.engine.stages.qa_gate", "QaGate"),
    "Critic": ("tools.gimo_server.engine.stages.critic", "Critic"),
}


def __getattr__(name: str) -> Any:
    ref = _STAGE_MAP.get(name)
    if not ref:
        raise AttributeError(name)
    module_name, class_name = ref
    module = import_module(module_name)
    return getattr(module, class_name)


__all__ = list(_STAGE_MAP.keys())
