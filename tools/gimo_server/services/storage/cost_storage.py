
from __future__ import annotations

import logging
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from filelock import FileLock
from pydantic import BaseModel

from ...config import OPS_DATA_DIR
from ...ops_models import CostEvent, CostAnalytics
from ..gics_service import GicsService
from .base_storage import BaseStorage

logger = logging.getLogger("orchestrator.ops.cost")

class CostStorage(BaseStorage):
    """Storage service for cost and usage metrics.
    
    Persists events to SQLite for aggregation and GICS for real-time syncing.
    """

    def __init__(self, conn: Optional[sqlite3.Connection] = None, gics: Optional[GicsService] = None):
        super().__init__(conn, gics)

    def ensure_tables(self):
        """Ensure database and tables exist."""
        # OPS_DATA_DIR check handled by BaseStorage/StorageService
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cost_events (
                id TEXT PRIMARY KEY,
                workflow_id TEXT,
                node_id TEXT,
                model TEXT,
                provider TEXT,
                task_type TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                cost_usd REAL,
                quality_score REAL,
                cascade_level INTEGER,
                cache_hit BOOLEAN,
                duration_ms INTEGER,
                timestamp TEXT
            )
        """)
        # Indices for fast aggregation
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_workflow ON cost_events(workflow_id)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_timestamp ON cost_events(timestamp)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_model ON cost_events(model)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_provider ON cost_events(provider)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_task_type ON cost_events(task_type)")
        if self._conn.in_transaction:
            self._conn.commit()

    def save_cost_event(self, event: CostEvent) -> None:
        """Save a cost event to storage."""
        try:
            # 1. Write to SQLite
            with self._conn:
                self._conn.execute("""
                    INSERT INTO cost_events (
                        id, workflow_id, node_id, model, provider, task_type,
                        input_tokens, output_tokens, total_tokens, cost_usd,
                        quality_score, cascade_level, cache_hit, duration_ms, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.id, event.workflow_id, event.node_id, event.model, event.provider, event.task_type,
                    event.input_tokens, event.output_tokens, event.total_tokens, event.cost_usd,
                    event.quality_score, event.cascade_level, event.cache_hit, event.duration_ms,
                    event.timestamp.isoformat()
                ))

            # 2. Sync to GICS (Best effort)
            if self.gics:
                key = f"ce:{event.workflow_id}:{event.node_id}:{int(event.timestamp.timestamp())}"
                self.gics.put(key, event.model_dump())

        except Exception as e:
            logger.error(f"Failed to save cost event {event.id}: {e}")

    def get_provider_spend(self, provider: str, days: int = 30) -> float:
        """Get total spend for a provider in the last N days."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            cursor = self._conn.execute("""
                SELECT SUM(cost_usd) FROM cost_events 
                WHERE provider = ? AND timestamp >= ?
            """, (provider, cutoff))
            result = cursor.fetchone()[0]
            return result if result else 0.0
        except Exception as e:
            logger.error(f"Failed to get provider spend: {e}")
            return 0.0

    def get_total_spend(self, days: int = 30) -> float:
        """Get total spend across all providers in the last N days."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            cursor = self._conn.execute("""
                SELECT SUM(cost_usd) FROM cost_events 
                WHERE timestamp >= ?
            """, (cutoff,))
            result = cursor.fetchone()[0]
            return result if result else 0.0
        except Exception as e:
            logger.error(f"Failed to get total spend: {e}")
            return 0.0

    def aggregate_by_model(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get usage aggregation by model."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            # conn.row_factory is set in StorageService/BaseStorage
            cursor = self._conn.execute("""
                SELECT
                    model,
                    SUM(cost_usd) as cost,
                    COUNT(*) as count
                FROM cost_events
                WHERE timestamp >= ?
                GROUP BY model
                ORDER BY cost DESC
            """, (cutoff,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to aggregate by model: {e}")
            return []

    def get_daily_costs(self, days: int = 30) -> List[Dict[str, Any]]:
         """Get daily cost timeseries."""
         try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            # Group by date part of timestamp (ISO format YYYY-MM-DD...)
            cursor = self._conn.execute("""
                SELECT 
                    substr(timestamp, 1, 10) as date,
                    SUM(cost_usd) as cost,
                    SUM(total_tokens) as tokens
                FROM cost_events
                WHERE timestamp >= ?
                GROUP BY date
                ORDER BY date ASC
            """, (cutoff,))
            return [dict(row) for row in cursor.fetchall()]
         except Exception as e:
            logger.error(f"Failed to get daily costs: {e}")
            return []

    def get_roi_leaderboard(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get model ROI leaderboard by task_type."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            cursor = self._conn.execute("""
                SELECT 
                    model,
                    task_type,
                    COUNT(*) as sample_count,
                    AVG(quality_score) as avg_quality,
                    AVG(cost_usd) as avg_cost,
                    (AVG(quality_score) / (AVG(cost_usd) + 0.000001)) as roi_score
                FROM cost_events
                WHERE timestamp >= ? AND quality_score > 0
                GROUP BY model, task_type
                ORDER BY task_type ASC, roi_score DESC
            """, (cutoff,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get ROI leaderboard: {e}")
            return []

    def get_cascade_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get stats on cascading efficiency."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            cursor = self._conn.execute("""
                SELECT 
                    task_type,
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN cascade_level > 0 THEN 1 ELSE 0 END) as cascaded_calls,
                    AVG(cascade_level) as avg_cascade_depth,
                    SUM(cost_usd) as total_spent
                FROM cost_events
                WHERE timestamp >= ?
                GROUP BY task_type
            """, (cutoff,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get cascade stats: {e}")
            return []

    def get_total_savings(self, days: int = 30) -> float:
        """Calculates total estimated savings from cache hits and cascading.
        
        NOTE: This is an estimation. Real savings = (Cost of full Opus/Sonnet call - Actual Cost)
        for every hit or cascade.
        """
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            # 1. Savings from Cache Hits (Assuming avg cost of a generic call if not hit)
            # We'll use a conservative estimate based on the average cost of non-cache-hit events.
            cursor = self._conn.execute("""
                SELECT SUM(avg_cost) FROM (
                    SELECT AVG(cost_usd) as avg_cost 
                    FROM cost_events 
                    WHERE cache_hit = 0 AND timestamp >= ?
                )
            """, (cutoff,))
            avg_non_cache_cost = cursor.fetchone()[0] or 0.005 # Fallback to 0.5 cents
            
            cursor = self._conn.execute("""
                SELECT COUNT(*) FROM cost_events WHERE cache_hit = 1 AND timestamp >= ?
            """, (cutoff,))
            cache_hits = cursor.fetchone()[0] or 0
            cache_savings = cache_hits * avg_non_cache_cost
            
            # 2. Savings from Cascading
            # Estimated as: Successful calls at level 0 that would have been higher tier.
            # We use (Avg cost of high tier [Sonnet ~0.015] - cost of this low tier) for successful level 0 calls.
            cursor = self._conn.execute("""
                SELECT SUM(0.015 - cost_usd) 
                FROM cost_events 
                WHERE cascade_level = 0 AND quality_score >= 80 AND cost_usd < 0.01 AND timestamp >= ?
            """, (cutoff,))
            cascade_savings = cursor.fetchone()[0] or 0.0
            
            total_savings = round(cache_savings + cascade_savings, 2)
            return total_savings
            
        except Exception as e:
            logger.error(f"Failed to calculate total savings: {e}")
            return 0.0

    def check_budget_alerts(self, global_budget: float, thresholds: List[int]) -> List[Dict[str, Any]]:
        """Checks if current spend breaches any percentage thresholds."""
        if not global_budget:
            return []
        
        # We assume monthly budget/thresholds for now as per plan
        current_spend = self.get_total_spend(days=30)
        percentage = (current_spend / global_budget) * 100
        
        alerts = []
        for t in sorted(thresholds, reverse=True): 
            if percentage >= (100 - t): 
                alerts.append({
                    "threshold": t,
                    "percentage": round(percentage, 1),
                    "current_spend": current_spend,
                    "global_budget": global_budget
                })
        return alerts

    def get_cache_stats(self, days: int = 30) -> Dict[str, Any]:
        """Returns hit rate and savings from cache."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            cursor = self._conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) as hits
                FROM cost_events
                WHERE timestamp >= ?
            """, (cutoff,))
            row = cursor.fetchone()
            total = row[0] or 0
            hits = row[1] or 0
            
            # Simple avg cost of non-hit calls for saving estimation
            cursor = self._conn.execute("""
                SELECT AVG(cost_usd) FROM cost_events WHERE cache_hit = 0 AND timestamp >= ?
            """, (cutoff,))
            avg_cost = cursor.fetchone()[0] or 0.005
            
            return {
                "total_calls": total,
                "cache_hits": hits,
                "hit_rate": round(hits / total, 3) if total > 0 else 0.0,
                "estimated_savings_usd": round(hits * avg_cost, 4)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"hit_rate": 0, "estimated_savings_usd": 0}

    def aggregate_by_task_type(self, days: int = 30) -> List[Dict[str, Any]]:
        """Usage aggregation by task type."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            cursor = self._conn.execute("""
                SELECT
                    task_type,
                    SUM(cost_usd) as cost,
                    AVG(quality_score) as quality,
                    COUNT(*) as count
                FROM cost_events
                WHERE timestamp >= ?
                GROUP BY task_type
                ORDER BY cost DESC
            """, (cutoff,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to aggregate by task type: {e}")
            return []

    def aggregate_by_provider(self, days: int = 30) -> List[Dict[str, Any]]:
        """Usage aggregation by provider."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            cursor = self._conn.execute("""
                SELECT
                    provider,
                    SUM(cost_usd) as cost,
                    SUM(total_tokens) as total_tokens,
                    COUNT(*) as count
                FROM cost_events
                WHERE timestamp >= ?
                GROUP BY provider
                ORDER BY cost DESC
            """, (cutoff,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to aggregate by provider: {e}")
            return []

    def get_avg_cost_by_task_type(self, task_type: str, model: Optional[str] = None, days: int = 90) -> Dict[str, Any]:
        """Calculates average metrics for a task_type (and optionally model) based on historical data.
        
        Used for predictive cost estimation.
        """
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            query = """
                SELECT 
                    AVG(cost_usd) as avg_cost,
                    AVG(total_tokens) as avg_tokens,
                    AVG(input_tokens) as avg_input_tokens,
                    AVG(output_tokens) as avg_output_tokens,
                    COUNT(*) as sample_count
                FROM cost_events
                WHERE task_type = ? AND timestamp >= ?
            """
            params = [task_type, cutoff]
            
            if model:
                query += " AND model = ?"
                params.append(model)
                
            cursor = self._conn.execute(query, params)
            row = cursor.fetchone()
            if row and row["sample_count"] > 0:
                return dict(row)
            return {"avg_cost": 0.0, "avg_tokens": 0, "avg_input_tokens": 0, "avg_output_tokens": 0, "sample_count": 0}
        except Exception as e:
            logger.error(f"Failed to get average cost for task_type '{task_type}' (model={model}): {e}")
            return {"avg_cost": 0.0, "avg_tokens": 0, "avg_input_tokens": 0, "avg_output_tokens": 0, "sample_count": 0}

    def get_spend_rate(self, hours: int = 24) -> float:
        """Calculates the average spend rate (USD/hour) over the last N hours."""
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
            cursor = self._conn.execute("""
                SELECT SUM(cost_usd) FROM cost_events 
                WHERE timestamp >= ?
            """, (cutoff,))
            total_spend = cursor.fetchone()[0] or 0.0
            return total_spend / hours
        except Exception as e:
            logger.error(f"Failed to get spend rate: {e}")
            return 0.0
