from __future__ import annotations

from typing import Any, Dict, List

from .storage_service import StorageService


class InstitutionalMemoryService:
    """Builds human-reviewable policy suggestions from trust history (MVP)."""

    def __init__(self, storage: StorageService):
        self.storage = storage

    def generate_suggestions(self, *, limit: int = 20) -> List[Dict[str, Any]]:
        records = self.storage.list_trust_records(limit=5000)
        suggestions: List[Dict[str, Any]] = []

        for record in records:
            approvals = int(record.get("approvals", 0) or 0)
            rejections = int(record.get("rejections", 0) or 0)
            failures = int(record.get("failures", 0) or 0)
            score = float(record.get("score", 0.0) or 0.0)
            policy = str(record.get("policy", "require_review"))
            dimension_key = str(record.get("dimension_key", ""))
            tool = dimension_key.split("|")[0] if "|" in dimension_key else dimension_key

            # High-confidence pattern: can be promoted to auto_approve
            if policy != "auto_approve" and approvals >= 20 and score >= 0.90 and failures <= 1:
                suggestions.append(
                    {
                        "dimension_key": dimension_key,
                        "tool": tool,
                        "action": "promote_auto_approve",
                        "reason": f"{approvals} approvals, score={score:.2f}, failures={failures}",
                        "confidence": round(min(0.99, 0.75 + score * 0.2), 2),
                        "stats": {
                            "approvals": approvals,
                            "rejections": rejections,
                            "failures": failures,
                            "score": score,
                            "current_policy": policy,
                        },
                    }
                )

            # Unsafe pattern: should be blocked by default
            if failures >= 5:
                suggestions.append(
                    {
                        "dimension_key": dimension_key,
                        "tool": tool,
                        "action": "block_dimension",
                        "reason": f"failure burst detected (failures={failures})",
                        "confidence": round(min(0.99, 0.70 + min(0.25, failures * 0.03)), 2),
                        "stats": {
                            "approvals": approvals,
                            "rejections": rejections,
                            "failures": failures,
                            "score": score,
                            "current_policy": policy,
                        },
                    }
                )

        suggestions.sort(key=lambda s: (s["confidence"], s["action"]), reverse=True)
        return suggestions[:limit]
