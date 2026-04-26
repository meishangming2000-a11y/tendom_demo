"""Stage-1 pre-grasp task skeleton."""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np

from .base_task import BaseTask
from .transitions import (
    PreGraspToStableGraspTransitionSpec,
    TransitionEvaluationInput,
    build_pre_grasp_to_stable_grasp_input,
    evaluate_pre_grasp_to_stable_grasp,
)


class PreGraspTask(BaseTask):
    """Reach a task-specific pre-grasp pose without requiring object contact."""

    task_name = "pre_grasp"

    def __init__(
        self,
        target_offset=(0.008, 0.0165, 0.0),
        position_tolerance=0.03,
        orientation_tolerance_rad=0.35,
        hold_steps=10,
        failure_distance=0.25,
        contact_as_failure=False,
        transition_to_stable_grasp: Optional[Dict[str, Any]] = None,
        observation_mode: Optional[str] = None,
    ):
        super().__init__(observation_mode=observation_mode)
        self.target_offset = np.asarray(target_offset, dtype=np.float32)
        self.position_tolerance = float(position_tolerance)
        self.orientation_tolerance_rad = float(orientation_tolerance_rad)
        self.hold_steps = int(hold_steps)
        self.failure_distance = float(failure_distance)
        self.contact_as_failure = bool(contact_as_failure)
        self.transition_to_stable_grasp_spec = PreGraspToStableGraspTransitionSpec(
            **dict(transition_to_stable_grasp or {})
        )
        self._target_palm_quat = None
        self._hold_counter = 0
        self._last_processed_step = -1

    def reset_task(self, env) -> None:
        # Keep the reset palm orientation as the target until a dedicated
        # object-relative orientation target is available for this embodiment.
        self._target_palm_quat = env._get_hand_orientation().copy()
        self._hold_counter = 0
        self._last_processed_step = -1

    def get_action_spec(self, env) -> Dict[str, Any]:
        return {
            "control_level": "joint",
            "shape": (env.nu,),
            "normalized": True,
            "range": [-1.0, 1.0],
            "notes": "Stage-1 simplification before tendon or motor abstractions.",
        }

    def get_task_config(self) -> Dict[str, Any]:
        return {
            "target_offset": self.target_offset.astype(np.float32).tolist(),
            "position_tolerance": float(self.position_tolerance),
            "orientation_tolerance_rad": float(self.orientation_tolerance_rad),
            "hold_steps": int(self.hold_steps),
            "failure_distance": float(self.failure_distance),
            "contact_as_failure": bool(self.contact_as_failure),
            "transition_to_stable_grasp": self.transition_to_stable_grasp_spec.to_dict(),
        }

    def get_task_spec(self) -> Dict[str, Any]:
        spec = self.get_task_config()
        spec["transition_to_stable_grasp_contract"] = (
            self.transition_to_stable_grasp_spec.get_contract()
        )
        return spec

    def get_target_palm_pose(self, env, info: Optional[Dict[str, Any]] = None) -> Dict[str, np.ndarray]:
        object_pos = env._get_object_position()
        object_quat = env._get_object_orientation()
        target_palm_pos = object_pos + self.target_offset
        target_palm_quat = (
            self._target_palm_quat.copy()
            if self._target_palm_quat is not None
            else env._get_hand_orientation().copy()
        )
        return {
            "object_position": object_pos.astype(np.float32),
            "object_quaternion": object_quat.astype(np.float32),
            "target_palm_position": target_palm_pos.astype(np.float32),
            "target_palm_quaternion": target_palm_quat.astype(np.float32),
        }

    def _compute_metrics(self, env, info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        palm_pos = env._get_palm_reference_position()
        palm_quat = env._get_hand_orientation()
        target_pose = self.get_target_palm_pose(env, info=info)
        object_pos = target_pose["object_position"]
        object_quat = target_pose["object_quaternion"]
        target_palm_pos = target_pose["target_palm_position"]
        target_palm_quat = target_pose["target_palm_quaternion"]

        relative_palm_position = palm_pos - object_pos
        position_error_vector = relative_palm_position - self.target_offset
        position_error = float(np.linalg.norm(position_error_vector))
        orientation_error = self.quaternion_angle_error(palm_quat, target_palm_quat)

        contact = bool(info.get("contact", False)) if info is not None else bool(env._check_contact())
        return {
            "object_position": object_pos.astype(np.float32),
            "object_quaternion": object_quat.astype(np.float32),
            "current_palm_position": palm_pos.astype(np.float32),
            "current_palm_quaternion": palm_quat.astype(np.float32),
            "target_palm_position": target_palm_pos.astype(np.float32),
            "target_palm_quaternion": target_palm_quat.astype(np.float32),
            "relative_palm_position": relative_palm_position.astype(np.float32),
            "position_error_vector": position_error_vector.astype(np.float32),
            "position_error": position_error,
            "orientation_error_rad": orientation_error,
            "contact": contact,
        }

    def get_transition_to_stable_grasp_input(
        self,
        env,
        metrics: Optional[Dict[str, Any]] = None,
        info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return the machine-readable pre_grasp output consumed by the transition contract."""
        resolved_metrics = metrics if metrics is not None else self._compute_metrics(env, info=info)
        return build_pre_grasp_to_stable_grasp_input(self, resolved_metrics)

    def check_success(self, env, info: Optional[Dict[str, Any]] = None) -> bool:
        metrics = self._compute_metrics(env, info=info)
        is_aligned = (
            metrics["position_error"] <= self.position_tolerance
            and metrics["orientation_error_rad"] <= self.orientation_tolerance_rad
        )

        if env.current_step != self._last_processed_step:
            self._hold_counter = self._hold_counter + 1 if is_aligned else 0
            self._last_processed_step = env.current_step

        return self._hold_counter >= self.hold_steps

    def check_failure(self, env, info: Optional[Dict[str, Any]] = None) -> bool:
        metrics = self._compute_metrics(env, info=info)
        if metrics["position_error"] >= self.failure_distance:
            return True
        if self.contact_as_failure and metrics["contact"]:
            return True
        return False

    def get_reward(self, env, action: np.ndarray, info: Optional[Dict[str, Any]] = None) -> float:
        metrics = self._compute_metrics(env, info=info)
        reward = -metrics["position_error"] - 0.1 * metrics["orientation_error_rad"]
        reward -= 0.001 * float(np.sum(np.asarray(action, dtype=np.float32) ** 2))
        if metrics["position_error"] <= self.position_tolerance:
            reward += 1.0
        if metrics["orientation_error_rad"] <= self.orientation_tolerance_rad:
            reward += 0.5
        reward += 0.1 * self._hold_counter
        if self.contact_as_failure and metrics["contact"]:
            reward -= 1.0
        return float(reward)

    def get_info(self, env, info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        metrics = self._compute_metrics(env, info=info)
        is_aligned = (
            metrics["position_error"] <= self.position_tolerance
            and metrics["orientation_error_rad"] <= self.orientation_tolerance_rad
        )
        transition_input = self.get_transition_to_stable_grasp_input(env, metrics=metrics, info=info)
        transition = evaluate_pre_grasp_to_stable_grasp(
            TransitionEvaluationInput(
                transition_name="pre_grasp_to_stable_grasp",
                source_task=self.get_name(),
                target_task="stable_grasp",
                source_info=transition_input,
                transition_spec=self.transition_to_stable_grasp_spec.to_dict(),
                source_task_config=self.get_task_config(),
                current_step=int(env.current_step),
            )
        )
        return {
            "task_reference_frame": "palm_object_relation",
            "task_control_level": "joint",
            "object_position": metrics["object_position"].tolist(),
            "object_quaternion": metrics["object_quaternion"].tolist(),
            "current_palm_position": metrics["current_palm_position"].tolist(),
            "current_palm_quaternion": metrics["current_palm_quaternion"].tolist(),
            "target_palm_position": metrics["target_palm_position"].tolist(),
            "target_palm_quaternion": metrics["target_palm_quaternion"].tolist(),
            "target_offset": self.target_offset.tolist(),
            "position_error": metrics["position_error"],
            "position_error_vector": metrics["position_error_vector"].tolist(),
            "orientation_error_rad": metrics["orientation_error_rad"],
            "pre_grasp_hold_steps": int(self._hold_counter),
            "pre_grasp_required_hold_steps": int(self.hold_steps),
            "pre_grasp_is_aligned": bool(is_aligned),
            "pre_grasp_contact_required": False,
            "pre_grasp_contact_as_failure": self.contact_as_failure,
            "pre_grasp_task_config": self.get_task_config(),
            "pre_grasp_task_spec": self.get_task_spec(),
            "pre_to_stable_transition_contract": self.transition_to_stable_grasp_spec.get_contract(),
            "pre_to_stable_transition_input": transition_input,
            "pre_to_stable_transition": transition.to_payload(),
            "task_status": "target_palm_pose_equals_object_pose_plus_offset",
            **transition.to_dict(prefix="pre_to_stable_transition"),
        }
