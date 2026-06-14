#!/usr/bin/env python3
"""Randomized robustness probe for the Stage3.11D-B event-gated ball pinch.

This stays MuJoCo-only. It perturbs the selected event-gated high-lift case
around object pose, grasp targeting, object size/mass, and friction. It can also
log simulated motor force-feedback signals derived from MuJoCo actuator loads.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
import train_stage3_11d_b_event_contact_gated_refine_v0 as event


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DEFAULT_SELECTED = META / "stage3_11d_b_event_contact_gated_refine_highlift_selected_v0.json"
DEFAULT_REPORT = DOCS / "stage3_11d_b_event_contact_gated_robustness_v0_report.md"
DEFAULT_METADATA = META / "stage3_11d_b_event_contact_gated_robustness_v0.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def selected_case_from_json(path: Path) -> event.RefineCase:
    raw = json.loads(path.read_text(encoding="utf-8"))
    case = raw.get("selected_case") or raw.get("case")
    if case is None:
        result = raw.get("result", {})
        case = result.get("case")
    if case is None:
        raise ValueError(f"Could not find selected_case in {path}")
    return event.RefineCase(
        name=str(case["name"]),
        candidate=event.broad.BallPinchCandidate(**case["candidate"]),
        tip_pair_separation_target=float(case["tip_pair_separation_target"]),
        grasp_offset_x=float(case["grasp_offset_x"]),
        grasp_offset_y=float(case["grasp_offset_y"]),
        grasp_offset_z=float(case["grasp_offset_z"]),
        ball_radius=float(case["ball_radius"]),
        ball_mass=float(case["ball_mass"]),
        hold_steps=int(case["hold_steps"]),
        min_lift_height=float(case["min_lift_height"]),
        ball_offset_x=float(case.get("ball_offset_x", 0.0)),
        ball_offset_y=float(case.get("ball_offset_y", 0.0)),
        ball_offset_z=float(case.get("ball_offset_z", 0.0)),
    )


def apply_base_offsets(base: event.RefineCase, args: argparse.Namespace) -> event.RefineCase:
    case = replace(
        base,
        grasp_offset_x=float(base.grasp_offset_x + args.base_grasp_offset_x_delta),
        grasp_offset_y=float(base.grasp_offset_y + args.base_grasp_offset_y_delta),
        grasp_offset_z=float(base.grasp_offset_z + args.base_grasp_offset_z_delta),
        ball_offset_x=float(base.ball_offset_x + args.base_ball_offset_x_delta),
        ball_offset_y=float(base.ball_offset_y + args.base_ball_offset_y_delta),
    )
    candidate_updates: dict[str, Any] = {}
    if args.override_thumb_abd is not None:
        candidate_updates["thumb_cmc_abd"] = float(args.override_thumb_abd)
    if args.override_thumb_mcp is not None:
        candidate_updates["thumb_mcp"] = float(args.override_thumb_mcp)
    if args.override_active_abd is not None:
        candidate_updates["active_mcp_abd"] = float(args.override_active_abd)
    if args.override_active_pip is not None:
        active_pip = float(args.override_active_pip)
        candidate_updates["active_pip"] = active_pip
        candidate_updates["active_dip"] = active_pip * 0.45
    if args.override_lift_j2 is not None:
        candidate_updates["lift_j2"] = float(args.override_lift_j2)
    if args.override_lift_steps is not None:
        candidate_updates["lift_steps"] = int(args.override_lift_steps)
    if candidate_updates:
        case = replace(case, candidate=replace(case.candidate, **candidate_updates))
    case_updates: dict[str, Any] = {}
    if args.override_grasp_offset_x is not None:
        case_updates["grasp_offset_x"] = float(args.override_grasp_offset_x)
    if args.override_grasp_offset_y is not None:
        case_updates["grasp_offset_y"] = float(args.override_grasp_offset_y)
    if args.override_grasp_offset_z is not None:
        case_updates["grasp_offset_z"] = float(args.override_grasp_offset_z)
    if args.override_tip_pair_separation is not None:
        case_updates["tip_pair_separation_target"] = float(args.override_tip_pair_separation)
    if args.override_hold_steps is not None:
        case_updates["hold_steps"] = int(args.override_hold_steps)
    if args.override_min_lift_height is not None:
        case_updates["min_lift_height"] = float(args.override_min_lift_height)
    if case_updates:
        case = replace(case, **case_updates)
    return case


def token(value: float) -> str:
    return f"{value:+.4f}".replace("+", "p").replace("-", "m").replace(".", "p")


def perturb_case(base: event.RefineCase, args: argparse.Namespace, rng: np.random.Generator, idx: int) -> event.RefineCase:
    object_dx = float(rng.uniform(-args.object_pose_noise_xy_m, args.object_pose_noise_xy_m))
    object_dy = float(rng.uniform(-args.object_pose_noise_xy_m, args.object_pose_noise_xy_m))
    grasp_dx = float(rng.uniform(-args.grasp_target_noise_xy_m, args.grasp_target_noise_xy_m))
    grasp_dy = float(rng.uniform(-args.grasp_target_noise_xy_m, args.grasp_target_noise_xy_m))
    grasp_dz = float(rng.uniform(-args.grasp_target_noise_z_m, args.grasp_target_noise_z_m))
    radius = max(0.010, float(base.ball_radius + rng.uniform(-args.radius_jitter_m, args.radius_jitter_m)))
    mass = max(0.002, float(base.ball_mass + rng.uniform(-args.mass_jitter_kg, args.mass_jitter_kg)))
    tip_scale = float(1.0 + rng.uniform(-args.friction_scale_jitter, args.friction_scale_jitter))
    ball_scale = float(1.0 + rng.uniform(-args.friction_scale_jitter, args.friction_scale_jitter))
    non_tip_scale = float(1.0 + rng.uniform(-args.friction_scale_jitter, args.friction_scale_jitter))
    candidate = replace(
        base.candidate,
        name=(
            f"robust_{idx:03d}_ox{token(object_dx)}_oy{token(object_dy)}"
            f"_gx{token(grasp_dx)}_gy{token(grasp_dy)}_r{radius:.4f}_m{mass:.4f}"
        ).replace(".", "p"),
        tip_sliding_mu=max(0.05, float(base.candidate.tip_sliding_mu * tip_scale)),
        ball_sliding_mu=max(0.05, float(base.candidate.ball_sliding_mu * ball_scale)),
        non_tip_sliding_mu=max(0.01, float(base.candidate.non_tip_sliding_mu * non_tip_scale)),
    )
    return event.RefineCase(
        name=candidate.name,
        candidate=candidate,
        tip_pair_separation_target=base.tip_pair_separation_target,
        grasp_offset_x=float(base.grasp_offset_x + grasp_dx),
        grasp_offset_y=float(base.grasp_offset_y + grasp_dy),
        grasp_offset_z=float(base.grasp_offset_z + grasp_dz),
        ball_radius=radius,
        ball_mass=mass,
        hold_steps=base.hold_steps,
        min_lift_height=base.min_lift_height,
        ball_offset_x=float(base.ball_offset_x + object_dx),
        ball_offset_y=float(base.ball_offset_y + object_dy),
        ball_offset_z=base.ball_offset_z,
    )


def event_args_from(args: argparse.Namespace) -> argparse.Namespace:
    ev = event.build_parser().parse_args([])
    ev.scene = Path(args.scene)
    ev.min_lift_steps_before_hold = int(args.min_lift_steps_before_hold)
    ev.hold_release_required_samples = int(args.hold_release_required_samples)
    ev.demo_lift_goal = float(args.demo_lift_goal)
    ev.morphology_sample_every = int(args.morphology_sample_every)
    ev.enable_motor_force_feedback = bool(args.enable_motor_force_feedback)
    ev.motor_torque_constant_nm_per_a = float(args.motor_torque_constant_nm_per_a)
    ev.motor_gear_ratio = float(args.motor_gear_ratio)
    ev.motor_gear_efficiency = float(args.motor_gear_efficiency)
    ev.motor_spool_radius_m = float(args.motor_spool_radius_m)
    ev.motor_current_limit_a = float(args.motor_current_limit_a)
    ev.motor_bus_voltage_v = float(args.motor_bus_voltage_v)
    ev.motor_current_noise_a = float(args.motor_current_noise_a)
    ev.motor_feedback_seed = int(args.seed)
    ev.enable_force_feedback_lift_gate = bool(args.enable_force_feedback_lift_gate)
    ev.force_feedback_enable_preload = bool(args.force_feedback_enable_preload)
    ev.force_feedback_preload_steps = int(args.force_feedback_preload_steps)
    ev.force_feedback_required_samples = int(args.force_feedback_required_samples)
    ev.force_feedback_min_preload_delta = float(args.force_feedback_min_preload_delta)
    ev.force_feedback_max_preload_delta = float(args.force_feedback_max_preload_delta)
    ev.force_feedback_lift_wait_close_delta = float(args.force_feedback_lift_wait_close_delta)
    ev.force_feedback_check_after_lift_steps = int(args.force_feedback_check_after_lift_steps)
    ev.force_feedback_max_lift_wait_steps = int(args.force_feedback_max_lift_wait_steps)
    ev.force_feedback_min_slow_lift_pair_tension_n = float(args.force_feedback_min_slow_lift_pair_tension_n)
    ev.force_feedback_min_hold_pair_tension_n = float(args.force_feedback_min_hold_pair_tension_n)
    ev.force_feedback_min_pair_balance = float(args.force_feedback_min_pair_balance)
    ev.force_feedback_max_pair_iq_a = float(args.force_feedback_max_pair_iq_a)
    return ev


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if row["success"]]
    feedback = [row.get("motor_force_feedback_summary", {}) for row in rows]
    feedback = [row for row in feedback if row.get("samples", 0)]
    slow_pair = [
        row.get("phase_summaries", {}).get("slow_lift", {}).get("pair_total_tension_mean_n", 0.0)
        for row in feedback
    ]
    hold_pair = [
        row.get("phase_summaries", {}).get("hold", {}).get("pair_total_tension_mean_n", 0.0)
        for row in feedback
    ]
    gate_rows = [row.get("force_feedback_gate", {}) for row in rows]
    return {
        "trials": int(len(rows)),
        "success_count": int(len(successes)),
        "contact_gate_success_count": int(sum(1 for row in rows if row["contact_gate_success"])),
        "lift_success_count": int(sum(1 for row in rows if row["lift_success"])),
        "true_pinch_success_count": int(sum(1 for row in rows if row["true_pinch_success"])),
        "release_success_count": int(sum(1 for row in rows if row["release_success"])),
        "terminal_reason_counts": dict(Counter(str(row["terminal_reason"]) for row in rows)),
        "success_hold_lift_mean_m": float(np.mean([row["hold_lift_m_max"] for row in successes])) if successes else 0.0,
        "success_hold_lift_min_m": float(min([row["hold_lift_m_max"] for row in successes])) if successes else 0.0,
        "success_hold_lift_max_m": float(max([row["hold_lift_m_max"] for row in successes])) if successes else 0.0,
        "motor_feedback_enabled": bool(len(feedback)),
        "motor_feedback_max_iq_a": float(max([row.get("max_abs_iq_a", 0.0) for row in feedback] + [0.0])),
        "motor_feedback_max_tendon_tension_n": float(
            max([row.get("max_tendon_tension_n", 0.0) for row in feedback] + [0.0])
        ),
        "motor_feedback_max_hand_iq_a": float(max([row.get("max_hand_abs_iq_a", 0.0) for row in feedback] + [0.0])),
        "motor_feedback_max_hand_tendon_tension_n": float(
            max([row.get("max_hand_tendon_tension_n", 0.0) for row in feedback] + [0.0])
        ),
        "motor_feedback_slow_lift_pair_tension_mean_n": float(np.mean(slow_pair)) if slow_pair else 0.0,
        "motor_feedback_hold_pair_tension_mean_n": float(np.mean(hold_pair)) if hold_pair else 0.0,
        "motor_feedback_saturation_trial_fraction": float(
            np.mean([float(row.get("saturation_sample_fraction", 0.0)) > 0.0 for row in feedback])
        )
        if feedback
        else 0.0,
        "force_feedback_gate_enabled": bool(any(row.get("enabled", False) for row in gate_rows)),
        "force_feedback_lift_low_force_samples_total": int(
            sum(int(row.get("lift_low_force_samples", 0)) for row in gate_rows)
        ),
        "force_feedback_lift_wait_steps_total": int(sum(int(row.get("lift_wait_steps", 0)) for row in gate_rows)),
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# Stage3.11D-B Event Contact-Gated Robustness v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- MuJoCo-only randomized diagnostic probe.\n",
        "- Parameter/action-phase evaluation, not neural-network training.\n",
        "- Motor force feedback is simulated from MuJoCo actuator loads, not hardware data.\n",
        "- No demo-gallery, full-action ACT/DP, or hardware-runtime promotion.\n\n",
        "## Randomization\n\n",
        f"- Trials: `{s['trials']}`\n",
        f"- Object pose XY noise: `+/- {payload['args']['object_pose_noise_xy_m']} m`\n",
        f"- Grasp target XY noise: `+/- {payload['args']['grasp_target_noise_xy_m']} m`\n",
        f"- Grasp target Z noise: `+/- {payload['args']['grasp_target_noise_z_m']} m`\n",
        f"- Radius jitter: `+/- {payload['args']['radius_jitter_m']} m`\n",
        f"- Mass jitter: `+/- {payload['args']['mass_jitter_kg']} kg`\n",
        f"- Friction scale jitter: `+/- {payload['args']['friction_scale_jitter']}`\n\n",
        "## Summary\n\n",
        f"- Full event true-pinch-release success: `{s['success_count']} / {s['trials']}`\n",
        f"- Contact-gate success: `{s['contact_gate_success_count']} / {s['trials']}`\n",
        f"- Lift gate success: `{s['lift_success_count']} / {s['trials']}`\n",
        f"- True-pinch morphology success: `{s['true_pinch_success_count']} / {s['trials']}`\n",
        f"- Release success: `{s['release_success_count']} / {s['trials']}`\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n",
        f"- Successful hold lift mean/min/max: `{s['success_hold_lift_mean_m']:.5f}` / "
        f"`{s['success_hold_lift_min_m']:.5f}` / `{s['success_hold_lift_max_m']:.5f} m`\n\n",
    ]
    if s["motor_feedback_enabled"]:
        lines.extend(
            [
                "## Simulated Motor Force Feedback\n\n",
                f"- Max |Iq| proxy: `{s['motor_feedback_max_iq_a']:.4f} A`\n",
                f"- Max tendon tension proxy: `{s['motor_feedback_max_tendon_tension_n']:.4f} N`\n",
                f"- Max hand-side |Iq| proxy: `{s['motor_feedback_max_hand_iq_a']:.4f} A`\n",
                f"- Max hand-side tendon tension proxy: `{s['motor_feedback_max_hand_tendon_tension_n']:.4f} N`\n",
                f"- Mean slow-lift pair tension proxy: `{s['motor_feedback_slow_lift_pair_tension_mean_n']:.4f} N`\n",
                f"- Mean hold pair tension proxy: `{s['motor_feedback_hold_pair_tension_mean_n']:.4f} N`\n",
                f"- Saturation trial fraction: `{s['motor_feedback_saturation_trial_fraction']:.3f}`\n\n",
                "## Force-Feedback Gate\n\n",
                f"- Enabled: `{s['force_feedback_gate_enabled']}`\n",
                f"- Lift low-force samples total: `{s['force_feedback_lift_low_force_samples_total']}`\n",
                f"- Lift wait steps total: `{s['force_feedback_lift_wait_steps_total']}`\n\n",
            ]
        )
    lines.extend(
        [
            "## Top Trials\n\n",
            "| trial | status | score | hold lift | two-tip | wrap | release | reason |\n",
            "|---:|---|---:|---:|---:|---:|---|---|\n",
        ]
    )
    ranked = sorted(payload["results"], key=lambda row: float(row["score"]), reverse=True)
    for idx, row in enumerate(ranked[: min(16, len(ranked))], start=1):
        hm = row.get("hold_morphology", {})
        lines.append(
            f"| {idx} | {row['status']} | {row['score']:.3f} | {row.get('hold_lift_m_max', 0.0):.4f} | "
            f"{hm.get('true_two_tip_pinch_fraction', 0.0):.3f} | "
            f"{hm.get('wrap_frame_fraction', 0.0):.3f} | `{row.get('release_success')}` | "
            f"`{row['terminal_reason']}` |\n"
        )
    lines.extend(
        [
            "\n## Next\n\n",
            "- If this randomized gate is acceptable, add a close-up camera and a short viewer/demo wrapper.\n",
            "- If failures cluster at contact_gate_failed, tune approach/IK or fingertip proxy geometry.\n",
            "- If failures cluster at lift_gate_failed, tune lift timing, friction/contact material, or force-feedback gating.\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage3.11D-B event-gated robustness probe.")
    parser.add_argument("--scene", type=Path, default=event.DEFAULT_SCENE)
    parser.add_argument("--selected", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--trials", type=int, default=24)
    parser.add_argument("--seed", type=int, default=20260611)
    parser.add_argument("--object-pose-noise-xy-m", type=float, default=0.003)
    parser.add_argument("--grasp-target-noise-xy-m", type=float, default=0.002)
    parser.add_argument("--grasp-target-noise-z-m", type=float, default=0.001)
    parser.add_argument("--radius-jitter-m", type=float, default=0.001)
    parser.add_argument("--mass-jitter-kg", type=float, default=0.002)
    parser.add_argument("--friction-scale-jitter", type=float, default=0.08)
    parser.add_argument("--base-grasp-offset-x-delta", type=float, default=0.0)
    parser.add_argument("--base-grasp-offset-y-delta", type=float, default=0.0)
    parser.add_argument("--base-grasp-offset-z-delta", type=float, default=0.0)
    parser.add_argument("--base-ball-offset-x-delta", type=float, default=0.0)
    parser.add_argument("--base-ball-offset-y-delta", type=float, default=0.0)
    parser.add_argument("--override-thumb-abd", type=float, default=None)
    parser.add_argument("--override-thumb-mcp", type=float, default=None)
    parser.add_argument("--override-active-abd", type=float, default=None)
    parser.add_argument("--override-active-pip", type=float, default=None)
    parser.add_argument("--override-grasp-offset-x", type=float, default=None)
    parser.add_argument("--override-grasp-offset-y", type=float, default=None)
    parser.add_argument("--override-grasp-offset-z", type=float, default=None)
    parser.add_argument("--override-tip-pair-separation", type=float, default=None)
    parser.add_argument("--override-lift-j2", type=float, default=None)
    parser.add_argument("--override-lift-steps", type=int, default=None)
    parser.add_argument("--override-hold-steps", type=int, default=None)
    parser.add_argument("--override-min-lift-height", type=float, default=None)
    parser.add_argument("--min-lift-steps-before-hold", type=int, default=300)
    parser.add_argument("--hold-release-required-samples", type=int, default=8)
    parser.add_argument("--demo-lift-goal", type=float, default=0.11)
    parser.add_argument("--morphology-sample-every", type=int, default=5)
    parser.add_argument("--enable-motor-force-feedback", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--motor-torque-constant-nm-per-a", type=float, default=0.035)
    parser.add_argument("--motor-gear-ratio", type=float, default=30.0)
    parser.add_argument("--motor-gear-efficiency", type=float, default=0.72)
    parser.add_argument("--motor-spool-radius-m", type=float, default=0.008)
    parser.add_argument("--motor-current-limit-a", type=float, default=4.0)
    parser.add_argument("--motor-bus-voltage-v", type=float, default=24.0)
    parser.add_argument("--motor-current-noise-a", type=float, default=0.025)
    parser.add_argument("--enable-force-feedback-lift-gate", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--force-feedback-enable-preload", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--force-feedback-preload-steps", type=int, default=80)
    parser.add_argument("--force-feedback-required-samples", type=int, default=2)
    parser.add_argument("--force-feedback-min-preload-delta", type=float, default=0.035)
    parser.add_argument("--force-feedback-max-preload-delta", type=float, default=0.08)
    parser.add_argument("--force-feedback-lift-wait-close-delta", type=float, default=0.015)
    parser.add_argument("--force-feedback-check-after-lift-steps", type=int, default=120)
    parser.add_argument("--force-feedback-max-lift-wait-steps", type=int, default=180)
    parser.add_argument("--force-feedback-min-slow-lift-pair-tension-n", type=float, default=4.0)
    parser.add_argument("--force-feedback-min-hold-pair-tension-n", type=float, default=2.0)
    parser.add_argument("--force-feedback-min-pair-balance", type=float, default=0.01)
    parser.add_argument("--force-feedback-max-pair-iq-a", type=float, default=4.0)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    import mujoco

    base = apply_base_offsets(selected_case_from_json(Path(args.selected)), args)
    rng = np.random.default_rng(int(args.seed))
    ev_args = event_args_from(args)
    scene = Path(args.scene).resolve()
    results = []
    for idx in range(max(1, int(args.trials))):
        case = perturb_case(base, args, rng, idx)
        model = mujoco.MjModel.from_xml_path(str(scene))
        row = event.run_event_candidate(model, mujoco, case, ev_args)
        row["trial_index"] = idx
        row["randomization"] = {
            "ball_offset_x": case.ball_offset_x,
            "ball_offset_y": case.ball_offset_y,
            "grasp_offset_x": case.grasp_offset_x,
            "grasp_offset_y": case.grasp_offset_y,
            "grasp_offset_z": case.grasp_offset_z,
            "ball_radius": case.ball_radius,
            "ball_mass": case.ball_mass,
            "tip_mu": case.candidate.tip_sliding_mu,
            "ball_mu": case.candidate.ball_sliding_mu,
            "non_tip_mu": case.candidate.non_tip_sliding_mu,
        }
        results.append(row)
        hm = row.get("hold_morphology", {})
        print(
            f"{idx + 1:03d}/{args.trials:03d} {row['status']} score={row['score']:.3f} "
            f"lift={row.get('hold_lift_m_max', 0.0):.4f} "
            f"two_tip={hm.get('true_two_tip_pinch_fraction', 0.0):.3f} "
            f"release={row['release_success']} reason={row['terminal_reason']}"
        )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.11D-B",
        "scene": str(scene),
        "selected": str(Path(args.selected)),
        "args": vars(args),
        "base_case": {
            "name": base.name,
            "candidate": base.candidate.__dict__,
            "tip_pair_separation_target": base.tip_pair_separation_target,
            "grasp_offset_x": base.grasp_offset_x,
            "grasp_offset_y": base.grasp_offset_y,
            "grasp_offset_z": base.grasp_offset_z,
            "ball_radius": base.ball_radius,
            "ball_mass": base.ball_mass,
            "hold_steps": base.hold_steps,
            "min_lift_height": base.min_lift_height,
        },
        "summary": summarize(results),
        "results": results,
        "boundary": {
            "mujoco_only": True,
            "randomized_diagnostic_not_training": True,
            "motor_feedback_is_simulated": bool(args.enable_motor_force_feedback),
            "hardware_runtime": False,
            "controller_promoted": False,
        },
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
