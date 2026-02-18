from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from .base_storage import BaseStorage
from ...ops_models import TrustEvent
from ..gics_service import GicsService

logger = logging.getLogger("orchestrator.services.storage.trust")

def _normalize_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if value:
        return str(value)
    return datetime.now(timezone.utc).isoformat()

class TrustStorage(BaseStorage):
    """Storage logic for trust events and dimension records (Hot/Cold tiers)."""

    def __init__(self, conn: Optional[Any] = None, gics_service: Optional[GicsService] = None):
        super().__init__(conn)
        self.gics = gics_service

    def ensure_tables(self) -> None:
        with self._conn:
            # Trust Events
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS trust_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dimension_key TEXT NOT NULL,
                    tool TEXT NOT NULL,
                    context TEXT NOT NULL,
                    model TEXT NOT NULL,
                    task_type TEXT,
                    outcome TEXT NOT NULL,
                    actor TEXT,
                    post_check_passed INTEGER DEFAULT 1,
                    duration_ms INTEGER DEFAULT 0,
                    tokens_used INTEGER DEFAULT 0,
                    cost_usd REAL DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._ensure_column("trust_events", "task_type", "TEXT")
            self._ensure_column("trust_events", "actor", "TEXT")
            self._ensure_column("trust_events", "post_check_passed", "INTEGER DEFAULT 1")
            self._ensure_column("trust_events", "duration_ms", "INTEGER DEFAULT 0")
            self._ensure_column("trust_events", "tokens_used", "INTEGER DEFAULT 0")
            self._ensure_column("trust_events", "cost_usd", "REAL DEFAULT 0")

            # Trust Records (hot tier materialized summary)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS trust_records (
                    dimension_key TEXT PRIMARY KEY,
                    approvals INTEGER DEFAULT 0,
                    rejections INTEGER DEFAULT 0,
                    failures INTEGER DEFAULT 0,
                    auto_approvals INTEGER DEFAULT 0,
                    streak INTEGER DEFAULT 0,
                    score REAL DEFAULT 0,
                    policy TEXT DEFAULT 'require_review',
                    circuit_state TEXT DEFAULT 'closed',
                    circuit_opened_at TEXT,
                    last_updated TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._ensure_column("trust_records", "circuit_opened_at", "TEXT")

    def save_trust_event(self, event: TrustEvent | Dict[str, Any]) -> None:
        event_data = event.model_dump() if isinstance(event, TrustEvent) else dict(event)
        timestamp = _normalize_timestamp(event_data.get("timestamp"))
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO trust_events (
                    dimension_key, tool, context, model, task_type, outcome,
                    actor, post_check_passed, duration_ms, tokens_used, cost_usd, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_data.get("dimension_key"),
                    event_data.get("tool"),
                    event_data.get("context", "*"),
                    event_data.get("model", "*"),
                    event_data.get("task_type"),
                    event_data.get("outcome"),
                    event_data.get("actor", "system"),
                    1 if event_data.get("post_check_passed", True) else 0,
                    int(event_data.get("duration_ms", 0)),
                    int(event_data.get("tokens_used", 0)),
                    float(event_data.get("cost_usd", 0.0)),
                    timestamp,
                ),
            )
        
        # Dual-write to GICS
        if self.gics:
            try:
                # Key format: te:dim:timestamp
                event_key = f"te:{event_data.get('dimension_key')}:{timestamp}"
                self.gics.put(event_key, event_data)
            except Exception as e:
                logger.error("Failed to push trust event to GICS: %s", e)

    def save_trust_events(self, events: List[TrustEvent | Dict[str, Any]]) -> None:
        if not events:
            return

        rows = []
        for event in events:
            event_data = event.model_dump() if isinstance(event, TrustEvent) else dict(event)
            rows.append(
                (
                    event_data.get("dimension_key"),
                    event_data.get("tool"),
                    event_data.get("context", "*"),
                    event_data.get("model", "*"),
                    event_data.get("task_type"),
                    event_data.get("outcome"),
                    event_data.get("actor", "system"),
                    1 if event_data.get("post_check_passed", True) else 0,
                    int(event_data.get("duration_ms", 0)),
                    int(event_data.get("tokens_used", 0)),
                    float(event_data.get("cost_usd", 0.0)),
                    _normalize_timestamp(event_data.get("timestamp")),
                )
            )

        with self._conn:
            self._conn.executemany(
                """
                INSERT INTO trust_events (
                    dimension_key, tool, context, model, task_type, outcome,
                    actor, post_check_passed, duration_ms, tokens_used, cost_usd, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            
        # Dual-write to GICS (batch)
        if self.gics:
            for event in events:
                try:
                    event_data = event.model_dump() if isinstance(event, TrustEvent) else dict(event)
                    timestamp = _normalize_timestamp(event_data.get("timestamp"))
                    event_key = f"te:{event_data.get('dimension_key')}:{timestamp}"
                    self.gics.put(event_key, event_data)
                except Exception as e:
                    logger.error("Failed to push batch trust event to GICS: %s", e)

    def list_trust_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        # Try GICS first
        if self.gics:
            try:
                # Key format: te:dim:timestamp
                items = self.gics.scan(prefix="te:", include_fields=True)
                if items:
                    events = []
                    for item in items:
                        fields = item.get("fields", {})
                        events.append({
                            "dimension_key": fields.get("dimension_key"),
                            "tool": fields.get("tool"),
                            "context": fields.get("context"),
                            "model": fields.get("model"),
                            "task_type": fields.get("task_type"),
                            "outcome": fields.get("outcome"),
                            "actor": fields.get("actor"),
                            "post_check_passed": bool(fields.get("post_check_passed", True)),
                            "duration_ms": fields.get("duration_ms", 0),
                            "tokens_used": fields.get("tokens_used", 0),
                            "cost_usd": fields.get("cost_usd", 0.0),
                            "timestamp": fields.get("timestamp"),
                        })
                    # Newest first
                    events.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
                    return events[:limit]
            except Exception as e:
                logger.error("Failed to list trust events from GICS: %s", e)

        # Fallback to SQLite
        rows = self._conn.execute(
            """
            SELECT
                dimension_key, tool, context, model, task_type, outcome,
                actor, post_check_passed, duration_ms, tokens_used, cost_usd, timestamp
            FROM trust_events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "dimension_key": row["dimension_key"],
                "tool": row["tool"],
                "context": row["context"],
                "model": row["model"],
                "task_type": row["task_type"],
                "outcome": row["outcome"],
                "actor": row["actor"],
                "post_check_passed": bool(row["post_check_passed"]),
                "duration_ms": row["duration_ms"],
                "tokens_used": row["tokens_used"],
                "cost_usd": row["cost_usd"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]

    def list_trust_events_by_dimension(self, dimension_key: str, limit: int = 100) -> List[Dict[str, Any]]:
        # Try GICS first
        if self.gics:
            try:
                prefix = f"te:{dimension_key}:"
                items = self.gics.scan(prefix=prefix, include_fields=True)
                if items:
                    events = []
                    for item in items:
                        fields = item.get("fields", {})
                        events.append({
                            "dimension_key": fields.get("dimension_key"),
                            "tool": fields.get("tool"),
                            "context": fields.get("context"),
                            "model": fields.get("model"),
                            "task_type": fields.get("task_type"),
                            "outcome": fields.get("outcome"),
                            "actor": fields.get("actor"),
                            "post_check_passed": bool(fields.get("post_check_passed", True)),
                            "duration_ms": fields.get("duration_ms", 0),
                            "tokens_used": fields.get("tokens_used", 0),
                            "cost_usd": fields.get("cost_usd", 0.0),
                            "timestamp": fields.get("timestamp"),
                        })
                    events.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
                    return events[:limit]
            except Exception as e:
                logger.error("Failed to list trust events by dimension from GICS: %s", e)

        # Fallback to SQLite
        rows = self._conn.execute(
            """
            SELECT
                dimension_key, tool, context, model, task_type, outcome,
                actor, post_check_passed, duration_ms, tokens_used, cost_usd, timestamp
            FROM trust_events
            WHERE dimension_key = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (dimension_key, limit),
        ).fetchall()
        return [
            {
                "dimension_key": row["dimension_key"],
                "tool": row["tool"],
                "context": row["context"],
                "model": row["model"],
                "task_type": row["task_type"],
                "outcome": row["outcome"],
                "actor": row["actor"],
                "post_check_passed": bool(row["post_check_passed"]),
                "duration_ms": row["duration_ms"],
                "tokens_used": row["tokens_used"],
                "cost_usd": row["cost_usd"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]

    def get_trust_record(self, dimension_key: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            """
            SELECT
                dimension_key, approvals, rejections, failures, auto_approvals,
                streak, score, policy, circuit_state, circuit_opened_at, last_updated
            FROM trust_records
            WHERE dimension_key = ?
            """,
            (dimension_key,),
        ).fetchone()
        if row is None:
            return None
        return {
            "dimension_key": row["dimension_key"],
            "approvals": int(row["approvals"] or 0),
            "rejections": int(row["rejections"] or 0),
            "failures": int(row["failures"] or 0),
            "auto_approvals": int(row["auto_approvals"] or 0),
            "streak": int(row["streak"] or 0),
            "score": float(row["score"] or 0.0),
            "policy": row["policy"] or "require_review",
            "circuit_state": row["circuit_state"] or "closed",
            "circuit_opened_at": row["circuit_opened_at"],
            "last_updated": row["last_updated"],
        }

    def upsert_trust_record(self, record: Dict[str, Any]) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO trust_records (
                    dimension_key, approvals, rejections, failures, auto_approvals,
                    streak, score, policy, circuit_state, circuit_opened_at, last_updated, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(dimension_key) DO UPDATE SET
                    approvals=excluded.approvals,
                    rejections=excluded.rejections,
                    failures=excluded.failures,
                    auto_approvals=excluded.auto_approvals,
                    streak=excluded.streak,
                    score=excluded.score,
                    policy=excluded.policy,
                    circuit_state=excluded.circuit_state,
                    circuit_opened_at=excluded.circuit_opened_at,
                    last_updated=excluded.last_updated,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    record.get("dimension_key"),
                    int(record.get("approvals", 0)),
                    int(record.get("rejections", 0)),
                    int(record.get("failures", 0)),
                    int(record.get("auto_approvals", 0)),
                    int(record.get("streak", 0)),
                    float(record.get("score", 0.0)),
                    str(record.get("policy", "require_review")),
                    str(record.get("circuit_state", "closed")),
                    record.get("circuit_opened_at"),
                    record.get("last_updated"),
                ),
            )

    def list_trust_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        # Try GICS first
        # Note: Trust records (dimensions) don't have a specific prefix in GICS right now, 
        # they are stored by dimension_key directly. 
        # We might need to rethink this or use the SQLite fallback for listing "all known dimensions"
        # unless we prefix them in GICS too.
        # For now, let's keep SQLite as the index for dimensions but GICS as source of truth for detail.
        
        rows = self._conn.execute(
            """
            SELECT
                dimension_key, approvals, rejections, failures, auto_approvals,
                streak, score, policy, circuit_state, circuit_opened_at, last_updated
            FROM trust_records
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        
        results = []
        for row in rows:
            dim_key = row["dimension_key"]
            # Try to get latest from GICS for each dimension listed
            detail = self.query_dimension(dim_key)
            if detail:
                results.append(detail)
            else:
                results.append({
                    "dimension_key": row["dimension_key"],
                    "approvals": int(row["approvals"] or 0),
                    "rejections": int(row["rejections"] or 0),
                    "failures": int(row["failures"] or 0),
                    "auto_approvals": int(row["auto_approvals"] or 0),
                    "streak": int(row["streak"] or 0),
                    "score": float(row["score"] or 0.0),
                    "policy": row["policy"] or "require_review",
                    "circuit_state": row["circuit_state"] or "closed",
                    "circuit_opened_at": row["circuit_opened_at"],
                    "last_updated": row["last_updated"],
                })
        return results

    # Merged logic from TrustStore (Heritage of trust_store.py)
    def save_dimension(self, dimension_key: str, data: Dict[str, Any]) -> None:
        """
        Save a trust record.
        1. Persist to SQL (Hot tier) for immediate queryability.
        2. Push to GICS Daemon for long-term behavioral analysis and storage.
        """
        # 1. Hot Tier (SQLite)
        self.upsert_trust_record(data)
        
        # 2. GICS Daemon (Analytics + Archive)
        if self.gics:
            try:
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
        hot = self.get_trust_record(dimension_key)
        if hot is not None:
            return hot

        # 2. Try GICS
        if self.gics:
            try:
                result = self.gics.get(dimension_key)
                if result and "fields" in result:
                    return result["fields"]
            except Exception as e:
                logger.error("Failed to query GICS for %s: %s", dimension_key, e)
            
        return None
