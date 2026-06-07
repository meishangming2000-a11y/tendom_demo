#!/usr/bin/env python3
"""Evaluate a Stage3.7 rule-based tactile/slip residual teacher.

Base controller:
    scripted arm/wrist + Stage3.6 learned hand/finger policy

Teacher residual:
    small tactile/slip-driven corrections on hand/finger actuator targets

This is a MuJoCo-only diagnostic. It is not a promoted policy.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch

from arm_hand_stage1_task_api import json_ready
from arm_hand_stage1_v2_bc_common import load_policy
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, Stage3Thresholds


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DATA = ROOT / "data"
CHECKPOINTS = ROOT / "checkpoints"
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import collect_stage3_sensor_fusion_expert_dataset_v0 as collect
import run_stage3_visual_guided_grasp_sweep as sweep
from eval_stage3_phase_hand_policy_v0 import predict_hand_action
from mujoco_egg_pose_sensor import EggPoseSensorConfig, MujocoEggPoseSensor
from mujoco_tactile_slip_sensor import MujocoTactileSlipSensor


DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_phase_hand_policy_v0.pth"
DEFAULT_REPORT = DOCS / "stage3_tactile_residual_teacher_v0_eval_report.md"
DEFAULT_METADATA = META / "stage3_tactile_residual_teacher_v0_eval.json"
DEFAULT_DATASET = DATA / "stage3_tactile_residual_teacher_dataset_v0.npz"

RESIDUAL_PHASES = {
    "gentle_close_fingers",
    "gentle_close_thumb",
    "contact_settle",
    "slow_lift",
    "hold",
}


def close_direction(name: str) -> float:
    lower = str(name).lower()
    if "thumb_cmc_joint" in lower and "abd" not in lower:
        return 0.0
    if "thumb_mcp" in lower:
        return 1.0
    if "finger" in lower or "thumb" in lower or any(key in lower for key in ("index", "middle", "ring", "little")):
        return -1.0
    return 0.0


def phase_allows_residual(phase_name: str, residual_phases: set[str]) -> bool:
    return str(phase_name) in residual_phases


def tactile_residual(
    tactile: dict[str, Any],
    hand_action_names: list[str],
    *,
    phase_name: str,
    phase_progress: float,
    residual_phases: set[str],
    slip_deadband: float,
    crush_deadband: float,
    penetration_deadband_m: float,
    failure_max_penetration_m: float,
    slip_close_gain: float,
    unstable_close_gain: float,
    no_contact_close_gain: float,
    lift_start_close_gain: float,
    lift_start_fraction: float,
    relax_gain: float,
    thumb_multiplier: float,
    max_abs_residual: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    residual = np.zeros(len(hand_action_names), dtype=np.float64)
    if not phase_allows_residual(phase_name, residual_phases):
        return residual, {"mode": "inactive_phase", "slip_drive": 0.0, "relax_drive": 0.0, "close_drive": 0.0}

    contact = bool(tactile.get("contact_present", False))
    grip_stable = bool(tactile.get("grip_stable", False))
    slip = float(tactile.get("slip_score", 0.0))
    crush = float(tactile.get("crush_risk", 0.0))
    penetration = float(tactile.get("max_penetration", 0.0))
    persistence = int(tactile.get("contact_persistence", 0))
    slip_drive = 0.0
    if contact:
        slip_drive = float(np.clip((slip - float(slip_deadband)) / max(1e-9, 1.0 - float(slip_deadband)), 0.0, 1.0))
    unstable_drive = 0.0
    if contact and not grip_stable and persistence >= 20 and phase_name in {"contact_settle", "slow_lift", "hold"}:
        unstable_drive = 1.0
    no_contact_drive = 0.0
    if not contact and phase_name in {"gentle_close_thumb", "contact_settle"}:
        no_contact_drive = 1.0
    lift_start_drive = 0.0
    if phase_name == "slow_lift":
        lift_start_drive = float(np.clip(1.0 - float(phase_progress) / max(1e-9, float(lift_start_fraction)), 0.0, 1.0))
    crush_drive = float(np.clip((crush - float(crush_deadband)) / max(1e-9, 1.0 - float(crush_deadband)), 0.0, 1.0))
    pen_drive = float(
        np.clip(
            (penetration - float(penetration_deadband_m))
            / max(1e-9, float(failure_max_penetration_m) - float(penetration_deadband_m)),
            0.0,
            1.0,
        )
    )
    relax_drive = max(crush_drive, pen_drive)
    close_drive = (
        float(slip_close_gain) * slip_drive
        + float(unstable_close_gain) * unstable_drive
        + float(no_contact_close_gain) * no_contact_drive
        + float(lift_start_close_gain) * lift_start_drive
    )
    relax = float(relax_gain) * relax_drive
    for idx, name in enumerate(hand_action_names):
        direction = close_direction(name)
        if direction == 0.0:
            continue
        multiplier = float(thumb_multiplier) if "thumb" in str(name).lower() else 1.0
        residual[idx] = direction * multiplier * (close_drive - relax)
    residual = np.clip(residual, -float(max_abs_residual), float(max_abs_residual))
    details = {
        "mode": "active",
        "slip_drive": float(slip_drive),
        "unstable_drive": float(unstable_drive),
        "no_contact_drive": float(no_contact_drive),
        "lift_start_drive": float(lift_start_drive),
        "relax_drive": float(relax_drive),
        "close_drive": float(close_drive),
        "max_abs_residual": float(np.max(np.abs(residual))) if residual.size else 0.0,
    }
    return residual, details


def clip_full_action(model, action: np.ndarray) -> np.ndarray:
    return collect.clip_action(model, action)


def collect_rows_to_npz(path: Path, rows: list[dict[str, Any]], checkpoint: dict[str, Any], payload: dict[str, Any]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        obs=np.asarray([row["obs"] for row in rows], dtype=np.float32),
        base_hand_actions=np.asarray([row["base_hand_action"] for row in rows], dtype=np.float32),
        residual_actions=np.asarray([row["residual"] for row in rows], dtype=np.float32),
        final_hand_actions=np.asarray([row["final_hand_action"] for row in rows], dtype=np.float32),
        tactile_scalars=np.asarray([row["tactile_scalars"] for row in rows], dtype=np.float32),
        phase_ids=np.asarray([row["phase_id"] for row in rows], dtype=np.int32),
        episode_ids=np.asarray([row["episode_id"] for row in rows], dtype=np.int32),
        step_ids=np.asarray([row["step_id"] for row in rows], dtype=np.int32),
        hand_action_names=np.asarray(list(checkpoint.get("hand_action_names", [])), dtype=str),
        residual_phase_table=np.asarray(sorted(RESIDUAL_PHASES), dtype=str),
        source_checkpoint=np.asarray([str(payload["checkpoint"])], dtype=str),
        dataset_version=np.asarray(["stage3_tactile_residual_teacher_dataset_v0"], dtype=str),
        metadata_json=np.asarray([json.dumps(json_ready(payload), ensure_ascii=False)], dtype=str),
    )


def run_teacher_episode(model, mujoco, policy, checkpoint: dict[str, Any], trial: sweep.TrialConfig, episode_id: int, args, device: torch.device) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    base_egg_position = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
    rng = np.random.default_rng(int(args.seed) + int(episode_id))
    if float(args.random_offset_std) > 0.0:
        egg_position = egg_position + rng.normal(0.0, float(args.random_offset_std), size=3)
        egg_position[2] = base_egg_position[2] + np.asarray(trial.offset_xyz, dtype=np.float64)[2]
    sweep.reset_episode(model, data, mujoco, egg_position)

    vision_sensor = MujocoEggPoseSensor(
        model,
        mujoco,
        EggPoseSensorConfig(camera_name=args.camera, width=int(args.width), height=int(args.height)),
    )
    vision_estimate = vision_sensor.estimate(data, label=f"stage3_tactile_residual_teacher_{episode_id:04d}_vision_acquire")
    if not collect.accepted_virtual_camera_estimate(vision_estimate, float(args.min_vision_confidence)):
        return (
            {
                "episode_id": int(episode_id),
                "trial": trial.name,
                "status": "FAIL",
                "success": False,
                "terminal_reason": "vision_acquire_failed",
                "failure_reasons": ["vision_acquire_failed"],
            },
            [],
        )
    vision = collect.make_vision_fields(vision_estimate)
    profile = collect.Stage3DatasetProfile("eval_clean_nominal", 1.0, 0.0, 0.0, 0)
    plan = collect.build_episode_plan(model, data, mujoco, trial=trial, egg_position=egg_position, vision_fields=vision, args=args, profile=profile)
    thresholds = Stage3Thresholds()
    tactile_sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=thresholds)
    tactile_sensor.reset(data)
    initial_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    previous_action: np.ndarray | None = None
    previous_residual = np.zeros(int(checkpoint["act_dim"]), dtype=np.float64)
    actuator_names = plan["actuator_names"]
    learned_phases = set(str(name) for name in checkpoint.get("learned_phases", []))
    residual_phases = set(item.strip() for item in str(args.residual_phases).split(",") if item.strip())
    hand_indices = np.asarray(checkpoint["hand_action_indices"], dtype=np.int32)
    hand_action_names = list(checkpoint["hand_action_names"])
    phase_name_to_id = {name: idx for idx, name in enumerate(list(checkpoint["feature_config"]["expert_phase_names"]))}

    contact_acquired = False
    grip_stable_before_lift = False
    first_contact_phase = "none"
    max_slip = 0.0
    max_crush = 0.0
    max_penetration = 0.0
    hold_steps = 0
    hold_stable_steps = 0
    hold_max_slip = 0.0
    contact_settle_steps_actual = 0
    contact_settle_stable_window = 0
    residual_active_steps = 0
    residual_abs_sum = 0.0
    residual_abs_max = 0.0
    trace = []
    dataset_rows: list[dict[str, Any]] = []
    step_count = 0
    approach_true_proxy_error = float("inf")
    approach_est_proxy_error = float("inf")

    for phase_name, start, end, steps in plan["phases"]:
        phase_steps = max(1, int(steps))
        if bool(args.adaptive_contact_settle) and phase_name == "contact_settle":
            phase_steps = max(1, int(args.max_contact_settle_steps))
        for local_step in range(phase_steps):
            progress = local_step / max(1, phase_steps - 1)
            tactile = tactile_sensor.sample(data)
            obs = collect.observation_vector(model, data, vision, tactile, phase_name=phase_name, progress=progress)
            expert_targets = sweep.blend_targets(start, end, progress)
            expert_action = sweep.actuator_targets(model, mujoco, actuator_names, expert_targets)
            base_hand_action = predict_hand_action(
                policy,
                checkpoint,
                obs,
                device=device,
                clip_to_train_range=not bool(args.no_train_range_clip),
            )
            residual, residual_details = tactile_residual(
                tactile,
                hand_action_names,
                phase_name=phase_name,
                phase_progress=progress,
                residual_phases=residual_phases,
                slip_deadband=float(args.slip_deadband),
                crush_deadband=float(args.crush_deadband),
                penetration_deadband_m=float(args.penetration_deadband),
                failure_max_penetration_m=float(thresholds.failure_max_penetration_m),
                slip_close_gain=float(args.slip_close_gain),
                unstable_close_gain=float(args.unstable_close_gain),
                no_contact_close_gain=float(args.no_contact_close_gain),
                lift_start_close_gain=float(args.lift_start_close_gain),
                lift_start_fraction=float(args.lift_start_fraction),
                relax_gain=float(args.relax_gain),
                thumb_multiplier=float(args.thumb_multiplier),
                max_abs_residual=float(args.max_abs_residual),
            )
            if float(args.residual_smoothing) > 0.0:
                smoothing = float(np.clip(args.residual_smoothing, 0.0, 0.99))
                residual = smoothing * previous_residual + (1.0 - smoothing) * residual
                previous_residual = residual.copy()
            final_hand_action = base_hand_action + residual
            if bool(args.clip_residual_to_train_range):
                final_hand_action = np.clip(final_hand_action, checkpoint["action_min"], checkpoint["action_max"])
            action = np.asarray(expert_action, dtype=np.float64).copy()
            used_learned_base = phase_name in learned_phases
            if used_learned_base:
                action[hand_indices] = final_hand_action
            if previous_action is not None and float(args.action_smoothing) > 0.0:
                smoothing = float(np.clip(args.action_smoothing, 0.0, 0.99))
                action = smoothing * previous_action + (1.0 - smoothing) * action
            previous_action = action.copy()
            action = clip_full_action(model, action)
            data.ctrl[:] = action
            mujoco.mj_step(model, data)
            next_tactile = tactile_sensor.sample(data)
            egg_now = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
            lift_height = float(egg_now[2] - initial_egg[2])
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
            if phase_name == "contact_settle":
                contact_settle_steps_actual += 1
                if bool(next_tactile["contact_present"]) and bool(next_tactile["grip_stable"]) and float(next_tactile["slip_score"]) <= float(args.settle_slip_threshold):
                    contact_settle_stable_window += 1
                else:
                    contact_settle_stable_window = 0
            max_slip = max(max_slip, float(next_tactile["slip_score"]))
            max_crush = max(max_crush, float(next_tactile["crush_risk"]))
            max_penetration = max(max_penetration, float(next_tactile.get("max_penetration", 0.0)))
            residual_abs = float(np.max(np.abs(residual))) if residual.size else 0.0
            residual_abs_sum += residual_abs
            residual_abs_max = max(residual_abs_max, residual_abs)
            residual_active_steps += int(residual_abs > 1e-9 and used_learned_base)
            if bool(args.save_dataset) and used_learned_base:
                dataset_rows.append(
                    {
                        "obs": obs.astype(np.float32),
                        "base_hand_action": base_hand_action.astype(np.float32),
                        "residual": residual.astype(np.float32),
                        "final_hand_action": final_hand_action.astype(np.float32),
                        "tactile_scalars": collect.tactile_scalars(next_tactile).astype(np.float32),
                        "phase_id": int(phase_name_to_id.get(phase_name, -1)),
                        "episode_id": int(episode_id),
                        "step_id": int(step_count),
                    }
                )
            if step_count % max(1, int(args.sample_every)) == 0:
                trace.append(
                    {
                        "step": int(step_count),
                        "phase": phase_name,
                        "learned_base": bool(used_learned_base),
                        "residual_abs_max": float(residual_abs),
                        "residual": residual_details,
                        "lift_height_m": lift_height,
                        "contact": bool(next_tactile["contact_present"]),
                        "stable": bool(next_tactile["grip_stable"]),
                        "slip": float(next_tactile["slip_score"]),
                        "crush": float(next_tactile["crush_risk"]),
                        "penetration": float(next_tactile.get("max_penetration", 0.0)),
                    }
                )
            step_count += 1
            if (
                bool(args.adaptive_contact_settle)
                and phase_name == "contact_settle"
                and contact_settle_steps_actual >= int(args.min_contact_settle_steps)
                and contact_settle_stable_window >= int(args.settle_stable_window_steps)
            ):
                break

    final_tactile = tactile_sensor.sample(data)
    final_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    final_contact = sweep.contact_summary(model, data, mujoco)
    hold_duration_s = float(hold_steps) * float(model.opt.timestep)
    hold_stable_fraction = float(hold_stable_steps / max(1, hold_steps))
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
        "max_crush_risk": float(max_crush),
        "max_penetration_m": float(max_penetration),
        "final_floor_contacts": int(final_contact["egg_floor_contact_count"]),
        "finite_state": bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all()),
        "residual_active_steps": int(residual_active_steps),
        "residual_abs_mean": float(residual_abs_sum / max(1, step_count)),
        "residual_abs_max": float(residual_abs_max),
        "contact_settle_steps_actual": int(contact_settle_steps_actual),
        "contact_settle_stable_window": int(contact_settle_stable_window),
        "total_steps": int(step_count),
    }
    reasons = collect.expert_failure_reasons(summary, args, thresholds)
    success = len(reasons) == 0
    risks = []
    if first_contact_phase == "approach":
        risks.append("early_contact_in_approach")
    if max_slip > thresholds.success_max_slip_score:
        risks.append("transient_or_hold_slip")
    return (
        {
            "episode_id": int(episode_id),
            "trial": trial.name,
            "status": "PASS" if success else "FAIL",
            "success": bool(success),
            "terminal_reason": "success_gentle_grasp_hold" if success else (reasons[0] if reasons else "unknown"),
            "failure_reasons": reasons,
            "risk_flags": risks,
            "summary": summary,
            "trace": trace,
            "policy_scope": "stage3_phase_hand_policy_plus_tactile_residual_teacher",
        },
        dataset_rows,
    )


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    success_count = sum(1 for row in results if row["success"])
    reasons: dict[str, int] = {}
    risks: dict[str, int] = {}
    for row in results:
        reasons[row["terminal_reason"]] = reasons.get(row["terminal_reason"], 0) + 1
        for risk in row.get("risk_flags", []):
            risks[risk] = risks.get(risk, 0) + 1
    values = lambda key: np.asarray([row["summary"][key] for row in results if "summary" in row], dtype=np.float64)
    out: dict[str, Any] = {
        "status": "PASS" if success_count == len(results) else ("PARTIAL" if success_count else "FAIL"),
        "episodes": len(results),
        "success_count": int(success_count),
        "terminal_reason_counts": reasons,
        "risk_flag_counts": risks,
    }
    for key in [
        "final_lift_height_m",
        "hold_stable_fraction",
        "hold_max_slip_score",
        "hold_final_slip_score",
        "max_slip_score",
        "max_crush_risk",
        "max_penetration_m",
        "approach_true_proxy_error_m",
        "residual_active_steps",
        "residual_abs_mean",
        "residual_abs_max",
        "contact_settle_steps_actual",
    ]:
        arr = values(key)
        if arr.size:
            out[f"{key}_mean"] = float(np.mean(arr))
            out[f"{key}_max"] = float(np.max(arr))
            out[f"{key}_min"] = float(np.min(arr))
    return out


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = payload["summary"]
    lines = [
        "# Stage3.7 Tactile Residual Teacher V0 Eval Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: **{s['status']}**\n",
        f"- Base checkpoint: `{payload['checkpoint']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Policy scope: `{payload['policy_scope']}`\n",
        f"- Residual phases: `{payload['residual_phases']}`\n",
        f"- Episodes: `{s['episodes']}`\n",
        f"- Success count: `{s['success_count']} / {s['episodes']}`\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n",
        f"- Risk flags: `{s['risk_flag_counts']}`\n",
        f"- Mean final lift: `{s.get('final_lift_height_m_mean', float('nan')):.6f} m`\n",
        f"- Mean hold stable fraction: `{s.get('hold_stable_fraction_mean', float('nan')):.3f}`\n",
        f"- Max transient slip: `{s.get('max_slip_score_max', float('nan')):.3f}`\n",
        f"- Max hold slip: `{s.get('hold_max_slip_score_max', float('nan')):.3f}`\n",
        f"- Max crush risk: `{s.get('max_crush_risk_max', float('nan')):.3f}`\n",
        f"- Max penetration: `{s.get('max_penetration_m_max', float('nan')):.6f} m`\n",
        f"- Mean residual active steps: `{s.get('residual_active_steps_mean', float('nan')):.1f}`\n",
        f"- Mean contact-settle steps: `{s.get('contact_settle_steps_actual_mean', float('nan')):.1f}`\n",
        f"- Max residual magnitude: `{s.get('residual_abs_max_max', float('nan')):.6f}`\n",
    ]
    if payload.get("dataset"):
        lines.append(f"- Residual dataset: `{payload['dataset']}`\n")
    lines.extend(
        [
            "\n## Teacher Parameters\n\n",
            f"- slip deadband: `{payload['teacher_args']['slip_deadband']}`\n",
            f"- slip close gain: `{payload['teacher_args']['slip_close_gain']}`\n",
            f"- unstable close gain: `{payload['teacher_args']['unstable_close_gain']}`\n",
            f"- no-contact close gain: `{payload['teacher_args']['no_contact_close_gain']}`\n",
            f"- lift-start close gain: `{payload['teacher_args']['lift_start_close_gain']}`\n",
            f"- lift-start fraction: `{payload['teacher_args']['lift_start_fraction']}`\n",
            f"- crush deadband: `{payload['teacher_args']['crush_deadband']}`\n",
            f"- penetration deadband: `{payload['teacher_args']['penetration_deadband']}`\n",
            f"- relax gain: `{payload['teacher_args']['relax_gain']}`\n",
            f"- thumb multiplier: `{payload['teacher_args']['thumb_multiplier']}`\n",
            f"- max abs residual: `{payload['teacher_args']['max_abs_residual']}`\n\n",
            f"- adaptive contact settle: `{payload['teacher_args']['adaptive_contact_settle']}`\n",
            f"- min contact settle steps: `{payload['teacher_args']['min_contact_settle_steps']}`\n",
            f"- max contact settle steps: `{payload['teacher_args']['max_contact_settle_steps']}`\n",
            f"- settle stable window steps: `{payload['teacher_args']['settle_stable_window_steps']}`\n",
            f"- settle slip threshold: `{payload['teacher_args']['settle_slip_threshold']}`\n\n",
            "## Episode Results\n\n",
            "| ep | trial | status | reason | residual steps | settle steps | max slip | lift m | stable | hold slip | final slip | crush | pen m | failures |\n",
            "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|\n",
        ]
    )
    for row in payload["results"]:
        if "summary" not in row:
            lines.append(f"| {row['episode_id']} | {row['trial']} | {row['status']} | {row['terminal_reason']} | 0 | 0 | nan | nan | nan | nan | nan | nan | nan | `{row.get('failure_reasons', [])}` |\n")
            continue
        r = row["summary"]
        lines.append(
            f"| {row['episode_id']} | {row['trial']} | {row['status']} | {row['terminal_reason']} | "
            f"{r['residual_active_steps']} | {r['contact_settle_steps_actual']} | {r['max_slip_score']:.3f} | {r['final_lift_height_m']:.5f} | "
            f"{r['hold_stable_fraction']:.3f} | {r['hold_max_slip_score']:.3f} | {r['hold_final_slip_score']:.3f} | "
            f"{r['max_crush_risk']:.3f} | {r['max_penetration_m']:.6f} | `{row.get('failure_reasons', [])}` |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This is a rule-based teacher, not a trained residual policy.\n",
            "- It tests whether tactile/slip fields can provide useful corrective labels before training a model.\n",
            "- Early approach contact is expected to remain unless the arm/wrist approach phase is changed.\n",
            "- A learned residual should only be trained from this teacher if it preserves success and improves at least one risk metric.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Stage3.7 tactile residual teacher.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--save-dataset", action="store_true")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=170)
    parser.add_argument("--random-offset-std", type=float, default=0.0)
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--min-vision-confidence", type=float, default=0.55)
    parser.add_argument("--functional-hit-threshold", type=float, default=0.015)
    parser.add_argument("--max-ik-dxy", type=float, default=0.006)
    parser.add_argument("--max-ik-dz", type=float, default=0.006)
    parser.add_argument("--min-hold-stable-fraction", type=float, default=0.80)
    parser.add_argument("--action-smoothing", type=float, default=0.0)
    parser.add_argument("--no-train-range-clip", action="store_true")
    parser.add_argument("--residual-phases", default="gentle_close_fingers,gentle_close_thumb,contact_settle,slow_lift,hold")
    parser.add_argument("--slip-deadband", type=float, default=0.20)
    parser.add_argument("--slip-close-gain", type=float, default=0.018)
    parser.add_argument("--unstable-close-gain", type=float, default=0.004)
    parser.add_argument("--no-contact-close-gain", type=float, default=0.001)
    parser.add_argument("--lift-start-close-gain", type=float, default=0.012)
    parser.add_argument("--lift-start-fraction", type=float, default=0.35)
    parser.add_argument("--crush-deadband", type=float, default=0.35)
    parser.add_argument("--penetration-deadband", type=float, default=0.004)
    parser.add_argument("--relax-gain", type=float, default=0.030)
    parser.add_argument("--thumb-multiplier", type=float, default=1.3)
    parser.add_argument("--max-abs-residual", type=float, default=0.025)
    parser.add_argument("--residual-smoothing", type=float, default=0.80)
    parser.add_argument("--clip-residual-to-train-range", action="store_true")
    parser.add_argument("--sample-every", type=int, default=200)
    parser.add_argument("--approach-steps", type=int, default=220)
    parser.add_argument("--hand-steps", type=int, default=140)
    parser.add_argument("--close-fingers-steps", type=int, default=180)
    parser.add_argument("--close-thumb-steps", type=int, default=180)
    parser.add_argument("--contact-settle-steps", type=int, default=180)
    parser.add_argument("--adaptive-contact-settle", action="store_true")
    parser.add_argument("--min-contact-settle-steps", type=int, default=180)
    parser.add_argument("--max-contact-settle-steps", type=int, default=1200)
    parser.add_argument("--settle-stable-window-steps", type=int, default=300)
    parser.add_argument("--settle-slip-threshold", type=float, default=0.18)
    parser.add_argument("--lift-steps", type=int, default=700)
    parser.add_argument("--hold-steps", type=int, default=1500)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"
    device = torch.device(args.device)
    import mujoco

    policy, checkpoint = load_policy(args.checkpoint, device)
    model = mujoco.MjModel.from_xml_path(str(Path(args.scene).resolve()))
    trials = sweep.trial_configs()
    results = []
    dataset_rows: list[dict[str, Any]] = []
    for episode_id in range(int(args.episodes)):
        trial = trials[episode_id % len(trials)]
        row, rows = run_teacher_episode(model, mujoco, policy, checkpoint, trial, episode_id, args, device)
        results.append(row)
        dataset_rows.extend(rows)
        summary = row.get("summary", {})
        print(
            f"ep={episode_id:03d} trial={trial.name} {row['status']} reason={row['terminal_reason']} "
            f"max_slip={summary.get('max_slip_score', float('nan')):.3f} "
            f"lift={summary.get('final_lift_height_m', float('nan')):.4f} "
            f"stable={summary.get('hold_stable_fraction', float('nan')):.3f} "
            f"residual_steps={summary.get('residual_active_steps', 0)}"
        )
    dataset_path = str(Path(args.dataset).resolve()) if bool(args.save_dataset) else ""
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "checkpoint_status": checkpoint.get("status"),
        "scene": str(Path(args.scene).resolve()),
        "device": str(device),
        "policy_scope": "stage3_phase_hand_policy_plus_tactile_residual_teacher",
        "residual_phases": [item.strip() for item in str(args.residual_phases).split(",") if item.strip()],
        "teacher_args": {
            "slip_deadband": float(args.slip_deadband),
            "slip_close_gain": float(args.slip_close_gain),
            "unstable_close_gain": float(args.unstable_close_gain),
            "no_contact_close_gain": float(args.no_contact_close_gain),
            "lift_start_close_gain": float(args.lift_start_close_gain),
            "lift_start_fraction": float(args.lift_start_fraction),
            "crush_deadband": float(args.crush_deadband),
            "penetration_deadband": float(args.penetration_deadband),
            "relax_gain": float(args.relax_gain),
            "thumb_multiplier": float(args.thumb_multiplier),
            "max_abs_residual": float(args.max_abs_residual),
            "residual_smoothing": float(args.residual_smoothing),
            "adaptive_contact_settle": bool(args.adaptive_contact_settle),
            "min_contact_settle_steps": int(args.min_contact_settle_steps),
            "max_contact_settle_steps": int(args.max_contact_settle_steps),
            "settle_stable_window_steps": int(args.settle_stable_window_steps),
            "settle_slip_threshold": float(args.settle_slip_threshold),
        },
        "args": vars(args),
        "summary": summarize(results),
        "results": results,
        "dataset": dataset_path,
        "dataset_rows": int(len(dataset_rows)),
        "training_ready": False,
    }
    if bool(args.save_dataset):
        collect_rows_to_npz(Path(args.dataset), dataset_rows, checkpoint, payload)
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, json_ready(payload))
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    if bool(args.save_dataset):
        print(f"Saved dataset: {args.dataset}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
