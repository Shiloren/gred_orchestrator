"""Resource Governor — admission control for task execution based on system load."""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .hardware_monitor_service import HardwareMonitorService

logger = logging.getLogger("orchestrator.resource_governor")


class TaskWeight(str, Enum):
    LIGHT = "light"      # file ops, git, lint
    MEDIUM = "medium"    # small LLM (<4K tokens)
    HEAVY = "heavy"      # large inference, multi-step


class AdmissionDecision(str, Enum):
    ALLOW = "allow"
    DEFER = "defer"
    REJECT = "reject"


class ResourceGovernor:
    """Evaluates system resources and decides whether to admit new tasks."""

    _thresholds = {
        "cpu_max": 85.0,
        "ram_max": 90.0,
        "vram_free_min_gb": 1.0,
        "gpu_temp_max": 85,
    }

    def __init__(self, hw_monitor: "HardwareMonitorService") -> None:
        self._hw = hw_monitor

    def evaluate(self, weight: TaskWeight = TaskWeight.MEDIUM) -> AdmissionDecision:
        """Check current system resources and decide whether to admit a task."""
        try:
            snap = self._hw.get_snapshot()
        except Exception as exc:
            logger.warning("Cannot get hardware snapshot: %s — allowing task", exc)
            return AdmissionDecision.ALLOW

        # CPU/RAM gate
        if snap.cpu_percent > self._thresholds["cpu_max"]:
            logger.info("CPU %.1f%% > %.1f%% — deferring %s task",
                        snap.cpu_percent, self._thresholds["cpu_max"], weight.value)
            return AdmissionDecision.DEFER
        if snap.ram_percent > self._thresholds["ram_max"]:
            logger.info("RAM %.1f%% > %.1f%% — deferring %s task",
                        snap.ram_percent, self._thresholds["ram_max"], weight.value)
            return AdmissionDecision.DEFER

        # GPU gate for heavy tasks
        if weight == TaskWeight.HEAVY:
            if snap.gpu_vram_free_gb < self._thresholds["vram_free_min_gb"] and snap.gpu_vram_gb > 0:
                logger.info("VRAM free %.2fGB < %.2fGB — deferring heavy task",
                            snap.gpu_vram_free_gb, self._thresholds["vram_free_min_gb"])
                return AdmissionDecision.DEFER
            if snap.gpu_temp and snap.gpu_temp > self._thresholds["gpu_temp_max"]:
                logger.info("GPU temp %.1f°C > %s°C — deferring heavy task",
                            snap.gpu_temp, self._thresholds["gpu_temp_max"])
                return AdmissionDecision.DEFER

        return AdmissionDecision.ALLOW

    def should_defer(self, weight: TaskWeight = TaskWeight.MEDIUM) -> bool:
        return self.evaluate(weight) != AdmissionDecision.ALLOW

    def update_thresholds(self, overrides: dict) -> None:
        self._thresholds.update(overrides)
