#!/usr/bin/env python3
"""Stage3.5 sensor-aware gentle grasp/lift/hold expert.

This expert stays entirely in MuJoCo:

virtual camera acquire -> IK approach -> gentle close/contact settle
-> slow lift -> 3 s hold -> tactile/slip/crush checks
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, Stage3Thresholds


ROOT = Path(__file__).resolve().parent
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import run_stage3_visual_guided_grasp_sweep as sweep
from mujoco_egg_pose_sensor import EggPoseSensorConfig, MujocoEggPoseSensor
from mujoco_tactile_slip_sensor import MujocoTactileSlipSensor


DEFAULT_REPORT = ROOT / "docs" / "stage3_sensor_aware_gentle_grasp_expert_v0_report.md"
DEFAULT_METADATA = ROOT / "metadata" / "stage3_sensor_aware_gentle_grasp_expert_v0.json"
DEFAULT_VISUAL_DIR = ROOT / "docs" / "visual_checks_stage3_sensor_aware_gentle_grasp_expert_v0"

DEBUG_TRIALS = {"center_nominal", "right_high_nominal", "lifted_diag"}


def accepted_virtual_camera_estimate(estimate: dict[str, Any], min_confidence: float) -> bool:
    return estimate.get("status") == "ok" and float(estimate.get("confidence", 0.0)) >= float(min_confidence)


def tactile_compact(tactile: dict[str, Any]) -> dict[str, Any]:
    return {
        "contact_present": bool(tactile["contact_present"]),
        "contact_regions": list(tactile["contact_regions"]),
        "contact_persistence": int(tactile["contact_persistence"]),
        "normal_contact_proxy": float(tactile["normal_contact_proxy"]),
        "slip_score": float(tactile["slip_score"]),
        "grip_stable": bool(tactile["grip_stable"]),
        "crush_risk": float(tactile["crush_risk"]),
        "egg_hand_contact_count": int(tactile.get("egg_hand_contact_count", 0)),
        "egg_floor_contact_count": int(tactile.get("egg_floor_contact_count", 0)),
        "egg_contact_region_counts": dict(tactile.get("egg_contact_region_counts", {})),
    }


def run_phase_with_tactile(
    model,
    data,
    mujoco,
    actuator_names: list[str],
    tactile_sensor: MujocoTactileSlipSensor,
    *,
    phase_name: str,
    start: dict[str, float],
    end: dict[str, float],
    steps: int,
    initial_egg: np.ndarray,
) -> dict[str, Any]:
    max_slip = 0.0
    max_crush = 0.0
    max_penetration = 0.0
    contact_steps = 0
    stable_steps = 0
    floor_contact_steps = 0
    first_contact_step = None
    final_tactile: dict[str, Any] | None = None
    for idx in range(max(1, int(steps))):
        alpha = idx / max(1, int(steps) - 1)
        targets = sweep.blend_targets(start, end, alpha)
        data.ctrl[:] = sweep.actuator_targets(model, mujoco, actuator_names, targets)
        mujoco.mj_step(model, data)
        tactile = tactile_sensor.sample(data)
        final_tactile = tactile
        max_slip = max(max_slip, float(tactile["slip_score"]))
        max_crush = max(max_crush, float(tactile["crush_risk"]))
        max_penetration = max(max_penetration, float(tactile.get("max_penetration", tactile["normal_contact_proxy"])))
        if tactile["contact_present"]:
            contact_steps += 1
            if first_contact_step is None:
                first_contact_step = idx
        if tactile["grip_stable"]:
            stable_steps += 1
        if int(tactile.get("egg_floor_contact_count", 0)) > 0:
            floor_contact_steps += 1
    assert final_tactile is not None
    egg_now = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    return {
        "phase": phase_name,
        "steps": int(steps),
        "egg_position": egg_now,
        "egg_lift_height_m": float(egg_now[2] - initial_egg[2]),
        "contact_steps": int(contact_steps),
        "stable_steps": int(stable_steps),
        "floor_contact_steps": int(floor_contact_steps),
        "first_contact_step": first_contact_step,
        "max_slip_score": float(max_slip),
        "max_crush_risk": float(max_crush),
        "max_penetration_m": float(max_penetration),
        "final_tactile": tactile_compact(final_tactile),
    }


def expert_failure_reasons(row: dict[str, Any], args: argparse.Namespace, thresholds: Stage3Thresholds) -> list[str]:
    reasons: list[str] = []
    if not row["vision_acquire"]["accepted"]:
        reasons.append("vision_acquire_failed")
    if row["ik_approach_dxy_m"] > float(args.max_ik_dxy) or row["ik_approach_dz_m"] > float(args.max_ik_dz):
        reasons.append("ik_alignment_error")
    if row["approach_true_proxy_error_m"] > float(args.functional_hit_threshold):
        reasons.append("functional_approach_missed_true_egg")
    if not row["contact_acquired"]:
        reasons.append("no_tactile_contact")
    if not row["grip_stable_before_lift"]:
        reasons.append("grip_not_stable_before_lift")
    if row["final_lift_height_m"] < float(thresholds.success_lift_height_m):
        reasons.append("insufficient_lift_height")
    if row["hold_duration_s"] < float(thresholds.success_hold_duration_s):
        reasons.append("insufficient_hold_duration")
    if row["hold_stable_fraction"] < float(args.min_hold_stable_fraction):
        reasons.append("unstable_hold_tactile")
    if row["hold_max_slip_score"] > float(thresholds.success_max_slip_score):
        reasons.append("hold_slip_score_high")
    if row["max_crush_risk"] > float(thresholds.success_max_crush_risk):
        reasons.append("crush_risk_high")
    if row["max_penetration_m"] > float(thresholds.success_max_penetration_m):
        reasons.append("excessive_penetration")
    if row["final_floor_contacts"] > 0:
        reasons.append("egg_on_floor_after_hold")
    if not row["finite_state"]:
        reasons.append("non_finite_state")
    return reasons


def run_expert_episode(
    model,
    mujoco,
    *,
    trial: sweep.TrialConfig,
    egg_position: np.ndarray,
    args: argparse.Namespace,
    visual_dir: Path,
) -> dict[str, Any]:
    data = mujoco.MjData(model)
    sweep.reset_episode(model, data, mujoco, egg_position)
    thresholds = Stage3Thresholds()
    actuator_names = sweep.base.actuator_names(model, mujoco)
    vision_sensor = MujocoEggPoseSensor(
        model,
        mujoco,
        EggPoseSensorConfig(camera_name=args.camera, width=int(args.width), height=int(args.height)),
    )
    debug_dir = visual_dir / trial.name / "virtual_camera" if args.render_snapshots and trial.name in DEBUG_TRIALS else None
    vision_estimate = vision_sensor.estimate(data, debug_dir=debug_dir, label=f"{trial.name}_vision_acquire")
    vision_accepted = accepted_virtual_camera_estimate(vision_estimate, float(args.min_vision_confidence))
    if not vision_accepted:
        return {
            "trial": trial.name,
            "trial_config": asdict(trial),
            "vision_acquire": {
                "accepted": False,
                "status": vision_estimate.get("status"),
                "confidence": float(vision_estimate.get("confidence", 0.0)),
                "mask_pixels": int(vision_estimate.get("mask_pixels", 0)),
            },
            "success": False,
            "failure_reasons": ["vision_acquire_failed"],
        }

    target_position = np.asarray(vision_estimate["position_world_est"], dtype=np.float64).copy()
    tactile_sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=thresholds)
    tactile_sensor.reset(data)
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
    data.ctrl[:] = sweep.actuator_targets(model, mujoco, actuator_names, pre_arm)
    mujoco.mj_forward(model, data)
    tactile_sensor.reset(data)
    initial_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    initial_tactile = tactile_sensor.sample(data)

    hand_targets = {
        "preshape": {**approach_arm, **sweep.base.PRESHAPE_TARGETS},
        "close_fingers": {**approach_arm, **sweep.base.LONG_FINGER_TARGETS},
        "close_thumb": {**approach_arm, **sweep.base.LONG_FINGER_TARGETS, **sweep.base.THUMB_SMOKE_TARGETS},
        "lift": {**lift_arm, **sweep.base.LONG_FINGER_TARGETS, **sweep.base.THUMB_SMOKE_TARGETS},
    }
    phases = [
        ("approach", pre_arm, approach_arm, int(args.approach_steps)),
        ("preshape", approach_arm, hand_targets["preshape"], int(args.hand_steps)),
        ("gentle_close_fingers", hand_targets["preshape"], hand_targets["close_fingers"], int(args.close_fingers_steps)),
        ("gentle_close_thumb", hand_targets["close_fingers"], hand_targets["close_thumb"], int(args.close_thumb_steps)),
        ("contact_settle", hand_targets["close_thumb"], hand_targets["close_thumb"], int(args.contact_settle_steps)),
        ("slow_lift", hand_targets["close_thumb"], hand_targets["lift"], int(args.lift_steps)),
        ("hold", hand_targets["lift"], hand_targets["lift"], int(args.hold_steps)),
    ]

    phase_rows = []
    screenshots: dict[str, str] = {}
    contact_acquired = False
    grip_stable_before_lift = False
    max_crush = 0.0
    max_pen = 0.0
    first_contact_phase = None
    approach_true_proxy_error = math.inf
    approach_est_proxy_error = math.inf
    for phase_name, start, end, steps in phases:
        phase = run_phase_with_tactile(
            model,
            data,
            mujoco,
            actuator_names,
            tactile_sensor,
            phase_name=phase_name,
            start=start,
            end=end,
            steps=steps,
            initial_egg=initial_egg,
        )
        if phase_name == "approach":
            proxy_now = sweep.proxy_position(model, data, mujoco, grasp_local)
            approach_true_proxy_error = float(np.linalg.norm(proxy_now - initial_egg))
            approach_est_proxy_error = float(np.linalg.norm(proxy_now - approach_target))
        if phase["contact_steps"] > 0 and first_contact_phase is None:
            first_contact_phase = phase_name
        contact_acquired = contact_acquired or phase["contact_steps"] > 0
        if phase_name in {"gentle_close_thumb", "contact_settle"}:
            grip_stable_before_lift = grip_stable_before_lift or bool(phase["final_tactile"]["grip_stable"])
        max_crush = max(max_crush, float(phase["max_crush_risk"]))
        max_pen = max(max_pen, float(phase["max_penetration_m"]))
        phase_rows.append(phase)
        if args.render_snapshots and trial.name in DEBUG_TRIALS and phase_name in {"approach", "contact_settle", "slow_lift", "hold"}:
            screenshots[phase_name] = sweep.render_trial_snapshot(
                model,
                data,
                mujoco,
                visual_dir / trial.name / f"{phase_name}.png",
            )

    final_tactile = tactile_sensor.sample(data)
    final_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    final_contact = sweep.contact_summary(model, data, mujoco)
    hold_phase = phase_rows[-1]
    hold_duration_s = float(args.hold_steps) * float(model.opt.timestep)
    hold_stable_fraction = float(hold_phase["stable_steps"] / max(1, hold_phase["steps"]))
    finite = bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all())
    row = {
        "trial": trial.name,
        "trial_config": asdict(trial),
        "vision_acquire": {
            "accepted": True,
            "status": vision_estimate.get("status"),
            "confidence": float(vision_estimate.get("confidence", 0.0)),
            "mask_pixels": int(vision_estimate.get("mask_pixels", 0)),
            "target_position_for_ik": target_position,
        },
        "initial_tactile": tactile_compact(initial_tactile),
        "first_contact_phase": first_contact_phase,
        "contact_acquired": bool(contact_acquired),
        "grip_stable_before_lift": bool(grip_stable_before_lift),
        "ik_approach_dxy_m": float(approach_solution["dxy"]),
        "ik_approach_dz_m": float(approach_solution["dz"]),
        "ik_lift_dxy_m": float(lift_solution["dxy"]),
        "ik_lift_dz_m": float(lift_solution["dz"]),
        "approach_true_proxy_error_m": float(approach_true_proxy_error),
        "approach_est_proxy_error_m": float(approach_est_proxy_error),
        "final_egg_position": final_egg,
        "final_lift_height_m": float(final_egg[2] - initial_egg[2]),
        "hold_duration_s": hold_duration_s,
        "hold_stable_fraction": hold_stable_fraction,
        "hold_max_slip_score": float(hold_phase["max_slip_score"]),
        "hold_final_slip_score": float(hold_phase["final_tactile"]["slip_score"]),
        "max_crush_risk": float(max_crush),
        "max_penetration_m": float(max_pen),
        "final_tactile": tactile_compact(final_tactile),
        "final_floor_contacts": int(final_contact["egg_floor_contact_count"]),
        "finite_state": finite,
        "phase_rows": phase_rows,
        "screenshots": screenshots,
    }
    row["risk_flags"] = []
    if first_contact_phase == "approach":
        row["risk_flags"].append("early_contact_in_approach")
    if any(float(phase["max_slip_score"]) > float(thresholds.success_max_slip_score) for phase in phase_rows if phase["phase"] != "hold"):
        row["risk_flags"].append("transient_nonhold_slip")
    row["failure_reasons"] = expert_failure_reasons(row, args, thresholds)
    row["success"] = len(row["failure_reasons"]) == 0
    return row


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "episodes": len(rows),
        "successes": int(sum(1 for row in rows if row.get("success"))),
        "failures": int(sum(1 for row in rows if not row.get("success"))),
    }
    for key in [
        "final_lift_height_m",
        "hold_stable_fraction",
        "hold_max_slip_score",
        "hold_final_slip_score",
        "max_crush_risk",
        "max_penetration_m",
        "approach_true_proxy_error_m",
    ]:
        values = np.asarray([float(row[key]) for row in rows if key in row and np.isfinite(float(row[key]))], dtype=np.float64)
        if values.size:
            out[f"{key}_mean"] = float(np.mean(values))
            out[f"{key}_max"] = float(np.max(values))
            out[f"{key}_min"] = float(np.min(values))
    reasons: dict[str, int] = {}
    risks: dict[str, int] = {}
    for row in rows:
        for reason in row.get("failure_reasons", []):
            reasons[reason] = reasons.get(reason, 0) + 1
        for risk in row.get("risk_flags", []):
            risks[risk] = risks.get(risk, 0) + 1
    out["failure_reasons"] = reasons
    out["risk_flags"] = risks
    return out


def write_report(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# Stage3.5 Sensor-Aware Gentle Grasp Expert V0\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "This MuJoCo-only expert uses virtual-camera pose acquisition and contact-derived tactile/slip checks to gently grasp, slowly lift, and hold the egg-like object for 3 seconds.\n\n",
        "## Result\n\n",
        f"- Status: `{payload['status']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Virtual camera: `{payload['camera']}`\n",
        f"- Episodes: `{s['episodes']}`\n",
        f"- Successes: `{s['successes']}` / `{s['episodes']}`\n",
        f"- Mean final lift: `{s.get('final_lift_height_m_mean', float('nan')):.6f} m`\n",
        f"- Mean hold stable fraction: `{s.get('hold_stable_fraction_mean', float('nan')):.3f}`\n",
        f"- Max hold slip score: `{s.get('hold_max_slip_score_max', float('nan')):.3f}`\n",
        f"- Max crush risk: `{s.get('max_crush_risk_max', float('nan')):.3f}`\n",
        f"- Max penetration: `{s.get('max_penetration_m_max', float('nan')):.6f} m`\n",
        f"- Failure reasons: `{s['failure_reasons']}`\n",
        f"- Risk flags: `{s['risk_flags']}`\n\n",
        "## Trial Summary\n\n",
        "| trial | success | lift m | hold stable | hold max slip | crush | penetration m | first contact | risks | failures |\n",
        "|---|---:|---:|---:|---:|---:|---:|---|---|---|\n",
    ]
    for row in payload["results"]:
        lines.append(
            f"| {row['trial']} | {int(row['success'])} | {row['final_lift_height_m']:.5f} | "
            f"{row['hold_stable_fraction']:.3f} | {row['hold_max_slip_score']:.3f} | "
            f"{row['max_crush_risk']:.3f} | {row['max_penetration_m']:.6f} | "
            f"`{row['first_contact_phase']}` | `{row['risk_flags']}` | `{row['failure_reasons']}` |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
        ]
    )
    if payload["status"] == "PASS":
        lines.append("- The Stage3.5 scripted expert passed the fixed 10-trial MuJoCo gate.\n")
    else:
        lines.append("- The Stage3.5 scripted expert did not pass; inspect failure reasons before collecting datasets or training policies.\n")
    lines.extend(
        [
            "- Visual pose is used for pre-contact localization; tactile/slip is used for post-contact stability and hold checks.\n",
            "- Early approach contact and transient non-hold slip are reported as risk flags for later control refinement, not hidden.\n",
            "- This does not claim real hardware or real-camera integration.\n\n",
            f"Metadata: `{payload['metadata']}`\n",
            f"Visual checks: `{payload['visual_dir']}`\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Stage3.5 sensor-aware gentle grasp/lift/hold expert.")
    parser.add_argument("--scene", default=str(CURRENT_STAGE3_SCENE))
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
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
    parser.add_argument("--render-snapshots", action=argparse.BooleanOptionalAction, default=True)
    return parser


def main() -> int:
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
    rows = []
    for trial in sweep.trial_configs():
        egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
        row = run_expert_episode(model, mujoco, trial=trial, egg_position=egg_position, args=args, visual_dir=visual_dir)
        rows.append(row)
        print(
            f"{trial.name}: success={row.get('success')} lift={row.get('final_lift_height_m', float('nan')):.4f} "
            f"hold_stable={row.get('hold_stable_fraction', float('nan')):.3f} failures={row.get('failure_reasons')}"
        )
    summary = summarize(rows)
    status = "PASS" if summary["successes"] == summary["episodes"] else "FAIL"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "scene": str(scene),
        "camera": str(args.camera),
        "thresholds": {
            "min_vision_confidence": float(args.min_vision_confidence),
            "functional_hit_threshold_m": float(args.functional_hit_threshold),
            "min_hold_stable_fraction": float(args.min_hold_stable_fraction),
            "hold_steps": int(args.hold_steps),
            "hold_duration_s": float(args.hold_steps) * float(model.opt.timestep),
        },
        "results": rows,
        "summary": summary,
        "metadata": str(metadata),
        "visual_dir": str(visual_dir),
    }
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    report_payload = json.loads(json.dumps(json_ready(payload)))
    write_report(report, report_payload)
    print(f"Status: {status}")
    print(f"Report: {report}")
    print(f"Metadata: {metadata}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
