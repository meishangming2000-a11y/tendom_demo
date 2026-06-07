#!/usr/bin/env python3
"""Closed-loop MuJoCo eval for the Stage3 ACT-lite chunk policy.

This evaluator is intentionally conservative. It can run the learned chunk
policy in two modes:

1. full_action: the model controls all 26 actuator targets.
2. scripted_arm_predicted_hand: the scripted visual-guided arm/wrist trajectory
   is kept, while the model controls the hand/finger actuator slice.

The second mode is the safer first gate because earlier Stage3 work showed
that monolithic full-action BC is brittle in approach/alignment phases.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import torch

from arm_hand_stage1_task_api import json_ready
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, Stage3Thresholds
from train_stage3_act_dp_baseline_v0 import ACTLiteChunkPolicy


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import collect_stage3_sensor_fusion_expert_dataset_v0 as collect
import eval_stage3_contact_transition_recovery_v0 as recovery
import eval_stage3_pinch_grasp_v0 as pinch
import run_stage3_visual_guided_grasp_sweep as sweep
from eval_stage3_tactile_phase_gate_v0 import gate_condition_reasons, record_phase_metric
from export_stage3_skill_act_dp_sequence_dataset_v0 import load_selected_pinch_candidate
from mujoco_egg_pose_sensor import EggPoseSensorConfig, MujocoEggPoseSensor
from mujoco_tactile_slip_sensor import MujocoTactileSlipSensor


DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_act_lite_chunk_policy_v0.pth"
DEFAULT_SELECTED_PINCH = META / "stage3_pinch_grasp_training_v0_selected.json"
DEFAULT_REPORT = DOCS / "stage3_act_lite_chunk_policy_v0_eval_report.md"
DEFAULT_METADATA = META / "stage3_act_lite_chunk_policy_v0_eval.json"

SKILL_ID_TO_INDEX = {
    "full_hand_gentle_grasp": 0,
    "thumb_index_middle_pinch": 1,
}


def load_chunk_policy(path: Path, device: torch.device) -> tuple[ACTLiteChunkPolicy, dict[str, Any]]:
    checkpoint = torch.load(Path(path).resolve(), map_location=device, weights_only=False)
    model = ACTLiteChunkPolicy(
        obs_dim=int(checkpoint["obs_dim"]),
        action_dim=int(checkpoint["action_dim"]),
        horizon=int(checkpoint["horizon"]),
        skill_count=int(checkpoint["skill_count"]),
        skill_embed_dim=int(checkpoint["skill_embed_dim"]),
        hidden_dim=int(checkpoint["hidden_dim"]),
        depth=int(checkpoint["depth"]),
        dropout=float(checkpoint.get("dropout", 0.0)),
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, checkpoint


def predict_chunk(policy: ACTLiteChunkPolicy, checkpoint: dict[str, Any], obs: np.ndarray, skill_index: int, device: torch.device) -> np.ndarray:
    obs_mean = np.asarray(checkpoint["obs_mean"], dtype=np.float32)
    obs_std = np.maximum(np.asarray(checkpoint["obs_std"], dtype=np.float32), 1e-6)
    action_mean = np.asarray(checkpoint["action_mean"], dtype=np.float32)
    action_std = np.maximum(np.asarray(checkpoint["action_std"], dtype=np.float32), 1e-6)
    with torch.no_grad():
        obs_t = torch.from_numpy(((np.asarray(obs, dtype=np.float32) - obs_mean) / obs_std)[None, :]).to(device)
        skill_t = torch.tensor([int(skill_index)], dtype=torch.long, device=device)
        pred = policy(obs_t, skill_t).detach().cpu().numpy()[0]
    chunk = pred.reshape(int(checkpoint["horizon"]), int(checkpoint["action_dim"]))
    return chunk * action_std.reshape(1, -1) + action_mean.reshape(1, -1)


def make_full_hand_args(args: argparse.Namespace) -> SimpleNamespace:
    return SimpleNamespace(
        seed=int(args.seed),
        random_offset_std=float(args.random_offset_std),
        camera=str(args.camera),
        width=int(args.width),
        height=int(args.height),
        min_vision_confidence=0.55,
        functional_hit_threshold=0.015,
        max_ik_dxy=0.006,
        max_ik_dz=0.006,
        min_hold_stable_fraction=0.80,
        approach_steps=320,
        hand_steps=140,
        close_fingers_steps=180,
        close_thumb_steps=180,
        contact_settle_steps=180,
        min_contact_settle_steps=2000,
        max_contact_settle_steps=2000,
        settle_stable_window_steps=300,
        gate_slip_threshold=0.18,
        gate_crush_threshold=0.35,
        gate_penetration_threshold=0.004,
        lift_steps=700,
        hold_steps=1500,
        sample_every=int(args.sample_every),
    )


def make_full_hand_fallback_args(args: argparse.Namespace) -> SimpleNamespace:
    return SimpleNamespace(
        seed=int(args.seed),
        random_offset_std=float(args.random_offset_std),
        camera=str(args.camera),
        width=int(args.width),
        height=int(args.height),
        min_vision_confidence=0.55,
        functional_hit_threshold=0.015,
        max_ik_dxy=0.006,
        max_ik_dz=0.006,
        min_hold_stable_fraction=0.80,
        action_smoothing=0.0,
        no_train_range_clip=False,
        sample_every=int(args.sample_every),
        approach_steps=320,
        hand_steps=140,
        close_fingers_steps=180,
        close_thumb_steps=180,
        contact_settle_steps=180,
        min_contact_settle_steps=2000,
        max_contact_settle_steps=2000,
        settle_stable_window_steps=300,
        gate_slip_threshold=0.18,
        gate_crush_threshold=0.35,
        gate_penetration_threshold=0.004,
        stop_approach_on_contact=False,
        min_approach_steps_before_contact_stop=90,
        approach_contact_stop_error_m=0.014,
        transition_gate_phases="slow_lift",
        transition_slip_threshold=float(args.full_hand_fallback_transition_slip_threshold),
        transition_crush_threshold=0.35,
        transition_penetration_threshold=0.004,
        max_transition_hold_steps_per_phase=int(args.full_hand_fallback_max_transition_hold_steps_per_phase),
        recovery_progress_drop=float(args.full_hand_fallback_recovery_progress_drop),
        recovery_stable_window_steps=int(args.full_hand_fallback_recovery_stable_window_steps),
        lift_steps=700,
        hold_steps=1500,
        capture_sequence=bool(getattr(args, "capture_sequence", False)),
    )


def make_pinch_args(args: argparse.Namespace) -> SimpleNamespace:
    return SimpleNamespace(
        seed=int(args.seed) + 20000,
        random_offset_std=float(args.random_offset_std),
        trial="cycle",
        camera=str(args.camera),
        final_cameras="stage3_egg_closeup,stage3_egg_overview",
        width=int(args.width),
        height=int(args.height),
        min_vision_confidence=0.55,
        min_final_vision_confidence=0.35,
        min_vision_lift_height=0.045,
        min_hold_stable_fraction=0.60,
        min_hold_pinch_fraction=0.55,
        min_hold_pinch_purity=0.55,
        approach_steps=320,
        hand_steps=140,
        pinch_close_steps=260,
        min_contact_settle_steps=400,
        max_contact_settle_steps=1000,
        settle_stable_window_steps=120,
        gate_slip_threshold=0.22,
        gate_crush_threshold=0.35,
        gate_penetration_threshold=0.004,
        lift_steps=700,
        hold_steps=700,
        sample_every=int(args.sample_every),
        render_vision_debug=False,
        debug_dir=DOCS / "visual_checks_stage3_act_lite_eval_v0",
    )


def select_trials(raw: str, count: int) -> list[sweep.TrialConfig]:
    all_trials = sweep.trial_configs()
    if raw.strip().lower() == "cycle":
        return [all_trials[i % len(all_trials)] for i in range(int(count))]
    names = [item.strip() for item in raw.split(",") if item.strip()]
    by_name = {trial.name: trial for trial in all_trials}
    missing = [name for name in names if name not in by_name]
    if missing:
        raise ValueError(f"Unknown trials {missing}; available={sorted(by_name)}")
    out = [by_name[name] for name in names]
    while len(out) < int(count):
        out.extend(out)
    return out[: int(count)]


def action_from_policy(
    *,
    policy: ACTLiteChunkPolicy,
    checkpoint: dict[str, Any],
    obs: np.ndarray,
    skill_index: int,
    expert_action: np.ndarray,
    device: torch.device,
    model: Any,
    execution_mode: str,
    hand_start_index: int,
    chunk_cache: dict[str, Any],
    replan_interval: int,
) -> np.ndarray:
    horizon = int(checkpoint["horizon"])
    if chunk_cache.get("chunk") is None or int(chunk_cache.get("cursor", 0)) >= int(replan_interval):
        chunk_cache["chunk"] = predict_chunk(policy, checkpoint, obs, skill_index, device)
        chunk_cache["cursor"] = 0
    idx = min(int(chunk_cache["cursor"]), horizon - 1)
    predicted = np.asarray(chunk_cache["chunk"][idx], dtype=np.float64)
    chunk_cache["cursor"] = int(chunk_cache["cursor"]) + 1
    if execution_mode == "full_action":
        action = predicted
    elif execution_mode == "scripted_arm_predicted_hand":
        action = np.asarray(expert_action, dtype=np.float64).copy()
        action[int(hand_start_index) :] = predicted[int(hand_start_index) :]
    else:
        raise ValueError(f"Unknown execution_mode={execution_mode!r}")
    return collect.clip_action(model, action)


def actuator_index_map(model: Any, mujoco: Any) -> dict[str, int]:
    return {
        str(mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)): int(i)
        for i in range(int(model.nu))
    }


def finger_actuator_indices(actuator_index: dict[str, int], finger: str) -> list[int]:
    return [
        actuator_index[name]
        for name in [
            f"{finger}_mcp_flex_joint_pos",
            f"{finger}_mcp_abd_joint_pos",
            f"{finger}_pip_joint_pos",
            f"{finger}_dip_joint_pos",
        ]
        if name in actuator_index
    ]


def thumb_actuator_indices(actuator_index: dict[str, int]) -> list[int]:
    return [
        actuator_index[name]
        for name in [
            "thumb_cmc_abd_joint_pos",
            "thumb_cmc_joint_pos",
            "thumb_mcp_joint_pos",
            "thumb_ip_joint_pos",
        ]
        if name in actuator_index
    ]


def blend_indices(action: np.ndarray, expert_action: np.ndarray, indices: list[int], alpha: float) -> None:
    if not indices:
        return
    a = float(np.clip(float(alpha), 0.0, 1.0))
    if a <= 0.0:
        return
    action[indices] = (1.0 - a) * action[indices] + a * expert_action[indices]


def apply_close_delta(action: np.ndarray, actuator_index: dict[str, int], candidate: pinch.PinchCandidate, delta: float) -> None:
    d = max(0.0, float(delta))
    if d <= 0.0:
        return

    def add(name: str, amount: float) -> None:
        if name in actuator_index:
            action[actuator_index[name]] += float(amount)

    for finger in candidate.active_fingers:
        add(f"{finger}_mcp_flex_joint_pos", -0.25 * d)
        add(f"{finger}_mcp_abd_joint_pos", -0.35 * d)
        add(f"{finger}_pip_joint_pos", -1.00 * d)
        add(f"{finger}_dip_joint_pos", -0.65 * d)
    add("thumb_cmc_abd_joint_pos", -0.20 * d)
    add("thumb_cmc_joint_pos", 0.12 * d)
    add("thumb_mcp_joint_pos", 0.65 * d)
    add("thumb_ip_joint_pos", -0.65 * d)


def apply_pinch_hold_repair(
    *,
    action: np.ndarray,
    expert_action: np.ndarray,
    tactile: dict[str, Any],
    phase_name: str,
    candidate: pinch.PinchCandidate,
    actuator_index: dict[str, int],
    model: Any,
    args: argparse.Namespace,
) -> tuple[np.ndarray, dict[str, Any] | None]:
    mode = str(getattr(args, "pinch_repair_mode", "none"))
    if mode == "none":
        return action, None
    phases = {item.strip() for item in str(getattr(args, "pinch_repair_phases", "slow_lift,hold")).split(",") if item.strip()}
    if phase_name not in phases:
        return action, None

    repaired = np.asarray(action, dtype=np.float64).copy()
    slip = float(tactile.get("slip_score", 0.0))
    crush = float(tactile.get("crush_risk", 0.0))
    penetration = float(tactile.get("max_penetration", 0.0))
    threshold = float(getattr(args, "pinch_repair_slip_threshold", 0.28))
    intensity = float(np.clip((slip - threshold) / max(1e-6, 1.0 - threshold), 0.0, 1.0))
    event: dict[str, Any] = {
        "mode": mode,
        "phase": phase_name,
        "slip": slip,
        "crush": crush,
        "penetration": penetration,
        "intensity": intensity,
        "inactive_alpha": 0.0,
        "expert_alpha": 0.0,
        "close_delta": 0.0,
    }

    active = set(candidate.active_fingers)
    inactive_indices: list[int] = []
    for finger in ("index", "middle", "ring", "little"):
        if finger not in active:
            inactive_indices.extend(finger_actuator_indices(actuator_index, finger))
    if mode in {"inactive_anchor", "inactive_anchor_slip_close", "all"}:
        inactive_alpha = float(getattr(args, "pinch_repair_inactive_alpha", 0.75))
        blend_indices(repaired, expert_action, inactive_indices, inactive_alpha)
        event["inactive_alpha"] = float(np.clip(inactive_alpha, 0.0, 1.0))

    if mode in {"expert_blend", "expert_blend_slip_close", "all"} and intensity > 0.0:
        hand_indices = list(range(int(args.hand_start_index), int(model.nu)))
        expert_alpha = float(getattr(args, "pinch_repair_expert_alpha", 0.20)) * intensity
        blend_indices(repaired, expert_action, hand_indices, expert_alpha)
        event["expert_alpha"] = float(np.clip(expert_alpha, 0.0, 1.0))

    if mode in {"slip_close", "inactive_anchor_slip_close", "expert_blend_slip_close", "all"} and intensity > 0.0:
        if crush <= float(getattr(args, "pinch_repair_max_crush", 0.25)) and penetration <= float(getattr(args, "pinch_repair_max_penetration", 0.0035)):
            close_delta = min(
                float(getattr(args, "pinch_repair_close_max", 0.08)),
                float(getattr(args, "pinch_repair_close_gain", 0.08)) * intensity,
            )
            apply_close_delta(repaired, actuator_index, candidate, close_delta)
            event["close_delta"] = float(close_delta)
    preclose_delta = float(getattr(args, "pinch_repair_preclose_delta", 0.0))
    if mode in {"slip_close", "inactive_anchor_slip_close", "expert_blend_slip_close", "all"} and preclose_delta > 0.0:
        if crush <= float(getattr(args, "pinch_repair_max_crush", 0.25)) and penetration <= float(getattr(args, "pinch_repair_max_penetration", 0.0035)):
            close_delta = min(float(getattr(args, "pinch_repair_close_max", 0.08)), max(0.0, preclose_delta) + float(event["close_delta"]))
            apply_close_delta(repaired, actuator_index, candidate, close_delta - float(event["close_delta"]))
            event["close_delta"] = float(close_delta)
    if event["inactive_alpha"] <= 0.0 and event["expert_alpha"] <= 0.0 and event["close_delta"] <= 0.0:
        return action, None
    return collect.clip_action(model, repaired), event


def run_full_hand_episode(
    *,
    model: Any,
    mujoco: Any,
    policy: ACTLiteChunkPolicy,
    checkpoint: dict[str, Any],
    trial: sweep.TrialConfig,
    episode_id: int,
    args: argparse.Namespace,
    device: torch.device,
) -> dict[str, Any]:
    cfg = make_full_hand_args(args)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    base_egg_position = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    rng = np.random.default_rng(int(cfg.seed) + int(episode_id))
    egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
    if float(cfg.random_offset_std) > 0.0:
        egg_position = egg_position + rng.normal(0.0, float(cfg.random_offset_std), size=3)
        egg_position[2] = base_egg_position[2] + np.asarray(trial.offset_xyz, dtype=np.float64)[2]
    sweep.reset_episode(model, data, mujoco, egg_position)

    vision_sensor = MujocoEggPoseSensor(
        model,
        mujoco,
        EggPoseSensorConfig(camera_name=cfg.camera, width=int(cfg.width), height=int(cfg.height)),
    )
    vision_estimate = vision_sensor.estimate(data, label=f"stage3_act_lite_full_{episode_id:04d}_vision_acquire")
    if not collect.accepted_virtual_camera_estimate(vision_estimate, float(cfg.min_vision_confidence)):
        return {
            "episode_id": int(episode_id),
            "skill_id": "full_hand_gentle_grasp",
            "trial": trial.name,
            "status": "FAIL",
            "success": False,
            "terminal_reason": "vision_acquire_failed",
            "failure_reasons": ["vision_acquire_failed"],
            "risk_flags": [],
        }
    vision = collect.make_vision_fields(vision_estimate)
    profile = collect.Stage3DatasetProfile("act_lite_eval", 1.0, 0.0, 0.0, 0)
    plan = collect.build_episode_plan(model, data, mujoco, trial=trial, egg_position=egg_position, vision_fields=vision, args=cfg, profile=profile)
    thresholds = Stage3Thresholds()
    tactile_sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=thresholds)
    tactile_sensor.reset(data)
    initial_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()

    contact_acquired = False
    grip_stable_before_lift = False
    first_contact_phase = "none"
    max_slip = 0.0
    pre_lift_max_slip = 0.0
    post_lift_max_slip = 0.0
    max_crush = 0.0
    max_penetration = 0.0
    hold_steps = 0
    hold_stable_steps = 0
    hold_max_slip = 0.0
    contact_settle_steps_actual = 0
    gate_stable_window = 0
    gate_release_reason = "not_reached"
    gate_release_step = 0
    pre_lift_tactile: dict[str, Any] | None = None
    approach_true_proxy_error = float("inf")
    approach_est_proxy_error = float("inf")
    phase_metrics: dict[str, dict[str, float]] = {}
    trace: list[dict[str, Any]] = []
    chunk_cache: dict[str, Any] = {"chunk": None, "cursor": 0}
    step_count = 0
    skill_index = SKILL_ID_TO_INDEX["full_hand_gentle_grasp"]

    for phase_name, start, end, steps in plan["phases"]:
        phase_steps = max(1, int(steps))
        if phase_name == "contact_settle":
            phase_steps = int(cfg.max_contact_settle_steps)
        local_step = 0
        while local_step < phase_steps:
            progress = local_step / max(1, phase_steps - 1)
            tactile = tactile_sensor.sample(data)
            obs = collect.observation_vector(model, data, vision, tactile, phase_name=phase_name, progress=progress)
            expert_targets = sweep.blend_targets(start, end, progress)
            expert_action = sweep.actuator_targets(model, mujoco, plan["actuator_names"], expert_targets)
            action = action_from_policy(
                policy=policy,
                checkpoint=checkpoint,
                obs=obs,
                skill_index=skill_index,
                expert_action=expert_action,
                device=device,
                model=model,
                execution_mode=str(args.execution_mode),
                hand_start_index=int(args.hand_start_index),
                chunk_cache=chunk_cache,
                replan_interval=int(args.replan_interval),
            )
            data.ctrl[:] = action
            mujoco.mj_step(model, data)
            next_tactile = tactile_sensor.sample(data)
            egg_now = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
            lift_height = float(egg_now[2] - initial_egg[2])
            record_phase_metric(phase_metrics, phase_name, next_tactile)

            if phase_name == "approach":
                proxy_now = sweep.proxy_position(model, data, mujoco, plan["grasp_local"])
                approach_true_proxy_error = float(np.linalg.norm(proxy_now - initial_egg))
                approach_est_proxy_error = float(np.linalg.norm(proxy_now - plan["approach_target"]))
            if next_tactile["contact_present"]:
                contact_acquired = True
                if first_contact_phase == "none":
                    first_contact_phase = phase_name
            if next_tactile["grip_stable"] and phase_name in {"gentle_close_thumb", "contact_settle"}:
                grip_stable_before_lift = True
            if phase_name == "hold":
                hold_steps += 1
                hold_stable_steps += int(bool(next_tactile["grip_stable"]))
                hold_max_slip = max(hold_max_slip, float(next_tactile["slip_score"]))

            slip = float(next_tactile["slip_score"])
            max_slip = max(max_slip, slip)
            if phase_name in {"approach", "preshape", "gentle_close_fingers", "gentle_close_thumb", "contact_settle"}:
                pre_lift_max_slip = max(pre_lift_max_slip, slip)
            else:
                post_lift_max_slip = max(post_lift_max_slip, slip)
            max_crush = max(max_crush, float(next_tactile["crush_risk"]))
            max_penetration = max(max_penetration, float(next_tactile.get("max_penetration", 0.0)))

            if phase_name == "contact_settle":
                contact_settle_steps_actual += 1
                pre_lift_tactile = dict(next_tactile)
                gate_reasons = gate_condition_reasons(next_tactile, cfg, thresholds)
                gate_stable_window = 0 if gate_reasons else gate_stable_window + 1
                if contact_settle_steps_actual >= int(cfg.min_contact_settle_steps) and gate_stable_window >= int(cfg.settle_stable_window_steps):
                    gate_release_reason = "stable_window_met"
                    gate_release_step = contact_settle_steps_actual
                elif contact_settle_steps_actual >= int(cfg.max_contact_settle_steps):
                    gate_release_reason = "max_steps_reached_stable" if not gate_reasons else "max_steps_reached_unstable"
                    gate_release_step = contact_settle_steps_actual

            if step_count % max(1, int(cfg.sample_every)) == 0:
                trace.append(
                    {
                        "step": int(step_count),
                        "phase": phase_name,
                        "progress": float(progress),
                        "lift_height_m": float(lift_height),
                        "contact": bool(next_tactile["contact_present"]),
                        "stable": bool(next_tactile["grip_stable"]),
                        "slip": float(next_tactile["slip_score"]),
                        "crush": float(next_tactile["crush_risk"]),
                        "penetration": float(next_tactile.get("max_penetration", 0.0)),
                    }
                )
            local_step += 1
            step_count += 1
            if phase_name == "contact_settle" and gate_release_reason != "not_reached":
                break

    final_tactile = tactile_sensor.sample(data)
    final_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    final_contact = sweep.contact_summary(model, data, mujoco)
    hold_duration_s = float(hold_steps) * float(model.opt.timestep)
    hold_stable_fraction = float(hold_stable_steps / max(1, hold_steps))
    if pre_lift_tactile is None:
        pre_lift_tactile = dict(final_tactile)
    summary = {
        "vision_accepted": True,
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
        "pre_lift_max_slip_score": float(pre_lift_max_slip),
        "post_lift_max_slip_score": float(post_lift_max_slip),
        "max_crush_risk": float(max_crush),
        "max_penetration_m": float(max_penetration),
        "final_floor_contacts": int(final_contact["egg_floor_contact_count"]),
        "finite_state": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "contact_settle_steps_actual": int(contact_settle_steps_actual),
        "gate_release_reason": gate_release_reason,
        "gate_release_step": int(gate_release_step),
        "gate_stable_window_at_release": int(gate_stable_window),
        "pre_lift_contact_present": bool(pre_lift_tactile.get("contact_present", False)),
        "pre_lift_grip_stable": bool(pre_lift_tactile.get("grip_stable", False)),
        "pre_lift_slip_score": float(pre_lift_tactile.get("slip_score", 0.0)),
        "pre_lift_crush_risk": float(pre_lift_tactile.get("crush_risk", 0.0)),
        "pre_lift_penetration_m": float(pre_lift_tactile.get("max_penetration", 0.0)),
        "phase_metrics": phase_metrics,
        "total_steps": int(step_count),
    }
    reasons = collect.expert_failure_reasons(summary, cfg, thresholds)
    success = len(reasons) == 0
    risks: list[str] = []
    if first_contact_phase == "approach":
        risks.append("early_contact_in_approach")
    if max_slip > thresholds.success_max_slip_score:
        risks.append("transient_or_hold_slip")
    if hold_max_slip > thresholds.success_max_slip_score:
        risks.append("hold_slip_high")
    return {
        "episode_id": int(episode_id),
        "skill_id": "full_hand_gentle_grasp",
        "trial": trial.name,
        "status": "PASS" if success else "FAIL",
        "success": bool(success),
        "terminal_reason": "success_gentle_grasp_hold" if success else (reasons[0] if reasons else "unknown"),
        "failure_reasons": reasons,
        "risk_flags": risks,
        "summary": summary,
        "trace": trace,
    }


def run_full_hand_fallback_episode(
    *,
    model: Any,
    mujoco: Any,
    fallback_policy: Any,
    fallback_checkpoint: dict[str, Any],
    trial: sweep.TrialConfig,
    episode_id: int,
    args: argparse.Namespace,
    device: torch.device,
) -> dict[str, Any]:
    cfg = make_full_hand_fallback_args(args)
    row = recovery.run_recovery_episode(model, mujoco, fallback_policy, fallback_checkpoint, trial, episode_id, cfg, device)
    row["skill_id"] = "full_hand_gentle_grasp"
    row["full_hand_control_mode"] = "stage3_7d_fallback"
    row["policy_scope"] = "stage3_7d_full_hand_fallback_inside_stage3_9g_act_lite_eval"
    summary = row.setdefault("summary", {})
    summary["full_hand_control_mode"] = "stage3_7d_fallback"
    return row


def run_pinch_episode(
    *,
    model: Any,
    mujoco: Any,
    policy: ACTLiteChunkPolicy,
    checkpoint: dict[str, Any],
    candidate: pinch.PinchCandidate,
    trial: sweep.TrialConfig,
    episode_id: int,
    args: argparse.Namespace,
    device: torch.device,
) -> dict[str, Any]:
    cfg = make_pinch_args(args)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    base_egg_position = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    rng = np.random.default_rng(int(cfg.seed) + int(episode_id) * 1009)
    egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
    if float(cfg.random_offset_std) > 0.0:
        egg_position = egg_position + rng.normal(0.0, float(cfg.random_offset_std), size=3)
        egg_position[2] = base_egg_position[2] + np.asarray(trial.offset_xyz, dtype=np.float64)[2]
    sweep.reset_episode(model, data, mujoco, egg_position)
    initial_vision = pinch.acquire_vision(
        model,
        data,
        mujoco,
        camera_name=str(cfg.camera),
        width=int(cfg.width),
        height=int(cfg.height),
        min_confidence=float(cfg.min_vision_confidence),
        debug_dir=None,
        label=f"stage3_act_lite_pinch_{episode_id:04d}_initial",
    )
    if not bool(initial_vision.get("accepted")):
        return {
            "episode_id": int(episode_id),
            "skill_id": "thumb_index_middle_pinch",
            "candidate": candidate.name,
            "trial": trial.name,
            "status": "FAIL",
            "success": False,
            "terminal_reason": "initial_vision_failed",
            "failure_reasons": ["initial_vision_failed"],
            "risk_flags": [],
        }

    plan = pinch.build_pinch_plan(model, data, mujoco, trial=trial, candidate=candidate, egg_position=egg_position, vision_estimate=initial_vision, args=cfg)
    vision = collect.make_vision_fields(initial_vision)
    thresholds = Stage3Thresholds()
    tactile_sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=thresholds)
    tactile_sensor.reset(data)
    initial_true_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    initial_vision_pos = np.asarray(initial_vision["position_world_est"], dtype=np.float64)
    actuator_index = actuator_index_map(model, mujoco)

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
    repair_counts: Counter[str] = Counter()
    repair_max_close_delta = 0.0
    repair_max_expert_alpha = 0.0
    repair_max_inactive_alpha = 0.0
    trace: list[dict[str, Any]] = []
    capture_sequence = bool(getattr(args, "capture_sequence", False))
    sequence_rows: dict[str, list[Any]] | None = None
    if capture_sequence:
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
            "repair_active": [],
            "repair_close_delta": [],
            "repair_expert_alpha": [],
            "repair_inactive_alpha": [],
            "safety_intervention_active": [],
            "lift_heights": [],
            "pinch_contact": [],
            "vision_pose_estimates": [],
            "vision_scalars": [],
            "tactile_scalars": [],
            "tactile_region_masks": [],
            "gt_object_positions": [],
            "gt_object_lift_heights": [],
        }
    chunk_cache: dict[str, Any] = {"chunk": None, "cursor": 0}
    step_count = 0
    contact_settle_steps_actual = 0
    approach_true_proxy_error = float("inf")
    skill_index = SKILL_ID_TO_INDEX["thumb_index_middle_pinch"]

    for phase_name, start, end, steps in plan["phases"]:
        phase_steps = int(steps)
        if phase_name == "contact_settle":
            phase_steps = int(cfg.max_contact_settle_steps)
        local_step = 0
        while local_step < phase_steps:
            progress = local_step / max(1, phase_steps - 1)
            tactile_pre = tactile_sensor.sample(data)
            obs = collect.observation_vector(model, data, vision, tactile_pre, phase_name=phase_name, progress=progress)
            targets = sweep.blend_targets(start, end, progress)
            expert_action = sweep.actuator_targets(model, mujoco, plan["actuator_names"], targets)
            action = action_from_policy(
                policy=policy,
                checkpoint=checkpoint,
                obs=obs,
                skill_index=skill_index,
                expert_action=expert_action,
                device=device,
                model=model,
                execution_mode=str(args.execution_mode),
                hand_start_index=int(args.hand_start_index),
                chunk_cache=chunk_cache,
                replan_interval=int(args.replan_interval),
            )
            action, repair_event = apply_pinch_hold_repair(
                action=action,
                expert_action=expert_action,
                tactile=tactile_pre,
                phase_name=phase_name,
                candidate=candidate,
                actuator_index=actuator_index,
                model=model,
                args=args,
            )
            if repair_event is not None:
                repair_counts[str(repair_event["mode"])] += 1
                repair_counts[f"{repair_event['mode']}:{phase_name}"] += 1
                repair_max_close_delta = max(repair_max_close_delta, float(repair_event.get("close_delta", 0.0)))
                repair_max_expert_alpha = max(repair_max_expert_alpha, float(repair_event.get("expert_alpha", 0.0)))
                repair_max_inactive_alpha = max(repair_max_inactive_alpha, float(repair_event.get("inactive_alpha", 0.0)))
            data.ctrl[:] = action
            mujoco.mj_step(model, data)
            tactile = tactile_sensor.sample(data)
            record_phase_metric(phase_metrics, phase_name, tactile)
            region_counts_total.update({str(k): int(v) for k, v in tactile.get("egg_contact_region_counts", {}).items()})
            egg_now = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
            lift_height = float(egg_now[2] - initial_true_egg[2])
            next_obs = collect.observation_vector(model, data, vision, tactile, phase_name=phase_name, progress=progress)
            if sequence_rows is not None:
                repair_active = bool(repair_event is not None)
                sequence_rows["obs"].append(obs)
                sequence_rows["actions"].append(collect.clip_action(model, action))
                sequence_rows["expert_actions"].append(collect.clip_action(model, expert_action))
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
                sequence_rows["learned_hand"].append(str(args.execution_mode) in {"full_action", "scripted_arm_predicted_hand"})
                sequence_rows["recovery_active"].append(False)
                sequence_rows["repair_active"].append(repair_active)
                sequence_rows["repair_close_delta"].append(float(repair_event.get("close_delta", 0.0)) if repair_event else 0.0)
                sequence_rows["repair_expert_alpha"].append(float(repair_event.get("expert_alpha", 0.0)) if repair_event else 0.0)
                sequence_rows["repair_inactive_alpha"].append(float(repair_event.get("inactive_alpha", 0.0)) if repair_event else 0.0)
                sequence_rows["safety_intervention_active"].append(repair_active)
                sequence_rows["lift_heights"].append(float(lift_height))
                sequence_rows["pinch_contact"].append(bool(pinch.pinch_contact_ok(tactile, candidate)))
                sequence_rows["vision_pose_estimates"].append(vision["object_pose_xyz_est"])
                sequence_rows["vision_scalars"].append(collect.vision_scalars(vision))
                sequence_rows["tactile_scalars"].append(collect.tactile_scalars(tactile))
                sequence_rows["tactile_region_masks"].append(collect.tactile_region_mask(tactile))
                sequence_rows["gt_object_positions"].append(egg_now)
                sequence_rows["gt_object_lift_heights"].append(float(lift_height))

            if phase_name == "approach":
                proxy_now = sweep.proxy_position(model, data, mujoco, plan["grasp_local"])
                approach_true_proxy_error = float(np.linalg.norm(proxy_now - initial_true_egg))
            if tactile["contact_present"]:
                contact_acquired = True
                if first_contact_phase == "none":
                    first_contact_phase = phase_name
            if phase_name in {"pinch_close", "contact_settle"} and pinch.pinch_contact_ok(tactile, candidate):
                pinch_contact_before_lift = True
            if phase_name == "contact_settle":
                contact_settle_steps_actual += 1
                gate_reasons = gate_condition_reasons(tactile, cfg, thresholds)
                gate_stable_window = 0 if gate_reasons else gate_stable_window + 1
                if contact_settle_steps_actual >= int(cfg.min_contact_settle_steps) and gate_stable_window >= int(cfg.settle_stable_window_steps):
                    gate_release_reason = "stable_window_met"
                elif contact_settle_steps_actual >= int(cfg.max_contact_settle_steps):
                    gate_release_reason = "max_steps_reached_stable" if not gate_reasons else "max_steps_reached_unstable"
            if phase_name == "hold":
                hold_steps += 1
                hold_stable_steps += int(bool(tactile["grip_stable"]))
                hold_max_slip = max(hold_max_slip, float(tactile["slip_score"]))
                if pinch.pinch_contact_ok(tactile, candidate):
                    hold_pinch_steps += 1
                hold_purity_sum += pinch.pinch_purity_score(tactile, candidate)
            max_slip = max(max_slip, float(tactile["slip_score"]))
            max_crush = max(max_crush, float(tactile["crush_risk"]))
            max_penetration = max(max_penetration, float(tactile.get("max_penetration", 0.0)))
            if step_count % max(1, int(cfg.sample_every)) == 0:
                trace.append(
                    {
                        "step": int(step_count),
                        "phase": phase_name,
                        "progress": float(progress),
                        "true_lift_height_m": float(lift_height),
                        "contact": bool(tactile["contact_present"]),
                        "pinch_contact": bool(pinch.pinch_contact_ok(tactile, candidate)),
                        "slip": float(tactile["slip_score"]),
                        "stable": bool(tactile["grip_stable"]),
                        "crush": float(tactile["crush_risk"]),
                        "penetration": float(tactile.get("max_penetration", 0.0)),
                        "repair_active": bool(repair_event is not None),
                        "repair_close_delta": float(repair_event.get("close_delta", 0.0)) if repair_event else 0.0,
                        "repair_expert_alpha": float(repair_event.get("expert_alpha", 0.0)) if repair_event else 0.0,
                        "repair_inactive_alpha": float(repair_event.get("inactive_alpha", 0.0)) if repair_event else 0.0,
                    }
                )
            local_step += 1
            step_count += 1
            if phase_name == "contact_settle" and gate_release_reason != "not_reached":
                break

    final_tactile = tactile_sensor.sample(data)
    final_true_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    final_contact = sweep.contact_summary(model, data, mujoco)
    final_cameras = [camera.strip() for camera in str(cfg.final_cameras).split(",") if camera.strip()]
    final_vision, final_vision_all = pinch.best_final_vision(
        model,
        data,
        mujoco,
        cameras=final_cameras,
        width=int(cfg.width),
        height=int(cfg.height),
        min_confidence=float(cfg.min_final_vision_confidence),
        debug_dir=None,
        label=f"stage3_act_lite_pinch_{episode_id:04d}_final",
    )
    final_vision_pos = np.asarray(final_vision.get("position_world_est", [math.nan, math.nan, math.nan]), dtype=np.float64)
    final_vision_primary_accepted = bool(final_vision.get("accepted"))
    final_vision_corroborated = False
    if (
        not final_vision_primary_accepted
        and str(getattr(args, "pinch_final_verification_mode", "strict_vision")) == "vision_tactile_corroborated"
        and final_vision.get("status") == "ok"
        and np.isfinite(final_vision_pos).all()
    ):
        low_confidence_vision_ok = (
            float(final_vision.get("confidence", 0.0)) >= float(args.pinch_final_corroboration_min_confidence)
            and int(final_vision.get("mask_pixels", 0)) >= int(args.pinch_final_corroboration_min_mask_pixels)
        )
        tactile_hold_ok = (
            hold_steps > 0
            and float(hold_stable_steps / max(1, hold_steps)) >= float(cfg.min_hold_stable_fraction)
            and float(hold_pinch_steps / max(1, hold_steps)) >= float(cfg.min_hold_pinch_fraction)
            and float(hold_max_slip) <= float(thresholds.success_max_slip_score)
            and float(max_crush) <= float(thresholds.success_max_crush_risk)
            and float(max_penetration) <= float(thresholds.success_max_penetration_m)
            and int(final_contact["egg_floor_contact_count"]) == 0
        )
        final_vision_corroborated = bool(low_confidence_vision_ok and tactile_hold_ok)
        if final_vision_corroborated:
            final_vision = dict(final_vision)
            final_vision["accepted"] = True
            final_vision["accepted_by"] = "vision_tactile_corroborated"
            final_vision["primary_accepted"] = False
    final_vision_accepted = bool(final_vision.get("accepted"))
    vision_lift = float(final_vision_pos[2] - initial_vision_pos[2]) if final_vision_accepted else float("nan")
    hold_stable_fraction = float(hold_stable_steps / max(1, hold_steps))
    hold_pinch_fraction = float(hold_pinch_steps / max(1, hold_steps))
    hold_purity_mean = float(hold_purity_sum / max(1, hold_steps))
    summary = {
        "initial_vision_accepted": bool(initial_vision.get("accepted")),
        "initial_vision_status": initial_vision.get("status"),
        "initial_vision_confidence": float(initial_vision.get("confidence", 0.0)),
        "initial_vision_mask_pixels": int(initial_vision.get("mask_pixels", 0)),
        "final_vision_accepted": bool(final_vision_accepted),
        "final_vision_primary_accepted": bool(final_vision_primary_accepted),
        "final_vision_corroborated": bool(final_vision_corroborated),
        "final_verification_mode": str(getattr(args, "pinch_final_verification_mode", "strict_vision")),
        "final_vision_camera": final_vision.get("camera"),
        "final_vision_status": final_vision.get("status"),
        "final_vision_accepted_by": final_vision.get("accepted_by", "strict_vision" if final_vision_primary_accepted else "none"),
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
        "repair_mode": str(getattr(args, "pinch_repair_mode", "none")),
        "repair_event_counts": dict(repair_counts),
        "repair_max_close_delta": float(repair_max_close_delta),
        "repair_max_expert_alpha": float(repair_max_expert_alpha),
        "repair_max_inactive_alpha": float(repair_max_inactive_alpha),
        "phase_metrics": phase_metrics,
        "finite_state": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "total_steps": int(step_count),
    }
    reasons = pinch.classify_failure_reasons(summary, cfg, thresholds)
    risks: list[str] = []
    if first_contact_phase == "approach":
        risks.append("early_contact_in_approach")
    if max_slip > thresholds.success_max_slip_score:
        risks.append("transient_slip_high")
    if hold_purity_mean < float(cfg.min_hold_pinch_purity):
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
        if bool(final_vision_corroborated):
            sequence_rows["safety_intervention_active"][-1] = True
    result = {
        "episode_id": int(episode_id),
        "skill_id": "thumb_index_middle_pinch",
        "candidate": candidate.name,
        "trial": trial.name,
        "status": "PASS" if success else "FAIL",
        "success": bool(success),
        "terminal_reason": terminal_reason,
        "failure_reasons": reasons,
        "risk_flags": risks,
        "summary": summary,
        "trace": trace,
        "final_vision": final_vision,
        "final_vision_all": final_vision_all,
    }
    if sequence_rows is not None:
        result["sequence_rows"] = sequence_rows
    return result


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_skill: dict[str, dict[str, Any]] = {}
    for skill in sorted(set(str(row["skill_id"]) for row in rows)):
        subset = [row for row in rows if row["skill_id"] == skill]
        by_skill[skill] = summarize_subset(subset)
    return {
        "status": "PASS" if all(row["success"] for row in rows) else ("PARTIAL" if any(row["success"] for row in rows) else "FAIL"),
        "episodes": int(len(rows)),
        "success_count": int(sum(1 for row in rows if row["success"])),
        "terminal_reason_counts": dict(Counter(str(row["terminal_reason"]) for row in rows)),
        "failure_reason_counts": dict(Counter(reason for row in rows for reason in row.get("failure_reasons", []))),
        "risk_flag_counts": dict(Counter(flag for row in rows for flag in row.get("risk_flags", []))),
        "by_skill": by_skill,
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
        "final_lift_height_m",
        "true_lift_height_m",
        "vision_lift_height_m",
        "hold_stable_fraction",
        "hold_pinch_fraction",
        "hold_max_slip_score",
        "max_slip_score",
        "max_crush_risk",
        "max_penetration_m",
    ]:
        vals = values(key)
        if vals.size:
            finite = vals[np.isfinite(vals)]
            if finite.size:
                out[f"{key}_mean"] = float(finite.mean())
                out[f"{key}_min"] = float(finite.min())
                out[f"{key}_max"] = float(finite.max())
    return out


def write_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage3 ACT-lite Chunk Policy v0 闭环评估报告\n\n",
        f"- 生成时间：`{payload['generated_at']}`\n",
        f"- 状态：`{summary['status']}`\n",
        f"- checkpoint：`{payload['checkpoint']}`\n",
        f"- 执行模式：`{payload['execution_mode']}`\n",
        f"- chunk 重规划间隔：`{payload['replan_interval']}`\n",
        f"- 成功数：`{summary['success_count']} / {summary['episodes']}`\n",
        f"- 训练状态：`{payload['checkpoint_status']}`\n",
        "- 边界：这是 MuJoCo 仿真闭环评估，不是硬件集成。\n\n",
        "## 技能汇总\n\n",
        "| 技能 | 成功 | 终止原因 | 失败项 | 风险标记 |\n",
        "| --- | ---: | --- | --- | --- |\n",
    ]
    for skill, row in summary["by_skill"].items():
        lines.append(
            f"| `{skill}` | {row['success_count']} / {row['episodes']} | "
            f"`{row['terminal_reason_counts']}` | `{row['failure_reason_counts']}` | `{row['risk_flag_counts']}` |\n"
        )
    lines.extend(["\n## 单次结果\n\n", "| ep | 技能 | 场景 | 状态 | 原因 | 抬升 | hold 稳定度 | hold 滑移 | 最大滑移 | 失败项 |\n", "| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |\n"])
    for row in payload["results"]:
        s = row.get("summary", {})
        lift = s.get("final_lift_height_m", s.get("true_lift_height_m", float("nan")))
        lines.append(
            f"| {row['episode_id']} | `{row['skill_id']}` | `{row['trial']}` | {row['status']} | `{row['terminal_reason']}` | "
            f"{float(lift):.4f} | {float(s.get('hold_stable_fraction', float('nan'))):.3f} | "
            f"{float(s.get('hold_max_slip_score', float('nan'))):.3f} | {float(s.get('max_slip_score', float('nan'))):.3f} | "
            f"`{row.get('failure_reasons', [])}` |\n"
        )
    lines.extend(
        [
            "\n## 解释\n\n",
            "- `full_action` 表示模型直接控制 26 个 actuator，是更难也更容易失稳的模式。\n",
            "- `scripted_arm_predicted_hand` 表示手臂/手腕仍由视觉引导脚本控制，ACT-lite 只控制手指闭合和保持，这是目前更合理的第一道闭环门槛。\n",
            "- 只有在成功率、滑移、挤压、穿透、落地接触都能接近或超过脚本 SkillZoo baseline 后，才适合继续提升为正式策略。\n\n",
            "## 如果成功\n\n",
            "下一步扩大随机姿态和场景数量，并和 Stage3.7D 全手、Stage3.8B 捏持脚本 baseline 做同条件对比。\n\n",
            "## 如果失败\n\n",
            "先按失败来源拆开：视觉/接近、接触建立、手指闭合、抬升保持、最终视觉确认。不要立刻扩大模型；优先调整 chunk 执行间隔、分技能头或 phase-specific head。\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Closed-loop eval for Stage3 ACT-lite chunk policy.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--selected-pinch-config", type=Path, default=DEFAULT_SELECTED_PINCH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--skills", default="full_hand_gentle_grasp,thumb_index_middle_pinch")
    parser.add_argument("--trials", default="center_nominal")
    parser.add_argument("--episodes-per-skill", type=int, default=1)
    parser.add_argument("--execution-mode", choices=["full_action", "scripted_arm_predicted_hand"], default="scripted_arm_predicted_hand")
    parser.add_argument("--replan-interval", type=int, default=16)
    parser.add_argument("--hand-start-index", type=int, default=6)
    parser.add_argument("--full-hand-control-mode", choices=["act_lite_hand", "stage3_7d_fallback"], default="act_lite_hand")
    parser.add_argument("--full-hand-fallback-checkpoint", type=Path, default=recovery.DEFAULT_CHECKPOINT)
    parser.add_argument("--full-hand-fallback-transition-slip-threshold", type=float, default=0.29)
    parser.add_argument("--full-hand-fallback-max-transition-hold-steps-per-phase", type=int, default=200)
    parser.add_argument("--full-hand-fallback-recovery-progress-drop", type=float, default=0.01)
    parser.add_argument("--full-hand-fallback-recovery-stable-window-steps", type=int, default=0)
    parser.add_argument(
        "--pinch-repair-mode",
        choices=["none", "inactive_anchor", "slip_close", "expert_blend", "inactive_anchor_slip_close", "expert_blend_slip_close", "all"],
        default="none",
    )
    parser.add_argument("--pinch-repair-phases", default="slow_lift,hold")
    parser.add_argument("--pinch-repair-slip-threshold", type=float, default=0.28)
    parser.add_argument("--pinch-repair-inactive-alpha", type=float, default=0.75)
    parser.add_argument("--pinch-repair-expert-alpha", type=float, default=0.20)
    parser.add_argument("--pinch-repair-close-gain", type=float, default=0.08)
    parser.add_argument("--pinch-repair-close-max", type=float, default=0.08)
    parser.add_argument("--pinch-repair-preclose-delta", type=float, default=0.0)
    parser.add_argument("--pinch-repair-max-crush", type=float, default=0.25)
    parser.add_argument("--pinch-repair-max-penetration", type=float, default=0.0035)
    parser.add_argument("--pinch-final-verification-mode", choices=["strict_vision", "vision_tactile_corroborated"], default="strict_vision")
    parser.add_argument("--pinch-final-corroboration-min-confidence", type=float, default=0.30)
    parser.add_argument("--pinch-final-corroboration-min-mask-pixels", type=int, default=500)
    parser.add_argument("--seed", type=int, default=270)
    parser.add_argument("--random-offset-std", type=float, default=0.0)
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--sample-every", type=int, default=240)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--capture-sequence", action="store_true")
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"
    device = torch.device(str(args.device))
    import mujoco

    policy, checkpoint = load_chunk_policy(args.checkpoint, device)
    fallback_policy = None
    fallback_checkpoint: dict[str, Any] | None = None
    if str(args.full_hand_control_mode) == "stage3_7d_fallback" and "full_hand_gentle_grasp" in str(args.skills):
        fallback_policy, fallback_checkpoint = recovery.load_policy(args.full_hand_fallback_checkpoint, device)
    model = mujoco.MjModel.from_xml_path(str(Path(args.scene).resolve()))
    candidate = load_selected_pinch_candidate(Path(args.selected_pinch_config))
    skills = [item.strip() for item in str(args.skills).split(",") if item.strip()]
    trials = select_trials(str(args.trials), int(args.episodes_per_skill))

    results: list[dict[str, Any]] = []
    episode_id = 0
    for skill in skills:
        if skill not in SKILL_ID_TO_INDEX:
            raise ValueError(f"Unknown skill {skill!r}; available={sorted(SKILL_ID_TO_INDEX)}")
        for local_idx in range(int(args.episodes_per_skill)):
            trial = trials[local_idx % len(trials)]
            if skill == "full_hand_gentle_grasp":
                if str(args.full_hand_control_mode) == "stage3_7d_fallback":
                    if fallback_policy is None or fallback_checkpoint is None:
                        raise RuntimeError("full-hand fallback policy was not loaded")
                    row = run_full_hand_fallback_episode(
                        model=model,
                        mujoco=mujoco,
                        fallback_policy=fallback_policy,
                        fallback_checkpoint=fallback_checkpoint,
                        trial=trial,
                        episode_id=episode_id,
                        args=args,
                        device=device,
                    )
                else:
                    row = run_full_hand_episode(model=model, mujoco=mujoco, policy=policy, checkpoint=checkpoint, trial=trial, episode_id=episode_id, args=args, device=device)
            else:
                row = run_pinch_episode(model=model, mujoco=mujoco, policy=policy, checkpoint=checkpoint, candidate=candidate, trial=trial, episode_id=episode_id, args=args, device=device)
            results.append(row)
            s = row.get("summary", {})
            lift = s.get("final_lift_height_m", s.get("true_lift_height_m", float("nan")))
            print(
                f"ep={episode_id:03d} skill={skill} trial={trial.name} {row['status']} "
                f"reason={row['terminal_reason']} lift={float(lift):.4f} "
                f"hold_slip={float(s.get('hold_max_slip_score', float('nan'))):.3f} "
                f"max_slip={float(s.get('max_slip_score', float('nan'))):.3f}"
            )
            episode_id += 1

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "checkpoint_status": checkpoint.get("status"),
        "scene": str(Path(args.scene).resolve()),
        "selected_pinch_config": str(Path(args.selected_pinch_config).resolve()),
        "execution_mode": str(args.execution_mode),
        "full_hand_control_mode": str(args.full_hand_control_mode),
        "full_hand_fallback_checkpoint": str(Path(args.full_hand_fallback_checkpoint).resolve()) if str(args.full_hand_control_mode) == "stage3_7d_fallback" else None,
        "replan_interval": int(args.replan_interval),
        "device": str(device),
        "args": vars(args),
        "summary": summarize(results),
        "results": results,
        "training_status": "closed_loop_eval_completed",
        "promoted_policy": False,
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(Path(args.report), json_ready(payload))
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0 if payload["summary"]["success_count"] == payload["summary"]["episodes"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
