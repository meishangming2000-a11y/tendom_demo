#!/usr/bin/env python3
"""Collect Stage3 virtual-vision + tactile/slip expert dataset V0.

This is the first learning-track dataset for the Stage3 egg task. It stays
inside MuJoCo and records sensor-abstraction observations from the current
scripted/IK expert:

virtual-camera acquire -> approach -> gentle close -> slow lift -> hold

Ground truth is logged for QA/evaluation only. The default training observation
is the Stage3 sensor vector: proprio + phase + virtual vision + tactile/slip.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
from stage3_sensor_aware_gentle_grasp_hold_task_api import (
    CURRENT_STAGE3_SCENE,
    DEFAULT_GOAL_LIFT_DELTA,
    DEFAULT_OBJECT_SHAPE,
    PHASES,
    TASK_CONTRACT_VERSION,
    TASK_NAME,
    Stage3Thresholds,
    build_contract,
)


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import run_stage3_visual_guided_grasp_sweep as sweep
from mujoco_egg_pose_sensor import EggPoseSensorConfig, MujocoEggPoseSensor
from mujoco_tactile_slip_sensor import MujocoTactileSlipSensor


DATASET_VERSION = "v0"
DEFAULT_DATASET = DATA / "stage3_sensor_fusion_expert_dataset_v0.npz"
DEFAULT_REPORT = DOCS / "stage3_sensor_fusion_expert_dataset_v0_report.md"
DEFAULT_METADATA = META / "stage3_sensor_fusion_expert_dataset_v0.json"

STAGE3_PHASE_MAP = {
    "approach": "approach",
    "preshape": "pre_contact_align",
    "gentle_close_fingers": "gentle_close",
    "gentle_close_thumb": "gentle_close",
    "pinch_close": "gentle_close",
    "contact_settle": "contact_settle",
    "slow_lift": "lift",
    "hold": "hold",
}

TERMINAL_REASONS = (
    "running",
    "success_gentle_grasp_hold",
    "vision_acquire_failed",
    "ik_alignment_error",
    "functional_approach_missed_true_egg",
    "no_tactile_contact",
    "grip_not_stable_before_lift",
    "insufficient_lift_height",
    "insufficient_hold_duration",
    "unstable_hold_tactile",
    "hold_slip_score_high",
    "crush_risk_high",
    "excessive_penetration",
    "egg_on_floor_after_hold",
    "non_finite_state",
)


@dataclass(frozen=True)
class Stage3DatasetProfile:
    name: str
    timing_scale: float
    action_noise_abs: float
    action_lag: float
    seed_offset: int


PROFILES = [
    Stage3DatasetProfile("clean_nominal", 1.0, 0.0, 0.0, 0),
    Stage3DatasetProfile("timing_fast_clean", 0.94, 0.0, 0.0, 1000),
    Stage3DatasetProfile("timing_slow_clean", 1.06, 0.0, 0.0, 2000),
]


def parse_profiles(raw: str) -> list[Stage3DatasetProfile]:
    requested = [item.strip() for item in raw.split(",") if item.strip()]
    by_name = {profile.name: profile for profile in PROFILES}
    missing = [name for name in requested if name not in by_name]
    if missing:
        raise ValueError(f"Unknown profiles {missing}; available={sorted(by_name)}")
    return [by_name[name] for name in requested]


def reason_code(reason: str) -> int:
    try:
        return TERMINAL_REASONS.index(reason)
    except ValueError:
        return TERMINAL_REASONS.index("non_finite_state")


def concatenate_rows(episodes: list[dict[str, Any]], key: str, dtype) -> np.ndarray:
    return np.concatenate([np.asarray(ep["rows"][key], dtype=dtype) for ep in episodes], axis=0)


def accepted_virtual_camera_estimate(estimate: dict[str, Any], min_confidence: float) -> bool:
    return estimate.get("status") == "ok" and float(estimate.get("confidence", 0.0)) >= float(min_confidence)


def phase_id(phase_name: str) -> int:
    return list(PHASES).index(STAGE3_PHASE_MAP.get(phase_name, phase_name))


def tactile_region_mask(tactile: dict[str, Any]) -> np.ndarray:
    regions = set(str(item) for item in tactile.get("contact_regions", []))
    return np.asarray(
        [
            "thumb" in regions,
            "index" in regions,
            "middle" in regions,
            "ring" in regions,
            "little" in regions,
            "palm" in regions,
            "support" in regions,
        ],
        dtype=np.float64,
    )


def make_vision_fields(vision_estimate: dict[str, Any]) -> dict[str, Any]:
    pose_est = np.asarray(vision_estimate["position_world_est"], dtype=np.float64)
    mask_pixels = int(vision_estimate.get("mask_pixels", 0))
    visibility = float(vision_estimate.get("visibility_fraction", 0.0))
    return {
        "object_pose_xyz_est": pose_est,
        "object_axis_est": np.array([0.0, 0.0, 1.0], dtype=np.float64),
        "object_shape_params_est": DEFAULT_OBJECT_SHAPE.copy(),
        "goal_pose_xyz_est": pose_est + DEFAULT_GOAL_LIFT_DELTA,
        "object_to_goal_est": DEFAULT_GOAL_LIFT_DELTA.copy(),
        "confidence": float(vision_estimate.get("confidence", 0.0)),
        "occlusion": float(np.clip(1.0 - min(1.0, visibility / 0.05), 0.0, 1.0)),
        "latency_steps": 0,
        "noise_std": 0.0,
        "status": str(vision_estimate.get("status", "unknown")),
        "mask_pixels": mask_pixels,
        "visibility_fraction": visibility,
        "fit_residual_rms": float(vision_estimate.get("fit_residual_rms", 0.0)),
    }


def observation_vector(model, data, vision: dict[str, Any], tactile: dict[str, Any], *, phase_name: str, progress: float) -> np.ndarray:
    phase_vec = np.zeros(len(PHASES), dtype=np.float64)
    phase_vec[phase_id(phase_name)] = 1.0
    return np.concatenate(
        [
            data.qpos.copy(),
            data.qvel.copy(),
            data.ctrl.copy(),
            phase_vec,
            np.asarray([float(progress)], dtype=np.float64),
            np.asarray(vision["object_pose_xyz_est"], dtype=np.float64),
            np.asarray(vision["object_axis_est"], dtype=np.float64),
            np.asarray(vision["object_shape_params_est"], dtype=np.float64),
            np.asarray(vision["goal_pose_xyz_est"], dtype=np.float64),
            np.asarray(vision["object_to_goal_est"], dtype=np.float64),
            np.asarray(
                [
                    float(vision["confidence"]),
                    float(vision["occlusion"]),
                    float(vision["latency_steps"]),
                    float(vision["noise_std"]),
                ],
                dtype=np.float64,
            ),
            np.asarray(
                [
                    float(tactile["contact_present"]),
                    float(tactile["normal_contact_proxy"]),
                    float(tactile["contact_persistence"]),
                    float(tactile["relative_tangential_motion"]),
                    float(tactile["slip_score"]),
                    float(tactile["grip_stable"]),
                    float(tactile["crush_risk"]),
                    float(tactile["release_contact_clear"]),
                ],
                dtype=np.float64,
            ),
        ]
    )


def tactile_scalars(tactile: dict[str, Any]) -> np.ndarray:
    return np.asarray(
        [
            float(tactile["contact_present"]),
            float(tactile["normal_contact_proxy"]),
            float(tactile["contact_persistence"]),
            float(tactile["relative_tangential_motion"]),
            float(tactile["slip_score"]),
            float(tactile["grip_stable"]),
            float(tactile["crush_risk"]),
            float(tactile["release_contact_clear"]),
            float(tactile.get("egg_hand_contact_count", 0)),
            float(tactile.get("egg_floor_contact_count", 0)),
            float(tactile.get("max_penetration", 0.0)),
        ],
        dtype=np.float64,
    )


def vision_scalars(vision: dict[str, Any]) -> np.ndarray:
    return np.asarray(
        [
            float(vision["confidence"]),
            float(vision["occlusion"]),
            float(vision["latency_steps"]),
            float(vision["noise_std"]),
            float(vision["mask_pixels"]),
            float(vision["visibility_fraction"]),
            float(vision["fit_residual_rms"]),
        ],
        dtype=np.float64,
    )


def clip_action(model, action: np.ndarray) -> np.ndarray:
    out = np.asarray(action, dtype=np.float64).copy()
    for aid in range(model.nu):
        if bool(model.actuator_ctrllimited[aid]):
            low, high = model.actuator_ctrlrange[aid]
            out[aid] = np.clip(out[aid], low, high)
    return out


def make_behavior_action(
    model,
    expert_action: np.ndarray,
    previous_behavior: np.ndarray | None,
    rng: np.random.Generator,
    profile: Stage3DatasetProfile,
) -> np.ndarray:
    behavior = np.asarray(expert_action, dtype=np.float64).copy()
    if previous_behavior is not None and profile.action_lag > 0.0:
        lag = float(np.clip(profile.action_lag, 0.0, 0.95))
        behavior = (1.0 - lag) * behavior + lag * previous_behavior
    if profile.action_noise_abs > 0.0:
        behavior = behavior + rng.normal(0.0, profile.action_noise_abs, size=behavior.shape)
    return clip_action(model, behavior)


def scaled_steps(base_steps: int, profile: Stage3DatasetProfile) -> int:
    return max(1, int(round(float(base_steps) * float(profile.timing_scale))))


def build_episode_plan(model, data, mujoco, *, trial: sweep.TrialConfig, egg_position: np.ndarray, vision_fields: dict[str, Any], args, profile: Stage3DatasetProfile):
    target_position = np.asarray(vision_fields["object_pose_xyz_est"], dtype=np.float64).copy()
    grasp_local = sweep.DEFAULT_GRASP_LOCAL.copy()
    solver = sweep.ArmProxyIkSolver(model, mujoco, grasp_local)
    approach_target = target_position.copy()
    approach_target[2] += float(trial.grasp_z_bias_m)
    lift_target = approach_target.copy()
    lift_target[2] += float(trial.lift_delta_m)
    approach_solution = solver.solve(approach_target, z_weight=10.0)
    lift_solution = solver.solve(lift_target, z_weight=6.0)
    approach_arm = sweep.arm_dict(approach_solution)
    lift_arm = sweep.arm_dict(lift_solution)
    pre_arm = dict(approach_arm)
    pre_arm["j2"] = float(np.clip(pre_arm["j2"] + float(trial.pre_j2_delta), -1.5708, 1.5708))
    sweep.reset_episode(model, data, mujoco, egg_position)
    for joint, value in pre_arm.items():
        data.qpos[sweep.base.joint_qadr(model, mujoco, joint)] = float(value)
    actuator_names = sweep.base.actuator_names(model, mujoco)
    data.ctrl[:] = sweep.actuator_targets(model, mujoco, actuator_names, pre_arm)
    mujoco.mj_forward(model, data)
    hand_targets = {
        "preshape": {**approach_arm, **sweep.base.PRESHAPE_TARGETS},
        "close_fingers": {**approach_arm, **sweep.base.LONG_FINGER_TARGETS},
        "close_thumb": {**approach_arm, **sweep.base.LONG_FINGER_TARGETS, **sweep.base.THUMB_SMOKE_TARGETS},
        "lift": {**lift_arm, **sweep.base.LONG_FINGER_TARGETS, **sweep.base.THUMB_SMOKE_TARGETS},
    }
    phases = [
        ("approach", pre_arm, approach_arm, scaled_steps(args.approach_steps, profile)),
        ("preshape", approach_arm, hand_targets["preshape"], scaled_steps(args.hand_steps, profile)),
        ("gentle_close_fingers", hand_targets["preshape"], hand_targets["close_fingers"], scaled_steps(args.close_fingers_steps, profile)),
        ("gentle_close_thumb", hand_targets["close_fingers"], hand_targets["close_thumb"], scaled_steps(args.close_thumb_steps, profile)),
        ("contact_settle", hand_targets["close_thumb"], hand_targets["close_thumb"], scaled_steps(args.contact_settle_steps, profile)),
        ("slow_lift", hand_targets["close_thumb"], hand_targets["lift"], scaled_steps(args.lift_steps, profile)),
        ("hold", hand_targets["lift"], hand_targets["lift"], scaled_steps(args.hold_steps, profile)),
    ]
    return {
        "phases": phases,
        "approach_solution": approach_solution,
        "lift_solution": lift_solution,
        "approach_target": approach_target,
        "lift_target": lift_target,
        "grasp_local": grasp_local,
        "actuator_names": actuator_names,
    }


def expert_failure_reasons(summary: dict[str, Any], args, thresholds: Stage3Thresholds) -> list[str]:
    reasons: list[str] = []
    if not bool(summary["vision_accepted"]):
        reasons.append("vision_acquire_failed")
    if summary["ik_approach_dxy_m"] > float(args.max_ik_dxy) or summary["ik_approach_dz_m"] > float(args.max_ik_dz):
        reasons.append("ik_alignment_error")
    if summary["approach_true_proxy_error_m"] > float(args.functional_hit_threshold):
        reasons.append("functional_approach_missed_true_egg")
    if not bool(summary["contact_acquired"]):
        reasons.append("no_tactile_contact")
    if not bool(summary["grip_stable_before_lift"]):
        reasons.append("grip_not_stable_before_lift")
    if summary["final_lift_height_m"] < float(thresholds.success_lift_height_m):
        reasons.append("insufficient_lift_height")
    if summary["hold_duration_s"] < float(thresholds.success_hold_duration_s):
        reasons.append("insufficient_hold_duration")
    if summary["hold_stable_fraction"] < float(args.min_hold_stable_fraction):
        reasons.append("unstable_hold_tactile")
    if summary["hold_max_slip_score"] > float(thresholds.success_max_slip_score):
        reasons.append("hold_slip_score_high")
    if summary["max_crush_risk"] > float(thresholds.success_max_crush_risk):
        reasons.append("crush_risk_high")
    if summary["max_penetration_m"] > float(thresholds.success_max_penetration_m):
        reasons.append("excessive_penetration")
    if summary["final_floor_contacts"] > 0:
        reasons.append("egg_on_floor_after_hold")
    if not bool(summary["finite_state"]):
        reasons.append("non_finite_state")
    return reasons


def reward_from_state(tactile: dict[str, Any], lift_height: float, *, final_success: bool = False, final_failure: bool = False) -> float:
    reward = 2.0 * float(np.clip(lift_height, -0.02, 0.12))
    reward += 0.15 if tactile["contact_present"] else 0.0
    reward += 0.25 if tactile["grip_stable"] else 0.0
    reward -= 0.20 * float(tactile["slip_score"])
    reward -= 0.30 * float(tactile["crush_risk"])
    reward += 5.0 if final_success else 0.0
    reward -= 5.0 if final_failure else 0.0
    return float(reward)


def collect_episode(model, mujoco, episode_id: int, trial: sweep.TrialConfig, profile: Stage3DatasetProfile, args) -> dict[str, Any]:
    rng = np.random.default_rng(int(args.seed) + int(profile.seed_offset) + int(episode_id))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    base_egg_position = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
    if float(args.random_offset_std) > 0.0:
        egg_position = egg_position + rng.normal(0.0, float(args.random_offset_std), size=3)
        egg_position[2] = base_egg_position[2] + np.asarray(trial.offset_xyz, dtype=np.float64)[2]

    sweep.reset_episode(model, data, mujoco, egg_position)
    vision_sensor = MujocoEggPoseSensor(
        model,
        mujoco,
        EggPoseSensorConfig(camera_name=args.camera, width=int(args.width), height=int(args.height)),
    )
    vision_estimate = vision_sensor.estimate(data, label=f"episode_{episode_id:04d}_vision_acquire")
    vision_accepted = accepted_virtual_camera_estimate(vision_estimate, float(args.min_vision_confidence))
    if not vision_accepted:
        raise RuntimeError(f"Episode {episode_id} vision failed: {vision_estimate}")
    vision = make_vision_fields(vision_estimate)
    plan = build_episode_plan(model, data, mujoco, trial=trial, egg_position=egg_position, vision_fields=vision, args=args, profile=profile)
    thresholds = Stage3Thresholds()
    tactile_sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=thresholds)
    tactile_sensor.reset(data)
    initial_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    initial_qpos = data.qpos.copy()
    initial_qvel = data.qvel.copy()
    initial_ctrl = data.ctrl.copy()
    previous_behavior: np.ndarray | None = None
    phase_names = [name for name, _, _, _ in plan["phases"]]
    total_steps = sum(steps for _, _, _, steps in plan["phases"])

    rows: dict[str, list[Any]] = {
        "obs": [],
        "actions": [],
        "expert_actions": [],
        "next_obs": [],
        "rewards": [],
        "dones": [],
        "successes": [],
        "failures": [],
        "terminal_reason_ids": [],
        "episode_ids": [],
        "step_ids": [],
        "phase_ids": [],
        "phase_step_ids": [],
        "vision_pose_estimates": [],
        "vision_scalars": [],
        "tactile_scalars": [],
        "tactile_region_masks": [],
        "gt_object_positions": [],
        "gt_object_lift_heights": [],
        "initial_object_positions": [],
        "initial_qpos": [],
        "initial_qvel": [],
        "initial_ctrl": [],
        "trial_ids": [],
        "profile_ids": [],
    }
    phase_summaries = []
    step_count = 0
    contact_acquired = False
    grip_stable_before_lift = False
    first_contact_phase = "none"
    max_slip = 0.0
    max_crush = 0.0
    max_penetration = 0.0
    hold_stable_steps = 0
    hold_steps = 0
    hold_max_slip = 0.0
    approach_true_proxy_error = math.inf
    approach_est_proxy_error = math.inf

    for phase_index, (phase_name, start, end, steps) in enumerate(plan["phases"]):
        phase_contact_steps = 0
        phase_stable_steps = 0
        phase_floor_steps = 0
        phase_max_slip = 0.0
        phase_max_crush = 0.0
        phase_max_pen = 0.0
        phase_start_step = step_count
        for local_step in range(max(1, int(steps))):
            progress = local_step / max(1, int(steps) - 1)
            tactile = tactile_sensor.sample(data)
            obs = observation_vector(model, data, vision, tactile, phase_name=phase_name, progress=progress)
            targets = sweep.blend_targets(start, end, progress)
            expert_action = sweep.actuator_targets(model, mujoco, plan["actuator_names"], targets)
            behavior_action = make_behavior_action(model, expert_action, previous_behavior, rng, profile)
            previous_behavior = behavior_action.copy()
            data.ctrl[:] = behavior_action
            mujoco.mj_step(model, data)
            next_tactile = tactile_sensor.sample(data)
            next_obs = observation_vector(model, data, vision, next_tactile, phase_name=phase_name, progress=progress)
            egg_now = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
            lift_height = float(egg_now[2] - initial_egg[2])

            if phase_name == "approach":
                proxy_now = sweep.proxy_position(model, data, mujoco, plan["grasp_local"])
                approach_true_proxy_error = float(np.linalg.norm(proxy_now - initial_egg))
                approach_est_proxy_error = float(np.linalg.norm(proxy_now - plan["approach_target"]))

            if next_tactile["contact_present"]:
                phase_contact_steps += 1
                contact_acquired = True
                if first_contact_phase == "none":
                    first_contact_phase = phase_name
            if next_tactile["grip_stable"]:
                phase_stable_steps += 1
                if phase_name in {"gentle_close_thumb", "contact_settle"}:
                    grip_stable_before_lift = True
            if int(next_tactile.get("egg_floor_contact_count", 0)) > 0:
                phase_floor_steps += 1
            phase_max_slip = max(phase_max_slip, float(next_tactile["slip_score"]))
            phase_max_crush = max(phase_max_crush, float(next_tactile["crush_risk"]))
            phase_max_pen = max(phase_max_pen, float(next_tactile.get("max_penetration", 0.0)))
            max_slip = max(max_slip, phase_max_slip)
            max_crush = max(max_crush, phase_max_crush)
            max_penetration = max(max_penetration, phase_max_pen)
            if phase_name == "hold":
                hold_steps += 1
                hold_stable_steps += int(bool(next_tactile["grip_stable"]))
                hold_max_slip = max(hold_max_slip, float(next_tactile["slip_score"]))

            rows["obs"].append(obs)
            rows["actions"].append(behavior_action)
            rows["expert_actions"].append(expert_action)
            rows["next_obs"].append(next_obs)
            rows["rewards"].append(reward_from_state(next_tactile, lift_height))
            rows["dones"].append(False)
            rows["successes"].append(False)
            rows["failures"].append(False)
            rows["terminal_reason_ids"].append(reason_code("running"))
            rows["episode_ids"].append(int(episode_id))
            rows["step_ids"].append(int(step_count))
            rows["phase_ids"].append(int(phase_index))
            rows["phase_step_ids"].append(int(local_step))
            rows["vision_pose_estimates"].append(vision["object_pose_xyz_est"])
            rows["vision_scalars"].append(vision_scalars(vision))
            rows["tactile_scalars"].append(tactile_scalars(next_tactile))
            rows["tactile_region_masks"].append(tactile_region_mask(next_tactile))
            rows["gt_object_positions"].append(egg_now)
            rows["gt_object_lift_heights"].append(lift_height)
            rows["initial_object_positions"].append(initial_egg)
            rows["initial_qpos"].append(initial_qpos)
            rows["initial_qvel"].append(initial_qvel)
            rows["initial_ctrl"].append(initial_ctrl)
            rows["trial_ids"].append(int(args.trial_names.index(trial.name)))
            rows["profile_ids"].append(int(args.profile_names.index(profile.name)))
            step_count += 1
        phase_summaries.append(
            {
                "phase": phase_name,
                "start_step": int(phase_start_step),
                "end_step": int(step_count),
                "contact_steps": int(phase_contact_steps),
                "stable_steps": int(phase_stable_steps),
                "floor_contact_steps": int(phase_floor_steps),
                "max_slip_score": float(phase_max_slip),
                "max_crush_risk": float(phase_max_crush),
                "max_penetration_m": float(phase_max_pen),
            }
        )

    final_tactile = tactile_sensor.sample(data)
    final_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    final_contact = sweep.contact_summary(model, data, mujoco)
    hold_duration_s = float(hold_steps) * float(model.opt.timestep)
    hold_stable_fraction = float(hold_stable_steps / max(1, hold_steps))
    finite = bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all())
    summary = {
        "vision_accepted": bool(vision_accepted),
        "ik_approach_dxy_m": float(plan["approach_solution"]["dxy"]),
        "ik_approach_dz_m": float(plan["approach_solution"]["dz"]),
        "ik_lift_dxy_m": float(plan["lift_solution"]["dxy"]),
        "ik_lift_dz_m": float(plan["lift_solution"]["dz"]),
        "approach_true_proxy_error_m": float(approach_true_proxy_error),
        "approach_est_proxy_error_m": float(approach_est_proxy_error),
        "contact_acquired": bool(contact_acquired),
        "grip_stable_before_lift": bool(grip_stable_before_lift),
        "first_contact_phase": first_contact_phase,
        "final_lift_height_m": float(final_egg[2] - initial_egg[2]),
        "hold_duration_s": float(hold_duration_s),
        "hold_stable_fraction": float(hold_stable_fraction),
        "hold_max_slip_score": float(hold_max_slip),
        "hold_final_slip_score": float(final_tactile["slip_score"]),
        "max_slip_score": float(max_slip),
        "max_crush_risk": float(max_crush),
        "max_penetration_m": float(max_penetration),
        "final_floor_contacts": int(final_contact["egg_floor_contact_count"]),
        "finite_state": bool(finite),
        "total_steps": int(total_steps),
    }
    reasons = expert_failure_reasons(summary, args, thresholds)
    success = len(reasons) == 0
    terminal_reason = "success_gentle_grasp_hold" if success else reasons[0]
    rows["dones"][-1] = True
    rows["successes"][-1] = bool(success)
    rows["failures"][-1] = not bool(success)
    rows["terminal_reason_ids"][-1] = reason_code(terminal_reason)
    rows["rewards"][-1] = reward_from_state(final_tactile, summary["final_lift_height_m"], final_success=success, final_failure=not success)
    return {
        "episode_id": int(episode_id),
        "trial": trial,
        "profile": profile,
        "initial_egg": initial_egg,
        "egg_position_command": egg_position,
        "vision": vision,
        "step_count": int(step_count),
        "terminal_reason": terminal_reason,
        "success": bool(success),
        "failure_reasons": reasons,
        "risk_flags": [
            flag
            for flag, enabled in {
                "early_contact_in_approach": first_contact_phase == "approach",
                "transient_nonhold_slip": any(
                    phase["max_slip_score"] > thresholds.success_max_slip_score
                    for phase in phase_summaries
                    if phase["phase"] != "hold"
                ),
            }.items()
            if enabled
        ],
        "summary": summary,
        "phase_summaries": phase_summaries,
        "rows": rows,
        "phase_name_table": phase_names,
    }


def write_dataset(dataset_path: Path, episodes: list[dict[str, Any]], model, mujoco, args) -> None:
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    joint_names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i) or f"joint_{i}" for i in range(model.njnt)]
    actuator_names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) or f"actuator_{i}" for i in range(model.nu)]
    np.savez_compressed(
        dataset_path,
        obs=concatenate_rows(episodes, "obs", np.float64),
        actions=concatenate_rows(episodes, "actions", np.float64),
        expert_actions=concatenate_rows(episodes, "expert_actions", np.float64),
        next_obs=concatenate_rows(episodes, "next_obs", np.float64),
        rewards=concatenate_rows(episodes, "rewards", np.float64),
        dones=concatenate_rows(episodes, "dones", np.bool_),
        successes=concatenate_rows(episodes, "successes", np.bool_),
        failures=concatenate_rows(episodes, "failures", np.bool_),
        terminal_reason_ids=concatenate_rows(episodes, "terminal_reason_ids", np.int32),
        episode_ids=concatenate_rows(episodes, "episode_ids", np.int32),
        step_ids=concatenate_rows(episodes, "step_ids", np.int32),
        phase_ids=concatenate_rows(episodes, "phase_ids", np.int32),
        phase_step_ids=concatenate_rows(episodes, "phase_step_ids", np.int32),
        vision_pose_estimates=concatenate_rows(episodes, "vision_pose_estimates", np.float64),
        vision_scalars=concatenate_rows(episodes, "vision_scalars", np.float64),
        tactile_scalars=concatenate_rows(episodes, "tactile_scalars", np.float64),
        tactile_region_masks=concatenate_rows(episodes, "tactile_region_masks", np.float64),
        gt_object_positions=concatenate_rows(episodes, "gt_object_positions", np.float64),
        gt_object_lift_heights=concatenate_rows(episodes, "gt_object_lift_heights", np.float64),
        initial_object_positions=concatenate_rows(episodes, "initial_object_positions", np.float64),
        initial_qpos=concatenate_rows(episodes, "initial_qpos", np.float64),
        initial_qvel=concatenate_rows(episodes, "initial_qvel", np.float64),
        initial_ctrl=concatenate_rows(episodes, "initial_ctrl", np.float64),
        trial_ids=concatenate_rows(episodes, "trial_ids", np.int32),
        profile_ids=concatenate_rows(episodes, "profile_ids", np.int32),
        joint_names=np.asarray(joint_names, dtype=str),
        actuator_names=np.asarray(actuator_names, dtype=str),
        stage3_phase_table=np.asarray(PHASES, dtype=str),
        expert_phase_table=np.asarray(episodes[0]["phase_name_table"], dtype=str),
        terminal_reason_table=np.asarray(TERMINAL_REASONS, dtype=str),
        trial_name_table=np.asarray(args.trial_names, dtype=str),
        profile_name_table=np.asarray(args.profile_names, dtype=str),
        task_name=np.asarray([TASK_NAME], dtype=str),
        contract_version=np.asarray([TASK_CONTRACT_VERSION], dtype=str),
        dataset_version=np.asarray([DATASET_VERSION], dtype=str),
        scene=np.asarray([str(Path(args.scene).resolve())], dtype=str),
        nq=np.asarray([model.nq], dtype=np.int32),
        nv=np.asarray([model.nv], dtype=np.int32),
        nu=np.asarray([model.nu], dtype=np.int32),
        contract_json=np.asarray([json.dumps(json_ready(build_contract(Path(args.scene))), ensure_ascii=False)], dtype=str),
        collection_args_json=np.asarray([json.dumps(json_ready(vars(args)), ensure_ascii=False)], dtype=str),
    )


def summarize_payload(dataset_path: Path, episodes: list[dict[str, Any]], model, args) -> dict[str, Any]:
    obs = concatenate_rows(episodes, "obs", np.float64)
    actions = concatenate_rows(episodes, "actions", np.float64)
    successes = [bool(ep["success"]) for ep in episodes]
    terminal_counts: dict[str, int] = {}
    risk_counts: dict[str, int] = {}
    for ep in episodes:
        terminal_counts[ep["terminal_reason"]] = terminal_counts.get(ep["terminal_reason"], 0) + 1
        for risk in ep["risk_flags"]:
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
    final_lifts = np.asarray([ep["summary"]["final_lift_height_m"] for ep in episodes], dtype=np.float64)
    hold_slips = np.asarray([ep["summary"]["hold_max_slip_score"] for ep in episodes], dtype=np.float64)
    final_slips = np.asarray([ep["summary"]["hold_final_slip_score"] for ep in episodes], dtype=np.float64)
    crush = np.asarray([ep["summary"]["max_crush_risk"] for ep in episodes], dtype=np.float64)
    pen = np.asarray([ep["summary"]["max_penetration_m"] for ep in episodes], dtype=np.float64)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task_name": TASK_NAME,
        "contract_version": TASK_CONTRACT_VERSION,
        "dataset_version": DATASET_VERSION,
        "scene": str(Path(args.scene).resolve()),
        "dataset": str(dataset_path),
        "episodes": len(episodes),
        "total_rows": int(obs.shape[0]),
        "obs_shape": list(obs.shape),
        "actions_shape": list(actions.shape),
        "success_count": int(sum(successes)),
        "terminal_reason_counts": terminal_counts,
        "risk_flag_counts": risk_counts,
        "final_lift_height_m_mean": float(np.mean(final_lifts)),
        "final_lift_height_m_min": float(np.min(final_lifts)),
        "hold_max_slip_score_max": float(np.max(hold_slips)),
        "hold_final_slip_score_max": float(np.max(final_slips)),
        "max_crush_risk_max": float(np.max(crush)),
        "max_penetration_m_max": float(np.max(pen)),
        "profiles": [asdict(profile) for profile in PROFILES if profile.name in args.profile_names],
        "trial_names": args.trial_names,
        "training_ready": False,
        "replay_qa_required": True,
        "bc_target_field": "expert_actions",
        "policy_input_field": "obs",
        "episode_summaries": [
            {
                "episode_id": ep["episode_id"],
                "trial": ep["trial"].name,
                "profile": ep["profile"].name,
                "step_count": ep["step_count"],
                "success": ep["success"],
                "terminal_reason": ep["terminal_reason"],
                "failure_reasons": ep["failure_reasons"],
                "risk_flags": ep["risk_flags"],
                "vision": {
                    "confidence": ep["vision"]["confidence"],
                    "mask_pixels": ep["vision"]["mask_pixels"],
                    "position_est": ep["vision"]["object_pose_xyz_est"],
                },
                "summary": ep["summary"],
                "phase_summaries": ep["phase_summaries"],
            }
            for ep in episodes
        ],
        "notes": [
            "Stage3 dataset V0 is scripted expert data for the virtual-vision + tactile/slip learning track.",
            "`obs` is the Stage3 sensor abstraction vector; ground-truth arrays are logging/eval only.",
            "Train only after replay QA passes.",
        ],
    }


def write_report(payload: dict[str, Any], report_path: Path, metadata_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Stage3 Sensor Fusion Expert Dataset V0 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Task: `{payload['task_name']}`\n",
        f"- Contract: `{payload['contract_version']}`\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Episodes: `{payload['episodes']}`\n",
        f"- Total rows: `{payload['total_rows']}`\n",
        f"- Obs shape: `{payload['obs_shape']}`\n",
        f"- Actions shape: `{payload['actions_shape']}`\n",
        f"- Success count: `{payload['success_count']} / {payload['episodes']}`\n",
        f"- Terminal reasons: `{payload['terminal_reason_counts']}`\n",
        f"- Risk flags: `{payload['risk_flag_counts']}`\n",
        f"- Mean final lift: `{payload['final_lift_height_m_mean']:.6f} m`\n",
        f"- Min final lift: `{payload['final_lift_height_m_min']:.6f} m`\n",
        f"- Max hold slip: `{payload['hold_max_slip_score_max']:.3f}`\n",
        f"- Max final hold slip: `{payload['hold_final_slip_score_max']:.3f}`\n",
        f"- Max crush risk: `{payload['max_crush_risk_max']:.3f}`\n",
        f"- Max penetration: `{payload['max_penetration_m_max']:.6f} m`\n",
        f"- Training ready: **No, replay QA required first**\n\n",
        "## Episode Summary\n\n",
        "| ep | trial | profile | rows | success | terminal | lift m | hold slip | final slip | crush | pen m | risks |\n",
        "|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|\n",
    ]
    for ep in payload["episode_summaries"]:
        s = ep["summary"]
        lines.append(
            f"| {ep['episode_id']} | {ep['trial']} | {ep['profile']} | {ep['step_count']} | {int(ep['success'])} | "
            f"{ep['terminal_reason']} | {s['final_lift_height_m']:.5f} | {s['hold_max_slip_score']:.3f} | "
            f"{s['hold_final_slip_score']:.3f} | {s['max_crush_risk']:.3f} | {s['max_penetration_m']:.6f} | "
            f"`{ep['risk_flags']}` |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This dataset is the first Stage3 learning-track data source.\n",
            "- It records sensor-abstraction observations from virtual vision and MuJoCo contact-derived tactile/slip.\n",
            "- Ground-truth object positions are present for evaluation and replay QA only.\n",
            "- The known Stage3.5 risks are expected to appear: early approach contact and transient non-hold slip.\n\n",
            "## Next Gate\n\n",
            "Run replay QA before any BC or residual-policy training:\n\n",
            "```powershell\n",
            "python .\\simulations\\models\\arm_hand_stage1_export\\replay_stage3_sensor_fusion_dataset.py\n",
            "```\n",
        ]
    )
    report_path.write_text("".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect Stage3 sensor-fusion expert dataset V0.")
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--profiles", default="clean_nominal")
    parser.add_argument("--seed", type=int, default=80)
    parser.add_argument("--random-offset-std", type=float, default=0.0)
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--min-vision-confidence", type=float, default=0.55)
    parser.add_argument("--functional-hit-threshold", type=float, default=0.015)
    parser.add_argument("--max-ik-dxy", type=float, default=0.006)
    parser.add_argument("--max-ik-dz", type=float, default=0.006)
    parser.add_argument("--min-hold-stable-fraction", type=float, default=0.80)
    parser.add_argument("--approach-steps", type=int, default=220)
    parser.add_argument("--hand-steps", type=int, default=140)
    parser.add_argument("--close-fingers-steps", type=int, default=180)
    parser.add_argument("--close-thumb-steps", type=int, default=180)
    parser.add_argument("--contact-settle-steps", type=int, default=180)
    parser.add_argument("--lift-steps", type=int, default=700)
    parser.add_argument("--hold-steps", type=int, default=1500)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    args.profile_names = [profile.name for profile in parse_profiles(args.profiles)]
    args.trial_names = [trial.name for trial in sweep.trial_configs()]
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(Path(args.scene).resolve()))
    profiles = parse_profiles(args.profiles)
    trials = sweep.trial_configs()
    episodes: list[dict[str, Any]] = []
    for episode_id in range(int(args.episodes)):
        profile = profiles[episode_id % len(profiles)]
        trial = trials[episode_id % len(trials)]
        ep = collect_episode(model, mujoco, episode_id, trial, profile, args)
        episodes.append(ep)
        print(
            f"ep={episode_id:03d} trial={trial.name} profile={profile.name} "
            f"success={ep['success']} rows={ep['step_count']} lift={ep['summary']['final_lift_height_m']:.4f} "
            f"risks={ep['risk_flags']}"
        )
    write_dataset(Path(args.dataset).resolve(), episodes, model, mujoco, args)
    payload = summarize_payload(Path(args.dataset).resolve(), episodes, model, args)
    write_report(payload, Path(args.report), Path(args.metadata))
    print(f"Dataset status: {payload['success_count']}/{payload['episodes']} success")
    print(f"Saved dataset: {Path(args.dataset).resolve()}")
    print(f"Saved report: {Path(args.report)}")
    print(f"Saved metadata: {Path(args.metadata)}")
    return 0 if payload["success_count"] == payload["episodes"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
