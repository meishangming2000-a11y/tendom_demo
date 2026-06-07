#!/usr/bin/env python3
"""Stage3 MuJoCo-only task contract for sensor-aware gentle egg grasp/hold.

This module starts the Stage3.0 contract lane. It defines the object, sensor
abstractions, success/failure checks, and report metadata without claiming a
hardware interface or a trained policy.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from arm_hand_stage1_task_api import actuator_to_joint_name, json_ready, name_or
from stage3_sensor_abstractions import (
    TACTILE_FIELD_NAMES,
    VISION_FIELD_NAMES,
    Stage3SensorConfig,
    Stage3SensorReplayKey,
    Stage3VisionConfig,
    build_tactile_observation,
    build_vision_observation,
    validate_sensor_observation,
)


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CURRENT_STAGE3_SCENE = ROOT / "mjcf" / "scene_arm_hand_export4_stage3_egg_gentle_grasp_hold_v0.xml"
DEFAULT_REPORT = DOCS / "stage3_sensor_aware_gentle_grasp_hold_v0_task_contract.md"
DEFAULT_META = META / "stage3_sensor_aware_gentle_grasp_hold_v0_task_contract.json"

TASK_NAME = "stage3_sensor_aware_gentle_grasp_hold"
TASK_CONTRACT_VERSION = "stage3_sensor_aware_gentle_grasp_hold_v0"
STAGE_NAME = "stage3_sensor_aware_mujoco_manipulation"

OBJECT_BODY_NAME = "egg"
OBJECT_JOINT_NAME = "egg_freejoint"
OBJECT_GEOM_NAME = "egg_geom"
DEFAULT_OBJECT_POSITION = np.array([0.19022382, 0.187702, -0.05538044], dtype=np.float64)
DEFAULT_OBJECT_QUAT = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
DEFAULT_OBJECT_SHAPE = np.array([0.022, 0.032, 0.038], dtype=np.float64)
DEFAULT_GOAL_LIFT_DELTA = np.array([0.0, 0.0, 0.05], dtype=np.float64)

PHASES = (
    "default_hold",
    "vision_acquire",
    "approach",
    "pre_contact_align",
    "gentle_close",
    "contact_settle",
    "grasp_secure_check",
    "lift",
    "hold",
    "slip_recover_or_abort",
    "release_or_reset",
)

TERMINAL_REASONS = (
    "running",
    "success_gentle_grasp_hold",
    "non_finite_state",
    "premature_object_push",
    "no_contact_timeout",
    "grasp_not_secure",
    "slip_detected",
    "object_dropped",
    "crush_risk_exceeded",
    "excessive_penetration",
    "bad_vision_confidence",
    "unstable_hold",
    "timeout",
)


@dataclass(frozen=True)
class Stage3Thresholds:
    success_lift_height_m: float = 0.05
    success_hold_duration_s: float = 3.0
    success_max_pose_drift_m: float = 0.025
    success_max_slip_score: float = 0.35
    success_max_crush_risk: float = 0.65
    success_max_penetration_m: float = 0.012
    failure_max_penetration_m: float = 0.020
    premature_push_xy_m: float = 0.010
    min_vision_confidence: float = 0.50
    no_contact_timeout_steps: int = 900
    max_episode_steps: int = 3000


VisionNoiseConfig = Stage3VisionConfig


def _as_array(value: Iterable[float], shape: tuple[int, ...], name: str) -> np.ndarray:
    arr = np.asarray(list(value), dtype=np.float64)
    if arr.shape != shape:
        raise ValueError(f"Expected {name} shape {shape}, got {arr.shape}")
    return arr


def _safe_unit(vec: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    if norm <= 1e-12:
        return fallback.copy()
    return vec / norm


def _region_from_names(names: list[str]) -> str:
    joined = " ".join(names).lower()
    for region in ("thumb", "index", "middle", "ring", "little"):
        if region in joined:
            return region
    if "palm" in joined or "hand_base" in joined or "wrist" in joined:
        return "palm"
    if "floor" in joined:
        return "support"
    if "arm" in joined or "link_" in joined or "ee_mount" in joined:
        return "arm"
    return "unknown"


class Stage3GentleGraspTaskAPI:
    def __init__(
        self,
        scene_path: str | Path = CURRENT_STAGE3_SCENE,
        *,
        thresholds: Stage3Thresholds | None = None,
        vision_config: VisionNoiseConfig | None = None,
        sensor_config: Stage3SensorConfig | None = None,
        rng_seed: int = 0,
    ):
        import mujoco

        self.mujoco = mujoco
        self.scene_path = Path(scene_path).resolve()
        self.model = mujoco.MjModel.from_xml_path(str(self.scene_path))
        self.data = mujoco.MjData(self.model)
        self.thresholds = thresholds or Stage3Thresholds()
        if sensor_config is None:
            sensor_config = Stage3SensorConfig(base_seed=int(rng_seed))
        if vision_config is not None:
            sensor_config = Stage3SensorConfig(
                base_seed=int(sensor_config.base_seed),
                vision=vision_config,
                tactile=sensor_config.tactile,
            )
        self.sensor_config = sensor_config
        self.vision_config = sensor_config.vision
        self.object_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, OBJECT_BODY_NAME)
        self.object_joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, OBJECT_JOINT_NAME)
        self.object_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, OBJECT_GEOM_NAME)
        if self.object_body_id < 0 or self.object_joint_id < 0 or self.object_geom_id < 0:
            raise ValueError(f"Stage3 scene must contain body={OBJECT_BODY_NAME!r}, joint={OBJECT_JOINT_NAME!r}, geom={OBJECT_GEOM_NAME!r}")
        self.object_qadr = int(self.model.jnt_qposadr[self.object_joint_id])
        self.object_dadr = int(self.model.jnt_dofadr[self.object_joint_id])
        self._actuator_names = [
            name_or(self.model, self.mujoco, self.mujoco.mjtObj.mjOBJ_ACTUATOR, i, f"actuator_{i}")
            for i in range(self.model.nu)
        ]
        self.reset_open()

    def reset_open(
        self,
        object_position: Iterable[float] | None = None,
        object_quat: Iterable[float] | None = None,
    ) -> dict[str, Any]:
        self.data.qpos[:] = self.model.qpos0
        self.data.qvel[:] = 0.0
        self.data.ctrl[:] = 0.0
        self.set_object_pose_world(
            DEFAULT_OBJECT_POSITION if object_position is None else object_position,
            DEFAULT_OBJECT_QUAT if object_quat is None else object_quat,
        )
        self.mujoco.mj_forward(self.model, self.data)
        return self.get_observation()

    def set_object_pose_world(self, position: Iterable[float], quat: Iterable[float] | None = None) -> None:
        pos = _as_array(position, (3,), "object position")
        q = DEFAULT_OBJECT_QUAT if quat is None else _as_array(quat, (4,), "object quat")
        self.data.qpos[self.object_qadr : self.object_qadr + 3] = pos
        self.data.qpos[self.object_qadr + 3 : self.object_qadr + 7] = q
        self.data.qvel[self.object_dadr : self.object_dadr + 6] = 0.0
        self.mujoco.mj_forward(self.model, self.data)

    def get_action_dim(self) -> int:
        return int(self.model.nu)

    def get_action_schema(self) -> dict[str, Any]:
        rows = []
        for aid, actuator_name in enumerate(self._actuator_names):
            ctrlrange = (
                self.model.actuator_ctrlrange[aid].copy()
                if bool(self.model.actuator_ctrllimited[aid])
                else np.array([np.nan, np.nan])
            )
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

    def get_proprio_schema(self) -> dict[str, Any]:
        return {
            "qpos": int(self.model.nq),
            "qvel": int(self.model.nv),
            "ctrl": int(self.model.nu),
        }

    def get_object_pose(self) -> dict[str, np.ndarray]:
        return {
            "position": self.data.qpos[self.object_qadr : self.object_qadr + 3].copy(),
            "quat": self.data.qpos[self.object_qadr + 3 : self.object_qadr + 7].copy(),
            "velocity": self.data.qvel[self.object_dadr : self.object_dadr + 6].copy(),
            "axis": self.data.xmat[self.object_body_id].reshape(3, 3)[:, 2].copy(),
        }

    def get_contact_summary(self, top_n: int = 10) -> dict[str, Any]:
        rows = []
        max_pen = 0.0
        egg_hand = 0
        egg_arm = 0
        egg_floor = 0
        regions: set[str] = set()
        for i in range(self.data.ncon):
            c = self.data.contact[i]
            g1, g2 = int(c.geom1), int(c.geom2)
            b1, b2 = int(self.model.geom_bodyid[g1]), int(self.model.geom_bodyid[g2])
            geom1 = name_or(self.model, self.mujoco, self.mujoco.mjtObj.mjOBJ_GEOM, g1, f"geom_{g1}")
            geom2 = name_or(self.model, self.mujoco, self.mujoco.mjtObj.mjOBJ_GEOM, g2, f"geom_{g2}")
            body1 = name_or(self.model, self.mujoco, self.mujoco.mjtObj.mjOBJ_BODY, b1, f"body_{b1}")
            body2 = name_or(self.model, self.mujoco, self.mujoco.mjtObj.mjOBJ_BODY, b2, f"body_{b2}")
            names = [geom1, geom2, body1, body2]
            has_egg = any("egg" in n.lower() for n in names)
            pen = max(0.0, -float(c.dist))
            max_pen = max(max_pen, pen)
            if has_egg:
                lower_names = [n.lower() for n in names]
                hand_hit = any(
                    ("palm" in n or "finger" in n or "thumb" in n or "distal" in n or "proximal" in n or "wrist" in n or "mcp" in n or "hand_base" in n)
                    for n in lower_names
                )
                arm_hit = any(n in {"base_link", "link_1", "link_2", "link_3", "ee_mount"} or n.endswith("_arm_collision_proxy_box") for n in lower_names)
                floor_hit = any("floor" in n for n in lower_names)
                if hand_hit:
                    egg_hand += 1
                if arm_hit:
                    egg_arm += 1
                if floor_hit:
                    egg_floor += 1
                regions.add(_region_from_names(names))
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
            "egg_hand_contact_count": int(egg_hand),
            "egg_arm_contact_count": int(egg_arm),
            "egg_floor_contact_count": int(egg_floor),
            "egg_contact_regions": sorted(regions),
            "top_contacts": rows[:top_n],
        }

    def get_vision_observation(
        self,
        *,
        goal_pose_xyz: Iterable[float] | None = None,
        deterministic: bool = False,
        episode_id: int = 0,
        step_index: int = 0,
        pose_history_xyz: Sequence[Iterable[float]] | None = None,
        vision_override: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        pose = self.get_object_pose()
        if vision_override is not None:
            raw_position = (
                vision_override.get("object_pose_xyz_est")
                if "object_pose_xyz_est" in vision_override
                else vision_override.get("position_world_est")
            )
            if raw_position is None:
                raw_position = vision_override.get("last_good_position")
            if raw_position is None:
                raw_position = pose["position"]
                pose_source = "ground_truth_debug_fallback_no_valid_virtual_camera_pose"
            else:
                pose_source = "virtual_camera"
            pose_est = _as_array(raw_position, (3,), "vision override pose")
            goal = (
                pose_est + DEFAULT_GOAL_LIFT_DELTA
                if goal_pose_xyz is None
                else _as_array(goal_pose_xyz, (3,), "goal pose")
            )
            axis_est = _safe_unit(
                np.asarray(vision_override.get("object_axis_est", pose["axis"]), dtype=np.float64),
                np.array([0.0, 0.0, 1.0], dtype=np.float64),
            )
            shape_est = np.maximum(
                0.001,
                np.asarray(vision_override.get("object_shape_params_est", DEFAULT_OBJECT_SHAPE), dtype=np.float64),
            )
            mask_retention = float(vision_override.get("mask_retention_ratio", 1.0))
            confidence = float(
                np.clip(
                    vision_override.get(
                        "tracking_confidence",
                        vision_override.get("confidence", 0.0 if vision_override.get("status") != "ok" else 1.0),
                    ),
                    0.0,
                    1.0,
                )
            )
            return {
                "object_pose_xyz_est": pose_est,
                "object_axis_est": axis_est,
                "object_shape_params_est": shape_est,
                "goal_pose_xyz_est": goal,
                "object_to_goal_est": goal - pose_est,
                "confidence": confidence,
                "occlusion": float(np.clip(1.0 - mask_retention, 0.0, 1.0)),
                "latency_steps": int(vision_override.get("latency_steps", 0)),
                "noise_std": float(vision_override.get("noise_std", vision_override.get("depth_noise_std_m", 0.0))),
                "latency_source": vision_override.get("latency_source", "virtual_camera_current_frame"),
                "vision_source": pose_source,
                "virtual_camera_status": vision_override.get("status", "ok"),
                "accepted_as_pose_update": bool(vision_override.get("accepted_as_pose_update", confidence >= self.thresholds.min_vision_confidence)),
                "mask_pixels": int(vision_override.get("mask_pixels", 0)),
                "mask_retention_ratio": mask_retention,
            }
        goal = (
            pose["position"] + DEFAULT_GOAL_LIFT_DELTA
            if goal_pose_xyz is None
            else _as_array(goal_pose_xyz, (3,), "goal pose")
        )
        replay_key = Stage3SensorReplayKey(int(self.sensor_config.base_seed), int(episode_id), int(step_index))
        obs = build_vision_observation(
            object_position=pose["position"],
            object_axis=pose["axis"],
            object_shape_params=DEFAULT_OBJECT_SHAPE,
            goal_pose_xyz=goal,
            config=self.vision_config,
            replay_key=replay_key,
            pose_history_xyz=pose_history_xyz,
        )
        obs["vision_source"] = "replay_safe_ground_truth_abstraction"
        obs["accepted_as_pose_update"] = bool(obs["confidence"] >= self.thresholds.min_vision_confidence)
        return obs

    def get_tactile_observation(self, *, contact_persistence_steps: int = 0) -> dict[str, Any]:
        contact = self.get_contact_summary()
        pose = self.get_object_pose()
        return build_tactile_observation(
            contact_summary=contact,
            object_velocity=pose["velocity"],
            contact_persistence_steps=int(contact_persistence_steps),
            success_max_slip_score=float(self.thresholds.success_max_slip_score),
            success_max_crush_risk=float(self.thresholds.success_max_crush_risk),
            failure_max_penetration_m=float(self.thresholds.failure_max_penetration_m),
            config=self.sensor_config.tactile,
        )

    def get_ground_truth_state(self, initial_object_position: Iterable[float] | None = None) -> dict[str, Any]:
        pose = self.get_object_pose()
        initial = pose["position"] if initial_object_position is None else _as_array(initial_object_position, (3,), "initial object position")
        contact = self.get_contact_summary()
        return {
            "object_pose": pose,
            "object_lift_height": float(pose["position"][2] - initial[2]),
            "object_displacement": float(np.linalg.norm(pose["position"] - initial)),
            "object_pose_drift_xy": float(np.linalg.norm((pose["position"] - initial)[:2])),
            "object_velocity_norm": float(np.linalg.norm(pose["velocity"])),
            "contact_summary": {key: value for key, value in contact.items() if key != "top_contacts"},
            "finite_state": bool(np.isfinite(self.data.qpos).all() and np.isfinite(self.data.qvel).all()),
        }

    def get_observation(
        self,
        *,
        phase: str = "vision_acquire",
        phase_progress: float = 0.0,
        contact_persistence_steps: int = 0,
        deterministic_vision: bool = False,
        episode_id: int = 0,
        step_index: int = 0,
        pose_history_xyz: Sequence[Iterable[float]] | None = None,
        vision_override: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if phase not in PHASES:
            raise ValueError(f"Unknown phase {phase!r}; available={PHASES}")
        vision = self.get_vision_observation(
            deterministic=deterministic_vision,
            episode_id=episode_id,
            step_index=step_index,
            pose_history_xyz=pose_history_xyz,
            vision_override=vision_override,
        )
        tactile = self.get_tactile_observation(contact_persistence_steps=contact_persistence_steps)
        sensor_validation = validate_sensor_observation(vision, tactile)
        phase_vec = np.zeros(len(PHASES), dtype=np.float64)
        phase_vec[PHASES.index(phase)] = 1.0
        vector = np.concatenate(
            [
                self.data.qpos.copy(),
                self.data.qvel.copy(),
                self.data.ctrl.copy(),
                phase_vec,
                np.array([float(phase_progress)], dtype=np.float64),
                vision["object_pose_xyz_est"],
                vision["object_axis_est"],
                vision["object_shape_params_est"],
                vision["goal_pose_xyz_est"],
                vision["object_to_goal_est"],
                np.array([vision["confidence"], vision["occlusion"], vision["latency_steps"], vision["noise_std"]], dtype=np.float64),
                np.array(
                    [
                        float(tactile["contact_present"]),
                        tactile["normal_contact_proxy"],
                        tactile["contact_persistence"],
                        tactile["relative_tangential_motion"],
                        tactile["slip_score"],
                        float(tactile["grip_stable"]),
                        tactile["crush_risk"],
                        float(tactile["release_contact_clear"]),
                    ],
                    dtype=np.float64,
                ),
            ]
        )
        return {
            "proprio": {
                "qpos": self.data.qpos.copy(),
                "qvel": self.data.qvel.copy(),
                "ctrl": self.data.ctrl.copy(),
            },
            "phase": {
                "id": PHASES.index(phase),
                "name": phase,
                "progress": float(phase_progress),
                "one_hot": phase_vec,
            },
            "vision": vision,
            "tactile": tactile,
            "sensor_validation": sensor_validation,
            "sensor_replay_key": Stage3SensorReplayKey(
                int(self.sensor_config.base_seed),
                int(episode_id),
                int(step_index),
            ).as_metadata(),
            "vector": vector,
        }

    def evaluate_state(
        self,
        initial_object_position: Iterable[float],
        *,
        phase: str = "vision_acquire",
        step_count: int = 0,
        hold_steps: int = 0,
        contact_persistence_steps: int = 0,
        lifted_once: bool = False,
        episode_id: int = 0,
        step_index: int = 0,
        pose_history_xyz: Sequence[Iterable[float]] | None = None,
        vision_override: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        thresholds = self.thresholds
        gt = self.get_ground_truth_state(initial_object_position)
        vision = self.get_vision_observation(
            deterministic=True,
            episode_id=episode_id,
            step_index=step_index,
            pose_history_xyz=pose_history_xyz,
            vision_override=vision_override,
        )
        tactile = self.get_tactile_observation(contact_persistence_steps=contact_persistence_steps)
        lift_height = float(gt["object_lift_height"])
        hold_duration_s = float(hold_steps) * float(self.model.opt.timestep)
        success_reasons: list[str] = []
        failure_reasons: list[str] = []
        success = bool(
            gt["finite_state"]
            and lift_height >= thresholds.success_lift_height_m
            and hold_duration_s >= thresholds.success_hold_duration_s
            and gt["object_pose_drift_xy"] <= thresholds.success_max_pose_drift_m
            and tactile["contact_present"]
            and tactile["slip_score"] <= thresholds.success_max_slip_score
            and tactile["crush_risk"] <= thresholds.success_max_crush_risk
            and gt["contact_summary"]["max_penetration"] <= thresholds.success_max_penetration_m
        )
        if success:
            success_reasons.append("success_gentle_grasp_hold")
        if not gt["finite_state"]:
            failure_reasons.append("non_finite_state")
        if phase in {"approach", "pre_contact_align"} and gt["object_pose_drift_xy"] > thresholds.premature_push_xy_m:
            failure_reasons.append("premature_object_push")
        if step_count >= thresholds.no_contact_timeout_steps and phase in {"gentle_close", "contact_settle"} and not tactile["contact_present"]:
            failure_reasons.append("no_contact_timeout")
        if phase in {"grasp_secure_check", "lift"} and not tactile["grip_stable"] and step_count >= thresholds.no_contact_timeout_steps:
            failure_reasons.append("grasp_not_secure")
        if bool(lifted_once) and tactile["slip_score"] > thresholds.success_max_slip_score:
            failure_reasons.append("slip_detected")
        if bool(lifted_once) and gt["contact_summary"]["egg_floor_contact_count"] > 0 and lift_height < 0.02:
            failure_reasons.append("object_dropped")
        if tactile["crush_risk"] > thresholds.success_max_crush_risk:
            failure_reasons.append("crush_risk_exceeded")
        if gt["contact_summary"]["max_penetration"] > thresholds.failure_max_penetration_m:
            failure_reasons.append("excessive_penetration")
        if vision["confidence"] < thresholds.min_vision_confidence:
            failure_reasons.append("bad_vision_confidence")
        if phase == "hold" and gt["object_pose_drift_xy"] > thresholds.success_max_pose_drift_m:
            failure_reasons.append("unstable_hold")
        if step_count >= thresholds.max_episode_steps and not success:
            failure_reasons.append("timeout")
        failure = bool(failure_reasons and not success)
        if success:
            status = "success"
            reason = "success_gentle_grasp_hold"
        elif failure:
            status = "failure"
            reason = failure_reasons[0]
        else:
            status = "running"
            reason = "running"
        return {
            "task_name": TASK_NAME,
            "contract_version": TASK_CONTRACT_VERSION,
            "episode_status": status,
            "terminal_reason": reason,
            "success": bool(success),
            "failure": bool(failure),
            "done": bool(success or failure),
            "step_count": int(step_count),
            "phase": phase,
            "success_reasons": success_reasons,
            "failure_reasons": failure_reasons,
            "official_metrics": {
                **gt,
                "hold_steps": int(hold_steps),
                "hold_duration_s": hold_duration_s,
                "slip_score": float(tactile["slip_score"]),
                "crush_risk": float(tactile["crush_risk"]),
                "vision_confidence": float(vision["confidence"]),
                "contact_persistence": int(contact_persistence_steps),
            },
            "sensor_inputs": {
                "vision": vision,
                "tactile": tactile,
            },
        }

    def get_observation_schema(self) -> dict[str, Any]:
        nq = int(self.model.nq)
        nv = int(self.model.nv)
        nu = int(self.model.nu)
        start = 0
        slices = {}
        fields = [
            ("proprio.qpos", nq),
            ("proprio.qvel", nv),
            ("proprio.ctrl", nu),
            ("phase.one_hot", len(PHASES)),
            ("phase.progress", 1),
            ("vision.object_pose_xyz_est", 3),
            ("vision.object_axis_est", 3),
            ("vision.object_shape_params_est", 3),
            ("vision.goal_pose_xyz_est", 3),
            ("vision.object_to_goal_est", 3),
            ("vision.scalars", 4),
            ("tactile.scalars", 8),
        ]
        for name, length in fields:
            slices[name] = {"start": start, "stop": start + length, "length": length}
            start += length
        return {
            "type": "flat_sensor_abstraction_vector",
            "dim": start,
            "phase_names": PHASES,
            "vision_fields": VISION_FIELD_NAMES,
            "tactile_fields": TACTILE_FIELD_NAMES,
            "slices": slices,
            "ground_truth_policy_input": False,
        }

    def get_task_contract(self) -> dict[str, Any]:
        required_hold_steps = int(np.ceil(self.thresholds.success_hold_duration_s / max(float(self.model.opt.timestep), 1e-9)))
        return {
            "task_name": TASK_NAME,
            "contract_version": TASK_CONTRACT_VERSION,
            "stage": STAGE_NAME,
            "training_ready": False,
            "mujoco_only": True,
            "hardware_integration": False,
            "scene": self.scene_path,
            "object": {
                "body_name": OBJECT_BODY_NAME,
                "joint_name": OBJECT_JOINT_NAME,
                "geom_name": OBJECT_GEOM_NAME,
                "shape": "ellipsoid",
                "shape_params_xyz_m": DEFAULT_OBJECT_SHAPE,
                "default_position_xyz": DEFAULT_OBJECT_POSITION,
                "fragile_proxy": "crush_risk from MuJoCo penetration/contact proxy",
            },
            "phases": PHASES,
            "action": self.get_action_schema(),
            "observation": self.get_observation_schema(),
            "thresholds": asdict(self.thresholds),
            "sensor_abstraction": {
                "version": "stage3_sensor_abstraction_v0",
                "requirements_doc": "docs/stage3_sensor_requirements_v0.md",
                "replay_safe": True,
                "sensor_config": self.sensor_config.as_metadata(),
                "policy_input_boundary": "sensor abstractions only; ground-truth fields are logging/eval/replay QA only",
            },
            "required_hold_steps": required_hold_steps,
            "success_when_all_true": [
                "object_lift_height >= 0.05 m",
                "hold_duration_s >= 3.0 s",
                "object_pose_drift_xy <= success_max_pose_drift_m",
                "slip_score <= success_max_slip_score",
                "crush_risk <= success_max_crush_risk",
                "max_penetration <= success_max_penetration_m",
                "finite_state is true",
            ],
            "failure_reasons": TERMINAL_REASONS,
            "dataset_fields": [
                "obs",
                "next_obs",
                "proprio_obs",
                "vision_obs",
                "tactile_obs",
                "gt_eval_state",
                "actions",
                "expert_actions",
                "residual_actions_optional",
                "phase_ids",
                "phase_step_ids",
                "episode_ids",
                "rewards",
                "dones",
                "successes",
                "failures",
                "terminal_reason_ids",
                "sensor_noise_params",
                "object_params",
            ],
            "blocked_policy_forms": [
                "unconstrained end-to-end policy over all phases",
                "fully live-observation BC for approach, first close, or early lift",
                "RL before task contract, replay QA, and termination QA pass",
            ],
        }


def build_contract(scene: Path = CURRENT_STAGE3_SCENE) -> dict[str, Any]:
    api = Stage3GentleGraspTaskAPI(scene)
    return api.get_task_contract()


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage3 Sensor-Aware Gentle Grasp/Hold Task Contract\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Task name: `{payload['task_name']}`\n",
        f"- Contract version: `{payload['contract_version']}`\n",
        f"- Stage: `{payload['stage']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Training ready: **{payload['training_ready']}**\n",
        f"- MuJoCo only: **{payload['mujoco_only']}**\n",
        f"- Hardware integration: **{payload['hardware_integration']}**\n\n",
        "## Object\n\n",
        f"- Body: `{payload['object']['body_name']}`\n",
        f"- Shape: `{payload['object']['shape']}`\n",
        f"- Shape params XYZ m: `{json_ready(payload['object']['shape_params_xyz_m'])}`\n",
        f"- Default position XYZ: `{json_ready(payload['object']['default_position_xyz'])}`\n\n",
        "## Phases\n\n",
    ]
    for phase in payload["phases"]:
        lines.append(f"- `{phase}`\n")
    lines.extend(["\n## Sensor Observation\n\n"])
    for field in payload["observation"]["vision_fields"]:
        lines.append(f"- `vision.{field}`\n")
    for field in payload["observation"]["tactile_fields"]:
        lines.append(f"- `tactile.{field}`\n")
    sensor = payload["sensor_abstraction"]
    lines.extend(
        [
            "\n## Sensor Abstraction\n\n",
            f"- Version: `{sensor['version']}`\n",
            f"- Requirements doc: `{sensor['requirements_doc']}`\n",
            f"- Replay safe: **{sensor['replay_safe']}**\n",
            f"- Replay key: `{sensor['sensor_config']['replay_key']}`\n",
            f"- Base seed: `{sensor['sensor_config']['base_seed']}`\n",
            "- Policy input boundary: sensor abstractions only; ground-truth fields are logging/eval/replay QA only.\n\n",
            "## Success Contract\n\n",
        ]
    )
    for item in payload["success_when_all_true"]:
        lines.append(f"- {item}\n")
    lines.extend(["\n## Failure Reasons\n\n"])
    for item in payload["failure_reasons"]:
        lines.append(f"- `{item}`\n")
    lines.extend(
        [
            "\n## Boundary\n\n",
            "- Stage3 uses simulated vision and synthetic tactile/slip abstractions only.\n",
            "- Ground-truth MuJoCo object state may be logged for labels, replay QA, and evaluation, but is not the default learned-policy input.\n",
            "- This contract does not claim a scripted expert, dataset, replay QA, trained policy, or hardware readiness yet.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the Stage3 sensor-aware gentle grasp/hold task contract.")
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_META)
    args = parser.parse_args()
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        **build_contract(args.scene),
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, payload)
    print(f"Report: {args.report}")
    print(f"Metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
