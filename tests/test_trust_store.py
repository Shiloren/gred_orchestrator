from __future__ import annotations

from pathlib import Path

from tools.gimo_server.services.storage_service import StorageService
from tools.gimo_server.services.trust_store import TrustStore
from tools.gimo_server.services.gics_service import GicsService


from unittest.mock import MagicMock

def test_trust_store_save_and_query(tmp_path):
    db_path = tmp_path / "gimo_test.db"
    original_db_path = StorageService.DB_PATH
    StorageService.DB_PATH = db_path
    
    mock_gics = MagicMock(spec=GicsService)
    
    try:
        storage = StorageService()
        store = TrustStore(storage, mock_gics)
        
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
        store.save_dimension(data["dimension_key"], data)
        
        # Verify it went to storage (Hot)
        hot = storage.get_trust_record(data["dimension_key"])
        assert hot is not None
        assert hot["policy"] == "auto_approve"
        
        # Verify it went to GICS
        mock_gics.put.assert_called_once_with(data["dimension_key"], data)
        
        # Test Query (Hot Hit)
        hit = store.query_dimension(data["dimension_key"])
        assert hit is not None
        assert hit["approvals"] == 30
        
        # Test Query (Hot Miss, GICS Hit)
        storage.upsert_trust_record({"dimension_key": data["dimension_key"], "approvals": 0}) 
        # overwriting with dummy data that we will ignore/delete to simulate miss
        # Let's simulate a miss by querying a different key that Gics has
        
        mock_gics.get.return_value = {"key": "other|key", "fields": {"policy": "blocked"}, "tier": "warm"}
        
        # We need to manually remove from sqlite to test miss? 
        # get_trust_record returns None if not found.
        # Let's query a strictly new key
        
        res = store.query_dimension("other|key")
        assert res["policy"] == "blocked"
        mock_gics.get.assert_called_with("other|key")

        storage.close()
    finally:
        StorageService.DB_PATH = original_db_path
