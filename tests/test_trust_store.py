from __future__ import annotations

from pathlib import Path

from tools.gimo_server.services.storage_service import StorageService
from tools.gimo_server.services.trust_store import TrustStore


def test_trust_store_hot_to_warm_and_query(tmp_path):
    db_path = tmp_path / "gimo_test.db"
    warm_path = tmp_path / "trust_active.gics"
    cold_dir = tmp_path / "trust_cold"

    original_db_path = StorageService.DB_PATH
    StorageService.DB_PATH = db_path
    try:
        storage = StorageService()
        storage.upsert_trust_record(
            {
                "dimension_key": "file_write|src/auth.py|sonnet|add_endpoint",
                "approvals": 30,
                "rejections": 1,
                "failures": 0,
                "auto_approvals": 20,
                "streak": 10,
                "score": 0.95,
                "policy": "auto_approve",
                "circuit_state": "closed",
                "circuit_opened_at": None,
                "last_updated": "2026-01-01T00:00:00Z",
            }
        )

        store = TrustStore(storage, warm_path=warm_path, cold_dir=cold_dir)
        flush_result = store.flush_hot_to_warm()
        assert flush_result["written"] == 1
        assert warm_path.exists()

        hit = store.query_dimension("file_write|src/auth.py|sonnet|add_endpoint")
        assert hit is not None
        assert hit["policy"] == "auto_approve"

        storage.close()
    finally:
        StorageService.DB_PATH = original_db_path


def test_trust_store_archive_and_verify(tmp_path):
    db_path = tmp_path / "gimo_test.db"
    warm_path = tmp_path / "trust_active.gics"
    cold_dir = tmp_path / "trust_cold"

    original_db_path = StorageService.DB_PATH
    StorageService.DB_PATH = db_path
    try:
        storage = StorageService()
        storage.upsert_trust_record(
            {
                "dimension_key": "shell_exec|*|claude|agent_task",
                "approvals": 5,
                "rejections": 0,
                "failures": 0,
                "auto_approvals": 1,
                "streak": 3,
                "score": 0.7,
                "policy": "require_review",
                "circuit_state": "closed",
                "circuit_opened_at": None,
                "last_updated": "2026-01-01T00:00:00Z",
            }
        )

        store = TrustStore(storage, warm_path=warm_path, cold_dir=cold_dir)
        store.flush_hot_to_warm()

        archived = store.archive_warm_to_cold(label="test")
        assert archived["archived"] is True

        cold_file = Path(archived["cold_file"])
        assert cold_file.exists()
        assert store.verify_cold_file(cold_file) is True

        health = store.health()
        assert health["cold_files"] >= 1
        assert health["latest_cold_verified"] is True

        storage.close()
    finally:
        StorageService.DB_PATH = original_db_path
