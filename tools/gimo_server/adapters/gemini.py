from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from .base import AgentAdapter, AgentSession, ProposedAction
from .generic_cli import GenericCLISession

logger = logging.getLogger("orchestrator.adapters.gemini")


class GeminiSession(GenericCLISession):
    """Session for Gemini CLI adapter."""

    PRE_TOOL_PREFIX = "GEMINI_PRE_TOOL:"
    METRICS_PREFIX = "GEMINI_METRICS:"
    ALLOW_CMD_PREFIX = "GEMINI_ALLOW"
    DENY_CMD_PREFIX = "GEMINI_DENY"

    def _handle_stdout_line(self, line: str) -> None:
        if line.startswith(self.PRE_TOOL_PREFIX):
            payload = line[len(self.PRE_TOOL_PREFIX):].strip()
            super()._handle_stdout_line(f"{self.PROPOSAL_PREFIX}{payload}")
            return

        if line.startswith(self.METRICS_PREFIX):
            raw_payload = line[len(self.METRICS_PREFIX):].strip()
            try:
                metrics = json.loads(raw_payload)
                if isinstance(metrics, dict):
                    self._metrics.update(metrics)
            except json.JSONDecodeError as exc:
                logger.warning("Invalid Gemini metrics payload ignored: %s", exc)
            return

        super()._handle_stdout_line(line)

    async def capture_proposals(self) -> List[ProposedAction]:
        return await super().capture_proposals()


class GeminiAdapter(AgentAdapter):
    """Adapter for orchestrating Gemini CLI.

    This adapter spawns a Gemini CLI process and communicates via
    standard input/output using a JSON stream format.

    Attributes:
        binary_path (str): Path to the gemini executable.
        trust_event_sink (callable): Callback for trust events.
        model_name (str): Identifier for the model (e.g., "gemini-1.5-pro").
        actor (str): Actor identifier for logging and trust attribution.
    """

    def __init__(
        self,
        binary_path: str = "gemini",
        *,
        trust_event_sink: Optional[Any] = None,
        model_name: str = "gemini-cli",
        actor: str = "agent:gemini",
    ):
        self.binary_path = binary_path
        self.trust_event_sink = trust_event_sink
        self.model_name = model_name
        self.actor = actor

    async def spawn(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        policy: Optional[Dict[str, Any]] = None,
    ) -> AgentSession:
        logger.info("Spawning Gemini CLI: %s", self.binary_path)

        command = [self.binary_path, "execute", task, "--output-format", "stream-json"]
        if context:
            command.extend(["--context", json.dumps(context)])
        if policy:
            command.extend(["--policy", json.dumps(policy)])

        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        task_type = str((context or {}).get("task_type") or (policy or {}).get("task_type") or "agent_task")
        return GeminiSession(
            process,
            task,
            trust_event_sink=self.trust_event_sink,
            model_name=self.model_name,
            task_type=task_type,
            actor=self.actor,
        )
