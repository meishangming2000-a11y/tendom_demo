"""Oracle observation builder for simulation-first development."""

from __future__ import annotations

import numpy as np


class OracleObservationBuilder:
    """Expose rich simulator-side state for development and debugging."""

    mode_name = "oracle"

    def get_name(self) -> str:
        return self.mode_name

    def get_dict(self, env):
        qpos_norm = np.clip(env.data.qpos.copy(), -1.0, 1.0).astype(np.float32)
        qvel_norm = np.clip(env.data.qvel.copy(), -1.0, 1.0).astype(np.float32)
        palm_pos = env._get_hand_position().astype(np.float32)
        palm_quat = env._get_hand_orientation().astype(np.float32)
        object_pos = env._get_object_position().astype(np.float32)
        object_quat = env._get_object_orientation().astype(np.float32)
        object_vel = env._get_object_velocity().astype(np.float32)
        rel_pos = (palm_pos - object_pos).astype(np.float32)
        contact_state = env._get_contact_state()

        return {
            "mode": self.mode_name,
            "joint_positions": qpos_norm,
            "joint_velocities": qvel_norm,
            "palm_position": palm_pos,
            "palm_orientation": palm_quat,
            "object_position": object_pos,
            "object_orientation": object_quat,
            "object_velocity": object_vel,
            "relative_position": rel_pos,
            "contact_state": contact_state,
            "notes": "Oracle observation exposes exact simulator state for development and evaluation.",
        }

    def get_vector(self, env) -> np.ndarray:
        # Keep the legacy 70D layout for backward compatibility with existing datasets and BC models.
        obs = self.get_dict(env)
        return np.concatenate(
            [
                obs["joint_positions"],
                obs["joint_velocities"],
                obs["palm_position"],
                obs["object_position"],
                obs["relative_position"],
            ]
        ).astype(np.float32)
