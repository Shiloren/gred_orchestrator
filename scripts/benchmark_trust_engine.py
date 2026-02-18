import time
import statistics
import sys
import os
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.gimo_server.services.trust_engine import TrustEngine, TrustThresholds, CircuitBreakerConfig

def benchmark_trust_engine_latency():
    # Setup mock storage
    mock_storage = MagicMock()
    mock_storage.list_trust_events.return_value = [
        {"dimension_key": "test_dim", "outcome": "approved", "timestamp": "2024-01-01T00:00:00Z"}
        for _ in range(100)
    ]
    mock_storage.get_trust_record.return_value = {}
    mock_storage.get_circuit_breaker_config.return_value = None
    
    engine = TrustEngine(trust_store=MagicMock(storage=mock_storage))
    
    latencies = []
    # Warmup
    for _ in range(10):
        engine.query_dimension("test_dim")
    
    # Measure
    for _ in range(100):
        start = time.perf_counter()
        engine.query_dimension("test_dim")
        latencies.append((time.perf_counter() - start) * 1000) # ms
        
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]
    
    print(f"TrustEngine Latency Benchmark (100 runs):")
    print(f"  Average: {avg_latency:.4f} ms")
    print(f"  P95:     {p95_latency:.4f} ms")
    
    assert avg_latency < 10, f"Average latency {avg_latency:.2f}ms exceeds 10ms target"
    print("SUCCESS: Latency is within acceptable limits (<10ms)")

if __name__ == "__main__":
    benchmark_trust_engine_latency()
