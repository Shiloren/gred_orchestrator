"""Engine public API.

Keep this module lightweight: importing `tools.gimo_server.engine.*` should not
pull optional/provider-heavy dependencies during test collection.
"""

from .contracts import StageInput, StageOutput, ExecutionStage, JournalEntry
from .pipeline import Pipeline, PipelineConfig
from .worker import RunWorker
from .journal import RunJournal
from .replay import ReplayEngine
from .risk_calibrator import RiskCalibrator
from .tools.executor import ToolExecutor, ToolExecutionResult

# Optional stage imports are guarded to avoid hard import-time failures when
# unrelated provider modules are unavailable in the environment.
try:
    from .stages.policy_gate import PolicyGate
    from .stages.risk_gate import RiskGate
    from .stages.llm_execute import LlmExecute
    from .stages.file_write import FileWrite
    from .stages.plan_stage import PlanStage
except Exception:  # pragma: no cover
    PolicyGate = None  # type: ignore[assignment]
    RiskGate = None  # type: ignore[assignment]
    LlmExecute = None  # type: ignore[assignment]
    FileWrite = None  # type: ignore[assignment]
    PlanStage = None  # type: ignore[assignment]

__all__ = [
    "StageInput",
    "StageOutput",
    "ExecutionStage",
    "JournalEntry",
    "Pipeline",
    "PipelineConfig",
    "RunWorker",
    "RunJournal",
    "ReplayEngine",
    "RiskCalibrator",
    "ToolExecutor",
    "ToolExecutionResult",
    "PolicyGate",
    "RiskGate",
    "LlmExecute",
    "FileWrite",
    "PlanStage",
]

