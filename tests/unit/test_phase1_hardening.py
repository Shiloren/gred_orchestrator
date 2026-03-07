from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tools.gimo_server.main import app
from tools.gimo_server.security import verify_token
from tools.gimo_server.security.auth import AuthContext
from tools.gimo_server.services.authority import ExecutionAuthority
from tools.gimo_server.services.log_rotation_service import LogRotationService
from tools.gimo_server.services.notification_service import (
    NotificationService,
    CIRCUIT_BREAKER_THRESHOLD,
)
from tools.gimo_server.services.ops_service import OpsService
from tools.gimo_server.services.resource_governor import (
    AdmissionDecision,
    ResourceGovernor,
    TaskWeight,
)
from tools.gimo_server.routers.ops import observability_router


def _override_auth() -> AuthContext:
    return AuthContext(token="test-token", role="admin")


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch, tmp_path):
    NotificationService.reset_state_for_tests()
    ExecutionAuthority.reset()
    monkeypatch.setattr(OpsService, "OPS_DIR", tmp_path)
    monkeypatch.setattr(OpsService, "DRAFTS_DIR", tmp_path / "drafts")
    monkeypatch.setattr(OpsService, "APPROVED_DIR", tmp_path / "approved")
    monkeypatch.setattr(OpsService, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(OpsService, "RUN_EVENTS_DIR", tmp_path / "run_events")
    monkeypatch.setattr(OpsService, "RUN_LOGS_DIR", tmp_path / "run_logs")
    monkeypatch.setattr(OpsService, "LOCKS_DIR", tmp_path / "locks")
    monkeypatch.setattr(OpsService, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(OpsService, "LOCK_FILE", tmp_path / ".ops.lock")
    OpsService.ensure_dirs()
    app.dependency_overrides[verify_token] = _override_auth
    yield
    app.dependency_overrides.clear()
    NotificationService.reset_state_for_tests()
    ExecutionAuthority.reset()


def test_realtime_metrics_endpoint_exposes_notification_metrics():
    local_app = FastAPI()
    local_app.include_router(observability_router.router, prefix="/ops")
    local_app.dependency_overrides[verify_token] = _override_auth
    with TestClient(local_app) as client:
        resp = client.get("/ops/realtime/metrics")
        assert resp.status_code == 200
        payload = resp.json()
        assert "published" in payload
        assert "dropped" in payload


def test_circuit_breaker_opens_for_slow_subscriber(monkeypatch):
    NotificationService.configure(queue_maxsize=1)
    _ = asyncio.run(NotificationService.subscribe())

    async def _emit_many():
        for idx in range(CIRCUIT_BREAKER_THRESHOLD + 2):
            await NotificationService._broadcast_now("evt", {"idx": idx, "critical": True})

    asyncio.run(_emit_many())
    metrics = NotificationService.get_metrics()
    assert metrics["circuit_opens"] >= 1


def test_event_driven_worker_notify_sets_wake_event():
    from tools.gimo_server.services.run_worker import RunWorker

    worker = RunWorker()
    assert not worker._wake_event.is_set()
    worker.notify()
    assert worker._wake_event.is_set()


def test_resource_governor_defers_on_high_cpu_and_vram():
    @dataclass
    class _Snap:
        cpu_percent: float
        ram_percent: float
        gpu_vram_free_gb: float
        gpu_vram_gb: float
        gpu_temp: float

    class _Hw:
        def __init__(self, snap):
            self._snap = snap

        def get_snapshot(self):
            return self._snap

    gov_cpu = ResourceGovernor(_Hw(_Snap(95.0, 40.0, 4.0, 8.0, 40.0)))
    assert gov_cpu.evaluate(TaskWeight.MEDIUM) == AdmissionDecision.DEFER

    gov_vram = ResourceGovernor(_Hw(_Snap(20.0, 30.0, 0.2, 8.0, 40.0)))
    assert gov_vram.evaluate(TaskWeight.HEAVY) == AdmissionDecision.DEFER


def test_append_only_state_and_materialized_read():
    approved = OpsService.create_draft(prompt="p", content="c")
    appr = OpsService.approve_draft(approved.id, approved_by="t")
    run = OpsService.create_run(appr.id)

    OpsService.update_run_status(run.id, "running", msg="start")
    OpsService.set_run_stage(run.id, "stage-1")
    OpsService.update_run_status(run.id, "done", msg="end")

    run_json = OpsService._run_path(run.id)
    events_jsonl = OpsService._run_events_path(run.id)
    assert run_json.exists()
    assert events_jsonl.exists()
    lines = [ln for ln in events_jsonl.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 3

    materialized = OpsService.get_run(run.id)
    assert materialized is not None
    assert materialized.status == "done"
    assert materialized.stage == "stage-1"


def test_log_rotation_rotates_and_deletes(tmp_path, monkeypatch):
    scan_dir = tmp_path / "logs"
    scan_dir.mkdir(parents=True, exist_ok=True)
    old_file = scan_dir / "old.log"
    old_file.write_text("x", encoding="utf-8")
    old_ts = (datetime.now(timezone.utc) - timedelta(days=40)).timestamp()
    import os
    os.utime(old_file, (old_ts, old_ts))

    large_file = scan_dir / "large.log"
    large_file.write_bytes(b"a" * (50 * 1024 * 1024 + 32))

    monkeypatch.setattr("tools.gimo_server.services.log_rotation_service.SCAN_DIRS", [scan_dir])
    monkeypatch.setattr("tools.gimo_server.services.log_rotation_service.OPS_DATA_DIR", tmp_path)

    stats = LogRotationService.run_rotation()
    assert stats["deleted"] >= 1
    assert stats["compressed"] >= 1
    assert (scan_dir / "large.log.gz").exists()
