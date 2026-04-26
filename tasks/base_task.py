"""Base interfaces for task-driven manipulation stages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import numpy as np


class BaseTask(ABC):
    """Shared task interface used by task-driven environments."""

    task_name = "base_task"

    def __init__(self, observation_mode: Optional[str] = None):
        self.observation_mode = observation_mode

    def get_name(self) -> str:
        """Return the stable task identifier."""
        return self.task_name

    def reset_task(self, env) -> None:
        """Reset task-local state after the environment resets."""

    def get_observation(self, env, mode: Optional[str] = None) -> np.ndarray:
        """Return the task observation in the requested mode."""
        resolved_mode = mode or self.observation_mode or env.observation_mode
        return env.get_observation(mode=resolved_mode)

    def get_task_config(self) -> Dict[str, Any]:
        """Return init-compatible task config for metadata or re-instantiation."""
        return {}

    def get_task_spec(self) -> Dict[str, Any]:
        """Return richer task metadata that may include non-init-only details."""
        return self.get_task_config()

    def get_evaluation_contract(self) -> Dict[str, Any]:
        """Return task-level evaluation contract metadata when available."""
        return {}

    def evaluate_state(self, env, info: Optional[Dict[str, Any]] = None):
        """Return an optional structured task-check result."""
        return None

    @abstractmethod
    def get_action_spec(self, env) -> Dict[str, Any]:
        """Describe the action interface expected by the task."""

    @abstractmethod
    def check_success(self, env, info: Optional[Dict[str, Any]] = None) -> bool:
        """Return whether the task is currently successful."""

    @abstractmethod
    def check_failure(self, env, info: Optional[Dict[str, Any]] = None) -> bool:
        """Return whether the task has entered a failure condition."""

    def get_reward(self, env, action: np.ndarray, info: Optional[Dict[str, Any]] = None) -> float:
        """Return the task reward."""
        return float(env.compute_default_reward(action, info=info))

    def get_info(self, env, info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return task-specific debug information."""
        return {}

    @staticmethod
    def quaternion_angle_error(quat_a: np.ndarray, quat_b: np.ndarray) -> float:
        """Compute the unsigned angular error between two quaternions."""
        qa = np.asarray(quat_a, dtype=np.float64)
        qb = np.asarray(quat_b, dtype=np.float64)
        qa /= max(np.linalg.norm(qa), 1e-8)
        qb /= max(np.linalg.norm(qb), 1e-8)
        dot = float(np.clip(np.abs(np.dot(qa, qb)), -1.0, 1.0))
        return float(2.0 * np.arccos(dot))
