from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from .contracts import ExecutionStage, StageOutput
from .pipeline import Pipeline

logger = logging.getLogger(__name__)

class RunWorker:
    """
    Slim version of the worker that delegates to the Pipeline.
    """
    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
        self.pipeline: Optional[Pipeline] = None

    async def execute_plan(self, stages: List[ExecutionStage], initial_context: Dict[str, Any]) -> StageOutput:
        self.pipeline = Pipeline(run_id=self.run_id, stages=stages)
        logger.info(f"Starting execution plan for run_id={self.run_id}")
        return await self.pipeline.run(initial_context)
