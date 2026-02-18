"""Tests for TrustStorage — the replacement for the legacy TrustStore.

TrustStore was merged into TrustStorage during the Paso 1.2 refactoring.
These tests verify the same functionality using the new API.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from tools.gimo_server.services.storage_service import StorageService
from tools.gimo_server.services.gics_service import GicsService


def test_trust_storage_save_and_query(tmp_path):
    db_path = tmp_path / "gimo_test.db"
    original_db_path = StorageService.DB_PATH
    StorageService.DB_PATH = db_path

    try:
        storage = StorageService()

        # Test Save
        data = {
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
        storage.upsert_trust_record(data)

        # Verify it was saved
        hot = storage.get_trust_record(data["dimension_key"])
        assert hot is not None
        assert hot["policy"] == "auto_approve"

        # Test query returns correct values
        hit = storage.get_trust_record(data["dimension_key"])
        assert hit is not None
        assert hit["approvals"] == 30

        storage.close()
    finally:
        StorageService.DB_PATH = original_db_path
