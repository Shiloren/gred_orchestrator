from __future__ import annotations

from typing import Protocol

from .models import DetectedIntent, ExecutionPlanDraft, SecurityDecision


class IntentEngine(Protocol):
    """Analiza la entrada del usuario para derivar intencion y plan."""
    def detect_intent(self, input_text: str, context: dict) -> DetectedIntent:
        ...


class SecurityGuard(Protocol):
    """Evalua riesgos y sanitiza intenciones antes de su ejecucion."""
    def evaluate(self, input_text: str, context: dict) -> SecurityDecision:
        ...


class DirectResponseEngine(Protocol):
    """Genera respuestas directas para intenciones sin plan complejo."""
    def can_bypass_llm(self, intent: DetectedIntent, context: dict) -> bool:
        ...

    def build_execution_plan(self, intent: DetectedIntent, context: dict) -> ExecutionPlanDraft:
        ...
