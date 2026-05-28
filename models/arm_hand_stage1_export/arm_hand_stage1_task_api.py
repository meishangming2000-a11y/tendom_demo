#!/usr/bin/env python3
"""Minimal task API for the arm + export4 hand Stage1 v2 baseline.

This is deliberately not a Gym wrapper yet. It gives the next scripts a stable
adapter surface for smoke rollouts, replay, and future retargeting scaffolds.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CURRENT_BASELINE_VERSION = "collision_proxy_v2"
CURRENT_MODEL = ROOT / "mjcf" / "arm_hand_export4_collision_proxy_v2.xml"
CURRENT_SCENE_WITHOUT_BALL = ROOT / "mjcf" / "scene_arm_hand_export4_collision_proxy_v2.xml"
CURRENT_SCENE_WITH_BALL = ROOT / "mjcf" / "scene_arm_hand_export4_collision_proxy_v2_ball.xml"
CURRENT_LIFT_SCENE = ROOT / "mjcf" / "scene_arm_hand_export4_lift_ball_demo.xml"
DEFAULT_SCENE = CURRENT_SCENE_WITH_BALL
DEFAULT_REPORT = DOCS / "arm_hand_stage1_v2_task_api_report.md"
DEFAULT_META = META / "arm_hand_stage1_v2_task_api.json"
TASK_CONTRACT_VERSION = "stage2_lift_ball_v0_1"
TASK_NAME = "arm_hand_stage1_lift_ball"
DEFAULT_MAX_EPISODE_STEPS = 1230

SCENE_REGISTRY = {
    "model": CURRENT_MODEL,
    "v2": CURRENT_SCENE_WITHOUT_BALL,
    "v2_ball": CURRENT_SCENE_WITH_BALL,
    "lift_demo": CURRENT_LIFT_SCENE,
}

TIP_SITES = {
    "index": "index_tip_site",
    "middle": "middle_tip_site",
    "ring": "ring_tip_site",
    "little": "little_tip_site",
    "thumb": "thumb_tip_site",
}
FINGER_ORDER = ("index", "middle", "ring", "little", "thumb")
OBSERVATION_SCALAR_NAMES = (
    "contact_count",
    "max_penetration",
    "ball_hand_contact_count",
    "ball_arm_contact_count",
    "index_tip_ball_distance",
    "middle_tip_ball_distance",
    "ring_tip_ball_distance",
    "little_tip_ball_distance",
    "thumb_tip_ball_distance",
)
DEFAULT_TASK_THRESHOLDS = {
    "success_lift_height_m": 0.08,
    "success_min_ball_hand_contacts": 1,
    "success_max_ball_floor_contacts": 0,
    "success_max_penetration_m": 0.015,
    "failure_max_penetration_m": 0.03,
    "failure_ball_drop_below_start_m": 0.03,
    "dropped_after_lift_height_m": 0.03,
}
DEFAULT_REWARD_WEIGHTS = {
    "lift_height": 10.0,
    "hand_contact_bonus": 1.0,
    "floor_contact_after_lift_penalty": -2.0,
    "penetration_penalty": -50.0,
    "four_finger_distance_penalty": -0.5,
    "thumb_distance_penalty": -0.25,
    "success_bonus": 10.0,
    "failure_penalty": -10.0,
}


def json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    return value


def name_or(model, mujoco, objtype, idx: int, fallback: str) -> str:
    return mujoco.mj_id2name(model, objtype, idx) or fallback


def actuator_to_joint_name(actuator_name: str) -> str:
    if actuator_name.startswith("a_"):
        return actuator_name[2:]
    if actuator_name.endswith("_pos"):
        return actuator_name[:-4]
    return actuator_name


def compute_lift_task_reward(
    metrics: dict[str, Any],
    thresholds: dict[str, float] | None = None,
    weights: dict[str, float] | None = None,
    *,
    success: bool = False,
    failure: bool = False,
) -> dict[str, Any]:
    thresholds = {**DEFAULT_TASK_THRESHOLDS, **(thresholds or {})}
    weights = {**DEFAULT_REWARD_WEIGHTS, **(weights or {})}
    contact = metrics["contact"]
    lift_height = float(metrics["ball_lift_height"])
    max_pen = float(contact["max_penetration"])
    lifted_enough_for_floor_penalty = lift_height >= thresholds["dropped_after_lift_height_m"]
    terms = {
        "lift_height": weights["lift_height"] * max(0.0, lift_height),
        "hand_contact_bonus": weights["hand_contact_bonus"] if contact["ball_hand_contact_count"] >= 1 else 0.0,
        "floor_contact_after_lift_penalty": weights["floor_contact_after_lift_penalty"]
        if lifted_enough_for_floor_penalty and contact.get("ball_floor_contact_count", 0) > 0
        else 0.0,
        "penetration_penalty": weights["penetration_penalty"] * max(0.0, max_pen - 0.005),
        "four_finger_distance_penalty": weights["four_finger_distance_penalty"] * float(metrics["four_finger_avg_tip_ball_distance"]),
        "thumb_distance_penalty": weights["thumb_distance_penalty"] * float(metrics["thumb_ball_distance"]),
        "success_bonus": weights["success_bonus"] if success else 0.0,
        "failure_penalty": weights["failure_penalty"] if failure else 0.0,
    }
    return {
        "total": float(sum(terms.values())),
        "terms": {key: float(value) for key, value in terms.items()},
        "note": "Candidate Stage2 shaping reward for contract validation; not tuned for training.",
    }


class ArmHandStage1TaskAPI:
    def __init__(self, scene_path: str | Path = DEFAULT_SCENE):
        import mujoco

        self.mujoco = mujoco
        self.scene_path = Path(scene_path).resolve()
        self.model = mujoco.MjModel.from_xml_path(str(self.scene_path))
        self.data = mujoco.MjData(self.model)
        self.mujoco.mj_forward(self.model, self.data)
        self._joint_names = [
            name_or(self.model, self.mujoco, self.mujoco.mjtObj.mjOBJ_JOINT, i, f"joint_{i}")
            for i in range(self.model.njnt)
        ]
        self._actuator_names = [
            name_or(self.model, self.mujoco, self.mujoco.mjtObj.mjOBJ_ACTUATOR, i, f"actuator_{i}")
            for i in range(self.model.nu)
        ]
        self.ball_body_id = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_BODY, "ball")
        self.ball_joint_id = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_JOINT, "ball_freejoint")
        self.ball_qadr = int(self.model.jnt_qposadr[self.ball_joint_id]) if self.ball_joint_id >= 0 else None
        self.ball_dadr = int(self.model.jnt_dofadr[self.ball_joint_id]) if self.ball_joint_id >= 0 else None
        self.ball_position = self._current_ball_position()
        self.reset_hand_open()

    def has_ball(self) -> bool:
        return self.ball_body_id >= 0 and self.ball_qadr is not None

    def _current_ball_position(self) -> np.ndarray:
        if self.ball_body_id >= 0:
            return self.data.xpos[self.ball_body_id].copy()
        return np.zeros(3, dtype=np.float64)

    def get_scene_role(self) -> str:
        for role, path in SCENE_REGISTRY.items():
            if self.scene_path == path.resolve():
                return role
        return "custom"

    def get_scene_info(self) -> dict[str, Any]:
        return {
            "scene": self.scene_path,
            "scene_role": self.get_scene_role(),
            "baseline_version": CURRENT_BASELINE_VERSION,
            "has_ball": self.has_ball(),
            "registry": SCENE_REGISTRY,
        }

    def set_ball_pose_world(self, position: Iterable[float], quat: Iterable[float] | None = None) -> None:
        self.ball_position = np.asarray(list(position), dtype=np.float64)
        if self.ball_position.shape != (3,):
            raise ValueError(f"Expected ball position shape {(3,)}, got {self.ball_position.shape}")
        if self.ball_qadr is not None:
            self.data.qpos[self.ball_qadr : self.ball_qadr + 3] = self.ball_position
            self.data.qpos[self.ball_qadr + 3 : self.ball_qadr + 7] = (
                np.asarray(list(quat), dtype=np.float64) if quat is not None else [1.0, 0.0, 0.0, 0.0]
            )
            if self.ball_dadr is not None:
                self.data.qvel[self.ball_dadr : self.ball_dadr + 6] = 0.0
        self.mujoco.mj_forward(self.model, self.data)

    def set_ball_pose(self, x: float, y: float, z: float) -> None:
        self.set_ball_pose_world([x, y, z])

    def get_body_position(self, body_name: str) -> np.ndarray:
        bid = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_BODY, body_name)
        if bid < 0:
            raise KeyError(body_name)
        return self.data.xpos[bid].copy()

    def get_body_frame(self, body_name: str) -> tuple[np.ndarray, np.ndarray]:
        bid = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_BODY, body_name)
        if bid < 0:
            raise KeyError(body_name)
        return self.data.xpos[bid].copy(), self.data.xmat[bid].reshape(3, 3).copy()

    def world_from_body_local(self, body_name: str, local_xyz: Iterable[float]) -> np.ndarray:
        pos, mat = self.get_body_frame(body_name)
        return pos + mat @ np.asarray(list(local_xyz), dtype=np.float64)

    def set_ball_pose_body_local(self, body_name: str, local_xyz: Iterable[float]) -> np.ndarray:
        world = self.world_from_body_local(body_name, local_xyz)
        self.set_ball_pose_world(world)
        return world

    def reset_hand_open(self, ball_position: Iterable[float] | None = None) -> dict[str, Any]:
        self.data.qpos[:] = self.model.qpos0
        self.data.qvel[:] = 0.0
        self.data.ctrl[:] = 0.0
        if ball_position is not None:
            self.set_ball_pose_world(ball_position)
        else:
            self.set_ball_pose_world(self.ball_position)
        self.mujoco.mj_forward(self.model, self.data)
        return self.get_observation()

    def get_joint_names(self) -> list[str]:
        return list(self._joint_names)

    def get_actuator_names(self) -> list[str]:
        return list(self._actuator_names)

    def get_actuator_joint_names(self) -> list[str]:
        return [actuator_to_joint_name(name) for name in self._actuator_names]

    def get_action_dim(self) -> int:
        return int(self.model.nu)

    def get_action_schema(self) -> dict[str, Any]:
        rows = []
        for aid, actuator_name in enumerate(self._actuator_names):
            ctrlrange = self.model.actuator_ctrlrange[aid].copy() if bool(self.model.actuator_ctrllimited[aid]) else np.array([np.nan, np.nan])
            rows.append(
                {
                    "index": int(aid),
                    "actuator": actuator_name,
                    "joint": actuator_to_joint_name(actuator_name),
                    "ctrl_limited": bool(self.model.actuator_ctrllimited[aid]),
                    "ctrlrange": ctrlrange,
                }
            )
        return {"type": "position_target_vector", "dim": self.get_action_dim(), "entries": rows}

    def get_observation_schema(self) -> dict[str, Any]:
        nq = int(self.model.nq)
        nv = int(self.model.nv)
        nu = int(self.model.nu)
        start = 0
        slices = {}
        for name, length in [
            ("qpos", nq),
            ("qvel", nv),
            ("ctrl", nu),
            ("fingertip_positions_xyz", 3 * len(FINGER_ORDER)),
            ("ball_position_xyz", 3),
            ("ball_velocity_6d", 6),
            ("contact_and_distance_scalars", len(OBSERVATION_SCALAR_NAMES)),
        ]:
            slices[name] = {"start": start, "stop": start + length, "length": length}
            start += length
        return {
            "type": "flat_vector",
            "dim": start,
            "finger_order": FINGER_ORDER,
            "scalar_names": OBSERVATION_SCALAR_NAMES,
            "slices": slices,
        }

    def get_task_contract(self) -> dict[str, Any]:
        return {
            "task_name": TASK_NAME,
            "contract_version": TASK_CONTRACT_VERSION,
            "stage": "stage2_task_system_dataset_v0",
            "baseline_version": CURRENT_BASELINE_VERSION,
            "training_ready": False,
            "scene_roles": {
                "default_api_scene": "v2_ball",
                "recommended_rollout_scene": "lift_demo",
                "scene_registry": SCENE_REGISTRY,
            },
            "observation": self.get_observation_schema(),
            "action": self.get_action_schema(),
            "official_metrics": [
                "ball_lift_height",
                "ball_displacement",
                "ball_velocity_norm",
                "ball_hand_contact_count",
                "ball_floor_contact_count",
                "ball_arm_contact_count",
                "max_penetration",
                "four_finger_avg_tip_ball_distance",
                "thumb_ball_distance",
                "finite_state",
            ],
            "reward": {
                "type": "candidate_shaping_reward_v0",
                "weights": DEFAULT_REWARD_WEIGHTS,
                "formula": [
                    "+ lift_height_weight * max(0, ball_lift_height)",
                    "+ hand_contact_bonus if ball_hand_contact_count >= 1",
                    "+ floor_contact_after_lift_penalty if lifted enough and ball still touches floor",
                    "+ penetration_penalty_weight * max(0, max_penetration - 0.005)",
                    "+ distance penalties for four-finger average and thumb-ball distance",
                    "+ success_bonus or failure_penalty at terminal states",
                ],
                "note": "This reward is for dataset-v0 labeling and later training discussion; it is not a tuned RL reward.",
            },
            "termination": {
                "max_episode_steps": DEFAULT_MAX_EPISODE_STEPS,
                "thresholds": DEFAULT_TASK_THRESHOLDS,
                "success_when_all_true": [
                    "ball_lift_height >= success_lift_height_m",
                    "ball_hand_contact_count >= success_min_ball_hand_contacts",
                    "ball_floor_contact_count <= success_max_ball_floor_contacts",
                    "max_penetration <= success_max_penetration_m",
                    "finite_state is true",
                ],
                "failure_when_any_true": [
                    "finite_state is false",
                    "max_penetration > failure_max_penetration_m",
                    "ball_lift_height < -failure_ball_drop_below_start_m",
                    "lifted_once and ball_floor_contact_count > 0",
                    "step_count >= max_episode_steps without success",
                ],
                "note": "Initial floor/table contact is allowed; floor contact becomes failure only after the ball has been lifted.",
            },
            "episode_result_schema": {
                "task_name": "string",
                "contract_version": "string",
                "episode_status": "success | failure | running",
                "terminal_reason": "success_lift_ball | non_finite_state | excessive_penetration | ball_dropped | floor_contact_after_lift | timeout | running",
                "success": "bool",
                "failure": "bool",
                "done": "bool",
                "step_count": "int",
                "initial_ball_position": "[3] float",
                "official_metrics": "dict",
                "reward": "dict with total and named terms",
                "debug_metrics": "optional dict; keep out of official dataset rows unless requested",
            },
        }

    def get_model_summary(self) -> dict[str, int]:
        return {
            "nbody": int(self.model.nbody),
            "njnt": int(self.model.njnt),
            "nu": int(self.model.nu),
            "ngeom": int(self.model.ngeom),
            "nsite": int(self.model.nsite),
            "nmesh": int(self.model.nmesh),
            "nq": int(self.model.nq),
            "nv": int(self.model.nv),
        }

    def apply_action(self, action: Iterable[float]) -> np.ndarray:
        arr = np.asarray(list(action), dtype=np.float64)
        if arr.shape != (self.model.nu,):
            raise ValueError(f"Expected action shape {(self.model.nu,)}, got {arr.shape}")
        for aid in range(self.model.nu):
            if bool(self.model.actuator_ctrllimited[aid]):
                low, high = self.model.actuator_ctrlrange[aid]
                arr[aid] = np.clip(arr[aid], low, high)
        self.data.ctrl[:] = arr
        return self.data.ctrl.copy()

    def action_from_targets(self, targets: dict[str, float]) -> np.ndarray:
        action = np.zeros(self.model.nu, dtype=np.float64)
        for aid, actuator_name in enumerate(self._actuator_names):
            joint_name = actuator_to_joint_name(actuator_name)
            value = float(targets.get(joint_name, 0.0))
            if bool(self.model.actuator_ctrllimited[aid]):
                low, high = self.model.actuator_ctrlrange[aid]
                value = float(np.clip(value, low, high))
            action[aid] = value
        return action

    def targets_from_current_qpos(self) -> dict[str, float]:
        targets = {}
        for actuator_name in self._actuator_names:
            joint_name = actuator_to_joint_name(actuator_name)
            jid = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_JOINT, joint_name)
            if jid < 0:
                continue
            qadr = int(self.model.jnt_qposadr[jid])
            targets[joint_name] = float(self.data.qpos[qadr])
        return targets

    def step_action(self, action: Iterable[float], n: int = 1, *, pin_ball: bool = False) -> dict[str, Any]:
        self.apply_action(action)
        return self.step(n=n, pin_ball=pin_ball)

    def step(self, n: int = 1, *, pin_ball: bool = True) -> dict[str, Any]:
        for _ in range(max(1, int(n))):
            if pin_ball:
                self.set_ball_pose(*self.ball_position)
            self.mujoco.mj_step(self.model, self.data)
            if pin_ball:
                self.set_ball_pose(*self.ball_position)
        return self.get_observation()

    def get_fingertip_positions(self) -> dict[str, np.ndarray]:
        out = {}
        for finger, site_name in TIP_SITES.items():
            sid = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_SITE, site_name)
            out[finger] = self.data.site_xpos[sid].copy() if sid >= 0 else np.full(3, np.nan)
        return out

    def get_ball_pose(self) -> dict[str, np.ndarray]:
        if self.ball_qadr is None:
            return {"position": self.ball_position.copy(), "quat": np.array([1.0, 0.0, 0.0, 0.0]), "velocity": np.zeros(6)}
        quat = self.data.qpos[self.ball_qadr + 3 : self.ball_qadr + 7].copy()
        vel = self.data.qvel[self.ball_dadr : self.ball_dadr + 6].copy() if self.ball_dadr is not None else np.zeros(6)
        return {"position": self.data.qpos[self.ball_qadr : self.ball_qadr + 3].copy(), "quat": quat, "velocity": vel}

    def get_contact_summary(self, top_n: int = 10) -> dict[str, Any]:
        rows = []
        max_pen = 0.0
        ball_hand = 0
        ball_arm = 0
        ball_floor = 0
        for i in range(self.data.ncon):
            c = self.data.contact[i]
            g1, g2 = int(c.geom1), int(c.geom2)
            b1, b2 = int(self.model.geom_bodyid[g1]), int(self.model.geom_bodyid[g2])
            geom1 = name_or(self.model, self.mujoco, self.mujoco.mjtObj.mjOBJ_GEOM, g1, f"geom_{g1}")
            geom2 = name_or(self.model, self.mujoco, self.mujoco.mjtObj.mjOBJ_GEOM, g2, f"geom_{g2}")
            body1 = name_or(self.model, self.mujoco, self.mujoco.mjtObj.mjOBJ_BODY, b1, f"body_{b1}")
            body2 = name_or(self.model, self.mujoco, self.mujoco.mjtObj.mjOBJ_BODY, b2, f"body_{b2}")
            names = [geom1, geom2, body1, body2]
            pen = max(0.0, -float(c.dist))
            max_pen = max(max_pen, pen)
            if any("ball" in n for n in names):
                hand_hit = any(
                    ("palm" in n or "finger" in n or "thumb" in n or "distal" in n or "proximal" in n or "wrist" in n or "mcp" in n or "hand_base" in n)
                    for n in names
                )
                arm_hit = any(
                    n in {"base_link", "link_1", "link_2", "link_3", "ee_mount"} or n.endswith("_arm_collision_proxy_box")
                    for n in names
                )
                if hand_hit:
                    ball_hand += 1
                if arm_hit:
                    ball_arm += 1
                if any("floor" in n for n in names):
                    ball_floor += 1
            rows.append(
                {
                    "geom1": geom1,
                    "geom2": geom2,
                    "body1": body1,
                    "body2": body2,
                    "dist": float(c.dist),
                    "penetration": pen,
                    "pos": np.asarray(c.pos).copy(),
                }
            )
        rows.sort(key=lambda row: row["penetration"], reverse=True)
        return {
            "contact_count": int(self.data.ncon),
            "max_penetration": float(max_pen),
            "ball_hand_contact_count": int(ball_hand),
            "ball_arm_contact_count": int(ball_arm),
            "ball_floor_contact_count": int(ball_floor),
            "top_contacts": rows[:top_n],
        }

    def compute_fingertip_ball_distances(self) -> dict[str, float]:
        ball = self.get_ball_pose()["position"]
        return {name: float(np.linalg.norm(pos - ball)) for name, pos in self.get_fingertip_positions().items()}

    def compute_task_metrics(self, initial_ball_position: Iterable[float] | None = None) -> dict[str, Any]:
        obs = self.get_observation()
        ball = obs["ball_position"].copy()
        initial = np.asarray(list(initial_ball_position), dtype=np.float64) if initial_ball_position is not None else ball.copy()
        distances = obs["fingertip_ball_distances"]
        four = [distances[name] for name in ["index", "middle", "ring", "little"]]
        contact = {key: value for key, value in obs["contact_summary"].items() if key != "top_contacts"}
        return {
            "ball_position": ball,
            "initial_ball_position": initial,
            "ball_lift_height": float(ball[2] - initial[2]),
            "ball_displacement": float(np.linalg.norm(ball - initial)),
            "ball_velocity_norm": float(np.linalg.norm(obs["ball_velocity"])),
            "contact": contact,
            "four_finger_avg_tip_ball_distance": float(np.mean(four)),
            "thumb_ball_distance": float(distances["thumb"]),
            "finite_state": bool(np.isfinite(self.data.qpos).all() and np.isfinite(self.data.qvel).all()),
        }

    def evaluate_lift_task_state(
        self,
        initial_ball_position: Iterable[float],
        *,
        step_count: int = 0,
        max_episode_steps: int = DEFAULT_MAX_EPISODE_STEPS,
        lifted_once: bool = False,
        thresholds: dict[str, float] | None = None,
        reward_weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        thresholds = {**DEFAULT_TASK_THRESHOLDS, **(thresholds or {})}
        metrics = self.compute_task_metrics(initial_ball_position)
        contact = metrics["contact"]
        lift_height = float(metrics["ball_lift_height"])
        success_reasons = []
        failure_reasons = []
        success = (
            metrics["finite_state"]
            and lift_height >= thresholds["success_lift_height_m"]
            and contact["ball_hand_contact_count"] >= thresholds["success_min_ball_hand_contacts"]
            and contact.get("ball_floor_contact_count", 0) <= thresholds["success_max_ball_floor_contacts"]
            and contact["max_penetration"] <= thresholds["success_max_penetration_m"]
        )
        if success:
            success_reasons.append("success_lift_ball")
        if not metrics["finite_state"]:
            failure_reasons.append("non_finite_state")
        if contact["max_penetration"] > thresholds["failure_max_penetration_m"]:
            failure_reasons.append("excessive_penetration")
        if lift_height < -thresholds["failure_ball_drop_below_start_m"]:
            failure_reasons.append("ball_dropped")
        if lifted_once and contact.get("ball_floor_contact_count", 0) > 0:
            failure_reasons.append("floor_contact_after_lift")
        if step_count >= max_episode_steps and not success:
            failure_reasons.append("timeout")
        failure = bool(failure_reasons and not success)
        if success:
            episode_status = "success"
            terminal_reason = "success_lift_ball"
        elif failure:
            episode_status = "failure"
            terminal_reason = failure_reasons[0]
        else:
            episode_status = "running"
            terminal_reason = "running"
        reward = compute_lift_task_reward(metrics, thresholds, reward_weights, success=success, failure=failure)
        return {
            "task_name": TASK_NAME,
            "contract_version": TASK_CONTRACT_VERSION,
            "episode_status": episode_status,
            "terminal_reason": terminal_reason,
            "success": bool(success),
            "failure": bool(failure),
            "done": bool(success or failure),
            "step_count": int(step_count),
            "success_reasons": success_reasons,
            "failure_reasons": failure_reasons,
            "official_metrics": metrics,
            "reward": reward,
        }

    def get_observation(self) -> dict[str, Any]:
        tips = self.get_fingertip_positions()
        ball = self.get_ball_pose()
        contact = self.get_contact_summary()
        distances = self.compute_fingertip_ball_distances()
        vector = np.concatenate(
            [
                self.data.qpos.copy(),
                self.data.qvel.copy(),
                self.data.ctrl.copy(),
                np.concatenate([tips[name] for name in ["index", "middle", "ring", "little", "thumb"]]),
                ball["position"].copy(),
                ball["velocity"].copy(),
                np.asarray(
                    [
                        contact["contact_count"],
                        contact["max_penetration"],
                        contact["ball_hand_contact_count"],
                        contact["ball_arm_contact_count"],
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
            "fingertip_positions": tips,
            "ball_position": ball["position"],
            "ball_quat": ball["quat"],
            "ball_velocity": ball["velocity"],
            "contact_summary": contact,
            "fingertip_ball_distances": distances,
            "vector": vector,
        }


def load_model(scene_path: str | Path = DEFAULT_SCENE) -> ArmHandStage1TaskAPI:
    return ArmHandStage1TaskAPI(scene_path)


def load_current_baseline(scene_role: str = "v2_ball") -> ArmHandStage1TaskAPI:
    if scene_role not in SCENE_REGISTRY:
        raise KeyError(f"Unknown scene role {scene_role!r}; available={sorted(SCENE_REGISTRY)}")
    return ArmHandStage1TaskAPI(SCENE_REGISTRY[scene_role])


def write_api_report(api: ArmHandStage1TaskAPI, report_path: Path = DEFAULT_REPORT, metadata_path: Path = DEFAULT_META) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    obs = api.get_observation()
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene_info": api.get_scene_info(),
        "model_summary": api.get_model_summary(),
        "joint_names": api.get_joint_names(),
        "actuator_names": api.get_actuator_names(),
        "actuator_joint_names": api.get_actuator_joint_names(),
        "action_dim": api.get_action_dim(),
        "action_schema": api.get_action_schema(),
        "observation_schema": api.get_observation_schema(),
        "task_contract": api.get_task_contract(),
        "observation_dim": int(len(obs["vector"])),
        "ball_position": obs["ball_position"],
        "contact_summary": obs["contact_summary"],
        "tip_sites": TIP_SITES,
        "stage2_status": "api_surface_ready_for_pose_sweep",
        "training_ready": False,
    }
    metadata_path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Arm-Hand Stage1 Task API Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{payload['scene_info']['scene']}`\n",
        f"- Scene role: `{payload['scene_info']['scene_role']}`\n",
        f"- Baseline version: `{payload['scene_info']['baseline_version']}`\n",
        f"- Model summary: `{payload['model_summary']}`\n",
        f"- Action dim: `{payload['action_dim']}`\n",
        f"- Observation dim: `{payload['observation_dim']}`\n",
        f"- Default ball position: `{json_ready(payload['ball_position'])}`\n",
        f"- Open contact count: `{payload['contact_summary']['contact_count']}`\n",
        f"- Open max penetration: `{payload['contact_summary']['max_penetration']:.6f} m`\n\n",
        "## Task Contract\n\n",
        f"- Task name: `{payload['task_contract']['task_name']}`\n",
        f"- Contract version: `{payload['task_contract']['contract_version']}`\n",
        f"- Max episode steps: `{payload['task_contract']['termination']['max_episode_steps']}`\n",
        f"- Training ready: **No**\n\n",
        "## Schema\n\n",
        f"- Action schema: `{json.dumps(json_ready(payload['action_schema']), ensure_ascii=False)}`\n",
        f"- Observation schema: `{json.dumps(json_ready(payload['observation_schema']), ensure_ascii=False)}`\n\n",
        "## Interface\n\n",
        "- `load_model(scene_path)`\n",
        "- `load_current_baseline(scene_role='v2_ball')`\n",
        "- `reset_hand_open()`\n",
        "- `set_ball_pose(x, y, z)`\n",
        "- `set_ball_pose_world(position, quat=None)`\n",
        "- `set_ball_pose_body_local(body_name, local_xyz)`\n",
        "- `world_from_body_local(body_name, local_xyz)`\n",
        "- `get_joint_names()`\n",
        "- `get_actuator_names()`\n",
        "- `get_action_schema()`\n",
        "- `get_observation_schema()`\n",
        "- `get_action_dim()`\n",
        "- `apply_action(action)`\n",
        "- `action_from_targets(targets)`\n",
        "- `targets_from_current_qpos()`\n",
        "- `step_action(action, n=1, pin_ball=False)`\n",
        "- `get_observation()`\n",
        "- `get_fingertip_positions()`\n",
        "- `get_ball_pose()`\n",
        "- `get_contact_summary()`\n",
        "- `compute_fingertip_ball_distances()`\n",
        "- `step(n=1, pin_ball=True)`\n\n",
        "## Notes\n\n",
        "- This is an adapter scaffold, not a training environment.\n",
        "- Default loading now targets collision proxy v2 with ball; legacy physics-v0 scenes remain available by explicit path.\n",
        "- Observation includes qpos, qvel, ctrl, fingertip positions, ball pose/velocity, contact summary, and fingertip-ball distances.\n",
        "- Current `*_mcp_flex_joint` names are preserved; semantic aliases should be handled above this API.\n",
    ]
    report_path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load the arm-hand task API and write a report.")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    args = parser.parse_args()
    api = load_model(args.scene)
    write_api_report(api)
    print(f"Loaded: {api.scene_path}")
    print(f"Action dim: {api.get_action_dim()}")
    print(f"Observation dim: {len(api.get_observation()['vector'])}")
    print(f"Saved report: {DEFAULT_REPORT}")


if __name__ == "__main__":
    main()
