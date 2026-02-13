from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ..ops_models import WorkflowNode


@dataclass
class RoutingDecision:
    model: str
    reason: str


class ModelRouterService:
    """Simple model router MVP for phase 3.3.

    Chooses model by task_type and can degrade to cheaper tier when budget is tight.
    """

    DEFAULT_POLICY: Dict[str, str] = {
        "classification": "haiku",
        "code_generation": "sonnet",
        "security_review": "opus",
        "formatting": "local",
        "default": "sonnet",
    }

    _TIERS = ["local", "haiku", "sonnet", "opus"]

    def choose_model(self, node: WorkflowNode, state: Dict[str, Any]) -> RoutingDecision:
        cfg = node.config if isinstance(node.config, dict) else {}
        task_type = str(cfg.get("task_type") or "").strip()

        base_model = str(
            cfg.get("model")
            or cfg.get("preferred_model")
            or self.DEFAULT_POLICY.get(task_type, self.DEFAULT_POLICY["default"])
        )

        if self._is_low_budget(state):
            degraded = self._degrade(base_model)
            if degraded != base_model:
                return RoutingDecision(model=degraded, reason=f"low_budget:{base_model}->{degraded}")
            return RoutingDecision(model=base_model, reason="low_budget:no_cheaper_tier")

        return RoutingDecision(model=base_model, reason=f"policy:{task_type or 'default'}")

    def _is_low_budget(self, state: Dict[str, Any]) -> bool:
        budget = state.get("budget") if isinstance(state.get("budget"), dict) else {}
        counters = state.get("budget_counters") if isinstance(state.get("budget_counters"), dict) else {}
        max_cost = budget.get("max_cost_usd")
        if not isinstance(max_cost, (int, float)) or float(max_cost) <= 0:
            return False
        spent = float(counters.get("cost_usd", 0.0) or 0.0)
        remaining_ratio = max(0.0, (float(max_cost) - spent) / float(max_cost))
        return remaining_ratio < 0.2

    def _degrade(self, model: str) -> str:
        m = str(model)
        if m not in self._TIERS:
            return m
        idx = self._TIERS.index(m)
        return self._TIERS[max(0, idx - 1)]
