from __future__ import annotations

import time
from typing import Any, Dict, List

from .storage_service import StorageService


class TrustEventBuffer:
    """In-memory TrustEvent buffer with flush by size/time."""

    def __init__(
        self,
        storage: StorageService,
        *,
        max_events: int = 50,
        flush_interval_seconds: int = 10,
    ):
        self.storage = storage
        self.max_events = max_events
        self.flush_interval_seconds = flush_interval_seconds
        self._buffer: List[Dict[str, Any]] = []
        self._last_flush_at = time.monotonic()

    @property
    def size(self) -> int:
        return len(self._buffer)

    def add_event(self, event: Dict[str, Any]) -> None:
        self._buffer.append(dict(event))
        self.flush_if_needed()

    def flush_if_needed(self) -> None:
        if not self._buffer:
            return
        age = time.monotonic() - self._last_flush_at
        if len(self._buffer) >= self.max_events or age >= self.flush_interval_seconds:
            self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        batch = list(self._buffer)
        self.storage.save_trust_events(batch)
        self._buffer.clear()
        self._last_flush_at = time.monotonic()
