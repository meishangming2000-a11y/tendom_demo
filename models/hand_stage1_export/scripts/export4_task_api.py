#!/usr/bin/env python3
"""Minimal task API scaffold for the export4 tuned MuJoCo hand.

This is intentionally not a Gym wrapper yet. It is a small, explicit interface
for scripted smoke tests, replay checks, retargeting scaffolds, and future
training-environment design.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np

from export4_wrist2_common import (
    DEFAULT_BALL_POSITION,
    DOCS_DIR,
    SCENE_TUNED,
    TIP_SITES,
    actuator_names as _actuator_names,
    contact_rows,
    contact_summary,
    json_ready,
    joint_names as _joint_names,
    load_model as _load_model,
    render_free_camera,
    set_ball_position,
    site_pos,
    write_text,
)


DEFAULT_REPORT = DOCS_DIR / "export4_task_api_report.md"


class Export4TaskAPI:
    """Small stateful wrapper around an export4 MuJoCo model/data pair."""

    def __init__(self, scene_path: str | Path = SCENE_TUNED):
        self.scene_path = Path(scene_path).resolve()
        self.mujoco, self.model, self.data = _load_model(self.scene_path)
        self.ball_position = np.asarray(DEFAULT_BALL_POSITION, dtype=np.float64)
        self._joint_names = _joint_names(self.model)
        self._actuator_names = _actuator_names(self.model)
        self.reset_hand_open()

    def reset_hand_open(self) -> Dict[str, Any]:
        self.data.qpos[:] = self.model.qpos0
        self.data.qvel[:] = 0.0
        self.data.ctrl[:] = 0.0
        set_ball_position(self.model, self.data, self.mujoco, self.ball_position)
        self.mujoco.mj_forward(self.model, self.data)
        return self.get_observation()

    def set_ball_pose(self, x: float, y: float, z: float) -> None:
        self.ball_position = np.asarray([x, y, z], dtype=np.float64)
        set_ball_position(self.model, self.data, self.mujoco, self.ball_position)
        self.mujoco.mj_forward(self.model, self.data)

    def get_joint_names(self) -> List[str]:
        return list(self._joint_names)

    def get_actuator_names(self) -> List[str]:
        return list(self._actuator_names)

    def get_action_dim(self) -> int:
        return int(self.model.nu)

    def apply_action(self, action: Iterable[float]) -> np.ndarray:
        action_arr = np.asarray(list(action), dtype=np.float64)
        if action_arr.shape != (self.model.nu,):
            raise ValueError(f"Expected action shape {(self.model.nu,)}, got {action_arr.shape}")
        for idx in range(self.model.nu):
            low, high = self.model.actuator_ctrlrange[idx]
            action_arr[idx] = np.clip(action_arr[idx], low, high)
        self.data.ctrl[:] = action_arr
        return self.data.ctrl.copy()

    def get_fingertip_positions(self) -> Dict[str, np.ndarray]:
        return {
            finger: site_pos(self.model, self.data, self.mujoco, site_name)
            for finger, site_name in TIP_SITES.items()
        }

    def get_ball_pose(self) -> Dict[str, np.ndarray]:
        jid = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_JOINT, "ball_freejoint")
        if jid < 0:
            return {
                "position": self.ball_position.copy(),
                "quat": np.asarray([1.0, 0.0, 0.0, 0.0]),
                "velocity": np.zeros(6),
            }
        qadr = int(self.model.jnt_qposadr[jid])
        dadr = int(self.model.jnt_dofadr[jid])
        return {
            "position": self.data.qpos[qadr : qadr + 3].copy(),
            "quat": self.data.qpos[qadr + 3 : qadr + 7].copy(),
            "velocity": self.data.qvel[dadr : dadr + 6].copy(),
        }

    def get_contact_summary(self) -> Dict[str, Any]:
        summary = contact_summary(self.model, self.data, self.mujoco)
        summary["top_contacts"] = contact_rows(self.model, self.data, self.mujoco, top_n=10)
        return summary

    def compute_fingertip_ball_distances(self) -> Dict[str, float]:
        ball = self.get_ball_pose()["position"]
        return {
            finger: float(np.linalg.norm(pos - ball))
            for finger, pos in self.get_fingertip_positions().items()
        }

    def get_observation(self) -> Dict[str, Any]:
        fingertips = self.get_fingertip_positions()
        ball = self.get_ball_pose()
        contact = self.get_contact_summary()
        distances = self.compute_fingertip_ball_distances()
        vector = np.concatenate(
            [
                self.data.qpos.copy(),
                self.data.qvel.copy(),
                self.data.ctrl.copy(),
                np.concatenate([fingertips[name] for name in ("index", "middle", "ring", "little", "thumb")]),
                ball["position"],
                ball["velocity"],
                np.asarray(
                    [
                        contact["contact_count"],
                        contact["max_penetration"],
                        contact["ball_hand_contact_count"],
                        contact["ball_hand_max_penetration"],
                        distances["index"],
                        distances["middle"],
                        distances["ring"],
                        distances["little"],
                        distances["thumb"],
                    ],
                    dtype=np.float64,
                ),
            ]
        )
        return {
            "qpos": self.data.qpos.copy(),
            "qvel": self.data.qvel.copy(),
            "ctrl": self.data.ctrl.copy(),
            "fingertip_positions": fingertips,
            "ball_position": ball["position"],
            "ball_quat": ball["quat"],
            "ball_velocity": ball["velocity"],
            "contact_count": contact["contact_count"],
            "max_penetration": contact["max_penetration"],
            "contact_summary": contact,
            "fingertip_ball_distances": distances,
            "vector": vector,
        }

    def step(self, n: int = 1, *, pin_ball: bool = False) -> Dict[str, Any]:
        for _ in range(max(1, int(n))):
            if pin_ball:
                set_ball_position(self.model, self.data, self.mujoco, self.ball_position)
            self.mujoco.mj_step(self.model, self.data)
            if pin_ball:
                set_ball_position(self.model, self.data, self.mujoco, self.ball_position)
                self.mujoco.mj_forward(self.model, self.data)
        return self.get_observation()

    def render_or_save_frame_if_available(self, output_path: str | Path | None = None, **camera_kwargs) -> Dict[str, Any] | None:
        if output_path is None:
            return None
        return render_free_camera(
            self.model,
            self.data,
            self.mujoco,
            Path(output_path).resolve(),
            **camera_kwargs,
        )


def load_model(scene_path: str | Path = SCENE_TUNED) -> Export4TaskAPI:
    return Export4TaskAPI(scene_path)


def _write_report(api: Export4TaskAPI, report_path: Path) -> None:
    obs = api.get_observation()
    payload = {
        "scene": str(api.scene_path),
        "nbody": int(api.model.nbody),
        "njnt": int(api.model.njnt),
        "nu": int(api.model.nu),
        "ngeom": int(api.model.ngeom),
        "nsite": int(api.model.nsite),
        "joint_names": api.get_joint_names(),
        "actuator_names": api.get_actuator_names(),
        "action_dim": api.get_action_dim(),
        "observation_vector_dim": int(len(obs["vector"])),
        "observation_fields": [
            "qpos",
            "qvel",
            "ctrl",
            "five fingertip site positions",
            "ball position",
            "ball velocity",
            "contact count",
            "max penetration",
            "fingertip-ball distances",
        ],
    }
    lines = [
        "# Export4 Task API Report\n\n",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}\n\n",
        "## Scope\n\n",
        "Minimal task API scaffold for the export4 tuned experimental scene. "
        "This is not a Gym wrapper, and no training is performed.\n\n",
        "## Model\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Bodies: `{payload['nbody']}`\n",
        f"- Joints: `{payload['njnt']}`\n",
        f"- Actuators/action dim: `{payload['nu']}`\n",
        f"- Geoms: `{payload['ngeom']}`\n",
        f"- Sites: `{payload['nsite']}`\n",
        f"- Observation vector dim: `{payload['observation_vector_dim']}`\n\n",
        "## Interface\n\n",
        "- `load_model(scene_path)`\n",
        "- `reset_hand_open()`\n",
        "- `set_ball_pose(x, y, z)`\n",
        "- `get_joint_names()`\n",
        "- `get_actuator_names()`\n",
        "- `get_action_dim()`\n",
        "- `apply_action(action)`\n",
        "- `get_observation()`\n",
        "- `get_fingertip_positions()`\n",
        "- `get_ball_pose()`\n",
        "- `get_contact_summary()`\n",
        "- `compute_fingertip_ball_distances()`\n",
        "- `step(n=1)`\n",
        "- `render_or_save_frame_if_available()`\n\n",
        "## Notes\n\n",
        "- `*_mcp_flex_joint` names are preserved but semantically treated as lateral spread / abduction-adduction for now.\n",
        "- The API is suitable for scripted smoke tests and adapter work, not training readiness.\n",
        "- TODO: finalize canonical palmar ball side before expanding dataset collection.\n",
    ]
    write_text(report_path, "".join(lines), "before_export4_task_api_report")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load export4 task API and write a small report.")
    parser.add_argument("--scene", default=str(SCENE_TUNED))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()
    api = load_model(args.scene)
    _write_report(api, Path(args.report).resolve())
    print(f"Loaded scene: {api.scene_path}")
    print(f"Action dim: {api.get_action_dim()}")
    print(f"Observation dim: {len(api.get_observation()['vector'])}")
    print(f"Saved report: {Path(args.report).resolve()}")


if __name__ == "__main__":
    main()
