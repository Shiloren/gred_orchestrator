from __future__ import annotations

import logging
import sqlite3
from typing import Any, Dict, Optional
from .base_storage import BaseStorage

logger = logging.getLogger("orchestrator.services.storage.config")

class ConfigStorage(BaseStorage):
    """Storage logic for circuit breakers and tool call idempotency."""

    def ensure_tables(self) -> None:
        with self._conn:
            # Circuit breaker config per dimension
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS circuit_breaker_configs (
                    dimension_key TEXT PRIMARY KEY,
                    window INTEGER NOT NULL,
                    failure_threshold INTEGER NOT NULL,
                    recovery_probes INTEGER NOT NULL,
                    cooldown_seconds INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Idempotency keys for tool calls
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_call_idempotency (
                    idempotency_key TEXT PRIMARY KEY,
                    tool TEXT NOT NULL,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def get_circuit_breaker_config(self, dimension_key: str) -> Optional[Dict[str, Any]]:
        # Try GICS first
        if self.gics:
            try:
                result = self.gics.get(f"cb:{dimension_key}")
                if result and "fields" in result:
                    return {
                        "dimension_key": dimension_key,
                        "window": int(result["fields"].get("window", 0)),
                        "failure_threshold": int(result["fields"].get("failure_threshold", 0)),
                        "recovery_probes": int(result["fields"].get("recovery_probes", 0)),
                        "cooldown_seconds": int(result["fields"].get("cooldown_seconds", 0)),
                    }
            except Exception as e:
                logger.error("Failed to get circuit breaker config from GICS: %s", e)

        # Fallback to SQLite
        row = self._conn.execute(
            """
            SELECT dimension_key, window, failure_threshold, recovery_probes, cooldown_seconds
            FROM circuit_breaker_configs
            WHERE dimension_key = ?
            """,
            (dimension_key,),
        ).fetchone()
        if row is None:
            return None
        return {
            "dimension_key": row["dimension_key"],
            "window": int(row["window"]),
            "failure_threshold": int(row["failure_threshold"]),
            "recovery_probes": int(row["recovery_probes"]),
            "cooldown_seconds": int(row["cooldown_seconds"]),
        }

    def upsert_circuit_breaker_config(self, dimension_key: str, config: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "dimension_key": dimension_key,
            "window": int(config["window"]),
            "failure_threshold": int(config["failure_threshold"]),
            "recovery_probes": int(config["recovery_probes"]),
            "cooldown_seconds": int(config["cooldown_seconds"]),
        }
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO circuit_breaker_configs (
                    dimension_key, window, failure_threshold, recovery_probes, cooldown_seconds, updated_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(dimension_key) DO UPDATE SET
                    window=excluded.window,
                    failure_threshold=excluded.failure_threshold,
                    recovery_probes=excluded.recovery_probes,
                    cooldown_seconds=excluded.cooldown_seconds,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    payload["dimension_key"],
                    payload["window"],
                    payload["failure_threshold"],
                    payload["recovery_probes"],
                    payload["cooldown_seconds"],
                ),
            )
        
        # Dual-write to GICS
        if self.gics:
            try:
                self.gics.put(f"cb:{dimension_key}", payload)
            except Exception as e:
                logger.error("Failed to push circuit breaker config %s to GICS: %s", dimension_key, e)

        return payload

    def register_tool_call_idempotency_key(
        self,
        *,
        idempotency_key: str,
        tool: str,
        context: Optional[str] = None,
    ) -> bool:
        if not idempotency_key:
            return True

        try:
            with self._conn:
                self._conn.execute(
                    """
                    INSERT INTO tool_call_idempotency (idempotency_key, tool, context)
                    VALUES (?, ?, ?)
                    """,
                    (str(idempotency_key), str(tool), context),
                )
            return True
        except sqlite3.IntegrityError:
            return False
