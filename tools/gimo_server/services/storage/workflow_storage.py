from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional
from .base_storage import BaseStorage

logger = logging.getLogger("orchestrator.services.storage.workflow")

class WorkflowStorage(BaseStorage):
    """Storage logic for workflows and checkpoints."""

    def ensure_tables(self) -> None:
        with self._conn:
            # Workflow graphs
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
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

    def save_workflow(self, workflow_id: str, data: str) -> None:
        if not isinstance(data, str):
            data = json.dumps(data)
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO workflows (id, data) VALUES (?, ?)",
                (workflow_id, data)
            )
        
        # Dual-write to GICS
        if self.gics:
            try:
                self.gics.put(f"wf:{workflow_id}", {"data": data})
            except Exception as e:
                logger.error("Failed to push workflow %s to GICS: %s", workflow_id, e)

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
        
        # Dual-write to GICS
        if self.gics:
            try:
                # Key includes timestamp for chronological tracking in GICS
                timestamp = int(time.time() * 1000)
                cp_key = f"wf:{workflow_id}:cp:{timestamp}"
                self.gics.put(cp_key, {
                    "workflow_id": workflow_id,
                    "node_id": node_id,
                    "state": state_payload,
                    "output": output_payload,
                    "status": status,
                    "timestamp": timestamp
                })
            except Exception as e:
                logger.error("Failed to push checkpoint for %s to GICS: %s", workflow_id, e)

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        # Try GICS first
        if self.gics:
            try:
                result = self.gics.get(f"wf:{workflow_id}")
                if result and "fields" in result:
                    data = result["fields"].get("data")
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except Exception:
                            pass
                    return {
                        "id": workflow_id,
                        "data": data,
                        "created_at": result.get("timestamp"), # Approximate
                    }
            except Exception as e:
                logger.error("Failed to get workflow from GICS: %s", e)

        # Fallback to SQLite
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
        # Try GICS first
        if self.gics:
            try:
                prefix = f"wf:{workflow_id}:cp:"
                items = self.gics.scan(prefix=prefix, include_fields=True)
                if items:
                    checkpoints = []
                    for item in items:
                        fields = item.get("fields", {})
                        checkpoints.append({
                            "workflow_id": fields.get("workflow_id"),
                            "node_id": fields.get("node_id"),
                            "state": self._maybe_parse_json(fields.get("state")),
                            "output": self._maybe_parse_json(fields.get("output")),
                            "status": fields.get("status"),
                            "timestamp": fields.get("timestamp"),
                        })
                    # Sort by timestamp (approximate for order)
                    checkpoints.sort(key=lambda x: x.get("timestamp") or 0)
                    return checkpoints
            except Exception as e:
                logger.error("Failed to list checkpoints from GICS: %s", e)

        # Fallback to SQLite
        rows = self._conn.execute(
            """
            SELECT workflow_id, node_id, state, output, status, timestamp
            FROM checkpoints
            WHERE workflow_id = ?
            ORDER BY id ASC
            """,
            (workflow_id,),
        ).fetchall()

        return [
            {
                "workflow_id": row["workflow_id"],
                "node_id": row["node_id"],
                "state": self._maybe_parse_json(row["state"]),
                "output": self._maybe_parse_json(row["output"]),
                "status": row["status"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]

    def _maybe_parse_json(self, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        try:
            return json.loads(value)
        except Exception:
            return value
