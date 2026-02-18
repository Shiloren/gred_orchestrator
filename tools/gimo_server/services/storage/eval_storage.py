from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from .base_storage import BaseStorage
from ...ops_models import EvalDataset, EvalRunReport

logger = logging.getLogger("orchestrator.services.storage.eval")

class EvalStorage(BaseStorage):
    """Storage logic for evaluation datasets and reports."""

    def ensure_tables(self) -> None:
        with self._conn:
            # Eval runs history
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
            run_id = int(cursor.lastrowid)
        
        # Dual-write to GICS
        if self.gics:
            try:
                workflow_id = data.get("workflow_id", "unknown")
                self.gics.put(f"er:{workflow_id}:{run_id}", data)
            except Exception as e:
                logger.error("Failed to push eval report %s to GICS: %s", run_id, e)
        
        return run_id

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
            dataset_id = int(cursor.lastrowid)
            
        # Dual-write to GICS
        if self.gics:
            try:
                workflow_id = data.get("workflow_id", "unknown")
                version = version_tag or "latest"
                self.gics.put(f"ed:{workflow_id}:{version}", data)
            except Exception as e:
                logger.error("Failed to push eval dataset %s to GICS: %s", dataset_id, e)

        return dataset_id

    def list_eval_datasets(self, *, workflow_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        # Try GICS first
        if self.gics:
            try:
                prefix = "ed:"
                if workflow_id:
                    prefix += f"{workflow_id}:"
                
                items = self.gics.scan(prefix=prefix, include_fields=True)
                if items:
                    datasets = []
                    for item in items:
                        fields = item.get("fields", {})
                        # fields in GICS is the full dataset object
                        datasets.append({
                            "dataset_id": 0, # Virtual ID
                            "workflow_id": fields.get("workflow_id"),
                            "version_tag": fields.get("version_tag", "latest"),
                            "created_at": item.get("timestamp"),
                        })
                    datasets.sort(key=lambda x: x.get("created_at") or 0, reverse=True)
                    return datasets[:limit]
            except Exception as e:
                logger.error("Failed to list eval datasets from GICS: %s", e)

        # Fallback to SQLite
        if workflow_id:
            rows = self._conn.execute(
                """
                SELECT id, workflow_id, version_tag, dataset_json, created_at
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
                SELECT id, workflow_id, version_tag, dataset_json, created_at
                FROM eval_datasets
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        results = []
        for row in rows:
            try:
                data = json.loads(row["dataset_json"])
            except Exception:
                data = {}
            
            results.append({
                "dataset_id": int(row["id"]),
                "workflow_id": row["workflow_id"],
                "version_tag": row["version_tag"],
                "created_at": row["created_at"],
                "name": data.get("name", "Untitled Dataset"),
                "description": data.get("description", ""),
                "cases": data.get("cases", []), # Frontend uses cases.length
            })
            
        return results

    def get_eval_dataset(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        # Note: GICS doesn't use the SQLite integer ID. 
        # For full migration, we should use (workflow_id, version_tag) as key.
        # For now, let's keep SQLite as the index for dataset_id.
        
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

        workflow_id = row["workflow_id"]
        version = row["version_tag"] or "latest"
        
        # Try GICS for latest data
        if self.gics:
            try:
                result = self.gics.get(f"ed:{workflow_id}:{version}")
                if result and "fields" in result:
                    return {
                        "dataset_id": int(row["id"]),
                        "workflow_id": workflow_id,
                        "version_tag": row["version_tag"],
                        "created_at": row["created_at"],
                        "dataset": result["fields"],
                    }
            except Exception as e:
                logger.error("Failed to get eval dataset from GICS: %s", e)

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
        # Try GICS first
        if self.gics:
            try:
                prefix = "er:"
                if workflow_id:
                    prefix += f"{workflow_id}:"
                
                items = self.gics.scan(prefix=prefix, include_fields=True)
                if items:
                    reports = []
                    for item in items:
                        fields = item.get("fields", {})
                        reports.append({
                            "run_id": 0, # Virtual key
                            "workflow_id": fields.get("workflow_id"),
                            "gate_passed": bool(fields.get("gate_passed")),
                            "pass_rate": float(fields.get("pass_rate",0.0)),
                            "avg_score": float(fields.get("avg_score",0.0)),
                            "total_cases": int(fields.get("total_cases",0)),
                            "passed_cases": int(fields.get("passed_cases",0)),
                            "failed_cases": int(fields.get("failed_cases",0)),
                            "created_at": item.get("timestamp"),
                        })
                    reports.sort(key=lambda x: x.get("created_at") or 0, reverse=True)
                    return reports[:limit]
            except Exception as e:
                logger.error("Failed to list eval reports from GICS: %s", e)

        # Fallback to SQLite
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

        workflow_id = row["workflow_id"]
        
        # Try GICS for detailed report
        if self.gics:
            try:
                # Key format: er:workflow_id:run_id
                result = self.gics.get(f"er:{workflow_id}:{run_id}")
                if result and "fields" in result:
                    return {
                        "run_id": int(row["id"]),
                        "workflow_id": workflow_id,
                        "created_at": row["created_at"],
                        "report": result["fields"],
                    }
            except Exception as e:
                logger.error("Failed to get eval report from GICS: %s", e)

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
