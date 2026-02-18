from __future__ import annotations

import logging
import sqlite3
from typing import Any, Dict, List, Optional

from ..config import OPS_DATA_DIR
from ..ops_models import EvalDataset, EvalRunReport, TrustEvent

from .storage.base_storage import BaseStorage
from .storage.workflow_storage import WorkflowStorage
from .storage.eval_storage import EvalStorage
from .storage.trust_storage import TrustStorage
from .storage.config_storage import ConfigStorage
from .storage.cost_storage import CostStorage
from .gics_service import GicsService

logger = logging.getLogger("orchestrator.services.storage")

class StorageService:
    """SQLite storage service for operational data (Facade for domain-specific storage)."""

    DB_PATH = BaseStorage.DB_PATH

    def __init__(self, conn: Optional[sqlite3.Connection] = None, gics: Optional[GicsService] = None):
        self._conn = conn
        self.gics = gics
        self.ensure_db()
        
        # Initialize sub-storages sharing the same connection and GICS instance
        self.workflows = WorkflowStorage(self._conn, gics=self.gics)
        self.eval = EvalStorage(self._conn, gics=self.gics)
        self.trust = TrustStorage(self._conn, gics_service=self.gics)
        self.config = ConfigStorage(self._conn, gics=self.gics)
        self.cost = CostStorage(self._conn, gics=self.gics)

    def ensure_db(self) -> None:
        if self._conn is None:
            OPS_DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.DB_PATH, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._create_tables()

    def _create_tables(self) -> None:
        """Centralized table creation for all domains."""
        # Delegates table creation to each sub-storage
        # Note: We need to instantiate them briefly if not already done, 
        # but since this is called from __init__ before they are assigned, 
        # we can just run the queries here or via temp instances.
        WorkflowStorage(self._conn).ensure_tables()
        EvalStorage(self._conn).ensure_tables()
        TrustStorage(self._conn).ensure_tables()
        ConfigStorage(self._conn).ensure_tables()
        CostStorage(self._conn).ensure_tables()
        
        # Audit entries and tool idempotency (config domain covers the latter)
        with self._conn:
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

    # --- Workflow Domain ---
    def save_workflow(self, workflow_id: str, data: str) -> None:
        return self.workflows.save_workflow(workflow_id, data)

    def save_checkpoint(self, workflow_id: str, node_id: str, state: Any, output: Optional[Any], status: str) -> None:
        return self.workflows.save_checkpoint(workflow_id, node_id, state, output, status)

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        return self.workflows.get_workflow(workflow_id)

    def list_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        return self.workflows.list_checkpoints(workflow_id)

    # --- Trust Domain ---
    def save_trust_event(self, event: TrustEvent | Dict[str, Any]) -> None:
        return self.trust.save_trust_event(event)

    def save_trust_events(self, events: List[TrustEvent | Dict[str, Any]]) -> None:
        return self.trust.save_trust_events(events)

    def list_trust_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.trust.list_trust_events(limit)

    def list_trust_events_by_dimension(self, dimension_key: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self.trust.list_trust_events_by_dimension(dimension_key, limit)

    def get_trust_record(self, dimension_key: str) -> Optional[Dict[str, Any]]:
        return self.trust.get_trust_record(dimension_key)

    def upsert_trust_record(self, record: Dict[str, Any]) -> None:
        return self.trust.upsert_trust_record(record)

    def list_trust_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.trust.list_trust_records(limit)

    # --- Config Domain ---
    def get_circuit_breaker_config(self, dimension_key: str) -> Optional[Dict[str, Any]]:
        return self.config.get_circuit_breaker_config(dimension_key)

    def upsert_circuit_breaker_config(self, dimension_key: str, config: Dict[str, Any]) -> Dict[str, Any]:
        return self.config.upsert_circuit_breaker_config(dimension_key, config)

    def register_tool_call_idempotency_key(self, *, idempotency_key: str, tool: str, context: Optional[str] = None) -> bool:
        return self.config.register_tool_call_idempotency_key(idempotency_key=idempotency_key, tool=tool, context=context)

    # --- Eval Domain ---
    def save_eval_report(self, report: EvalRunReport | Dict[str, Any]) -> int:
        return self.eval.save_eval_report(report)

    def save_eval_dataset(self, dataset: EvalDataset | Dict[str, Any], *, version_tag: Optional[str] = None) -> int:
        return self.eval.save_eval_dataset(dataset, version_tag=version_tag)

    def list_eval_datasets(self, *, workflow_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self.eval.list_eval_datasets(workflow_id=workflow_id, limit=limit)

    def get_eval_dataset(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        return self.eval.get_eval_dataset(dataset_id)

    def list_eval_reports(self, *, workflow_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return self.eval.list_eval_reports(workflow_id=workflow_id, limit=limit)

    def get_eval_report(self, run_id: int) -> Optional[Dict[str, Any]]:
        return self.eval.get_eval_report(run_id)

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            # Sub-storages share the connection, so they are effectively closed too
