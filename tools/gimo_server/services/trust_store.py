from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import OPS_DATA_DIR
from .storage_service import StorageService


class TrustStore:
    """3-tier trust storage (HOT/WARM/COLD) MVP.

    HOT: SQLite trust_records via StorageService
    WARM: append-only JSONL file (active segment)
    COLD: archived warm segments with SHA-256 sidecar
    """

    def __init__(
        self,
        storage: StorageService,
        *,
        warm_path: Optional[Path] = None,
        cold_dir: Optional[Path] = None,
    ):
        self.storage = storage
        self.warm_path = warm_path or (OPS_DATA_DIR / "trust_active.gics")
        self.cold_dir = cold_dir or (OPS_DATA_DIR / "trust_cold")
        self.warm_path.parent.mkdir(parents=True, exist_ok=True)
        self.cold_dir.mkdir(parents=True, exist_ok=True)

    def flush_hot_to_warm(self, *, limit: int = 1000) -> Dict[str, Any]:
        records = self.storage.list_trust_records(limit=limit)
        if not records:
            return {"written": 0, "warm_path": str(self.warm_path)}

        now = datetime.now(timezone.utc).isoformat()
        with self.warm_path.open("a", encoding="utf-8") as f:
            for record in records:
                entry = {
                    "flushed_at": now,
                    "dimension_key": record.get("dimension_key"),
                    "record": record,
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return {"written": len(records), "warm_path": str(self.warm_path)}

    def query_dimension(self, dimension_key: str) -> Optional[Dict[str, Any]]:
        hot = self.storage.get_trust_record(dimension_key)
        if hot is not None:
            return hot

        if not self.warm_path.exists():
            return None

        # Scan warm entries newest-first
        lines = self.warm_path.read_text(encoding="utf-8").splitlines()
        for raw in reversed(lines):
            try:
                item = json.loads(raw)
            except Exception:
                continue
            if item.get("dimension_key") == dimension_key:
                record = item.get("record")
                return record if isinstance(record, dict) else None
        return None

    def archive_warm_to_cold(self, *, label: Optional[str] = None) -> Dict[str, Any]:
        if not self.warm_path.exists() or self.warm_path.stat().st_size == 0:
            return {"archived": False, "reason": "warm_empty"}

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        suffix = f"_{label}" if label else ""
        cold_file = self.cold_dir / f"trust_{ts}{suffix}.gics"
        content = self.warm_path.read_bytes()
        cold_file.write_bytes(content)

        digest = hashlib.sha256(content).hexdigest()
        sha_file = cold_file.with_suffix(cold_file.suffix + ".sha256")
        sha_file.write_text(digest, encoding="utf-8")

        # truncate warm segment after archive
        self.warm_path.write_text("", encoding="utf-8")

        return {
            "archived": True,
            "cold_file": str(cold_file),
            "sha256": digest,
        }

    def verify_cold_file(self, cold_file: Path) -> bool:
        target = Path(cold_file)
        sha_file = target.with_suffix(target.suffix + ".sha256")
        if not target.exists() or not sha_file.exists():
            return False
        content = target.read_bytes()
        actual = hashlib.sha256(content).hexdigest()
        expected = sha_file.read_text(encoding="utf-8").strip()
        return actual == expected

    def health(self) -> Dict[str, Any]:
        cold_files = sorted(self.cold_dir.glob("trust_*.gics"))
        latest = cold_files[-1] if cold_files else None
        latest_ok = self.verify_cold_file(latest) if latest else True
        return {
            "warm_path": str(self.warm_path),
            "warm_exists": self.warm_path.exists(),
            "warm_bytes": self.warm_path.stat().st_size if self.warm_path.exists() else 0,
            "cold_files": len(cold_files),
            "latest_cold_file": str(latest) if latest else None,
            "latest_cold_verified": latest_ok,
        }
