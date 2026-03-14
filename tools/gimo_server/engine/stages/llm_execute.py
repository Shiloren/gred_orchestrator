from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from ..contracts import StageInput, StageOutput, ExecutionStage
from ...services.provider_service import ProviderService

class LlmExecute(ExecutionStage):
    @property
    def name(self) -> str:
        return "llm_execute"

    async def execute(self, input: StageInput) -> StageOutput:
        prompt = input.context.get("prompt")
        if not prompt:
            return StageOutput(status="fail", artifacts={"error": "Missing prompt in context"})
            
        gen_context = input.context.get("gen_context", {})
        
        try:
            resp = await ProviderService.static_generate(
                prompt=prompt,
                context=gen_context
            )
            
            return StageOutput(
                status="continue",
                artifacts={
                    "llm_response": resp,
                    "content": resp.get("content", ""),
                    "usage": {
                        "prompt_tokens": resp.get("prompt_tokens"),
                        "completion_tokens": resp.get("completion_tokens"),
                        "cost_usd": resp.get("cost_usd")
                    }
                }
            )
        except Exception as e:
            return StageOutput(status="fail", artifacts={"error": str(e)})

    async def rollback(self, input: StageInput) -> None:
        """LLM execution is stateless, nothing to rollback."""
        pass

