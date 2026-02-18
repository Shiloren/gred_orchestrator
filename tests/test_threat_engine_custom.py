import time
import pytest
from tools.gimo_server.security.threat_level import ThreatEngine, ThreatLevel, EventSeverity

def test_threat_engine_escalation():
    engine = ThreatEngine()
    assert engine.level == ThreatLevel.NOMINAL
    
    # Simulate multiple auth failures from same source
    source = "192.168.1.1"
    for _ in range(3):
        engine.record_auth_failure(source)
    
    assert engine.level == ThreatLevel.ALERT
    
    # Simulate global auth failures
    for i in range(10):
        engine.record_auth_failure(f"192.168.1.{i+10}")
        
    assert engine.level == ThreatLevel.LOCKDOWN

def test_threat_engine_decay():
    engine = ThreatEngine()
    engine.level = ThreatLevel.ALERT
    
    # Mock time to test decay
    with pytest.MonkeyPatch.context() as mp:
        initial_time = time.time()
        mp.setattr(time, "time", lambda: initial_time + 121)
        
        changed = engine.tick_decay()
        assert changed is True
        assert engine.level == ThreatLevel.NOMINAL

def test_threat_engine_whitelist():
    engine = ThreatEngine()
    # Localhost should not escalate
    for _ in range(100):
        engine.record_auth_failure("127.0.0.1")
    
    assert engine.level == ThreatLevel.NOMINAL

def test_threat_engine_snapshot():
    engine = ThreatEngine()
    engine.record_auth_failure("1.1.1.1")
    snap = engine.snapshot()
    assert snap["threat_level"] == 0
    assert snap["active_sources"] == 1
