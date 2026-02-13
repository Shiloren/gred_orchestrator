from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import OPS_DATA_DIR
from .gics_service import GicsService
from .storage_service import StorageService

logger = logging.getLogger("orchestrator.trust_store")


class TrustStore:
    """
    Manages trust dimension records.
    
    Architecture V2 (GICS 1.3.2):
    - HOT data: Kept in SQLite via StorageService (for fast query/indexing).
    - ARCHIVE data: Offloaded to GICS Daemon via GicsService.
      The Daemon handles MemTable -> Warm (WAL) -> Cold tiered storage.
    """

    def __init__(self, storage: StorageService, gics_service: GicsService):
        self.storage = storage
        self.gics = gics_service

    def save_dimension(self, dimension_key: str, data: Dict[str, Any]) -> None:
        """
        Save a trust record.
        1. Persist to SQL (Hot tier) for immediate queryability.
        2. Push to GICS Daemon for long-term behavioral analysis and storage.
        """
        # 1. Hot Tier (SQLite)
        self.storage.upsert_trust_record(data)
        
        # 2. GICS Daemon (Analytics + Archive)
        try:
            # We explicitly strip 'dimension_key' from fields if it's the key itself, 
            # but GICS allow fields to contain anything.
            self.gics.put(dimension_key, data)
        except Exception as e:
            logger.error("Failed to push trust record %s to GICS: %s", dimension_key, e)

    def query_dimension(self, dimension_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a trust record.
        1. Try Hot Tier (SQLite).
        2. If missing, try GICS Daemon (Warm/Cold tiers).
        """
        # 1. Try Hot
        hot = self.storage.get_trust_record(dimension_key)
        if hot is not None:
            return hot

        # 2. Try GICS
        try:
            result = self.gics.get(dimension_key)
            if result and "fields" in result:
                # GICS returns {key, fields, tier, behavior...}
                return result["fields"]
        except Exception as e:
            logger.error("Failed to query GICS for %s: %s", dimension_key, e)
            
        return None



