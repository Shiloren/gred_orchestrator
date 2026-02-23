from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from collections import defaultdict

from ...ops_models import CostEvent

logger = logging.getLogger("orchestrator.ops.cost")

class CostStorage:
    """Storage service for cost and usage metrics.
    
    Persists events to GICS for real-time syncing and aggregation.
    """

    def __init__(self, conn: Optional[Any] = None, gics: Optional[Any] = None):
        self._conn = conn # Maintained temporarily for API compatibility
        self.gics = gics

    def ensure_tables(self):
        """No-op: using GICS."""
        pass

    def save_cost_event(self, event: CostEvent) -> None:
        """Save a cost event to storage."""
        if not self.gics:
            return
        try:
            key = f"ce:{event.workflow_id}:{event.node_id}:{int(event.timestamp.timestamp())}:{event.id}"
            self.gics.put(key, event.model_dump())
        except Exception as e:
            logger.error(f"Failed to save cost event {event.id}: {e}")

    def _fetch_events(self, days: Optional[int] = 30, hours: Optional[int] = None) -> List[Dict[str, Any]]:
        if not self.gics:
            return []
        try:
            now = datetime.now(timezone.utc)
            if hours is not None:
                cutoff = now - timedelta(hours=hours)
            elif days is not None:
                cutoff = now - timedelta(days=days)
            else:
                cutoff = now - timedelta(days=3650) # 10 years fallback
                
            items = self.gics.scan("ce:", include_fields=True)
            events = []
            for item in items:
                fields = item.get("fields", {})
                if "timestamp" in fields:
                    try:
                        ts_val = fields["timestamp"]
                        if isinstance(ts_val, datetime):
                            ts = ts_val
                        else:
                            ts_str = str(ts_val)
                            if ts_str.endswith('Z'):
                                ts_str = ts_str[:-1] + '+00:00'
                            ts = datetime.fromisoformat(ts_str)
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        if ts >= cutoff:
                            events.append(fields)
                    except ValueError:
                        pass
            return events
        except Exception as e:
            logger.error(f"Failed to fetch cost events: {e}")
            return []

    def get_provider_spend(self, provider: str, days: int = 30) -> float:
        events = self._fetch_events(days=days)
        return sum(e.get("cost_usd", 0.0) for e in events if e.get("provider") == provider)

    def get_total_spend(self, days: int = 30) -> float:
        events = self._fetch_events(days=days)
        return sum(e.get("cost_usd", 0.0) for e in events)

    def aggregate_by_model(self, days: int = 30) -> List[Dict[str, Any]]:
        events = self._fetch_events(days=days)
        agg = defaultdict(lambda: {"cost": 0.0, "count": 0})
        for e in events:
            model = e.get("model", "unknown")
            agg[model]["cost"] += e.get("cost_usd", 0.0)
            agg[model]["count"] += 1
            
        result = [{"model": k, "cost": v["cost"], "count": v["count"]} for k, v in agg.items()]
        return sorted(result, key=lambda x: x["cost"], reverse=True)

    def get_daily_costs(self, days: int = 30) -> List[Dict[str, Any]]:
        events = self._fetch_events(days=days)
        agg = defaultdict(lambda: {"cost": 0.0, "tokens": 0})
        for e in events:
            if "timestamp" in e:
                ts_val = e["timestamp"]
                if isinstance(ts_val, datetime):
                    date = ts_val.strftime("%Y-%m-%d")
                else:
                    date = str(ts_val)[:10] # YYYY-MM-DD
                agg[date]["cost"] += e.get("cost_usd", 0.0)
                agg[date]["tokens"] += e.get("total_tokens", 0)
                
        result = [{"date": k, "cost": v["cost"], "tokens": v["tokens"]} for k, v in agg.items()]
        return sorted(result, key=lambda x: x["date"])

    def get_roi_leaderboard(self, days: int = 30) -> List[Dict[str, Any]]:
        events = self._fetch_events(days=days)
        agg = defaultdict(lambda: {"count": 0, "sum_quality": 0.0, "sum_cost": 0.0})
        for e in events:
            qs = e.get("quality_score", 0.0)
            if qs > 0:
                key = (e.get("model", "unknown"), e.get("task_type", "unknown"))
                agg[key]["count"] += 1
                agg[key]["sum_quality"] += qs
                agg[key]["sum_cost"] += e.get("cost_usd", 0.0)
                
        result = []
        for (model, task_type), v in agg.items():
            avg_quality = v["sum_quality"] / v["count"]
            avg_cost = v["sum_cost"] / v["count"]
            roi_score = avg_quality / (avg_cost + 0.000001)
            result.append({
                "model": model,
                "task_type": task_type,
                "sample_count": v["count"],
                "avg_quality": avg_quality,
                "avg_cost": avg_cost,
                "roi_score": roi_score
            })
        # Order by task_type ASC, roi_score DESC
        return sorted(result, key=lambda x: (x["task_type"], -x["roi_score"]))

    def get_cascade_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        events = self._fetch_events(days=days)
        agg = defaultdict(lambda: {"total_calls": 0, "cascaded_calls": 0, "sum_cascade_depth": 0, "total_spent": 0.0})
        for e in events:
            tt = e.get("task_type", "unknown")
            casc_lvl = e.get("cascade_level", 0)
            
            agg[tt]["total_calls"] += 1
            if casc_lvl > 0:
                agg[tt]["cascaded_calls"] += 1
            agg[tt]["sum_cascade_depth"] += casc_lvl
            agg[tt]["total_spent"] += e.get("cost_usd", 0.0)
            
        result = []
        for tt, v in agg.items():
            result.append({
                "task_type": tt,
                "total_calls": v["total_calls"],
                "cascaded_calls": v["cascaded_calls"],
                "avg_cascade_depth": v["sum_cascade_depth"] / max(1, v["total_calls"]),
                "total_spent": v["total_spent"]
            })
        return result

    def get_total_savings(self, days: int = 30) -> float:
        events = self._fetch_events(days=days)
        
        non_cache_costs = [e.get("cost_usd", 0.0) for e in events if not e.get("cache_hit", False)]
        avg_non_cache_cost = sum(non_cache_costs) / len(non_cache_costs) if non_cache_costs else 0.005
        
        cache_hits = sum(1 for e in events if e.get("cache_hit", False))
        cache_savings = cache_hits * avg_non_cache_cost
        
        cascade_savings = sum(
            (0.015 - e.get("cost_usd", 0.0))
            for e in events
            if e.get("cascade_level", 0) == 0 and e.get("quality_score", 0.0) >= 80 and e.get("cost_usd", 0.0) < 0.01
        )
        
        return round(cache_savings + cascade_savings, 2)

    def check_budget_alerts(self, global_budget: float, thresholds: List[int]) -> List[Dict[str, Any]]:
        if not global_budget:
            return []
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
        events = self._fetch_events(days=days)
        total = len(events)
        hits = sum(1 for e in events if e.get("cache_hit", False))
        
        non_cache_costs = [e.get("cost_usd", 0.0) for e in events if not e.get("cache_hit", False)]
        avg_cost = sum(non_cache_costs) / len(non_cache_costs) if non_cache_costs else 0.005
        
        return {
            "total_calls": total,
            "cache_hits": hits,
            "hit_rate": round(hits / total, 3) if total > 0 else 0.0,
            "estimated_savings_usd": round(hits * avg_cost, 4)
        }

    def aggregate_by_task_type(self, days: int = 30) -> List[Dict[str, Any]]:
        events = self._fetch_events(days=days)
        agg = defaultdict(lambda: {"cost": 0.0, "sum_quality": 0.0, "count": 0})
        for e in events:
            tt = e.get("task_type", "unknown")
            agg[tt]["cost"] += e.get("cost_usd", 0.0)
            agg[tt]["sum_quality"] += e.get("quality_score", 0.0)
            agg[tt]["count"] += 1
            
        result = [
            {
                "task_type": k,
                "cost": v["cost"],
                "quality": v["sum_quality"] / v["count"] if v["count"] > 0 else 0.0,
                "count": v["count"]
            }
            for k, v in agg.items()
        ]
        return sorted(result, key=lambda x: x["cost"], reverse=True)

    def aggregate_by_provider(self, days: int = 30) -> List[Dict[str, Any]]:
        events = self._fetch_events(days=days)
        agg = defaultdict(lambda: {"cost": 0.0, "tokens": 0, "count": 0})
        for e in events:
            p = e.get("provider", "unknown")
            agg[p]["cost"] += e.get("cost_usd", 0.0)
            agg[p]["tokens"] += e.get("total_tokens", 0)
            agg[p]["count"] += 1
            
        result = [
            {"provider": k, "cost": v["cost"], "total_tokens": v["tokens"], "count": v["count"]}
            for k, v in agg.items()
        ]
        return sorted(result, key=lambda x: x["cost"], reverse=True)

    def get_avg_cost_by_task_type(self, task_type: str, model: Optional[str] = None, days: int = 90) -> Dict[str, Any]:
        events = self._fetch_events(days=days)
        valid_events = [e for e in events if e.get("task_type") == task_type and (not model or e.get("model") == model)]
        
        if not valid_events:
            return {"avg_cost": 0.0, "avg_tokens": 0, "avg_input_tokens": 0, "avg_output_tokens": 0, "sample_count": 0}
            
        count = len(valid_events)
        return {
            "avg_cost": sum(e.get("cost_usd", 0.0) for e in valid_events) / count,
            "avg_tokens": sum(e.get("total_tokens", 0) for e in valid_events) / count,
            "avg_input_tokens": sum(e.get("input_tokens", 0) for e in valid_events) / count,
            "avg_output_tokens": sum(e.get("output_tokens", 0) for e in valid_events) / count,
            "sample_count": count
        }

    def get_spend_rate(self, hours: int = 24) -> float:
        events = self._fetch_events(hours=hours)
        total_spend = sum(e.get("cost_usd", 0.0) for e in events)
        return total_spend / hours
