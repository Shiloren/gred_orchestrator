from __future__ import annotations

from tools.gimo_server.services.trust_event_buffer import TrustEventBuffer


class StubStorage:
    def __init__(self):
        self.saved_batches = []

    def save_trust_events(self, events):
        self.saved_batches.append(list(events))


def test_trust_event_buffer_flushes_on_max_events():
    storage = StubStorage()
    buffer = TrustEventBuffer(storage=storage, max_events=2, flush_interval_seconds=999)

    buffer.add_event({"tool": "a", "outcome": "approved"})
    assert buffer.size == 1
    assert storage.saved_batches == []

    buffer.add_event({"tool": "b", "outcome": "rejected"})
    assert buffer.size == 0
    assert len(storage.saved_batches) == 1
    assert len(storage.saved_batches[0]) == 2


def test_trust_event_buffer_flush_if_needed_by_time():
    storage = StubStorage()
    buffer = TrustEventBuffer(storage=storage, max_events=50, flush_interval_seconds=0)

    buffer.add_event({"tool": "x", "outcome": "approved"})
    # flush_interval_seconds=0 forces immediate flush
    assert buffer.size == 0
    assert len(storage.saved_batches) == 1
    assert storage.saved_batches[0][0]["tool"] == "x"
