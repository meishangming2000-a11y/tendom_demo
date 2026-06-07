#!/usr/bin/env python3
"""Stage3 dynamic occlusion perception test.

This script keeps Stage3 MuJoCo-only. It uses rendered RGB-D/segmentation as the
policy-visible perception path, while MuJoCo truth is used only for evaluation.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

import run_stage3_visual_guided_grasp_sweep as sweep
from mujoco_egg_pose_sensor import DEFAULT_SCENE, EggPoseSensorConfig, MujocoEggPoseSensor, json_ready, write_json


SENSOR_ROOT = Path(__file__).resolve().parent
DEFAULT_REPORT = SENSOR_ROOT / "reports" / "stage3_dynamic_occlusion_perception_v0.md"
DEFAULT_METADATA = SENSOR_ROOT / "metadata" / "stage3_dynamic_occlusion_perception_v0.json"
DEFAULT_VISUAL_DIR = SENSOR_ROOT / "visual_checks" / "stage3_dynamic_occlusion_perception_v0"

CONTROL_WINDOW_PHASES = {
    "initial_acquire",
    "pre_approach",
    "approach",
    "preshape",
    "close_fingers",
    "close_thumb",
    "close_hold",
}
DEFAULT_DEBUG_TRIALS = {"center_nominal", "right_high_nominal", "lifted_diag"}
DEFAULT_DEBUG_STAGES = {"initial_acquire", "pre_approach", "approach", "close_thumb", "hold_lift"}


def parse_name_set(value: str | None, default: set[str]) -> set[str]:
    if value is None:
        return set(default)
    if value.strip().lower() in {"", "none", "off"}:
        return set()
    if value.strip().lower() in {"all", "*"}:
        return {"*"}
    return {item.strip() for item in value.split(",") if item.strip()}


def name_enabled(name: str, enabled: set[str]) -> bool:
    return "*" in enabled or name in enabled


def make_perception_sample(
    *,
    sensor: MujocoEggPoseSensor,
    model,
    data,
    mujoco,
    stage: str,
    debug_dir: Path | None,
    label: str,
    initial_mask_pixels: int | None,
    args: argparse.Namespace,
) -> dict[str, Any]:
    estimate = sensor.estimate(data, debug_dir=debug_dir, label=label)
    truth = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    mask_pixels = int(estimate.get("mask_pixels", 0))
    raw_confidence = float(estimate.get("confidence", 0.0))
    if initial_mask_pixels is None or initial_mask_pixels <= 0:
        mask_retention = 1.0 if mask_pixels > 0 else 0.0
    else:
        mask_retention = float(mask_pixels / max(1, int(initial_mask_pixels)))
    tracking_confidence = float(np.clip(raw_confidence * min(1.0, mask_retention), 0.0, 1.0))
    status_ok = estimate.get("status") == "ok"
    position_est = None
    position_error = math.inf
    if status_ok:
        position_est = np.asarray(estimate["position_world_est"], dtype=np.float64).copy()
        position_error = float(np.linalg.norm(position_est - truth))

    low_visibility = bool(mask_retention < float(args.low_visibility_ratio))
    accepted = bool(
        status_ok
        and mask_pixels >= int(args.accept_min_mask_pixels)
        and tracking_confidence >= float(args.min_tracking_confidence)
    )
    false_confident_bad = bool(accepted and position_error > float(args.bad_estimate_error))
    confidence_not_reduced = bool(
        low_visibility and tracking_confidence > float(args.low_visibility_tracking_confidence_max)
    )

    return {
        "stage": stage,
        "sensor_status": estimate.get("status", "failed"),
        "sensor_reason": estimate.get("reason"),
        "mask_pixels": mask_pixels,
        "mask_retention_ratio": mask_retention,
        "raw_confidence": raw_confidence,
        "tracking_confidence": tracking_confidence,
        "low_visibility": low_visibility,
        "accepted_as_pose_update": accepted,
        "fallback_action": "update_last_good" if accepted else "freeze_last_good",
        "false_confident_bad_estimate": false_confident_bad,
        "confidence_not_reduced_under_low_visibility": confidence_not_reduced,
        "position_world_est": position_est,
        "truth_position_world": truth,
        "position_error_m": position_error,
        "debug_images": estimate.get("debug_images", {}),
    }


def summarize_samples(samples: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    accepted_errors = [
        float(row["position_error_m"])
        for row in samples
        if row.get("accepted_as_pose_update") and np.isfinite(float(row.get("position_error_m", math.inf)))
    ]
    all_errors = [
        float(row["position_error_m"])
        for row in samples
        if row.get("sensor_status") == "ok" and np.isfinite(float(row.get("position_error_m", math.inf)))
    ]
    control_last_good_errors = [
        float(row["last_good_error_m"])
        for row in samples
        if row.get("stage") in CONTROL_WINDOW_PHASES and np.isfinite(float(row.get("last_good_error_m", math.inf)))
    ]
    final_last_good_errors = [
        float(row["last_good_error_m"])
        for row in samples
        if np.isfinite(float(row.get("last_good_error_m", math.inf)))
    ]
    low_visibility_rows = [row for row in samples if row.get("low_visibility")]
    out: dict[str, Any] = {
        "samples": len(samples),
        "sensor_ok_samples": int(sum(1 for row in samples if row.get("sensor_status") == "ok")),
        "accepted_updates": int(sum(1 for row in samples if row.get("accepted_as_pose_update"))),
        "frozen_updates": int(sum(1 for row in samples if not row.get("accepted_as_pose_update"))),
        "low_visibility_samples": len(low_visibility_rows),
        "false_confident_bad_estimates": int(sum(1 for row in samples if row.get("false_confident_bad_estimate"))),
        "confidence_not_reduced_under_low_visibility": int(
            sum(1 for row in samples if row.get("confidence_not_reduced_under_low_visibility"))
        ),
        "min_mask_retention_ratio": float(min((float(row["mask_retention_ratio"]) for row in samples), default=math.inf)),
        "min_tracking_confidence": float(min((float(row["tracking_confidence"]) for row in samples), default=math.inf)),
        "accept_min_mask_pixels": int(args.accept_min_mask_pixels),
        "min_tracking_confidence_threshold": float(args.min_tracking_confidence),
        "bad_estimate_error_threshold_m": float(args.bad_estimate_error),
        "last_good_control_error_threshold_m": float(args.last_good_control_error_threshold),
    }
    if accepted_errors:
        out["max_accepted_error_m"] = float(max(accepted_errors))
        out["mean_accepted_error_m"] = float(np.mean(accepted_errors))
    if all_errors:
        out["max_sensor_ok_error_m"] = float(max(all_errors))
        out["mean_sensor_ok_error_m"] = float(np.mean(all_errors))
    if control_last_good_errors:
        out["max_last_good_control_error_m"] = float(max(control_last_good_errors))
    if final_last_good_errors:
        out["max_last_good_any_phase_error_m"] = float(max(final_last_good_errors))
        out["final_last_good_error_m"] = float(final_last_good_errors[-1])
    return out


def perception_failure_reasons(row: dict[str, Any], args: argparse.Namespace) -> list[str]:
    reasons: list[str] = []
    summary = row.get("perception_summary", {})
    initial = row.get("initial_perception", {})
    if not initial.get("accepted_as_pose_update", False):
        reasons.append("initial_acquire_failed")
    if int(summary.get("false_confident_bad_estimates", 0)) > 0:
        reasons.append("false_confident_bad_estimate")
    if int(summary.get("confidence_not_reduced_under_low_visibility", 0)) > 0:
        reasons.append("low_visibility_confidence_not_reduced")
    if float(summary.get("max_last_good_control_error_m", math.inf)) > float(args.last_good_control_error_threshold):
        reasons.append("last_good_control_error_too_large")
    return reasons


def run_dynamic_visual_episode(
    model,
    mujoco,
    *,
    trial: sweep.TrialConfig,
    egg_position: np.ndarray,
    sensor: MujocoEggPoseSensor,
    args: argparse.Namespace,
    visual_dir: Path,
    debug_trials: set[str],
    debug_stages: set[str],
) -> dict[str, Any]:
    data = mujoco.MjData(model)
    sweep.reset_episode(model, data, mujoco, egg_position)
    actuator_names = sweep.base.actuator_names(model, mujoco)
    grasp_local = sweep.DEFAULT_GRASP_LOCAL.copy()
    solver = sweep.ArmProxyIkSolver(model, mujoco, grasp_local)
    debug_this_trial = name_enabled(trial.name, debug_trials)

    def sample_debug_dir(stage: str) -> Path | None:
        if debug_this_trial and name_enabled(stage, debug_stages):
            return visual_dir / trial.name / "sensor"
        return None

    samples: list[dict[str, Any]] = []
    initial_sample = make_perception_sample(
        sensor=sensor,
        model=model,
        data=data,
        mujoco=mujoco,
        stage="initial_acquire",
        debug_dir=sample_debug_dir("initial_acquire"),
        label=f"{trial.name}_initial_acquire",
        initial_mask_pixels=None,
        args=args,
    )
    initial_mask_pixels = int(initial_sample.get("mask_pixels", 0))
    last_good_position = None
    last_good_stage = None
    if initial_sample["accepted_as_pose_update"]:
        last_good_position = np.asarray(initial_sample["position_world_est"], dtype=np.float64).copy()
        last_good_stage = "initial_acquire"
    initial_sample["last_good_position"] = last_good_position
    initial_sample["last_good_stage"] = last_good_stage
    initial_sample["last_good_error_m"] = (
        float(np.linalg.norm(last_good_position - initial_sample["truth_position_world"]))
        if last_good_position is not None
        else math.inf
    )
    samples.append(initial_sample)

    if last_good_position is None:
        row = {
            "trial": trial.name,
            "target_source": "visual_dynamic",
            "trial_config": asdict(trial),
            "sensor_status": initial_sample["sensor_status"],
            "sensor_confidence": initial_sample["raw_confidence"],
            "sensor_tracking_confidence": initial_sample["tracking_confidence"],
            "sensor_mask_pixels": initial_sample["mask_pixels"],
            "initial_perception": initial_sample,
            "perception_samples": samples,
            "perception_summary": summarize_samples(samples, args),
            "success": False,
            "failure_reasons": ["initial_acquire_failed"],
        }
        return row

    target_position_for_ik = np.asarray(last_good_position, dtype=np.float64).copy()
    approach_target = target_position_for_ik.copy()
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
    data.ctrl[:] = sweep.actuator_targets(model, mujoco, actuator_names, pre_arm)
    mujoco.mj_forward(model, data)
    initial_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()

    def record_sample(stage: str) -> dict[str, Any]:
        nonlocal last_good_position, last_good_stage
        sample = make_perception_sample(
            sensor=sensor,
            model=model,
            data=data,
            mujoco=mujoco,
            stage=stage,
            debug_dir=sample_debug_dir(stage),
            label=f"{trial.name}_{stage}",
            initial_mask_pixels=initial_mask_pixels,
            args=args,
        )
        if sample["accepted_as_pose_update"]:
            last_good_position = np.asarray(sample["position_world_est"], dtype=np.float64).copy()
            last_good_stage = stage
        sample["last_good_position"] = last_good_position.copy() if last_good_position is not None else None
        sample["last_good_stage"] = last_good_stage
        sample["last_good_error_m"] = (
            float(np.linalg.norm(last_good_position - sample["truth_position_world"]))
            if last_good_position is not None
            else math.inf
        )
        samples.append(sample)
        return sample

    pre_sample = record_sample("pre_approach")

    hand_targets = {
        "preshape": {**approach_arm, **sweep.base.PRESHAPE_TARGETS},
        "close_fingers": {**approach_arm, **sweep.base.LONG_FINGER_TARGETS},
        "close_thumb": {**approach_arm, **sweep.base.LONG_FINGER_TARGETS, **sweep.base.THUMB_SMOKE_TARGETS},
        "lift": {**lift_arm, **sweep.base.LONG_FINGER_TARGETS, **sweep.base.THUMB_SMOKE_TARGETS},
    }
    phases = [
        ("approach", pre_arm, approach_arm, args.approach_steps),
        ("preshape", approach_arm, hand_targets["preshape"], args.hand_steps),
        ("close_fingers", hand_targets["preshape"], hand_targets["close_fingers"], args.close_fingers_steps),
        ("close_thumb", hand_targets["close_fingers"], hand_targets["close_thumb"], args.close_thumb_steps),
        ("close_hold", hand_targets["close_thumb"], hand_targets["close_thumb"], trial.close_hold_steps),
        ("lift", hand_targets["close_thumb"], hand_targets["lift"], args.lift_steps),
        ("hold_lift", hand_targets["lift"], hand_targets["lift"], args.hold_steps),
    ]

    phase_rows: list[dict[str, Any]] = []
    max_hand_contacts = 0
    max_penetration_seen = 0.0
    approach_true_proxy_error = math.inf
    approach_est_proxy_error = math.inf
    screenshots: dict[str, str] = {}
    for phase_name, start, end, steps in phases:
        sweep.run_phase(model, data, mujoco, actuator_names, start, end, int(steps))
        egg_now = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
        proxy_now = sweep.proxy_position(model, data, mujoco, grasp_local)
        contact = sweep.contact_summary(model, data, mujoco)
        max_hand_contacts = max(max_hand_contacts, int(contact["egg_hand_contact_count"]))
        max_penetration_seen = max(max_penetration_seen, float(contact["max_penetration_m"]))
        if phase_name == "approach":
            approach_true_proxy_error = float(np.linalg.norm(proxy_now - initial_egg))
            approach_est_proxy_error = float(np.linalg.norm(proxy_now - approach_target))
        perception_sample = record_sample(phase_name)
        phase_rows.append(
            {
                "phase": phase_name,
                "egg_position": egg_now,
                "egg_lift_height_m": float(egg_now[2] - initial_egg[2]),
                "proxy_position": proxy_now,
                "contact": contact,
                "perception": perception_sample,
            }
        )
        if (
            args.render_snapshots
            and debug_this_trial
            and phase_name in {"approach", "close_thumb", "hold_lift"}
        ):
            screenshots[phase_name] = sweep.render_trial_snapshot(
                model,
                data,
                mujoco,
                visual_dir / trial.name / f"visual_dynamic_{phase_name}.png",
            )

    final_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    final_contact = sweep.contact_summary(model, data, mujoco)
    finite = bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all())
    final_lift = float(final_egg[2] - initial_egg[2])
    row = {
        "trial": trial.name,
        "target_source": "visual_dynamic",
        "trial_config": asdict(trial),
        "sensor_status": initial_sample["sensor_status"],
        "sensor_confidence": initial_sample["raw_confidence"],
        "sensor_tracking_confidence": initial_sample["tracking_confidence"],
        "sensor_mask_pixels": initial_sample["mask_pixels"],
        "initial_perception": initial_sample,
        "pre_approach_perception": pre_sample,
        "egg_initial_position": initial_egg,
        "target_position_for_ik": target_position_for_ik,
        "approach_target": approach_target,
        "ik_approach_dxy_m": approach_solution["dxy"],
        "ik_approach_dz_m": approach_solution["dz"],
        "ik_lift_dxy_m": lift_solution["dxy"],
        "ik_lift_dz_m": lift_solution["dz"],
        "approach_true_proxy_error_m": float(approach_true_proxy_error),
        "approach_est_proxy_error_m": float(approach_est_proxy_error),
        "final_egg_position": final_egg,
        "final_lift_height_m": final_lift,
        "max_hand_contacts": int(max_hand_contacts),
        "final_hand_contacts": int(final_contact["egg_hand_contact_count"]),
        "final_floor_contacts": int(final_contact["egg_floor_contact_count"]),
        "max_penetration_m": float(max_penetration_seen),
        "finite_state": finite,
        "phase_rows": phase_rows,
        "perception_samples": samples,
        "perception_summary": summarize_samples(samples, args),
        "screenshots": screenshots,
    }
    row["precision_hit_pass"] = float(row["approach_true_proxy_error_m"]) <= float(args.precision_hit_threshold)
    row["functional_hit_pass"] = float(row["approach_true_proxy_error_m"]) <= float(args.functional_hit_threshold)
    task_reasons = sweep.trial_failure_reasons(
        row,
        success_lift_height=args.success_lift_height,
        max_penetration=args.max_success_penetration,
        functional_hit_threshold=args.functional_hit_threshold,
    )
    perception_reasons = perception_failure_reasons(row, args)
    row["task_failure_reasons"] = task_reasons
    row["perception_failure_reasons"] = perception_reasons
    row["failure_reasons"] = task_reasons + perception_reasons
    row["success"] = len(row["failure_reasons"]) == 0
    return row


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "episodes": len(rows),
        "successes": int(sum(1 for row in rows if row.get("success"))),
        "failures": int(sum(1 for row in rows if not row.get("success"))),
    }
    for key in ["final_lift_height_m", "approach_true_proxy_error_m", "max_penetration_m"]:
        values = np.asarray([float(row[key]) for row in rows if key in row and np.isfinite(float(row[key]))])
        if values.size:
            out[f"{key}_mean"] = float(np.mean(values))
            out[f"{key}_max"] = float(np.max(values))
            out[f"{key}_min"] = float(np.min(values))
    reasons: dict[str, int] = {}
    for row in rows:
        for reason in row.get("failure_reasons", []):
            reasons[reason] = reasons.get(reason, 0) + 1
    out["failure_reasons"] = reasons
    return out


def summarize_perception(rows: list[dict[str, Any]]) -> dict[str, Any]:
    samples = [sample for row in rows for sample in row.get("perception_samples", [])]
    accepted_errors = [
        float(sample["position_error_m"])
        for sample in samples
        if sample.get("accepted_as_pose_update") and np.isfinite(float(sample.get("position_error_m", math.inf)))
    ]
    control_last_good = [
        float(sample["last_good_error_m"])
        for sample in samples
        if sample.get("stage") in CONTROL_WINDOW_PHASES and np.isfinite(float(sample.get("last_good_error_m", math.inf)))
    ]
    phase_summary: dict[str, dict[str, Any]] = {}
    for sample in samples:
        phase = str(sample.get("stage"))
        item = phase_summary.setdefault(
            phase,
            {
                "samples": 0,
                "accepted_updates": 0,
                "low_visibility_samples": 0,
                "min_mask_retention_ratio": math.inf,
                "max_position_error_m": 0.0,
            },
        )
        item["samples"] += 1
        item["accepted_updates"] += int(bool(sample.get("accepted_as_pose_update")))
        item["low_visibility_samples"] += int(bool(sample.get("low_visibility")))
        item["min_mask_retention_ratio"] = min(
            float(item["min_mask_retention_ratio"]),
            float(sample.get("mask_retention_ratio", math.inf)),
        )
        if np.isfinite(float(sample.get("position_error_m", math.inf))):
            item["max_position_error_m"] = max(float(item["max_position_error_m"]), float(sample["position_error_m"]))

    out: dict[str, Any] = {
        "samples": len(samples),
        "sensor_ok_samples": int(sum(1 for sample in samples if sample.get("sensor_status") == "ok")),
        "accepted_updates": int(sum(1 for sample in samples if sample.get("accepted_as_pose_update"))),
        "frozen_updates": int(sum(1 for sample in samples if not sample.get("accepted_as_pose_update"))),
        "low_visibility_samples": int(sum(1 for sample in samples if sample.get("low_visibility"))),
        "false_confident_bad_estimates": int(sum(1 for sample in samples if sample.get("false_confident_bad_estimate"))),
        "confidence_not_reduced_under_low_visibility": int(
            sum(1 for sample in samples if sample.get("confidence_not_reduced_under_low_visibility"))
        ),
        "phase_summary": phase_summary,
    }
    if accepted_errors:
        out["max_accepted_error_m"] = float(max(accepted_errors))
        out["mean_accepted_error_m"] = float(np.mean(accepted_errors))
    if control_last_good:
        out["max_last_good_control_error_m"] = float(max(control_last_good))
    return out


def pair_summary(visual_rows: list[dict[str, Any]], oracle_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    oracle_by_trial = {row["trial"]: row for row in oracle_rows}
    rows: list[dict[str, Any]] = []
    for visual in visual_rows:
        oracle = oracle_by_trial.get(visual["trial"])
        summary = visual.get("perception_summary", {})
        rows.append(
            {
                "trial": visual["trial"],
                "visual_success": bool(visual.get("success")),
                "oracle_success": bool(oracle.get("success")) if oracle is not None else False,
                "visual_lift_m": float(visual.get("final_lift_height_m", math.nan)),
                "oracle_lift_m": float(oracle.get("final_lift_height_m", math.nan)) if oracle is not None else math.nan,
                "low_visibility_samples": int(summary.get("low_visibility_samples", 0)),
                "frozen_updates": int(summary.get("frozen_updates", 0)),
                "max_accepted_error_m": float(summary.get("max_accepted_error_m", math.nan)),
                "max_last_good_control_error_m": float(summary.get("max_last_good_control_error_m", math.nan)),
                "final_last_good_error_m": float(summary.get("final_last_good_error_m", math.nan)),
                "failure_reasons": list(visual.get("failure_reasons", [])),
                "oracle_failure_reasons": list(oracle.get("failure_reasons", [])) if oracle is not None else ["missing_oracle"],
            }
        )
    return rows


def write_report(path: Path, payload: dict[str, Any]) -> None:
    visual_summary = payload["summary_visual"]
    oracle_summary = payload["summary_oracle"]
    perception_summary = payload["summary_perception"]
    lines = [
        "# Stage3 Dynamic Occlusion Perception V0\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "This MuJoCo-only Stage3 test checks perception during the actual approach, closure, lift, and hold phases. It re-renders from the perception camera at each phase boundary, applies a last-good tracking decision, and compares the resulting sensor output against MuJoCo truth for evaluation only.\n\n",
        "## Gate\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Perception camera: `{payload['camera']}`\n",
        f"- Trial groups: `{payload['trial_groups']}`\n",
        f"- Visual dynamic episodes: `{visual_summary['episodes']}`\n",
        f"- Oracle episodes: `{oracle_summary['episodes']}`\n",
        f"- Runtime tracking confidence: `raw_confidence * relative_mask_retention`\n",
        f"- Accepted update threshold: confidence >= `{payload['thresholds']['min_tracking_confidence']:.3f}`, mask pixels >= `{payload['thresholds']['accept_min_mask_pixels']}`\n",
        f"- Bad accepted estimate threshold: `{payload['thresholds']['bad_estimate_error_m']:.3f} m`\n",
        f"- Last-good control-window threshold: `{payload['thresholds']['last_good_control_error_threshold_m']:.3f} m`\n\n",
        "## Overall Result\n\n",
        f"- Visual dynamic success: `{visual_summary['successes']}` / `{visual_summary['episodes']}`\n",
        f"- Oracle success: `{oracle_summary['successes']}` / `{oracle_summary['episodes']}`\n",
        f"- Perception samples: `{perception_summary['samples']}`\n",
        f"- Accepted pose updates: `{perception_summary['accepted_updates']}`\n",
        f"- Frozen last-good updates: `{perception_summary['frozen_updates']}`\n",
        f"- Low-visibility samples: `{perception_summary['low_visibility_samples']}`\n",
        f"- False confident bad estimates: `{perception_summary['false_confident_bad_estimates']}`\n",
        f"- Max accepted pose error: `{perception_summary.get('max_accepted_error_m', float('nan')):.6f} m`\n",
        f"- Max last-good error before lift/control handoff: `{perception_summary.get('max_last_good_control_error_m', float('nan')):.6f} m`\n\n",
        "## Trial Results\n\n",
        "| trial | visual | oracle | visual lift m | oracle lift m | low-vis | frozen | max accepted err m | max last-good control err m | final last-good err m | visual failure | oracle failure |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|\n",
    ]
    for row in payload["paired_results"]:
        lines.append(
            f"| {row['trial']} | {int(row['visual_success'])} | {int(row['oracle_success'])} | "
            f"{row['visual_lift_m']:.5f} | {row['oracle_lift_m']:.5f} | "
            f"{row['low_visibility_samples']} | {row['frozen_updates']} | "
            f"{row['max_accepted_error_m']:.6f} | {row['max_last_good_control_error_m']:.6f} | "
            f"{row['final_last_good_error_m']:.6f} | `{row['failure_reasons']}` | `{row['oracle_failure_reasons']}` |\n"
        )
    lines.extend(["\n## Phase Visibility Summary\n\n"])
    lines.extend(
        [
            "| stage | samples | accepted | low-vis | min mask retention | max pose err m |\n",
            "|---|---:|---:|---:|---:|---:|\n",
        ]
    )
    phase_order = [
        "initial_acquire",
        "pre_approach",
        "approach",
        "preshape",
        "close_fingers",
        "close_thumb",
        "close_hold",
        "lift",
        "hold_lift",
    ]
    phase_summary = perception_summary.get("phase_summary", {})
    for phase in phase_order:
        if phase not in phase_summary:
            continue
        item = phase_summary[phase]
        lines.append(
            f"| {phase} | {item['samples']} | {item['accepted_updates']} | "
            f"{item['low_visibility_samples']} | {item['min_mask_retention_ratio']:.3f} | "
            f"{item['max_position_error_m']:.6f} |\n"
        )
    lines.extend(["\n## Interpretation\n\n"])
    if visual_summary["successes"] == visual_summary["episodes"] and int(perception_summary["false_confident_bad_estimates"]) == 0:
        lines.append("- Dynamic perception passed the current control-window gate: no accepted estimate was badly wrong, and the visual-guided grasp/lift still matched the oracle success rate.\n")
    else:
        lines.append("- Dynamic perception did not fully pass; inspect the listed failure reasons before expanding the perception model.\n")
    if int(perception_summary["low_visibility_samples"]) > 0:
        lines.append("- Low-visibility samples occurred, and the tracker used last-good freezing rather than blindly accepting every rendered pose.\n")
    else:
        lines.append("- This run did not create heavy low-visibility cases; the next useful stress test is a synthetic occluder/noisy-mask probe.\n")
    lines.extend(
        [
            "- The final last-good error after lift is diagnostic only. Once the egg is in hand, control should increasingly rely on contact/tactile/slip abstractions rather than camera-only pose tracking.\n",
            "- This is not a real-camera or hardware integration test.\n\n",
            f"Metadata: `{payload['metadata']}`\n",
            f"Visual checks: `{payload['visual_dir']}`\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Stage3 dynamic occlusion perception test.")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
    parser.add_argument("--max-trials", type=int, default=None)
    parser.add_argument("--accept-min-mask-pixels", type=int, default=500)
    parser.add_argument("--min-tracking-confidence", type=float, default=0.55)
    parser.add_argument("--low-visibility-ratio", type=float, default=0.70)
    parser.add_argument("--low-visibility-tracking-confidence-max", type=float, default=0.55)
    parser.add_argument("--bad-estimate-error", type=float, default=0.015)
    parser.add_argument("--last-good-control-error-threshold", type=float, default=0.025)
    parser.add_argument("--success-lift-height", type=float, default=0.05)
    parser.add_argument("--precision-hit-threshold", type=float, default=0.008)
    parser.add_argument("--functional-hit-threshold", type=float, default=0.015)
    parser.add_argument("--max-success-penetration", type=float, default=0.012)
    parser.add_argument("--approach-steps", type=int, default=200)
    parser.add_argument("--hand-steps", type=int, default=120)
    parser.add_argument("--close-fingers-steps", type=int, default=160)
    parser.add_argument("--close-thumb-steps", type=int, default=160)
    parser.add_argument("--lift-steps", type=int, default=300)
    parser.add_argument("--hold-steps", type=int, default=120)
    parser.add_argument("--debug-trials", default=",".join(sorted(DEFAULT_DEBUG_TRIALS)))
    parser.add_argument("--debug-stages", default=",".join(sorted(DEFAULT_DEBUG_STAGES)))
    parser.add_argument("--render-snapshots", action=argparse.BooleanOptionalAction, default=True)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    scene = Path(args.scene).resolve()
    report = Path(args.report).resolve()
    metadata = Path(args.metadata).resolve()
    visual_dir = Path(args.visual_dir).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)

    import mujoco

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    base_egg_position = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    sensor = MujocoEggPoseSensor(
        model,
        mujoco,
        EggPoseSensorConfig(
            camera_name=args.camera,
            width=int(args.width),
            height=int(args.height),
        ),
    )
    debug_trials = parse_name_set(args.debug_trials, DEFAULT_DEBUG_TRIALS)
    debug_stages = parse_name_set(args.debug_stages, DEFAULT_DEBUG_STAGES)
    trials = sweep.trial_configs()
    if args.max_trials is not None:
        trials = trials[: max(0, int(args.max_trials))]

    visual_rows: list[dict[str, Any]] = []
    oracle_rows: list[dict[str, Any]] = []
    for trial in trials:
        egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
        visual_row = run_dynamic_visual_episode(
            model,
            mujoco,
            trial=trial,
            egg_position=egg_position,
            sensor=sensor,
            args=args,
            visual_dir=visual_dir,
            debug_trials=debug_trials,
            debug_stages=debug_stages,
        )
        oracle_row = sweep.run_one_episode(
            model,
            mujoco,
            trial=trial,
            target_source="oracle",
            egg_position=egg_position,
            target_position_for_ik=egg_position,
            sensor_estimate=None,
            args=args,
            visual_dir=visual_dir,
        )
        visual_rows.append(visual_row)
        oracle_rows.append(oracle_row)
        ps = visual_row.get("perception_summary", {})
        print(
            f"{trial.name}: visual={visual_row.get('success')} oracle={oracle_row.get('success')} "
            f"low_vis={ps.get('low_visibility_samples', 0)} frozen={ps.get('frozen_updates', 0)} "
            f"max_acc_err={ps.get('max_accepted_error_m', math.nan):.5f}"
        )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(scene),
        "camera": str(args.camera),
        "trial_groups": len(trials),
        "thresholds": {
            "accept_min_mask_pixels": int(args.accept_min_mask_pixels),
            "min_tracking_confidence": float(args.min_tracking_confidence),
            "low_visibility_ratio": float(args.low_visibility_ratio),
            "low_visibility_tracking_confidence_max": float(args.low_visibility_tracking_confidence_max),
            "bad_estimate_error_m": float(args.bad_estimate_error),
            "last_good_control_error_threshold_m": float(args.last_good_control_error_threshold),
            "success_lift_height_m": float(args.success_lift_height),
            "precision_hit_threshold_m": float(args.precision_hit_threshold),
            "functional_hit_threshold_m": float(args.functional_hit_threshold),
            "max_success_penetration_m": float(args.max_success_penetration),
        },
        "visual_results": visual_rows,
        "oracle_results": oracle_rows,
        "paired_results": pair_summary(visual_rows, oracle_rows),
        "summary_visual": summarize_rows(visual_rows),
        "summary_oracle": summarize_rows(oracle_rows),
        "summary_perception": summarize_perception(visual_rows),
        "metadata": str(metadata),
        "visual_dir": str(visual_dir),
    }
    write_json(metadata, payload)
    report_payload = json.loads(json.dumps(json_ready(payload)))
    write_report(report, report_payload)
    print(f"Visual dynamic successes: {payload['summary_visual']['successes']} / {payload['summary_visual']['episodes']}")
    print(f"Oracle successes: {payload['summary_oracle']['successes']} / {payload['summary_oracle']['episodes']}")
    print(f"Report: {report}")
    print(f"Metadata: {metadata}")


if __name__ == "__main__":
    main()
