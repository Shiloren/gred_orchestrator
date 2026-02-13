from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any, Dict

from ..config import OPS_DATA_DIR
from ..ops_models import PolicyConfig


class PolicyService:
    """Simple Policy-as-Code service (JSON rules, fail-closed friendly)."""

    POLICY_PATH: Path = OPS_DATA_DIR / "policy_rules.json"

    @classmethod
    def _default(cls) -> PolicyConfig:
        return PolicyConfig(rules=[])

    @classmethod
    def get_config(cls) -> PolicyConfig:
        if not cls.POLICY_PATH.exists():
            return cls._default()
        try:
            payload = json.loads(cls.POLICY_PATH.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return cls._default()
            return PolicyConfig.model_validate(payload)
        except Exception:
            return cls._default()

    @classmethod
    def set_config(cls, config: PolicyConfig) -> PolicyConfig:
        cls.POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.POLICY_PATH.write_text(config.model_dump_json(indent=2), encoding="utf-8")
        return config

    @classmethod
    def decide(
        cls,
        *,
        tool: str,
        context: str,
        trust_score: float,
    ) -> Dict[str, Any]:
        cfg = cls.get_config()
        tool_s = str(tool or "")
        context_s = str(context or "*")

        for idx, rule in enumerate(cfg.rules):
            tool_match = fnmatch.fnmatch(tool_s, str(rule.match.tool or "*"))
            context_match = fnmatch.fnmatch(context_s, str(rule.match.context or "*"))
            if not (tool_match and context_match):
                continue

            action = str(rule.action)
            min_score = rule.min_trust_score

            if min_score is not None and trust_score < float(min_score):
                action = "require_review"

            return {
                "decision": action,
                "rule_index": idx,
                "matched": {
                    "tool": rule.match.tool,
                    "context": rule.match.context,
                },
                "override": rule.override,
                "min_trust_score": min_score,
            }

        return {
            "decision": "allow",
            "rule_index": None,
            "matched": None,
            "override": None,
            "min_trust_score": None,
        }
