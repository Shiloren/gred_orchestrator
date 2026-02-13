from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..config import OPS_DATA_DIR
from ..ops_models import EvalDataset, EvalRunReport, TrustEvent

logger = logging.getLogger("orchestrator.services.storage")


def _normalize_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if value:
        return str(value)
    return datetime.now(timezone.utc).isoformat()


class StorageService:
    """SQLite storage service for operational data."""

    DB_PATH = OPS_DATA_DIR / "gimo_ops.db"

    def __init__(self):
        self._conn: Optional[sqlite3.Connection] = None
        self.ensure_db()

    def ensure_db(self) -> None:
        OPS_DATA_DIR.mkdir(parents=True, exist_ok=True)
        if self._conn is None:
            self._conn = sqlite3.connect(self.DB_PATH, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._create_tables()

    def _create_tables(self) -> None:
        with self._conn:
            # Workflow graphs
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Nodes and Edges (denormalized in workflow data for MVP, but can be separate)
            
            # Checkpoints
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    output TEXT,
                    status TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
                )
            """)
            
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
            
            # Audit log entries
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Eval runs history (Fase 4.4 persistence)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS eval_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    gate_passed INTEGER NOT NULL,
                    pass_rate REAL NOT NULL,
                    avg_score REAL NOT NULL,
                    total_cases INTEGER NOT NULL,
                    passed_cases INTEGER NOT NULL,
                    failed_cases INTEGER NOT NULL,
                    report_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Eval datasets history (versioned snapshots)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS eval_datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    version_tag TEXT,
                    dataset_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Idempotency keys for write/destructive tool calls (Roadmap v2 Fase 2.4)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_call_idempotency (
                    idempotency_key TEXT PRIMARY KEY,
                    tool TEXT NOT NULL,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def _ensure_column(self, table: str, column: str, column_def: str) -> None:
        rows = self._conn.execute(f"PRAGMA table_info({table})").fetchall()
        existing = {row["name"] for row in rows}
        if column not in existing:
            self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_def}")

    def save_workflow(self, workflow_id: str, data: str) -> None:
        if not isinstance(data, str):
            data = json.dumps(data)
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO workflows (id, data) VALUES (?, ?)",
                (workflow_id, data)
            )

    def save_checkpoint(
        self,
        workflow_id: str,
        node_id: str,
        state: Any,
        output: Optional[Any],
        status: str,
    ) -> None:
        state_payload = state if isinstance(state, str) else json.dumps(state)
        output_payload = output if isinstance(output, str) or output is None else json.dumps(output)
        with self._conn:
            self._conn.execute(
                "INSERT INTO checkpoints (workflow_id, node_id, state, output, status) VALUES (?, ?, ?, ?, ?)",
                (workflow_id, node_id, state_payload, output_payload, status)
            )

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT id, data, created_at FROM workflows WHERE id = ?",
            (workflow_id,),
        ).fetchone()
        if row is None:
            return None

        try:
            parsed_data: Any = json.loads(row["data"])
        except Exception:
            parsed_data = row["data"]

        return {
            "id": row["id"],
            "data": parsed_data,
            "created_at": row["created_at"],
        }

    def list_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT workflow_id, node_id, state, output, status, timestamp
            FROM checkpoints
            WHERE workflow_id = ?
            ORDER BY id ASC
            """,
            (workflow_id,),
        ).fetchall()

        def _maybe_json(value: Any) -> Any:
            if value is None:
                return None
            try:
                return json.loads(value)
            except Exception:
                return value

        return [
            {
                "workflow_id": row["workflow_id"],
                "node_id": row["node_id"],
                "state": _maybe_json(row["state"]),
                "output": _maybe_json(row["output"]),
                "status": row["status"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]

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

    def list_trust_events(self, limit: int = 100) -> List[Dict[str, Any]]:
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
        return [
            {
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
            for row in rows
        ]

    def get_circuit_breaker_config(self, dimension_key: str) -> Optional[Dict[str, Any]]:
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
        return payload

    def save_eval_report(self, report: EvalRunReport | Dict[str, Any]) -> int:
        data = report.model_dump() if isinstance(report, EvalRunReport) else dict(report)
        payload = json.dumps(data, ensure_ascii=False)
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO eval_runs (
                    workflow_id, gate_passed, pass_rate, avg_score,
                    total_cases, passed_cases, failed_cases, report_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(data.get("workflow_id", "")),
                    1 if bool(data.get("gate_passed", False)) else 0,
                    float(data.get("pass_rate", 0.0) or 0.0),
                    float(data.get("avg_score", 0.0) or 0.0),
                    int(data.get("total_cases", 0) or 0),
                    int(data.get("passed_cases", 0) or 0),
                    int(data.get("failed_cases", 0) or 0),
                    payload,
                ),
            )
        return int(cursor.lastrowid)

    def save_eval_dataset(
        self,
        dataset: EvalDataset | Dict[str, Any],
        *,
        version_tag: Optional[str] = None,
    ) -> int:
        data = dataset.model_dump() if isinstance(dataset, EvalDataset) else dict(dataset)
        payload = json.dumps(data, ensure_ascii=False)
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO eval_datasets (workflow_id, version_tag, dataset_json)
                VALUES (?, ?, ?)
                """,
                (
                    str(data.get("workflow_id", "")),
                    version_tag,
                    payload,
                ),
            )
        return int(cursor.lastrowid)

    def list_eval_datasets(self, *, workflow_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        if workflow_id:
            rows = self._conn.execute(
                """
                SELECT id, workflow_id, version_tag, created_at
                FROM eval_datasets
                WHERE workflow_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (workflow_id, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT id, workflow_id, version_tag, created_at
                FROM eval_datasets
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "dataset_id": int(row["id"]),
                "workflow_id": row["workflow_id"],
                "version_tag": row["version_tag"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def get_eval_dataset(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            """
            SELECT id, workflow_id, version_tag, dataset_json, created_at
            FROM eval_datasets
            WHERE id = ?
            """,
            (int(dataset_id),),
        ).fetchone()
        if row is None:
            return None

        try:
            dataset = json.loads(row["dataset_json"])
        except Exception:
            dataset = None

        return {
            "dataset_id": int(row["id"]),
            "workflow_id": row["workflow_id"],
            "version_tag": row["version_tag"],
            "created_at": row["created_at"],
            "dataset": dataset,
        }

    def list_eval_reports(self, *, workflow_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        if workflow_id:
            rows = self._conn.execute(
                """
                SELECT id, workflow_id, gate_passed, pass_rate, avg_score,
                       total_cases, passed_cases, failed_cases, created_at
                FROM eval_runs
                WHERE workflow_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (workflow_id, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT id, workflow_id, gate_passed, pass_rate, avg_score,
                       total_cases, passed_cases, failed_cases, created_at
                FROM eval_runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "run_id": int(row["id"]),
                "workflow_id": row["workflow_id"],
                "gate_passed": bool(row["gate_passed"]),
                "pass_rate": float(row["pass_rate"]),
                "avg_score": float(row["avg_score"]),
                "total_cases": int(row["total_cases"]),
                "passed_cases": int(row["passed_cases"]),
                "failed_cases": int(row["failed_cases"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def get_eval_report(self, run_id: int) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            """
            SELECT id, workflow_id, report_json, created_at
            FROM eval_runs
            WHERE id = ?
            """,
            (int(run_id),),
        ).fetchone()
        if row is None:
            return None

        try:
            report = json.loads(row["report_json"])
        except Exception:
            report = None

        return {
            "run_id": int(row["id"]),
            "workflow_id": row["workflow_id"],
            "created_at": row["created_at"],
            "report": report,
        }

    def register_tool_call_idempotency_key(
        self,
        *,
        idempotency_key: str,
        tool: str,
        context: Optional[str] = None,
    ) -> bool:
        """Register an idempotency key.

        Returns True when key is new, False when key already exists.
        """
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

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
