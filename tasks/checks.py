"""Common task-check interfaces for structured manipulation tasks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import numpy as np


def _serialize_value(value: Any) -> Any:
    """Convert numpy-heavy structures into JSON-friendly values."""
    if isinstance(value, np.ndarray):
        return value.astype(np.float32).tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    return value


@dataclass
class TaskCheckInput:
    """Machine-readable input passed into a task checker."""

    task_name: str
    observation: Optional[np.ndarray]
    base_info: Dict[str, Any]
    task_config: Dict[str, Any]
    adapter: Any
    current_step: int


@dataclass
class TaskCheckResult:
    """Unified success/failure evaluation payload."""

    success: bool
    failure: bool
    reason: str
    official_flags: Dict[str, bool] = field(default_factory=dict)
    official_metrics: Dict[str, Any] = field(default_factory=dict)
    debug_metrics: Dict[str, Any] = field(default_factory=dict)
    backend_type: str = "unknown"
    checker_name: str = "unknown_checker"
    notes: str = ""
    contract_name: str = "task_evaluation_contract"
    contract_version: str = "v1"

    @property
    def flags(self) -> Dict[str, bool]:
        """Backward-compatible alias for the official task flags."""
        return self.official_flags

    @property
    def metrics(self) -> Dict[str, Any]:
        """Backward-compatible alias for the official task metrics."""
        return self.official_metrics

    def to_payload(self) -> Dict[str, Any]:
        """Return the structured evaluation payload without flattening debug fields."""
        return {
            "success": bool(self.success),
            "failure": bool(self.failure),
            "reason": str(self.reason),
            "checker_name": str(self.checker_name),
            "backend_type": str(self.backend_type),
            "notes": str(self.notes),
            "contract_name": str(self.contract_name),
            "contract_version": str(self.contract_version),
            "official_flags": _serialize_value(self.official_flags),
            "official_metrics": _serialize_value(self.official_metrics),
            "debug_metrics": _serialize_value(self.debug_metrics),
        }

    def to_dict(self, prefix: str = "task_check") -> Dict[str, Any]:
        """Flatten the result into a JSON-friendly info payload."""
        structured_payload = self.to_payload()
        payload = {
            f"{prefix}_success": structured_payload["success"],
            f"{prefix}_failure": structured_payload["failure"],
            f"{prefix}_reason": structured_payload["reason"],
            f"{prefix}_checker_name": structured_payload["checker_name"],
            f"{prefix}_backend_type": structured_payload["backend_type"],
            f"{prefix}_notes": structured_payload["notes"],
            f"{prefix}_contract_name": structured_payload["contract_name"],
            f"{prefix}_contract_version": structured_payload["contract_version"],
            f"{prefix}_official_flags": structured_payload["official_flags"],
            f"{prefix}_official_metrics": structured_payload["official_metrics"],
            f"{prefix}_debug_metrics": structured_payload["debug_metrics"],
            f"{prefix}_flags": structured_payload["official_flags"],
            f"{prefix}_metrics": structured_payload["official_metrics"],
        }

        for key, value in sorted(self.official_flags.items()):
            payload[f"{prefix}_{key}"] = bool(value)
        for key, value in sorted(self.official_metrics.items()):
            payload[f"{prefix}_{key}"] = _serialize_value(value)
        return payload


class BaseTaskChecker(ABC):
    """Abstract success/failure checker used by structured tasks."""

    checker_name = "base_task_checker"

    def reset(self, adapter: Any = None) -> None:
        """Reset checker-local state at the start of an episode."""

    @abstractmethod
    def evaluate(self, check_input: TaskCheckInput) -> TaskCheckResult:
        """Evaluate the current task state."""


__all__ = ["TaskCheckInput", "TaskCheckResult", "BaseTaskChecker"]
