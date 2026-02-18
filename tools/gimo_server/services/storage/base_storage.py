from __future__ import annotations

import logging
import sqlite3
from typing import Optional

from ...config import OPS_DATA_DIR

from ..gics_service import GicsService

logger = logging.getLogger("orchestrator.services.storage.base")

class BaseStorage:
    """Base class for domain-specific storage services."""
    
    DB_PATH = OPS_DATA_DIR / "gimo_ops.db"

    def __init__(self, conn: Optional[sqlite3.Connection] = None, gics: Optional[GicsService] = None):
        self._conn = conn
        self.gics = gics
        if self._conn is None:
            OPS_DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.DB_PATH, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._conn.execute("PRAGMA journal_mode=WAL")

    def _ensure_column(self, table: str, column: str, column_def: str) -> None:
        rows = self._conn.execute(f"PRAGMA table_info({table})").fetchall()
        existing = {row["name"] for row in rows}
        if column not in existing:
            self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_def}")
