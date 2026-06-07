#!/usr/bin/env python3
"""Evaluate Stage3.7C contact-transition gating.

Base controller:
    scripted arm/wrist + Stage3.6 learned hand/finger policy
    + Stage3.7B tactile lift-permission gate

Stage3.7C adds contact-transition handling before the lift gate:
    - optionally stop approach early once contact is detected near the target
    - pause slow-lift progress while tactile slip is high

This is still MuJoCo-only virtual-camera + synthetic tactile work. It is a
repair probe for the remaining transient-slip peaks, not a hardware interface.
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
from eval_stage3_tactile_phase_gate_v0 import gate_condition_reasons, merge_phase_hand_action, record_phase_metric
from mujoco_egg_pose_sensor import EggPoseSensorConfig, MujocoEggPoseSensor
from mujoco_tactile_slip_sensor import MujocoTactileSlipSensor


DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_phase_hand_policy_v0.pth"
DEFAULT_REPORT = DOCS / "stage3_contact_transition_gate_v0_eval_report.md"
DEFAULT_METADATA = META / "stage3_contact_transition_gate_v0_eval.json"


def parse_phase_set(value: str) -> set[str]:
    return {item.strip() for item in str(value).split(",") if item.strip()}


def transition_gate_reasons(tactile: dict[str, Any], *, phase_name: str, transition_phases: set[str], args) -> list[str]:
    if phase_name not in transition_phases:
        return []
    if not bool(tactile.get("contact_present", False)):
        return []
    reasons: list[str] = []
    if float(tactile.get("slip_score", 0.0)) > float(args.transition_slip_threshold):
        reasons.append("slip_high")
    if float(tactile.get("crush_risk", 0.0)) > float(args.transition_crush_threshold):
        reasons.append("crush_high")
    if float(tactile.get("max_penetration", 0.0)) > float(args.transition_penetration_threshold):
        reasons.append("penetration_high")
    return reasons


def run_transition_episode(
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
    vision_estimate = vision_sensor.estimate(data, label=f"stage3_contact_transition_gate_{episode_id:04d}_vision_acquire")
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
    transition_phases = parse_phase_set(args.transition_gate_phases)

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
    transition_hold_steps = 0
    transition_hold_events = 0
    transition_hold_counts: Counter[str] = Counter()
    transition_budget_exhausted_counts: Counter[str] = Counter()
    approach_contact_stop_events = 0
    approach_contact_stop_step = 0
    approach_contact_stop_error_m = float("nan")
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
        local_step = 0
        phase_extra_steps = 0
        phase_had_transition_hold = False
        while local_step < phase_steps:
            progress = local_step / max(1, phase_steps - 1)
            tactile = tactile_sensor.sample(data)
            pre_trans_reasons = transition_gate_reasons(tactile, phase_name=phase_name, transition_phases=transition_phases, args=args)

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
            if phase_name in {"approach", "preshape", "gentle_close_fingers", "gentle_close_thumb", "contact_settle"}:
                pre_lift_max_slip = max(pre_lift_max_slip, slip)
            else:
                post_lift_max_slip = max(post_lift_max_slip, slip)
            max_crush = max(max_crush, float(next_tactile["crush_risk"]))
            max_penetration = max(max_penetration, float(next_tactile.get("max_penetration", 0.0)))

            gate_reasons = gate_condition_reasons(next_tactile, args, thresholds)
            post_trans_reasons = transition_gate_reasons(next_tactile, phase_name=phase_name, transition_phases=transition_phases, args=args)
            trans_reasons = sorted(set(pre_trans_reasons + post_trans_reasons))
            transition_budget_left = phase_extra_steps < int(args.max_transition_hold_steps_per_phase)
            hold_transition = bool(trans_reasons) and transition_budget_left
            if bool(trans_reasons) and not transition_budget_left:
                transition_budget_exhausted_counts[phase_name] += 1
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

            if hold_transition:
                phase_extra_steps += 1
                transition_hold_steps += 1
                transition_hold_counts[phase_name] += 1
                if not phase_had_transition_hold:
                    transition_hold_events += 1
                    phase_had_transition_hold = True
            else:
                local_step += 1

            if step_count % max(1, int(args.sample_every)) == 0:
                trace.append(
                    {
                        "step": int(step_count),
                        "phase": phase_name,
                        "progress": float(progress),
                        "learned_hand": bool(used_learned_hand),
                        "transition_hold": bool(hold_transition),
                        "transition_reasons": trans_reasons,
                        "lift_height_m": float(lift_height),
                        "contact": bool(next_tactile["contact_present"]),
                        "stable": bool(next_tactile["grip_stable"]),
                        "slip": float(next_tactile["slip_score"]),
                        "crush": float(next_tactile["crush_risk"]),
                        "penetration": float(next_tactile.get("max_penetration", 0.0)),
                        "gate_window": int(gate_stable_window) if phase_name == "contact_settle" else 0,
                    }
                )
            step_count += 1

            if (
                bool(args.stop_approach_on_contact)
                and phase_name == "approach"
                and bool(next_tactile.get("contact_present", False))
                and local_step >= int(args.min_approach_steps_before_contact_stop)
                and approach_true_proxy_error <= float(args.approach_contact_stop_error_m)
            ):
                approach_contact_stop_events += 1
                approach_contact_stop_step = int(local_step)
                approach_contact_stop_error_m = float(approach_true_proxy_error)
                break
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
        "transition_hold_steps": int(transition_hold_steps),
        "transition_hold_events": int(transition_hold_events),
        "transition_hold_counts": dict(transition_hold_counts),
        "transition_budget_exhausted_counts": dict(transition_budget_exhausted_counts),
        "approach_contact_stop_events": int(approach_contact_stop_events),
        "approach_contact_stop_step": int(approach_contact_stop_step),
        "approach_contact_stop_error_m": float(approach_contact_stop_error_m),
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
    if transition_budget_exhausted_counts:
        risks.append("transition_gate_budget_exhausted")
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
        "policy_scope": "scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_and_transition_gates",
        "learned_phases": sorted(learned_phases),
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    success_count = sum(1 for row in results if row["success"])
    reasons: dict[str, int] = {}
    risks: dict[str, int] = {}
    gate_reasons: dict[str, int] = {}
    transition_hold_phase_counts: Counter[str] = Counter()
    transition_budget_phase_counts: Counter[str] = Counter()
    top_slip_phase_counts: Counter[str] = Counter()
    for row in results:
        reasons[row["terminal_reason"]] = reasons.get(row["terminal_reason"], 0) + 1
        for risk in row.get("risk_flags", []):
            risks[risk] = risks.get(risk, 0) + 1
        summary = row.get("summary", {})
        gate_reason = str(summary.get("gate_release_reason", "none"))
        gate_reasons[gate_reason] = gate_reasons.get(gate_reason, 0) + 1
        transition_hold_phase_counts.update(summary.get("transition_hold_counts", {}))
        transition_budget_phase_counts.update(summary.get("transition_budget_exhausted_counts", {}))
        phase_metrics = summary.get("phase_metrics", {})
        if phase_metrics:
            top_phase = max(phase_metrics.items(), key=lambda item: float(item[1].get("max_slip_score", 0.0)))[0]
            top_slip_phase_counts[top_phase] += 1

    def values(key: str) -> np.ndarray:
        return np.asarray([row["summary"][key] for row in results if "summary" in row], dtype=np.float64)

    out: dict[str, Any] = {
        "status": "PASS" if success_count == len(results) else ("PARTIAL" if success_count else "FAIL"),
        "episodes": len(results),
        "success_count": int(success_count),
        "terminal_reason_counts": reasons,
        "risk_flag_counts": risks,
        "gate_release_reason_counts": gate_reasons,
        "transition_hold_phase_counts": dict(transition_hold_phase_counts),
        "transition_budget_phase_counts": dict(transition_budget_phase_counts),
        "top_slip_phase_counts": dict(top_slip_phase_counts),
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
        "transition_hold_steps",
        "transition_hold_events",
        "approach_contact_stop_events",
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
        "# Stage3.7C Contact Transition Gate V0 Eval Report\n\n",
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
        f"- Top-slip phases: `{s['top_slip_phase_counts']}`\n",
        f"- Transition holds by phase: `{s['transition_hold_phase_counts']}`\n",
        f"- Transition budget exhaustion: `{s['transition_budget_phase_counts']}`\n",
        f"- Mean final lift: `{s.get('final_lift_height_m_mean', float('nan')):.6f} m`\n",
        f"- Mean hold stable fraction: `{s.get('hold_stable_fraction_mean', float('nan')):.3f}`\n",
        f"- Mean max transient slip: `{s.get('max_slip_score_mean', float('nan')):.3f}`\n",
        f"- Max transient slip: `{s.get('max_slip_score_max', float('nan')):.3f}`\n",
        f"- Max hold slip: `{s.get('hold_max_slip_score_max', float('nan')):.3f}`\n",
        f"- Max crush risk: `{s.get('max_crush_risk_max', float('nan')):.3f}`\n",
        f"- Max penetration: `{s.get('max_penetration_m_max', float('nan')):.6f} m`\n",
        f"- Mean transition hold steps: `{s.get('transition_hold_steps_mean', float('nan')):.1f}`\n",
        f"- Mean approach contact-stop events: `{s.get('approach_contact_stop_events_mean', float('nan')):.1f}`\n",
        "\n## Gate Parameters\n\n",
        f"- stop approach on contact: `{payload['transition_args']['stop_approach_on_contact']}`\n",
        f"- approach contact stop error: `{payload['transition_args']['approach_contact_stop_error_m']}`\n",
        f"- transition gate phases: `{payload['transition_args']['transition_gate_phases']}`\n",
        f"- transition slip threshold: `{payload['transition_args']['transition_slip_threshold']}`\n",
        f"- transition crush threshold: `{payload['transition_args']['transition_crush_threshold']}`\n",
        f"- transition penetration threshold: `{payload['transition_args']['transition_penetration_threshold']}`\n",
        f"- max transition hold steps per phase: `{payload['transition_args']['max_transition_hold_steps_per_phase']}`\n",
        f"- contact-settle gate: `{payload['transition_args']['min_contact_settle_steps']} / {payload['transition_args']['max_contact_settle_steps']}`\n",
        "\n## Episode Results\n\n",
        "| ep | trial | status | max slip | top phase | transition holds | approach stop | settle | lift m | stable | hold slip | crush | pen m | risks |\n",
        "|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|\n",
    ]
    for row in payload["results"]:
        if "summary" not in row:
            lines.append(f"| {row['episode_id']} | {row['trial']} | {row['status']} | nan | n/a | 0 | 0 | 0 | nan | nan | nan | nan | nan | `{row.get('risk_flags', [])}` |\n")
            continue
        r = row["summary"]
        phase_metrics = r.get("phase_metrics", {})
        top_phase = "n/a"
        if phase_metrics:
            top_phase = max(phase_metrics.items(), key=lambda item: float(item[1].get("max_slip_score", 0.0)))[0]
        lines.append(
            f"| {row['episode_id']} | {row['trial']} | {row['status']} | "
            f"{r['max_slip_score']:.3f} | {top_phase} | {r['transition_hold_steps']} | "
            f"{r['approach_contact_stop_events']} | {r['contact_settle_steps_actual']} | "
            f"{r['final_lift_height_m']:.5f} | {r['hold_stable_fraction']:.3f} | "
            f"{r['hold_max_slip_score']:.3f} | {r['max_crush_risk']:.3f} | "
            f"{r['max_penetration_m']:.6f} | `{row.get('risk_flags', [])}` |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This is a MuJoCo-only repair probe layered on Stage3.7B.\n",
            "- It tests whether contact-transition pauses reduce transient slip before changing the learned hand policy.\n",
            "- Success is still judged by the Stage3 gentle-grasp hold criteria; full-episode transient slip is reported as a risk flag.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Stage3.7C contact-transition gate.")
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
    parser.add_argument("--stop-approach-on-contact", action="store_true", default=False)
    parser.add_argument("--no-stop-approach-on-contact", action="store_false", dest="stop_approach_on_contact")
    parser.add_argument("--min-approach-steps-before-contact-stop", type=int, default=90)
    parser.add_argument("--approach-contact-stop-error-m", type=float, default=0.014)
    parser.add_argument("--transition-gate-phases", default="slow_lift")
    parser.add_argument("--transition-slip-threshold", type=float, default=0.28)
    parser.add_argument("--transition-crush-threshold", type=float, default=0.35)
    parser.add_argument("--transition-penetration-threshold", type=float, default=0.004)
    parser.add_argument("--max-transition-hold-steps-per-phase", type=int, default=150)
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
        row = run_transition_episode(model, mujoco, policy, checkpoint, trial, episode_id, args, device)
        results.append(row)
        summary = row.get("summary", {})
        print(
            f"ep={episode_id:03d} trial={trial.name} {row['status']} reason={row['terminal_reason']} "
            f"max_slip={summary.get('max_slip_score', float('nan')):.3f} "
            f"hold_slip={summary.get('hold_max_slip_score', float('nan')):.3f} "
            f"transition_holds={summary.get('transition_hold_steps', 0)} "
            f"approach_stop={summary.get('approach_contact_stop_events', 0)} "
            f"lift={summary.get('final_lift_height_m', float('nan')):.4f}"
        )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "checkpoint_status": checkpoint.get("status"),
        "scene": str(Path(args.scene).resolve()),
        "device": str(device),
        "policy_scope": "scripted_arm_wrist_phase_hand_policy_plus_tactile_phase_and_transition_gates",
        "transition_args": {
            "stop_approach_on_contact": bool(args.stop_approach_on_contact),
            "min_approach_steps_before_contact_stop": int(args.min_approach_steps_before_contact_stop),
            "approach_contact_stop_error_m": float(args.approach_contact_stop_error_m),
            "transition_gate_phases": sorted(parse_phase_set(args.transition_gate_phases)),
            "transition_slip_threshold": float(args.transition_slip_threshold),
            "transition_crush_threshold": float(args.transition_crush_threshold),
            "transition_penetration_threshold": float(args.transition_penetration_threshold),
            "max_transition_hold_steps_per_phase": int(args.max_transition_hold_steps_per_phase),
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
