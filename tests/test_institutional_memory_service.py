from __future__ import annotations

from tools.gimo_server.services.institutional_memory_service import InstitutionalMemoryService


class _StubStorage:
    def __init__(self, records):
        self._records = records

    def list_trust_records(self, limit: int = 100):
        return self._records[:limit]


def test_institutional_memory_suggests_promote_auto_approve():
    svc = InstitutionalMemoryService(
        _StubStorage(
            [
                {
                    "dimension_key": "file_write|src/auth.py|sonnet|add_endpoint",
                    "approvals": 25,
                    "rejections": 1,
                    "failures": 0,
                    "score": 0.93,
                    "policy": "require_review",
                }
            ]
        )
    )

    suggestions = svc.generate_suggestions(limit=10)
    assert len(suggestions) == 1
    assert suggestions[0]["action"] == "promote_auto_approve"
    assert suggestions[0]["tool"] == "file_write"


def test_institutional_memory_suggests_block_on_failure_burst():
    svc = InstitutionalMemoryService(
        _StubStorage(
            [
                {
                    "dimension_key": "shell_exec|*|claude|agent_task",
                    "approvals": 2,
                    "rejections": 1,
                    "failures": 7,
                    "score": 0.21,
                    "policy": "require_review",
                }
            ]
        )
    )

    suggestions = svc.generate_suggestions(limit=10)
    assert len(suggestions) == 1
    assert suggestions[0]["action"] == "block_dimension"
    assert "failure burst" in suggestions[0]["reason"]
