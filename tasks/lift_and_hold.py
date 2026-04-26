"""Lift-and-hold task skeleton."""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np

from .base_task import BaseTask


class LiftAndHoldTask(BaseTask):
    """Placeholder lift-and-hold task for future task-driven rollout support."""

    task_name = "lift_and_hold"

    def __init__(
        self,
        lift_height_delta=0.05,
        required_hold_steps=20,
        observation_mode: Optional[str] = None,
    ):
        super().__init__(observation_mode=observation_mode)
        self.lift_height_delta = float(lift_height_delta)
        self.required_hold_steps = int(required_hold_steps)
        self.initial_object_height = None
        self._hold_counter = 0
        self._last_processed_step = -1

    def reset_task(self, env) -> None:
        self.initial_object_height = float(env._get_object_height())
        self._hold_counter = 0
        self._last_processed_step = -1

    def get_action_spec(self, env) -> Dict[str, Any]:
        return {
            "control_level": "joint",
            "shape": (env.nu,),
            "normalized": True,
            "range": [-1.0, 1.0],
            "notes": "Placeholder until lift-specific actuation and task constraints are finalized.",
        }

    def _target_height(self) -> float:
        return float((self.initial_object_height or 0.0) + self.lift_height_delta)

    def check_success(self, env, info: Optional[Dict[str, Any]] = None) -> bool:
        base_info = info or env._build_base_info()
        lifted = float(base_info.get("object_height", 0.0)) >= self._target_height()
        grasp_ready = bool(base_info.get("grasp_contact", False))

        if env.current_step != self._last_processed_step:
            self._hold_counter = self._hold_counter + 1 if (lifted and grasp_ready) else 0
            self._last_processed_step = env.current_step

        return self._hold_counter >= self.required_hold_steps

    def check_failure(self, env, info: Optional[Dict[str, Any]] = None) -> bool:
        base_info = info or env._build_base_info()
        return bool(base_info.get("object_on_floor", False)) and env.current_step > 0

    def get_reward(self, env, action: np.ndarray, info: Optional[Dict[str, Any]] = None) -> float:
        base_info = info or env._build_base_info()
        reward = float(env.compute_default_reward(action, info=base_info))
        reward += max(0.0, float(base_info.get("object_height", 0.0)) - self._target_height()) * 5.0
        reward += 0.2 * self._hold_counter
        return reward

    def get_info(self, env, info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        base_info = info or env._build_base_info()
        return {
            "lift_initial_height": float(self.initial_object_height or 0.0),
            "lift_target_height": self._target_height(),
            "lift_current_height": float(base_info.get("object_height", 0.0)),
            "lift_hold_steps": int(self._hold_counter),
            "task_status": "placeholder_logic_not_fully_finalized",
            "todo": "Replace with task-specific lift-and-hold success and failure checks.",
        }
