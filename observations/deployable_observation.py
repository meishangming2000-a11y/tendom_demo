"""Deployable observation builder for future real-system alignment."""

from __future__ import annotations

import numpy as np


class DeployableObservationBuilder:
    """Expose a deployable-friendly observation interface with placeholders."""

    mode_name = "deployable"

    def get_name(self) -> str:
        return self.mode_name

    def get_dict(self, env):
        qpos_norm = np.clip(env.data.qpos.copy(), -1.0, 1.0).astype(np.float32)
        qvel_norm = np.clip(env.data.qvel.copy(), -1.0, 1.0).astype(np.float32)

        # Stage-1 placeholders:
        # - palm position estimate is mirrored from simulator state
        # - object pose estimate is mirrored from simulator state
        # - motor and tendon signals are zero placeholders until hardware sensing is confirmed
        palm_position_estimate = env._get_hand_position().astype(np.float32)
        object_pose_estimate = env._get_object_position().astype(np.float32)
        relative_pose_estimate = (palm_position_estimate - object_pose_estimate).astype(np.float32)
        motor_position_placeholder = np.zeros(env.nu, dtype=np.float32)
        motor_current_placeholder = np.zeros(env.nu, dtype=np.float32)
        tendon_signal_placeholder = np.zeros(env.nu, dtype=np.float32)

        return {
            "mode": self.mode_name,
            "joint_positions": qpos_norm,
            "joint_velocities": qvel_norm,
            "palm_position_estimate": palm_position_estimate,
            "object_pose_estimate": object_pose_estimate,
            "relative_pose_estimate": relative_pose_estimate,
            "motor_position_placeholder": motor_position_placeholder,
            "motor_current_placeholder": motor_current_placeholder,
            "tendon_signal_placeholder": tendon_signal_placeholder,
            "notes": (
                "Deployable observation keeps a stable interface while using simulator-derived "
                "placeholders for object and motor sensing."
            ),
        }

    def get_vector(self, env) -> np.ndarray:
        # Keep the vector layout aligned with the current policy pipeline for backward compatibility.
        obs = self.get_dict(env)
        return np.concatenate(
            [
                obs["joint_positions"],
                obs["joint_velocities"],
                obs["palm_position_estimate"],
                obs["object_pose_estimate"],
                obs["relative_pose_estimate"],
            ]
        ).astype(np.float32)
