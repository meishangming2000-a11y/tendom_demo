#!/usr/bin/env python3
"""Evaluate Stage3 pinch-style grasp candidates.

This is a MuJoCo-only Stage3 branch. It keeps virtual-camera localization and
synthetic tactile/slip sensing, but replaces the learned full-hand closure with
scripted pinch candidates such as thumb+index or thumb+index+middle.

The purpose is not a tiny one-off probe: each candidate is run over multiple
trials, scored with vision-assisted lift checks plus tactile pinch-contact
criteria, and written to a report for follow-up repair.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import zlib
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, Stage3Thresholds


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import collect_stage3_sensor_fusion_expert_dataset_v0 as collect
import run_stage3_visual_guided_grasp_sweep as sweep
from eval_stage3_tactile_phase_gate_v0 import gate_condition_reasons, record_phase_metric
from mujoco_egg_pose_sensor import EggPoseSensorConfig, MujocoEggPoseSensor
from mujoco_tactile_slip_sensor import MujocoTactileSlipSensor


DEFAULT_REPORT = DOCS / "stage3_pinch_grasp_v0_eval_report.md"
DEFAULT_METADATA = META / "stage3_pinch_grasp_v0_eval.json"
DEFAULT_DEBUG_DIR = DOCS / "visual_checks_stage3_pinch_grasp_v0"

ACTIVE_FINGER_REGIONS = {"index", "middle"}


@dataclass(frozen=True)
class PinchCandidate:
    name: str
    active_fingers: tuple[str, ...]
    thumb_cmc_abd: float
    thumb_cmc: float
    thumb_mcp: float
    thumb_ip: float
    active_mcp_flex: float
    active_mcp_abd: float
    active_pip: float
    active_dip: float
    inactive_scale: float
    approach_z_bias_delta: float = 0.0
    lift_delta_scale: float = 1.0


PINCH_CANDIDATES: dict[str, PinchCandidate] = {
    "thumb_index_light": PinchCandidate(
        name="thumb_index_light",
        active_fingers=("index",),
        thumb_cmc_abd=-0.32,
        thumb_cmc=0.00,
        thumb_mcp=0.28,
        thumb_ip=-0.28,
        active_mcp_flex=-0.055,
        active_mcp_abd=-0.62,
        active_pip=-0.78,
        active_dip=-0.38,
        inactive_scale=0.25,
    ),
    "thumb_index_middle": PinchCandidate(
        name="thumb_index_middle",
        active_fingers=("index", "middle"),
        thumb_cmc_abd=-0.34,
        thumb_cmc=0.00,
        thumb_mcp=0.30,
        thumb_ip=-0.30,
        active_mcp_flex=-0.060,
        active_mcp_abd=-0.62,
        active_pip=-0.84,
        active_dip=-0.42,
        inactive_scale=0.20,
    ),
    "thumb_index_middle_strong": PinchCandidate(
        name="thumb_index_middle_strong",
        active_fingers=("index", "middle"),
        thumb_cmc_abd=-0.38,
        thumb_cmc=0.02,
        thumb_mcp=0.36,
        thumb_ip=-0.36,
        active_mcp_flex=-0.075,
        active_mcp_abd=-0.70,
        active_pip=-0.98,
        active_dip=-0.52,
        inactive_scale=0.15,
        approach_z_bias_delta=-0.002,
    ),
    "tripod_support": PinchCandidate(
        name="tripod_support",
        active_fingers=("index", "middle", "ring"),
        thumb_cmc_abd=-0.36,
        thumb_cmc=0.02,
        thumb_mcp=0.34,
        thumb_ip=-0.34,
        active_mcp_flex=-0.070,
        active_mcp_abd=-0.66,
        active_pip=-0.90,
        active_dip=-0.46,
        inactive_scale=0.18,
    ),
}


def selected_candidates(spec: str) -> list[PinchCandidate]:
    if spec.strip().lower() in {"all", "*"}:
        return list(PINCH_CANDIDATES.values())
    names = [name.strip() for name in spec.split(",") if name.strip()]
    out = []
    for name in names:
        if name not in PINCH_CANDIDATES:
            raise ValueError(f"Unknown pinch candidate {name!r}; choose from {sorted(PINCH_CANDIDATES)}")
        out.append(PINCH_CANDIDATES[name])
    return out


def candidate_from_config(path: Path) -> PinchCandidate:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cfg = payload.get("selected_candidate", payload)
    required = {
        "name",
        "active_fingers",
        "thumb_cmc_abd",
        "thumb_cmc",
        "thumb_mcp",
        "thumb_ip",
        "active_mcp_flex",
        "active_mcp_abd",
        "active_pip",
        "active_dip",
        "inactive_scale",
    }
    missing = sorted(required - set(cfg))
    if missing:
        raise ValueError(f"Candidate config {path} is missing fields: {missing}")
    return PinchCandidate(
        name=str(cfg["name"]),
        active_fingers=tuple(str(x) for x in cfg["active_fingers"]),
        thumb_cmc_abd=float(cfg["thumb_cmc_abd"]),
        thumb_cmc=float(cfg["thumb_cmc"]),
        thumb_mcp=float(cfg["thumb_mcp"]),
        thumb_ip=float(cfg["thumb_ip"]),
        active_mcp_flex=float(cfg["active_mcp_flex"]),
        active_mcp_abd=float(cfg["active_mcp_abd"]),
        active_pip=float(cfg["active_pip"]),
        active_dip=float(cfg["active_dip"]),
        inactive_scale=float(cfg["inactive_scale"]),
        approach_z_bias_delta=float(cfg.get("approach_z_bias_delta", 0.0)),
        lift_delta_scale=float(cfg.get("lift_delta_scale", 1.0)),
    )


def finger_joint_targets(
    *,
    candidate: PinchCandidate,
    finger: str,
    preshape: dict[str, float],
) -> dict[str, float]:
    names = {
        "mcp_flex": f"{finger}_mcp_flex_joint",
        "mcp_abd": f"{finger}_mcp_abd_joint",
        "pip": f"{finger}_pip_joint",
        "dip": f"{finger}_dip_joint",
    }
    if finger in candidate.active_fingers:
        return {
            names["mcp_flex"]: candidate.active_mcp_flex,
            names["mcp_abd"]: candidate.active_mcp_abd,
            names["pip"]: candidate.active_pip,
            names["dip"]: candidate.active_dip,
        }
    scale = float(candidate.inactive_scale)
    return {
        joint_name: float(preshape.get(joint_name, 0.0)) * scale
        for joint_name in names.values()
    }


def pinch_hand_targets(candidate: PinchCandidate) -> dict[str, float]:
    targets: dict[str, float] = {}
    preshape = dict(sweep.base.PRESHAPE_TARGETS)
    for finger in ("index", "middle", "ring", "little"):
        targets.update(finger_joint_targets(candidate=candidate, finger=finger, preshape=preshape))
    targets.update(
        {
            "thumb_cmc_abd_joint": float(candidate.thumb_cmc_abd),
            "thumb_cmc_joint": float(candidate.thumb_cmc),
            "thumb_mcp_joint": float(candidate.thumb_mcp),
            "thumb_ip_joint": float(candidate.thumb_ip),
        }
    )
    return targets


def selected_trial(name: str) -> sweep.TrialConfig:
    for trial in sweep.trial_configs():
        if trial.name == name:
            return trial
    raise ValueError(f"Unknown trial {name!r}; choose from {[trial.name for trial in sweep.trial_configs()]}")


def accepted_estimate(estimate: dict[str, Any], min_confidence: float) -> bool:
    return estimate.get("status") == "ok" and float(estimate.get("confidence", 0.0)) >= float(min_confidence)


def acquire_vision(
    model,
    data,
    mujoco,
    *,
    camera_name: str,
    width: int,
    height: int,
    min_confidence: float,
    debug_dir: Path | None,
    label: str,
) -> dict[str, Any]:
    sensor = MujocoEggPoseSensor(
        model,
        mujoco,
        EggPoseSensorConfig(camera_name=camera_name, width=int(width), height=int(height)),
    )
    estimate = sensor.estimate(data, debug_dir=debug_dir, label=label)
    estimate["accepted"] = accepted_estimate(estimate, min_confidence)
    return estimate


def best_final_vision(
    model,
    data,
    mujoco,
    *,
    cameras: list[str],
    width: int,
    height: int,
    min_confidence: float,
    debug_dir: Path | None,
    label: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    estimates = []
    for camera_name in cameras:
        estimate = acquire_vision(
            model,
            data,
            mujoco,
            camera_name=camera_name,
            width=width,
            height=height,
            min_confidence=min_confidence,
            debug_dir=debug_dir,
            label=f"{label}_{camera_name}",
        )
        estimates.append(estimate)
    accepted = [item for item in estimates if bool(item.get("accepted"))]
    if accepted:
        accepted.sort(key=lambda item: float(item.get("confidence", 0.0)), reverse=True)
        return accepted[0], estimates
    estimates.sort(key=lambda item: float(item.get("confidence", 0.0)), reverse=True)
    return estimates[0], estimates


def build_pinch_plan(
    model,
    data,
    mujoco,
    *,
    trial: sweep.TrialConfig,
    candidate: PinchCandidate,
    egg_position: np.ndarray,
    vision_estimate: dict[str, Any],
    args,
) -> dict[str, Any]:
    target_position = np.asarray(vision_estimate["position_world_est"], dtype=np.float64).copy()
    grasp_local = sweep.DEFAULT_GRASP_LOCAL.copy()
    solver = sweep.ArmProxyIkSolver(model, mujoco, grasp_local)
    approach_target = target_position.copy()
    approach_target[2] += float(trial.grasp_z_bias_m) + float(candidate.approach_z_bias_delta)
    lift_target = approach_target.copy()
    lift_target[2] += float(trial.lift_delta_m) * float(candidate.lift_delta_scale)
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

    pinch_close = {**approach_arm, **pinch_hand_targets(candidate)}
    pinch_preshape = {**approach_arm, **sweep.base.PRESHAPE_TARGETS}
    pinch_lift = {**lift_arm, **pinch_hand_targets(candidate)}
    phases = [
        ("approach", pre_arm, approach_arm, int(args.approach_steps)),
        ("preshape", approach_arm, pinch_preshape, int(args.hand_steps)),
        ("pinch_close", pinch_preshape, pinch_close, int(args.pinch_close_steps)),
        ("contact_settle", pinch_close, pinch_close, int(args.max_contact_settle_steps)),
        ("slow_lift", pinch_close, pinch_lift, int(args.lift_steps)),
        ("hold", pinch_lift, pinch_lift, int(args.hold_steps)),
    ]
    return {
        "phases": phases,
        "actuator_names": actuator_names,
        "grasp_local": grasp_local,
        "approach_target": approach_target,
        "lift_target": lift_target,
        "approach_solution": approach_solution,
        "lift_solution": lift_solution,
    }


def pinch_contact_ok(tactile: dict[str, Any], candidate: PinchCandidate) -> bool:
    regions = set(str(region) for region in tactile.get("contact_regions", []))
    active = set(candidate.active_fingers)
    return "thumb" in regions and bool(regions.intersection(active))


def pinch_purity_score(tactile: dict[str, Any], candidate: PinchCandidate) -> float:
    counts = {str(k): int(v) for k, v in tactile.get("egg_contact_region_counts", {}).items()}
    if not counts:
        return 0.0
    desired = {"thumb", *candidate.active_fingers}
    desired_count = sum(count for region, count in counts.items() if region in desired)
    hand_count = sum(count for region, count in counts.items() if region not in {"support", "floor", "arm", "unknown"})
    return float(desired_count / max(1, hand_count))


def classify_failure_reasons(summary: dict[str, Any], args, thresholds: Stage3Thresholds) -> list[str]:
    reasons: list[str] = []
    if not bool(summary.get("initial_vision_accepted", False)):
        reasons.append("initial_vision_failed")
    if not bool(summary.get("final_vision_accepted", False)):
        reasons.append("final_vision_failed_or_occluded")
    if float(summary.get("vision_lift_height_m", -math.inf)) < float(args.min_vision_lift_height):
        reasons.append("vision_lift_too_small")
    if float(summary.get("true_lift_height_m", -math.inf)) < float(thresholds.success_lift_height_m):
        reasons.append("true_lift_too_small")
    if not bool(summary.get("pinch_contact_before_lift", False)):
        reasons.append("no_thumb_finger_pinch_before_lift")
    if float(summary.get("hold_pinch_fraction", 0.0)) < float(args.min_hold_pinch_fraction):
        reasons.append("pinch_not_maintained_in_hold")
    if float(summary.get("hold_stable_fraction", 0.0)) < float(args.min_hold_stable_fraction):
        reasons.append("hold_tactile_unstable")
    if float(summary.get("hold_max_slip_score", math.inf)) > float(thresholds.success_max_slip_score):
        reasons.append("hold_slip_score_high")
    if float(summary.get("max_crush_risk", math.inf)) > float(thresholds.success_max_crush_risk):
        reasons.append("crush_risk_high")
    if float(summary.get("max_penetration_m", math.inf)) > float(thresholds.success_max_penetration_m):
        reasons.append("penetration_high")
    if int(summary.get("final_floor_contacts", 0)) > 0:
        reasons.append("egg_still_touching_floor")
    if not bool(summary.get("finite_state", False)):
        reasons.append("non_finite_state")
    return reasons


def run_pinch_episode(
    model,
    mujoco,
    *,
    candidate: PinchCandidate,
    trial: sweep.TrialConfig,
    episode_id: int,
    args,
) -> dict[str, Any]:
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    base_egg_position = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
    stable_candidate_hash = int(zlib.adler32(candidate.name.encode("utf-8")) % 997)
    rng = np.random.default_rng(int(args.seed) + int(episode_id) * 1009 + stable_candidate_hash)
    if float(args.random_offset_std) > 0.0:
        egg_position = egg_position + rng.normal(0.0, float(args.random_offset_std), size=3)
        egg_position[2] = base_egg_position[2] + np.asarray(trial.offset_xyz, dtype=np.float64)[2]
    sweep.reset_episode(model, data, mujoco, egg_position)

    debug_dir = None
    if bool(args.render_vision_debug):
        debug_dir = Path(args.debug_dir) / candidate.name / f"{episode_id:03d}_{trial.name}"
    initial_vision = acquire_vision(
        model,
        data,
        mujoco,
        camera_name=str(args.camera),
        width=int(args.width),
        height=int(args.height),
        min_confidence=float(args.min_vision_confidence),
        debug_dir=debug_dir,
        label="initial",
    )
    if not bool(initial_vision.get("accepted")):
        return {
            "episode_id": int(episode_id),
            "candidate": candidate.name,
            "trial": trial.name,
            "status": "FAIL",
            "success": False,
            "terminal_reason": "initial_vision_failed",
            "failure_reasons": ["initial_vision_failed"],
            "summary": {
                "initial_vision_accepted": False,
                "initial_vision_status": initial_vision.get("status"),
                "initial_vision_confidence": float(initial_vision.get("confidence", 0.0)),
                "initial_vision_mask_pixels": int(initial_vision.get("mask_pixels", 0)),
            },
        }

    plan = build_pinch_plan(
        model,
        data,
        mujoco,
        trial=trial,
        candidate=candidate,
        egg_position=egg_position,
        vision_estimate=initial_vision,
        args=args,
    )
    thresholds = Stage3Thresholds()
    tactile_sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=thresholds)
    tactile_sensor.reset(data)
    initial_true_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    initial_vision_pos = np.asarray(initial_vision["position_world_est"], dtype=np.float64)
    vision = collect.make_vision_fields(initial_vision)

    contact_acquired = False
    pinch_contact_before_lift = False
    gate_stable_window = 0
    gate_release_reason = "not_reached"
    hold_steps = 0
    hold_stable_steps = 0
    hold_pinch_steps = 0
    hold_purity_sum = 0.0
    hold_max_slip = 0.0
    max_slip = 0.0
    max_crush = 0.0
    max_penetration = 0.0
    first_contact_phase = "none"
    phase_metrics: dict[str, dict[str, float]] = {}
    region_counts_total: Counter[str] = Counter()
    trace: list[dict[str, Any]] = []
    capture_sequence = bool(getattr(args, "capture_sequence", False))
    sequence_rows: dict[str, list[Any]] | None = None
    record_tactile_sensor: MujocoTactileSlipSensor | None = None
    current_record_tactile: dict[str, Any] | None = None
    if capture_sequence:
        record_tactile_sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=thresholds)
        record_tactile_sensor.reset(data)
        current_record_tactile = record_tactile_sensor.sample(data)
        sequence_rows = {
            "obs": [],
            "actions": [],
            "expert_actions": [],
            "next_obs": [],
            "rewards": [],
            "dones": [],
            "successes": [],
            "failures": [],
            "terminal_reasons": [],
            "step_ids": [],
            "phase_names": [],
            "phase_step_ids": [],
            "phase_progress": [],
            "nominal_progress": [],
            "control_progress": [],
            "learned_hand": [],
            "recovery_active": [],
            "lift_heights": [],
            "pinch_contact": [],
            "vision_pose_estimates": [],
            "vision_scalars": [],
            "tactile_scalars": [],
            "tactile_region_masks": [],
            "gt_object_positions": [],
            "gt_object_lift_heights": [],
        }
    step_count = 0
    contact_settle_steps_actual = 0
    approach_true_proxy_error = float("inf")

    gate_min_steps = max(0, int(args.min_contact_settle_steps))
    gate_max_steps = max(1, int(args.max_contact_settle_steps))
    if gate_max_steps < gate_min_steps:
        gate_max_steps = gate_min_steps

    for phase_name, start, end, steps in plan["phases"]:
        phase_steps = int(steps)
        if phase_name == "contact_settle":
            phase_steps = gate_max_steps
        local_step = 0
        while local_step < phase_steps:
            progress = local_step / max(1, phase_steps - 1)
            if sequence_rows is not None and current_record_tactile is not None:
                obs = collect.observation_vector(model, data, vision, current_record_tactile, phase_name=phase_name, progress=progress)
            targets = sweep.blend_targets(start, end, progress)
            action = collect.clip_action(
                model,
                sweep.actuator_targets(model, mujoco, plan["actuator_names"], targets),
            )
            data.ctrl[:] = action
            mujoco.mj_step(model, data)
            tactile = tactile_sensor.sample(data)
            record_phase_metric(phase_metrics, phase_name, tactile)
            region_counts_total.update({str(k): int(v) for k, v in tactile.get("egg_contact_region_counts", {}).items()})
            egg_now = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
            lift_height = float(egg_now[2] - initial_true_egg[2])
            if sequence_rows is not None and record_tactile_sensor is not None:
                record_tactile = record_tactile_sensor.sample(data)
                next_obs = collect.observation_vector(model, data, vision, record_tactile, phase_name=phase_name, progress=progress)
                sequence_rows["obs"].append(obs)
                sequence_rows["actions"].append(action)
                sequence_rows["expert_actions"].append(action)
                sequence_rows["next_obs"].append(next_obs)
                sequence_rows["rewards"].append(collect.reward_from_state(tactile, lift_height))
                sequence_rows["dones"].append(False)
                sequence_rows["successes"].append(False)
                sequence_rows["failures"].append(False)
                sequence_rows["terminal_reasons"].append("running")
                sequence_rows["step_ids"].append(int(step_count))
                sequence_rows["phase_names"].append(str(phase_name))
                sequence_rows["phase_step_ids"].append(int(local_step))
                sequence_rows["phase_progress"].append(float(progress))
                sequence_rows["nominal_progress"].append(float(progress))
                sequence_rows["control_progress"].append(float(progress))
                sequence_rows["learned_hand"].append(False)
                sequence_rows["recovery_active"].append(False)
                sequence_rows["lift_heights"].append(float(lift_height))
                sequence_rows["pinch_contact"].append(bool(pinch_contact_ok(tactile, candidate)))
                sequence_rows["vision_pose_estimates"].append(vision["object_pose_xyz_est"])
                sequence_rows["vision_scalars"].append(collect.vision_scalars(vision))
                sequence_rows["tactile_scalars"].append(collect.tactile_scalars(record_tactile))
                sequence_rows["tactile_region_masks"].append(collect.tactile_region_mask(record_tactile))
                sequence_rows["gt_object_positions"].append(egg_now)
                sequence_rows["gt_object_lift_heights"].append(float(lift_height))
                current_record_tactile = record_tactile

            if phase_name == "approach":
                proxy_now = sweep.proxy_position(model, data, mujoco, plan["grasp_local"])
                approach_true_proxy_error = float(np.linalg.norm(proxy_now - initial_true_egg))

            if tactile["contact_present"]:
                contact_acquired = True
                if first_contact_phase == "none":
                    first_contact_phase = phase_name
            if phase_name in {"pinch_close", "contact_settle"} and pinch_contact_ok(tactile, candidate):
                pinch_contact_before_lift = True

            if phase_name == "contact_settle":
                contact_settle_steps_actual += 1
                gate_reasons = gate_condition_reasons(tactile, args, thresholds)
                if gate_reasons:
                    gate_stable_window = 0
                else:
                    gate_stable_window += 1
                if contact_settle_steps_actual >= gate_min_steps and gate_stable_window >= int(args.settle_stable_window_steps):
                    gate_release_reason = "stable_window_met"
                elif contact_settle_steps_actual >= gate_max_steps:
                    gate_release_reason = "max_steps_reached_stable" if not gate_reasons else "max_steps_reached_unstable"

            if phase_name == "hold":
                hold_steps += 1
                hold_stable_steps += int(bool(tactile["grip_stable"]))
                hold_max_slip = max(hold_max_slip, float(tactile["slip_score"]))
                if pinch_contact_ok(tactile, candidate):
                    hold_pinch_steps += 1
                hold_purity_sum += pinch_purity_score(tactile, candidate)

            max_slip = max(max_slip, float(tactile["slip_score"]))
            max_crush = max(max_crush, float(tactile["crush_risk"]))
            max_penetration = max(max_penetration, float(tactile.get("max_penetration", 0.0)))

            if step_count % max(1, int(args.sample_every)) == 0:
                trace.append(
                    {
                        "step": int(step_count),
                        "phase": phase_name,
                        "progress": float(progress),
                        "true_lift_height_m": float(lift_height),
                        "contact": bool(tactile["contact_present"]),
                        "pinch_contact": bool(pinch_contact_ok(tactile, candidate)),
                        "regions": list(tactile.get("contact_regions", [])),
                        "slip": float(tactile["slip_score"]),
                        "stable": bool(tactile["grip_stable"]),
                        "crush": float(tactile["crush_risk"]),
                        "penetration": float(tactile.get("max_penetration", 0.0)),
                    }
                )

            local_step += 1
            step_count += 1
            if phase_name == "contact_settle" and gate_release_reason != "not_reached":
                break

    final_tactile = tactile_sensor.sample(data)
    final_true_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    final_contact = sweep.contact_summary(model, data, mujoco)
    final_cameras = [camera.strip() for camera in str(args.final_cameras).split(",") if camera.strip()]
    final_vision, final_vision_all = best_final_vision(
        model,
        data,
        mujoco,
        cameras=final_cameras,
        width=int(args.width),
        height=int(args.height),
        min_confidence=float(args.min_final_vision_confidence),
        debug_dir=debug_dir,
        label="final",
    )
    final_vision_pos = np.asarray(final_vision.get("position_world_est", [math.nan, math.nan, math.nan]), dtype=np.float64)
    vision_lift = float(final_vision_pos[2] - initial_vision_pos[2]) if bool(final_vision.get("accepted")) else float("nan")
    hold_stable_fraction = float(hold_stable_steps / max(1, hold_steps))
    hold_pinch_fraction = float(hold_pinch_steps / max(1, hold_steps))
    hold_purity_mean = float(hold_purity_sum / max(1, hold_steps))

    summary = {
        "initial_vision_accepted": bool(initial_vision.get("accepted")),
        "initial_vision_status": initial_vision.get("status"),
        "initial_vision_confidence": float(initial_vision.get("confidence", 0.0)),
        "initial_vision_mask_pixels": int(initial_vision.get("mask_pixels", 0)),
        "final_vision_accepted": bool(final_vision.get("accepted")),
        "final_vision_camera": final_vision.get("camera"),
        "final_vision_status": final_vision.get("status"),
        "final_vision_confidence": float(final_vision.get("confidence", 0.0)),
        "final_vision_mask_pixels": int(final_vision.get("mask_pixels", 0)),
        "vision_lift_height_m": float(vision_lift),
        "true_lift_height_m": float(final_true_egg[2] - initial_true_egg[2]),
        "vision_true_lift_error_m": float(abs(vision_lift - (final_true_egg[2] - initial_true_egg[2]))) if np.isfinite(vision_lift) else float("nan"),
        "approach_true_proxy_error_m": float(approach_true_proxy_error),
        "ik_approach_dxy_m": float(plan["approach_solution"]["dxy"]),
        "ik_approach_dz_m": float(plan["approach_solution"]["dz"]),
        "ik_lift_dxy_m": float(plan["lift_solution"]["dxy"]),
        "ik_lift_dz_m": float(plan["lift_solution"]["dz"]),
        "contact_acquired": bool(contact_acquired),
        "pinch_contact_before_lift": bool(pinch_contact_before_lift),
        "first_contact_phase": first_contact_phase,
        "contact_settle_steps_actual": int(contact_settle_steps_actual),
        "gate_release_reason": gate_release_reason,
        "gate_stable_window_at_release": int(gate_stable_window),
        "hold_stable_fraction": float(hold_stable_fraction),
        "hold_pinch_fraction": float(hold_pinch_fraction),
        "hold_pinch_purity_mean": float(hold_purity_mean),
        "hold_max_slip_score": float(hold_max_slip),
        "hold_final_slip_score": float(final_tactile["slip_score"]),
        "max_slip_score": float(max_slip),
        "max_crush_risk": float(max_crush),
        "max_penetration_m": float(max_penetration),
        "final_floor_contacts": int(final_contact["egg_floor_contact_count"]),
        "final_hand_contacts": int(final_contact["egg_hand_contact_count"]),
        "final_contact_regions": list(final_tactile.get("contact_regions", [])),
        "region_counts_total": dict(region_counts_total),
        "phase_metrics": phase_metrics,
        "finite_state": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "total_steps": int(step_count),
    }
    reasons = classify_failure_reasons(summary, args, thresholds)
    risks: list[str] = []
    if first_contact_phase == "approach":
        risks.append("early_contact_in_approach")
    if max_slip > thresholds.success_max_slip_score:
        risks.append("transient_slip_high")
    if hold_purity_mean < float(args.min_hold_pinch_purity):
        risks.append("low_pinch_purity")
    if not bool(final_vision.get("accepted")):
        risks.append("final_vision_occluded_or_low_confidence")
    success = len(reasons) == 0
    terminal_reason = "success_vision_confirmed_pinch_lift_hold" if success else (reasons[0] if reasons else "unknown")
    if sequence_rows is not None and sequence_rows["dones"]:
        sequence_rows["dones"][-1] = True
        sequence_rows["successes"][-1] = bool(success)
        sequence_rows["failures"][-1] = not bool(success)
        sequence_rows["terminal_reasons"][-1] = terminal_reason
        sequence_rows["rewards"][-1] = collect.reward_from_state(
            final_tactile,
            summary["true_lift_height_m"],
            final_success=bool(success),
            final_failure=not bool(success),
        )
    result = {
        "episode_id": int(episode_id),
        "candidate": candidate.name,
        "candidate_config": candidate.__dict__,
        "trial": trial.name,
        "status": "PASS" if success else "FAIL",
        "success": bool(success),
        "terminal_reason": terminal_reason,
        "failure_reasons": reasons,
        "risk_flags": risks,
        "summary": summary,
        "trace": trace,
        "initial_vision": initial_vision,
        "final_vision": final_vision,
        "final_vision_all": final_vision_all,
        "policy_scope": "scripted_arm_wrist_visual_guided_pinch_candidates_with_synthetic_tactile_success_check",
    }
    if sequence_rows is not None:
        result["sequence_rows"] = sequence_rows
    return result


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_candidate: dict[str, dict[str, Any]] = {}
    for candidate in sorted(set(str(row["candidate"]) for row in rows)):
        subset = [row for row in rows if row["candidate"] == candidate]
        by_candidate[candidate] = summarize_subset(subset)
    return {
        "status": "PASS" if all(row["success"] for row in rows) else ("PARTIAL" if any(row["success"] for row in rows) else "FAIL"),
        "episodes": int(len(rows)),
        "success_count": int(sum(1 for row in rows if row["success"])),
        "terminal_reason_counts": dict(Counter(str(row["terminal_reason"]) for row in rows)),
        "failure_reason_counts": dict(Counter(reason for row in rows for reason in row.get("failure_reasons", []))),
        "risk_flag_counts": dict(Counter(flag for row in rows for flag in row.get("risk_flags", []))),
        "by_candidate": by_candidate,
    }


def summarize_subset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "episodes": int(len(rows)),
        "success_count": int(sum(1 for row in rows if row["success"])),
        "terminal_reason_counts": dict(Counter(str(row["terminal_reason"]) for row in rows)),
        "failure_reason_counts": dict(Counter(reason for row in rows for reason in row.get("failure_reasons", []))),
        "risk_flag_counts": dict(Counter(flag for row in rows for flag in row.get("risk_flags", []))),
    }

    def values(key: str) -> np.ndarray:
        return np.asarray([row["summary"][key] for row in rows if "summary" in row and key in row["summary"]], dtype=np.float64)

    for key in [
        "vision_lift_height_m",
        "true_lift_height_m",
        "vision_true_lift_error_m",
        "hold_stable_fraction",
        "hold_pinch_fraction",
        "hold_pinch_purity_mean",
        "hold_max_slip_score",
        "max_slip_score",
        "max_crush_risk",
        "max_penetration_m",
        "approach_true_proxy_error_m",
        "contact_settle_steps_actual",
    ]:
        arr = values(key)
        arr = arr[np.isfinite(arr)]
        if arr.size:
            out[f"{key}_mean"] = float(np.mean(arr))
            out[f"{key}_min"] = float(np.min(arr))
            out[f"{key}_max"] = float(np.max(arr))
    return out


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = payload["summary"]
    lines = [
        "# Stage3 Pinch Grasp V0 Eval Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "这是 MuJoCo-only 的虚拟摄像机 + 合成触觉/滑移实验，不使用现实摄像头或真实硬件。\n\n",
        "目标是尽力实现 pinch-style grasp（捏持式抓取）：用拇指和少数手指把鸡蛋掐住、抬起并保持。\n\n",
        "## Success Criteria\n\n",
        "- 初始虚拟摄像机必须成功估计鸡蛋位置。\n",
        "- 最终虚拟摄像机必须再次看到鸡蛋，并估计出足够抬升高度。\n",
        "- MuJoCo 真值也记录为验证项，防止视觉估计误判。\n",
        "- 触觉接触必须包含 thumb + index/middle 等主动手指区域。\n",
        "- hold 阶段要维持足够的 pinch contact fraction、低滑移、低挤压和低穿透。\n\n",
        "## Summary\n\n",
        f"- Status: **{s['status']}**\n",
        f"- Episodes: `{s['episodes']}`\n",
        f"- Success count: `{s['success_count']} / {s['episodes']}`\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n",
        f"- Failure reasons: `{s['failure_reason_counts']}`\n",
        f"- Risk flags: `{s['risk_flag_counts']}`\n\n",
        "## Candidate Summary\n\n",
        "| candidate | success | vision lift mean | true lift mean | hold stable | hold pinch | purity | hold slip max | max slip max | failures |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|\n",
    ]
    for name, row in s["by_candidate"].items():
        lines.append(
            f"| {name} | {row['success_count']}/{row['episodes']} | "
            f"{row.get('vision_lift_height_m_mean', float('nan')):.5f} | "
            f"{row.get('true_lift_height_m_mean', float('nan')):.5f} | "
            f"{row.get('hold_stable_fraction_mean', float('nan')):.3f} | "
            f"{row.get('hold_pinch_fraction_mean', float('nan')):.3f} | "
            f"{row.get('hold_pinch_purity_mean_mean', float('nan')):.3f} | "
            f"{row.get('hold_max_slip_score_max', float('nan')):.3f} | "
            f"{row.get('max_slip_score_max', float('nan')):.3f} | "
            f"`{row['failure_reason_counts']}` |\n"
        )

    lines.extend(
        [
            "\n## Episode Results\n\n",
            "| ep | candidate | trial | status | vision lift | true lift | final cam | final conf | hold pinch | stable | hold slip | crush | pen | failure reasons |\n",
            "|---:|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---|\n",
        ]
    )
    for row in payload["results"]:
        r = row.get("summary", {})
        lines.append(
            f"| {row['episode_id']} | {row['candidate']} | {row['trial']} | {row['status']} | "
            f"{r.get('vision_lift_height_m', float('nan')):.5f} | "
            f"{r.get('true_lift_height_m', float('nan')):.5f} | "
            f"{r.get('final_vision_camera', 'n/a')} | "
            f"{r.get('final_vision_confidence', float('nan')):.3f} | "
            f"{r.get('hold_pinch_fraction', float('nan')):.3f} | "
            f"{r.get('hold_stable_fraction', float('nan')):.3f} | "
            f"{r.get('hold_max_slip_score', float('nan')):.3f} | "
            f"{r.get('max_crush_risk', float('nan')):.3f} | "
            f"{r.get('max_penetration_m', float('nan')):.6f} | "
            f"`{row.get('failure_reasons', [])}` |\n"
        )

    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- 如果某个 candidate 成功率为 0，但 vision lift 明显为正，说明可能是触觉 pinch 判据或 hold 稳定性不足。\n",
            "- 如果 final vision 经常失败，说明捏持后遮挡太强，需要换最终验收相机或调整手指姿态。\n",
            "- 如果 true lift 很低，说明抓法本身没有把鸡蛋带起来，下一轮应优先改接近姿态和 thumb/index 闭合目标。\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Stage3 visual-assisted pinch grasp candidates.")
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--debug-dir", type=Path, default=DEFAULT_DEBUG_DIR)
    parser.add_argument("--candidates", default="all")
    parser.add_argument("--candidate-config", type=Path, default=None)
    parser.add_argument("--episodes-per-candidate", type=int, default=3)
    parser.add_argument("--seed", type=int, default=230)
    parser.add_argument("--random-offset-std", type=float, default=0.0)
    parser.add_argument("--trial", default="cycle", help="Use a trial name or 'cycle'.")
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--final-cameras", default="stage3_egg_closeup,stage3_egg_overview")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--min-vision-confidence", type=float, default=0.55)
    parser.add_argument(
        "--min-final-vision-confidence",
        type=float,
        default=0.35,
        help="Final lift verification can be lower because the hand partially occludes the egg.",
    )
    parser.add_argument("--min-vision-lift-height", type=float, default=0.045)
    parser.add_argument("--min-hold-stable-fraction", type=float, default=0.60)
    parser.add_argument("--min-hold-pinch-fraction", type=float, default=0.55)
    parser.add_argument("--min-hold-pinch-purity", type=float, default=0.55)
    parser.add_argument("--approach-steps", type=int, default=320)
    parser.add_argument("--hand-steps", type=int, default=140)
    parser.add_argument("--pinch-close-steps", type=int, default=260)
    parser.add_argument("--min-contact-settle-steps", type=int, default=400)
    parser.add_argument("--max-contact-settle-steps", type=int, default=1000)
    parser.add_argument("--settle-stable-window-steps", type=int, default=120)
    parser.add_argument("--gate-slip-threshold", type=float, default=0.22)
    parser.add_argument("--gate-crush-threshold", type=float, default=0.35)
    parser.add_argument("--gate-penetration-threshold", type=float, default=0.004)
    parser.add_argument("--lift-steps", type=int, default=700)
    parser.add_argument("--hold-steps", type=int, default=900)
    parser.add_argument("--sample-every", type=int, default=200)
    parser.add_argument("--render-vision-debug", action="store_true")
    args = parser.parse_args()

    import mujoco

    model = mujoco.MjModel.from_xml_path(str(Path(args.scene).resolve()))
    all_trials = sweep.trial_configs()
    candidates = [candidate_from_config(Path(args.candidate_config))] if args.candidate_config else selected_candidates(str(args.candidates))
    results: list[dict[str, Any]] = []
    episode_id = 0
    for candidate in candidates:
        for local_episode in range(int(args.episodes_per_candidate)):
            if str(args.trial) == "cycle":
                trial = all_trials[local_episode % len(all_trials)]
            else:
                trial = selected_trial(str(args.trial))
            row = run_pinch_episode(model, mujoco, candidate=candidate, trial=trial, episode_id=episode_id, args=args)
            results.append(row)
            r = row.get("summary", {})
            print(
                f"ep={episode_id:03d} candidate={candidate.name} trial={trial.name} {row['status']} "
                f"reason={row['terminal_reason']} vision_lift={r.get('vision_lift_height_m', float('nan')):.4f} "
                f"true_lift={r.get('true_lift_height_m', float('nan')):.4f} "
                f"pinch={r.get('hold_pinch_fraction', float('nan')):.3f} "
                f"stable={r.get('hold_stable_fraction', float('nan')):.3f}"
            )
            episode_id += 1

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(Path(args.scene).resolve()),
        "policy_scope": "scripted_arm_wrist_visual_guided_pinch_candidates_with_synthetic_tactile_success_check",
        "candidates": [candidate.__dict__ for candidate in candidates],
        "success_criteria": {
            "min_vision_lift_height": float(args.min_vision_lift_height),
            "min_hold_stable_fraction": float(args.min_hold_stable_fraction),
            "min_hold_pinch_fraction": float(args.min_hold_pinch_fraction),
            "min_hold_pinch_purity": float(args.min_hold_pinch_purity),
            "final_cameras": [camera.strip() for camera in str(args.final_cameras).split(",") if camera.strip()],
            "min_initial_vision_confidence": float(args.min_vision_confidence),
            "min_final_vision_confidence": float(args.min_final_vision_confidence),
            "uses_visual_final_lift_check": True,
        },
        "args": vars(args),
        "summary": summarize(results),
        "results": results,
        "training_ready": False,
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(Path(args.report), json_ready(payload))
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
