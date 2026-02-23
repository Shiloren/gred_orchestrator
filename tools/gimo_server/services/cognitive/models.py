from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


IntentName = Literal["CREATE_PLAN", "ASK_STATUS", "HELP", "UNKNOWN"]
DecisionPath = Literal["security_block", "direct_response", "llm_generate"]


@dataclass
class DetectedIntent:
    """Estructura las variables clave detectadas de un mensaje natural."""
    name: IntentName
    confidence: float = 0.5
    reason: str = ""


@dataclass
class SecurityDecision:
    """Resultado del analisis de riesgo antes de iniciar una ejecucion."""
    allowed: bool
    risk_level: Literal["low", "medium", "high"] = "low"
    reason: str = ""
    flags: List[str] = field(default_factory=list)


@dataclass
class ExecutionPlanDraft:
    """Borrador estructurado post-intencion, previo al GraphEngine."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CognitiveDecision:
    """Estado final cognitivo (Intencion + Seguridad + Plan)."""
    intent: DetectedIntent
    security: SecurityDecision
    decision_path: DecisionPath
    can_bypass_llm: bool = False
    direct_content: Optional[str] = None
    error_actionable: Optional[str] = None
    context_updates: Dict[str, Any] = field(default_factory=dict)
