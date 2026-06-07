#!/usr/bin/env python3
"""Evaluate Stage3.7B tactile-gated phase timing / lift permission.

Base controller:
    scripted arm/wrist + Stage3.6 learned hand/finger policy

Stage3.7B adds conservative phase timing plus a MuJoCo-only tactile gate
between contact_settle and lift:
    wait until contact is present, grip is stable, slip is below threshold, and
    crush/penetration stay below conservative limits for a sustained window.

This script intentionally does not add hand/finger residual actions. Stage3.7A
showed that the useful direction was phase timing, not learned residual labels.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
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
DEFAULT_REPORT = DOCS / "stage3_tactile_phase_gate_v0_eval_report.md"
DEFAULT_METADATA = META / "stage3_tactile_phase_gate_v0_eval.json"


def merge_phase_hand_action(
    expert_action: np.ndarray,
    hand_action: np.ndarray,
    checkpoint: dict[str, Any],
    *,
    phase_name: str,
    learned_phases: set[str],
) -> tuple[np.ndarray, bool]:
    merged = np.asarray(expert_action, dtype=np.float64).copy()
    if phase_name not in learned_phases:
        return merged, False
    hand_indices = np.asarray(checkpoint["hand_action_indices"], dtype=np.int32)
    if hand_indices.size != hand_action.size:
        raise ValueError(f"hand index/action mismatch: {hand_indices.size} vs {hand_action.size}")
    merged[hand_indices] = np.asarray(hand_action, dtype=np.float64)
    return merged, True


def gate_condition_reasons(tactile: dict[str, Any], args, thresholds: Stage3Thresholds) -> list[str]:
    reasons: list[str] = []
    if not bool(tactile.get("contact_present", False)):
        reasons.append("no_contact")
    if not bool(tactile.get("grip_stable", False)):
        reasons.append("grip_not_stable")
    if float(tactile.get("slip_score", 0.0)) > float(args.gate_slip_threshold):
        reasons.append("slip_high")
    if float(tactile.get("crush_risk", 0.0)) > float(args.gate_crush_threshold):
        reasons.append("crush_high")
    penetration_limit = min(float(args.gate_penetration_threshold), float(thresholds.success_max_penetration_m))
    if float(tactile.get("max_penetration", 0.0)) > penetration_limit:
        reasons.append("penetration_high")
    return reasons


def record_phase_metric(metrics: dict[str, dict[str, float]], phase_name: str, tactile: dict[str, Any]) -> None:
    phase = metrics.setdefault(
        phase_name,
        {
            "max_slip_score": 0.0,
            "max_crush_risk": 0.0,
            "max_penetration_m": 0.0,
        },
    )
    phase["max_slip_score"] = max(float(phase["max_slip_score"]), float(tactile.get("slip_score", 0.0)))
    phase["max_crush_risk"] = max(float(phase["max_crush_risk"]), float(tactile.get("crush_risk", 0.0)))
    phase["max_penetration_m"] = max(float(phase["max_penetration_m"]), float(tactile.get("max_penetration", 0.0)))


def run_gate_episode(
    model,
    mujoco,
    policy,
    checkpoint: dict[str, Any],
    trial: sweep.TrialConfig,
    episode_id: int,
    args,
    device: torch.device,
) -> dict[str, Any]:
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
    vision_estimate = vision_sensor.estimate(data, label=f"stage3_tactile_phase_gate_{episode_id:04d}_vision_acquire")
    if not collect.accepted_virtual_camera_estimate(vision_estimate, float(args.min_vision_confidence)):
        return {
            "episode_id": int(episode_id),
            "trial": trial.name,
            "status": "FAIL",
            "success": False,
            "terminal_reason": "vision_acquire_failed",
            "failure_reasons": ["vision_acquire_failed"],
        }

    vision = collect.make_vision_fields(vision_estimate)
    profile = collect.Stage3DatasetProfile("eval_clean_nominal", 1.0, 0.0, 0.0, 0)
    plan = collect.build_episode_plan(
        model,
        data,
        mujoco,
        trial=trial,
        egg_position=egg_position,
        vision_fields=vision,
        args=args,
        profile=profile,
    )
    thresholds = Stage3Thresholds()
    tactile_sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=thresholds)
    tactile_sensor.reset(data)

    initial_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    previous_action: np.ndarray | None = None
    actuator_names = plan["actuator_names"]
    learned_phases = set(str(name) for name in checkpoint.get("learned_phases", []))

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
    learned_control_steps = 0
    contact_settle_steps_actual = 0
    gate_stable_window = 0
    gate_opened = False
    gate_release_reason = "not_reached"
    gate_release_step = 0
    gate_block_counts: Counter[str] = Counter()
    pre_lift_tactile: dict[str, Any] | None = None
    phase_metrics: dict[str, dict[str, float]] = {}
    trace: list[dict[str, Any]] = []
    step_count = 0
    approach_true_proxy_error = float("inf")
    approach_est_proxy_error = float("inf")

    gate_min_steps = max(0, int(args.min_contact_settle_steps))
    gate_max_steps = max(1, int(args.max_contact_settle_steps))
    if gate_max_steps < gate_min_steps:
        gate_max_steps = gate_min_steps

    for phase_name, start, end, steps in plan["phases"]:
        phase_steps = max(1, int(steps))
        if phase_name == "contact_settle":
            phase_steps = gate_max_steps
        for local_step in range(phase_steps):
            progress = local_step / max(1, phase_steps - 1)
            tactile = tactile_sensor.sample(data)
            obs = collect.observation_vector(model, data, vision, tactile, phase_name=phase_name, progress=progress)
            expert_targets = sweep.blend_targets(start, end, progress)
            expert_action = sweep.actuator_targets(model, mujoco, actuator_names, expert_targets)
            hand_action = predict_hand_action(
                policy,
                checkpoint,
                obs,
                device=device,
                clip_to_train_range=not bool(args.no_train_range_clip),
            )
            action, used_learned_hand = merge_phase_hand_action(
                expert_action,
                hand_action,
                checkpoint,
                phase_name=phase_name,
                learned_phases=learned_phases,
            )
            learned_control_steps += int(bool(used_learned_hand))
            if previous_action is not None and float(args.action_smoothing) > 0.0:
                smoothing = float(np.clip(args.action_smoothing, 0.0, 0.99))
                action = smoothing * previous_action + (1.0 - smoothing) * action
            previous_action = action.copy()
            data.ctrl[:] = collect.clip_action(model, action)
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
            if phase_name in {"approach", "pre_contact_align", "gentle_close_fingers", "gentle_close_thumb", "contact_settle"}:
                pre_lift_max_slip = max(pre_lift_max_slip, slip)
            else:
                post_lift_max_slip = max(post_lift_max_slip, slip)
            max_crush = max(max_crush, float(next_tactile["crush_risk"]))
            max_penetration = max(max_penetration, float(next_tactile.get("max_penetration", 0.0)))

            gate_reasons = gate_condition_reasons(next_tactile, args, thresholds)
            if phase_name == "contact_settle":
                contact_settle_steps_actual += 1
                pre_lift_tactile = dict(next_tactile)
                if gate_reasons:
                    gate_stable_window = 0
                    gate_block_counts.update(gate_reasons)
                else:
                    gate_stable_window += 1
                if contact_settle_steps_actual >= gate_min_steps and gate_stable_window >= int(args.settle_stable_window_steps):
                    gate_opened = True
                    gate_release_reason = "stable_window_met"
                    gate_release_step = contact_settle_steps_actual
                elif contact_settle_steps_actual >= gate_max_steps:
                    gate_opened = False
                    gate_release_reason = "max_steps_reached_stable" if not gate_reasons else "max_steps_reached_unstable"
                    gate_release_step = contact_settle_steps_actual

            if step_count % max(1, int(args.sample_every)) == 0:
                trace.append(
                    {
                        "step": int(step_count),
                        "phase": phase_name,
                        "learned_hand": bool(used_learned_hand),
                        "lift_height_m": float(lift_height),
                        "contact": bool(next_tactile["contact_present"]),
                        "stable": bool(next_tactile["grip_stable"]),
                        "slip": float(next_tactile["slip_score"]),
                        "crush": float(next_tactile["crush_risk"]),
                        "penetration": float(next_tactile.get("max_penetration", 0.0)),
                        "gate_window": int(gate_stable_window) if phase_name == "contact_settle" else 0,
                        "gate_block_reasons": gate_reasons if phase_name == "contact_settle" else [],
                    }
                )
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
        "learned_control_steps": int(learned_control_steps),
        "contact_settle_steps_actual": int(contact_settle_steps_actual),
        "gate_opened_before_lift": bool(gate_opened),
        "gate_release_reason": gate_release_reason,
        "gate_release_step": int(gate_release_step),
        "gate_stable_window_at_release": int(gate_stable_window),
        "pre_lift_contact_present": bool(pre_lift_tactile.get("contact_present", False)),
        "pre_lift_grip_stable": bool(pre_lift_tactile.get("grip_stable", False)),
        "pre_lift_slip_score": float(pre_lift_tactile.get("slip_score", 0.0)),
        "pre_lift_crush_risk": float(pre_lift_tactile.get("crush_risk", 0.0)),
        "pre_lift_penetration_m": float(pre_lift_tactile.get("max_penetration", 0.0)),
        "total_steps": int(step_count),
        "phase_metrics": phase_metrics,
        "gate_block_reason_counts": dict(gate_block_counts),
    }
    reasons = collect.expert_failure_reasons(summary, args, thresholds)
    success = len(reasons) == 0
    risks: list[str] = []
    if first_contact_phase == "approach":
        risks.append("early_contact_in_approach")
    if max_slip > thresholds.success_max_slip_score:
        risks.append("transient_or_hold_slip")
    if gate_release_reason == "max_steps_reached_unstable":
        risks.append("lift_gate_forced_unstable")
    if hold_max_slip > thresholds.success_max_slip_score:
        risks.append("hold_slip_high")
    return {
        "episode_id": int(episode_id),
        "trial": trial.name,
        "status": "PASS" if success else "FAIL",
        "success": bool(success),
        "terminal_reason": "success_gentle_grasp_hold" if success else (reasons[0] if reasons else "unknown"),
        "failure_reasons": reasons,
        "risk_flags": risks,
        "summary": summary,
        "trace": trace,
        "policy_scope": "scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_gate",
        "learned_phases": sorted(learned_phases),
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    success_count = sum(1 for row in results if row["success"])
    reasons: dict[str, int] = {}
    risks: dict[str, int] = {}
    gate_reasons: dict[str, int] = {}
    for row in results:
        reasons[row["terminal_reason"]] = reasons.get(row["terminal_reason"], 0) + 1
        for risk in row.get("risk_flags", []):
            risks[risk] = risks.get(risk, 0) + 1
        summary = row.get("summary", {})
        gate_reason = str(summary.get("gate_release_reason", "none"))
        gate_reasons[gate_reason] = gate_reasons.get(gate_reason, 0) + 1

    def values(key: str) -> np.ndarray:
        return np.asarray([row["summary"][key] for row in results if "summary" in row], dtype=np.float64)

    out: dict[str, Any] = {
        "status": "PASS" if success_count == len(results) else ("PARTIAL" if success_count else "FAIL"),
        "episodes": len(results),
        "success_count": int(success_count),
        "terminal_reason_counts": reasons,
        "risk_flag_counts": risks,
        "gate_release_reason_counts": gate_reasons,
    }
    for key in [
        "final_lift_height_m",
        "hold_stable_fraction",
        "hold_max_slip_score",
        "hold_final_slip_score",
        "max_slip_score",
        "pre_lift_max_slip_score",
        "post_lift_max_slip_score",
        "max_crush_risk",
        "max_penetration_m",
        "approach_true_proxy_error_m",
        "learned_control_steps",
        "contact_settle_steps_actual",
        "gate_release_step",
        "gate_stable_window_at_release",
        "pre_lift_slip_score",
        "pre_lift_crush_risk",
        "pre_lift_penetration_m",
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
        "# Stage3.7B Tactile Phase Gate V0 Eval Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: **{s['status']}**\n",
        f"- Base checkpoint: `{payload['checkpoint']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Policy scope: `{payload['policy_scope']}`\n",
        f"- Episodes: `{s['episodes']}`\n",
        f"- Success count: `{s['success_count']} / {s['episodes']}`\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n",
        f"- Risk flags: `{s['risk_flag_counts']}`\n",
        f"- Gate release reasons: `{s['gate_release_reason_counts']}`\n",
        f"- Mean final lift: `{s.get('final_lift_height_m_mean', float('nan')):.6f} m`\n",
        f"- Mean hold stable fraction: `{s.get('hold_stable_fraction_mean', float('nan')):.3f}`\n",
        f"- Mean max transient slip: `{s.get('max_slip_score_mean', float('nan')):.3f}`\n",
        f"- Max transient slip: `{s.get('max_slip_score_max', float('nan')):.3f}`\n",
        f"- Mean pre-lift max slip: `{s.get('pre_lift_max_slip_score_mean', float('nan')):.3f}`\n",
        f"- Mean post-lift max slip: `{s.get('post_lift_max_slip_score_mean', float('nan')):.3f}`\n",
        f"- Max hold slip: `{s.get('hold_max_slip_score_max', float('nan')):.3f}`\n",
        f"- Max crush risk: `{s.get('max_crush_risk_max', float('nan')):.3f}`\n",
        f"- Max penetration: `{s.get('max_penetration_m_max', float('nan')):.6f} m`\n",
        f"- Mean contact-settle steps: `{s.get('contact_settle_steps_actual_mean', float('nan')):.1f}`\n",
        f"- Mean gate stable window at release: `{s.get('gate_stable_window_at_release_mean', float('nan')):.1f}`\n",
        "\n## Gate Parameters\n\n",
        f"- min contact-settle steps: `{payload['gate_args']['min_contact_settle_steps']}`\n",
        f"- max contact-settle steps: `{payload['gate_args']['max_contact_settle_steps']}`\n",
        f"- stable window steps: `{payload['gate_args']['settle_stable_window_steps']}`\n",
        f"- gate slip threshold: `{payload['gate_args']['gate_slip_threshold']}`\n",
        f"- gate crush threshold: `{payload['gate_args']['gate_crush_threshold']}`\n",
        f"- gate penetration threshold: `{payload['gate_args']['gate_penetration_threshold']}`\n",
        "\n## Episode Results\n\n",
        "| ep | trial | status | gate reason | settle | gate window | max slip | pre-lift slip | lift m | stable | hold slip | crush | pen m | risks |\n",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|\n",
    ]
    for row in payload["results"]:
        if "summary" not in row:
            lines.append(f"| {row['episode_id']} | {row['trial']} | {row['status']} | n/a | 0 | 0 | nan | nan | nan | nan | nan | nan | nan | `{row.get('risk_flags', [])}` |\n")
            continue
        r = row["summary"]
        lines.append(
            f"| {row['episode_id']} | {row['trial']} | {row['status']} | {r['gate_release_reason']} | "
            f"{r['contact_settle_steps_actual']} | {r['gate_stable_window_at_release']} | "
            f"{r['max_slip_score']:.3f} | {r['pre_lift_slip_score']:.3f} | "
            f"{r['final_lift_height_m']:.5f} | {r['hold_stable_fraction']:.3f} | "
            f"{r['hold_max_slip_score']:.3f} | {r['max_crush_risk']:.3f} | "
            f"{r['max_penetration_m']:.6f} | `{row.get('risk_flags', [])}` |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This is a MuJoCo-only virtual-camera + synthetic-tactile evaluation.\n",
            "- It preserves the Stage3.6 learned hand policy and adds only lift-permission timing.\n",
            "- It intentionally does not produce hand-residual training labels.\n",
            "- `transient_or_hold_slip` is reported as a risk flag even when hold slip remains below the success threshold.\n",
            "- Early approach contact remains a separate approach-gating problem unless the arm/wrist path is changed.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Stage3.7B tactile phase gate.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
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
    parser.add_argument("--sample-every", type=int, default=200)
    parser.add_argument("--approach-steps", type=int, default=320)
    parser.add_argument("--hand-steps", type=int, default=140)
    parser.add_argument("--close-fingers-steps", type=int, default=180)
    parser.add_argument("--close-thumb-steps", type=int, default=180)
    parser.add_argument("--contact-settle-steps", type=int, default=180)
    parser.add_argument("--min-contact-settle-steps", type=int, default=2000)
    parser.add_argument("--max-contact-settle-steps", type=int, default=2000)
    parser.add_argument("--settle-stable-window-steps", type=int, default=300)
    parser.add_argument("--gate-slip-threshold", type=float, default=0.18)
    parser.add_argument("--gate-crush-threshold", type=float, default=0.35)
    parser.add_argument("--gate-penetration-threshold", type=float, default=0.004)
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
    for episode_id in range(int(args.episodes)):
        trial = trials[episode_id % len(trials)]
        row = run_gate_episode(model, mujoco, policy, checkpoint, trial, episode_id, args, device)
        results.append(row)
        summary = row.get("summary", {})
        print(
            f"ep={episode_id:03d} trial={trial.name} {row['status']} reason={row['terminal_reason']} "
            f"gate={summary.get('gate_release_reason', 'n/a')} "
            f"settle={summary.get('contact_settle_steps_actual', 0)} "
            f"max_slip={summary.get('max_slip_score', float('nan')):.3f} "
            f"hold_slip={summary.get('hold_max_slip_score', float('nan')):.3f} "
            f"lift={summary.get('final_lift_height_m', float('nan')):.4f}"
        )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "checkpoint_status": checkpoint.get("status"),
        "scene": str(Path(args.scene).resolve()),
        "device": str(device),
        "policy_scope": "scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_gate",
        "gate_args": {
            "min_contact_settle_steps": int(args.min_contact_settle_steps),
            "max_contact_settle_steps": int(args.max_contact_settle_steps),
            "settle_stable_window_steps": int(args.settle_stable_window_steps),
            "gate_slip_threshold": float(args.gate_slip_threshold),
            "gate_crush_threshold": float(args.gate_crush_threshold),
            "gate_penetration_threshold": float(args.gate_penetration_threshold),
        },
        "args": vars(args),
        "summary": summarize(results),
        "results": results,
        "training_ready": False,
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, json_ready(payload))
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
