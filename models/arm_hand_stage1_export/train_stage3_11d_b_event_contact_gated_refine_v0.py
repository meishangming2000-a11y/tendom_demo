#!/usr/bin/env python3
"""Stage3.11D-B event-driven true-pinch refinement.

This is MuJoCo-only local parameter/action-phase search. It extends the broad
small-ball search by waiting for thumb+active true-tip contact before lifting
and releasing after a short stable lifted window.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
from external_sensors.mujoco_motor_force_feedback_sensor import (
    MotorForceFeedbackConfig,
    MujocoMotorForceFeedbackSensor,
    summarize_motor_force_feedback_samples,
)
import train_stage3_11d_b_ball_true_pinch_release_candidates_v0 as broad


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DEFAULT_SCENE = broad.DEFAULT_SCENE
DEFAULT_REPORT = DOCS / "stage3_11d_b_event_contact_gated_refine_v0_report.md"
DEFAULT_METADATA = META / "stage3_11d_b_event_contact_gated_refine_v0.json"
DEFAULT_SELECTED = META / "stage3_11d_b_event_contact_gated_refine_selected_v0.json"
DEFAULT_VISUAL_DIR = DOCS / "visual_checks_stage3_11d_b_event_contact_gated_refine_v0"
DEFAULT_SEED = META / "stage3_11d_b_ball_true_pinch_release_selected_v0.json"
EXTRA_RENDER_LABELS = {"02_contact_gate", "03_slow_lift", "04_hold", "05_release_open", "06_settle_release"}
EXTRA_RENDER_VIEWS = {
    "finger_side": {"azimuth": 118.0, "elevation": -14.0, "distance": 0.25, "lookat_dz": 0.005},
    "thumb_side": {"azimuth": 238.0, "elevation": -14.0, "distance": 0.25, "lookat_dz": 0.005},
}


@dataclass(frozen=True)
class RefineCase:
    name: str
    candidate: broad.BallPinchCandidate
    tip_pair_separation_target: float
    grasp_offset_x: float
    grasp_offset_y: float
    grasp_offset_z: float
    ball_radius: float
    ball_mass: float
    hold_steps: int
    min_lift_height: float
    ball_offset_x: float = 0.0
    ball_offset_y: float = 0.0
    ball_offset_z: float = 0.0


def parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def candidate_from_seed(path: Path) -> broad.BallPinchCandidate:
    raw = json.loads(path.read_text(encoding="utf-8"))
    candidate = raw.get("selected_candidate", raw.get("candidate", raw))
    return broad.BallPinchCandidate(**candidate)


def metric_distance(values: dict[str, float], base: dict[str, float], scales: dict[str, float]) -> float:
    total = 0.0
    for key, value in values.items():
        scale = max(float(scales.get(key, 1.0)), 1e-9)
        total += ((float(value) - float(base[key])) / scale) ** 2
    return math.sqrt(total)


def format_token(value: float, digits: int = 3) -> str:
    return f"{value:+.{digits}f}".replace("+", "p").replace("-", "m").replace(".", "p")


def local_cases(args: argparse.Namespace) -> list[RefineCase]:
    seed = candidate_from_seed(Path(args.seed_candidate))
    base_values = {
        "thumb_cmc_abd": seed.thumb_cmc_abd,
        "thumb_mcp": seed.thumb_mcp,
        "active_mcp_abd": seed.active_mcp_abd,
        "active_pip": seed.active_pip,
        "tip_sep": float(args.base_tip_pair_separation_target),
        "grasp_x": float(args.grasp_offset_x),
        "grasp_y": float(args.grasp_offset_y),
        "grasp_z": float(args.base_grasp_offset_z),
        "lift_j2": seed.lift_j2,
        "lift_steps": float(seed.lift_steps),
        "hold_steps": float(args.base_hold_steps),
        "min_lift": float(args.base_min_lift_height),
    }
    scales = {
        "thumb_cmc_abd": 0.08,
        "thumb_mcp": 0.06,
        "active_mcp_abd": 0.08,
        "active_pip": 0.10,
        "tip_sep": 0.006,
        "grasp_x": 0.001,
        "grasp_y": 0.001,
        "grasp_z": 0.002,
        "lift_j2": 0.08,
        "lift_steps": 120.0,
        "hold_steps": 80.0,
        "min_lift": 0.015,
    }
    grasp_x_values = (
        parse_float_list(args.grasp_offset_x_values)
        if args.grasp_offset_x_values
        else [float(args.grasp_offset_x)]
    )
    grasp_y_values = (
        parse_float_list(args.grasp_offset_y_values)
        if args.grasp_offset_y_values
        else [float(args.grasp_offset_y)]
    )
    raw: list[tuple[float, RefineCase]] = []
    for thumb_abd in parse_float_list(args.thumb_abd_values):
        for thumb_mcp in parse_float_list(args.thumb_mcp_values):
            for active_abd in parse_float_list(args.active_abd_values):
                for active_pip in parse_float_list(args.active_pip_values):
                    for tip_sep in parse_float_list(args.tip_pair_separation_values):
                        for grasp_x in grasp_x_values:
                            for grasp_y in grasp_y_values:
                                for grasp_z in parse_float_list(args.grasp_offset_z_values):
                                    for lift_j2 in parse_float_list(args.lift_j2_values):
                                        for lift_steps in parse_int_list(args.lift_steps_values):
                                            for hold_steps in parse_int_list(args.hold_steps_values):
                                                for min_lift in parse_float_list(args.min_lift_height_values):
                                                    values = {
                                                        "thumb_cmc_abd": thumb_abd,
                                                        "thumb_mcp": thumb_mcp,
                                                        "active_mcp_abd": active_abd,
                                                        "active_pip": active_pip,
                                                        "tip_sep": tip_sep,
                                                        "grasp_x": grasp_x,
                                                        "grasp_y": grasp_y,
                                                        "grasp_z": grasp_z,
                                                        "lift_j2": lift_j2,
                                                        "lift_steps": float(lift_steps),
                                                        "hold_steps": float(hold_steps),
                                                        "min_lift": min_lift,
                                                    }
                                                    dist = metric_distance(values, base_values, scales)
                                                    name = (
                                                        f"event_thumb_{seed.active_finger}"
                                                        f"_tabd{format_token(thumb_abd)}"
                                                        f"_tmcp{format_token(thumb_mcp)}"
                                                        f"_aabd{format_token(active_abd)}"
                                                        f"_apip{format_token(active_pip)}"
                                                        f"_sep{tip_sep:.3f}"
                                                        f"_gx{format_token(grasp_x, 4)}"
                                                        f"_gy{format_token(grasp_y, 4)}"
                                                        f"_gz{format_token(grasp_z, 4)}"
                                                        f"_lj2{format_token(lift_j2)}"
                                                        f"_ls{int(lift_steps)}"
                                                        f"_hs{int(hold_steps)}"
                                                        f"_ml{min_lift:.3f}"
                                                    ).replace("+", "p").replace("-", "m").replace(".", "p")
                                                    candidate = broad.BallPinchCandidate(
                                                        name=name,
                                                        active_finger=seed.active_finger,
                                                        thumb_cmc_abd=float(thumb_abd),
                                                        thumb_cmc=float(seed.thumb_cmc),
                                                        thumb_mcp=float(thumb_mcp),
                                                        thumb_ip=float(seed.thumb_ip),
                                                        active_mcp_flex=float(seed.active_mcp_flex),
                                                        active_mcp_abd=float(active_abd),
                                                        active_pip=float(active_pip),
                                                        active_dip=float(active_pip * 0.45),
                                                        inactive_scale=float(args.inactive_scale),
                                                        tip_sliding_mu=float(args.tip_mu),
                                                        non_tip_sliding_mu=float(args.non_tip_mu),
                                                        ball_sliding_mu=float(args.ball_mu),
                                                        lift_j2=float(lift_j2),
                                                        lift_steps=int(lift_steps),
                                                    )
                                                    raw.append(
                                                        (
                                                            dist,
                                                            RefineCase(
                                                                name=name,
                                                                candidate=candidate,
                                                                tip_pair_separation_target=float(tip_sep),
                                                                grasp_offset_x=float(grasp_x),
                                                                grasp_offset_y=float(grasp_y),
                                                                grasp_offset_z=float(grasp_z),
                                                                ball_radius=float(args.ball_radius),
                                                                ball_mass=float(args.ball_mass),
                                                                ball_offset_x=0.0,
                                                                ball_offset_y=0.0,
                                                                ball_offset_z=0.0,
                                                                hold_steps=int(hold_steps),
                                                                min_lift_height=float(min_lift),
                                                            ),
                                                        )
                                                    )
    raw.sort(key=lambda item: (item[0], item[1].name))
    return [case for _, case in raw[: max(1, int(args.max_cases))]]


def run_args_for_case(args: argparse.Namespace, case: RefineCase) -> SimpleNamespace:
    base = broad.build_parser().parse_args([])
    data = vars(base)
    data.update(
        {
            "scene": Path(args.scene),
            "ball_radius": case.ball_radius,
            "ball_mass": case.ball_mass,
            "tip_mu": case.candidate.tip_sliding_mu,
            "non_tip_mu": case.candidate.non_tip_sliding_mu,
            "ball_mu": case.candidate.ball_sliding_mu,
            "inactive_scale": case.candidate.inactive_scale,
            "grasp_offset_x": case.grasp_offset_x,
            "grasp_offset_y": case.grasp_offset_y,
            "grasp_offset_z": case.grasp_offset_z,
            "tip_pair_separation_target": case.tip_pair_separation_target,
            "ik_maxiter": int(args.ik_maxiter),
            "approach_steps": int(args.approach_steps),
            "preshape_steps": int(args.preshape_steps),
            "close_steps": int(args.close_steps),
            "settle_steps": int(args.contact_gate_max_steps),
            "hold_steps": int(case.hold_steps),
            "release_steps": int(args.release_steps),
            "release_settle_steps": int(args.release_settle_steps),
            "lift_j2": case.candidate.lift_j2,
            "lift_steps": case.candidate.lift_steps,
            "morphology_sample_every": int(args.morphology_sample_every),
            "min_lift_height": case.min_lift_height,
            "max_hold_floor_contact_fraction": float(args.max_hold_floor_contact_fraction),
            "min_true_pinch_fraction": float(args.min_true_pinch_fraction),
            "max_wrap_fraction": float(args.max_wrap_fraction),
            "max_non_tip_ratio": float(args.max_non_tip_ratio),
            "max_penetration_m": float(args.max_penetration_m),
            "final_height_tolerance": float(args.final_height_tolerance),
        }
    )
    return SimpleNamespace(**data)


def safe_case_dir_name(name: str) -> str:
    if len(name) <= 92:
        return name
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:10]
    return f"{name[:78]}__{digest}"


def apply_targets(model, data, mujoco, names: list[str], targets: dict[str, float]) -> None:
    for joint, value in targets.items():
        qadr = broad.joint_qadr(model, mujoco, joint)
        if qadr is not None:
            data.qpos[qadr] = float(value)
    data.ctrl[:] = broad.ball_demo.ctrl_from_targets(model, mujoco, names, targets)


def step_toward(model, data, mujoco, names: list[str], start: dict[str, float], end: dict[str, float], alpha: float) -> dict[str, float]:
    target = broad.ball_demo.blend_targets(start, end, float(alpha))
    data.ctrl[:] = broad.ball_demo.ctrl_from_targets(model, mujoco, names, target)
    mujoco.mj_step(model, data)
    return target


def run_event_candidate(model, mujoco, case: RefineCase, args: argparse.Namespace, *, render_dir: Path | None = None) -> dict[str, Any]:
    run_args = run_args_for_case(args, case)
    candidate = case.candidate
    data = mujoco.MjData(model)
    ball_config = broad.configure_ball_model(model, mujoco, run_args)
    mujoco.mj_forward(model, data)
    initial_ball = broad.ball_position(model, data, mujoco)
    if ball_config.get("configured"):
        initial_ball = initial_ball.copy()
        initial_ball[2] = float(ball_config["floor_z_m"]) + float(ball_config["radius_m"])
    initial_ball = initial_ball.copy()
    initial_ball[0] += float(case.ball_offset_x)
    initial_ball[1] += float(case.ball_offset_y)
    initial_ball[2] += float(case.ball_offset_z)
    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    broad.ball_demo.set_ball_pose(model, data, mujoco, initial_ball)
    mujoco.mj_forward(model, data)

    names = broad.ball_demo.actuator_names(model, mujoco)
    default_targets = broad.actuated_joint_targets_from_qpos(model, data, mujoco, names)
    material_changes = broad.set_contact_materials(model, mujoco, candidate)
    ik = broad.solve_arm_for_tip_pair(model, mujoco, candidate, initial_ball, run_args)
    targets = broad.phase_targets(default_targets, ik["joints"], candidate)
    apply_targets(model, data, mujoco, names, targets["pre"])
    broad.ball_demo.set_ball_pose(model, data, mujoco, initial_ball)
    mujoco.mj_forward(model, data)

    snapshots: dict[str, str] = {}
    hold_frames: list[dict[str, Any]] = []
    lift_frames: list[dict[str, Any]] = []
    contact_gate_frames: list[dict[str, Any]] = []
    hold_lifts: list[float] = []
    lift_lifts: list[float] = []
    max_lift = 0.0
    max_pen = 0.0
    dense_trace_enabled = bool(getattr(args, "capture_dense_sensor_trace", False))
    dense_trace_sample_every = max(1, int(getattr(args, "dense_trace_sample_every", 1)))
    dense_sensor_trace: list[dict[str, Any]] = []
    motor_feedback_sensor = (
        MujocoMotorForceFeedbackSensor(
            MotorForceFeedbackConfig(
                torque_constant_nm_per_a=float(args.motor_torque_constant_nm_per_a),
                gear_ratio=float(args.motor_gear_ratio),
                gear_efficiency=float(args.motor_gear_efficiency),
                spool_radius_m=float(args.motor_spool_radius_m),
                current_limit_a=float(args.motor_current_limit_a),
                bus_voltage_v=float(args.motor_bus_voltage_v),
                current_noise_a=float(args.motor_current_noise_a),
                seed=int(args.motor_feedback_seed),
            )
        )
        if bool(args.enable_motor_force_feedback)
        else None
    )
    motor_feedback_samples: list[dict[str, Any]] = []

    def sample(
        label: str,
        *,
        phase_step: int | None = None,
        phase_progress: float = 0.0,
        record_dense: bool | None = None,
    ) -> dict[str, Any]:
        nonlocal max_lift, max_pen
        rows = broad.contact_rows(model, data, mujoco)
        morph = broad.frame_morphology(rows, candidate)
        ball = broad.ball_position(model, data, mujoco)
        lift = float(ball[2] - initial_ball[2])
        max_lift = max(max_lift, lift)
        max_pen = max(max_pen, max([float(row["penetration"]) for row in rows] + [0.0]))
        frame = {
            "label": label,
            "initial_ball": initial_ball.copy(),
            "ball_position": ball,
            "lift_m": lift,
            "morphology": morph,
            "max_penetration_m": float(max([float(row["penetration"]) for row in rows] + [0.0])),
        }
        state_required = bool(getattr(args, "include_frame_state", False)) or callable(
            getattr(args, "residual_quality_predictor", None)
        )
        if state_required:
            frame["ctrl"] = np.asarray(data.ctrl, dtype=np.float32).copy()
            frame["qpos"] = np.asarray(data.qpos, dtype=np.float32).copy()
            frame["qvel"] = np.asarray(data.qvel, dtype=np.float32).copy()
        if motor_feedback_sensor is not None:
            feedback = motor_feedback_sensor.observe(
                model,
                data,
                mujoco,
                phase=label,
                active_pair=("thumb", candidate.active_finger),
            )
            frame["motor_force_feedback"] = feedback
            motor_feedback_samples.append(feedback)
        should_record_dense = dense_trace_enabled if record_dense is None else bool(record_dense)
        if should_record_dense and dense_trace_enabled:
            dense_sensor_trace.append(
                {
                    "dense_step_index": int(len(dense_sensor_trace)),
                    "label": label,
                    "phase_step": int(phase_step) if phase_step is not None else -1,
                    "phase_progress": float(phase_progress),
                    "time_s": float(data.time),
                    "ball_position": np.asarray(ball, dtype=np.float32).copy(),
                    "lift_m": float(lift),
                    "morphology": morph,
                    "max_penetration_m": float(frame["max_penetration_m"]),
                    "motor_force_feedback": frame.get("motor_force_feedback", {}),
                    "ctrl": np.asarray(data.ctrl, dtype=np.float32).copy(),
                    "qpos": np.asarray(data.qpos, dtype=np.float32).copy(),
                    "qvel": np.asarray(data.qvel, dtype=np.float32).copy(),
                }
            )
        return frame

    def clamp_joint_target(joint: str, value: float) -> float:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint)
        if jid < 0:
            return float(value)
        lo, hi = (float(v) for v in model.jnt_range[jid])
        return float(np.clip(float(value), lo, hi))

    def with_pair_preload(target: dict[str, float], level: float) -> dict[str, float]:
        if level <= 0.0:
            return copy.deepcopy(target)
        out = copy.deepcopy(target)
        active = candidate.active_finger
        edits = {
            "thumb_mcp_joint": out.get("thumb_mcp_joint", candidate.thumb_mcp) + 0.55 * level,
            "thumb_ip_joint": out.get("thumb_ip_joint", candidate.thumb_ip) - 0.40 * level,
            f"{active}_pip_joint": out.get(f"{active}_pip_joint", candidate.active_pip) - level,
            f"{active}_dip_joint": out.get(f"{active}_dip_joint", candidate.active_dip) - 0.45 * level,
            f"{active}_mcp_abd_joint": out.get(f"{active}_mcp_abd_joint", candidate.active_mcp_abd) - 0.20 * level,
        }
        for joint, value in edits.items():
            out[joint] = clamp_joint_target(joint, value)
        return out

    def pair_feedback_from_frame(frame: dict[str, Any]) -> dict[str, Any]:
        return frame.get("motor_force_feedback", {}).get("active_pair", {})

    def pair_force_ok(frame: dict[str, Any], phase: str) -> bool:
        if not bool(args.enable_force_feedback_lift_gate):
            return True
        pair = pair_feedback_from_frame(frame)
        if not pair.get("configured", False):
            return False
        min_tension = (
            float(args.force_feedback_min_hold_pair_tension_n)
            if phase == "hold"
            else float(args.force_feedback_min_slow_lift_pair_tension_n)
        )
        return bool(
            float(pair.get("total_tendon_tension_n", 0.0)) >= min_tension
            and float(pair.get("balance_ratio", 0.0)) >= float(args.force_feedback_min_pair_balance)
            and float(pair.get("max_abs_iq_a", 0.0)) <= float(args.force_feedback_max_pair_iq_a)
            and int(pair.get("saturated_actuator_count", 0)) == 0
        )

    def pair_quality_ok(frame: dict[str, Any], phase: str) -> bool:
        if not bool(getattr(args, "enable_motor_force_feedback", False)):
            return True
        pair = pair_feedback_from_frame(frame)
        if not pair.get("configured", False):
            return False
        min_tension = (
            float(args.force_feedback_min_hold_pair_tension_n)
            if phase == "hold"
            else float(args.force_feedback_min_slow_lift_pair_tension_n)
        )
        return bool(
            float(pair.get("total_tendon_tension_n", 0.0)) >= min_tension
            and float(pair.get("balance_ratio", 0.0)) >= float(args.force_feedback_min_pair_balance)
            and float(pair.get("max_abs_iq_a", 0.0)) <= float(args.force_feedback_max_pair_iq_a)
            and int(pair.get("saturated_actuator_count", 0)) == 0
        )

    def frame_lift_quality_ok(frame: dict[str, Any], phase: str) -> bool:
        morph = frame.get("morphology", {})
        if not isinstance(morph, dict):
            morph = {}
        morphology_ok = bool(
            bool(morph.get("true_two_tip_pinch", False))
            and int(morph.get("floor_contacts", 0)) == 0
            and not bool(morph.get("wrap_or_support", False))
            and float(frame.get("max_penetration_m", 0.0)) <= float(args.max_penetration_m)
        )
        rule_quality_ok = bool(morphology_ok and pair_quality_ok(frame, phase))
        predictor = getattr(args, "residual_quality_predictor", None)
        if callable(predictor):
            prediction = predictor(frame=frame, phase=phase, case=case, run_args=run_args)
            if isinstance(prediction, dict):
                frame["residual_quality_prediction"] = prediction
                threshold = float(getattr(args, "residual_quality_predictor_threshold", 0.5))
                risk_threshold = float(getattr(args, "residual_quality_predictor_risk_threshold", 0.5))
                predicted_quality_ok = bool(
                    float(prediction.get("morphology_clean_now", 1.0)) >= threshold
                    and float(prediction.get("lift_quality_now", 1.0)) >= threshold
                    and float(prediction.get("wrap_now", 0.0)) <= risk_threshold
                    and float(prediction.get("floor_contact_now", 0.0)) <= risk_threshold
                    and float(prediction.get("penetration_risk_now", 0.0)) <= risk_threshold
                )
                if bool(getattr(args, "residual_quality_predictor_requires_rule_ok", True)):
                    return bool(rule_quality_ok and predicted_quality_ok)
                return predicted_quality_ok
        return rule_quality_ok

    def residual_adjust_eligible(frame: dict[str, Any]) -> bool:
        morph = frame.get("morphology", {})
        if not isinstance(morph, dict):
            morph = {}
        if int(morph.get("floor_contacts", 0)) > 0:
            return False
        if float(frame.get("max_penetration_m", 0.0)) > float(args.max_penetration_m):
            return False
        if bool(morph.get("wrap_or_support", False)) and not bool(
            getattr(args, "residual_micro_adjust_allow_wrap", False)
        ):
            return False
        return True

    def maybe_render(label: str) -> None:
        if render_dir is None:
            return
        path = render_dir / f"{label}.png"
        frame = sample(label)
        snapshots[label] = broad.render_frame(model, data, mujoco, candidate, path, frame)
        if bool(getattr(args, "render_extra_side_views", False)) and label in EXTRA_RENDER_LABELS:
            for view_name, view in EXTRA_RENDER_VIEWS.items():
                view_path = render_dir / f"{label}_{view_name}.png"
                snapshots[f"{label}_{view_name}"] = broad.render_frame(
                    model,
                    data,
                    mujoco,
                    candidate,
                    view_path,
                    frame,
                    camera_view=view,
                )

    maybe_render("00_start")
    fixed_phases = [
        ("approach", targets["pre"], targets["approach"], int(args.approach_steps)),
        ("preshape", targets["approach"], targets["preshape"], int(args.preshape_steps)),
        ("pinch_close", targets["preshape"], targets["close"], int(args.close_steps)),
    ]
    for phase, start, end, steps in fixed_phases:
        for idx in range(max(1, steps)):
            alpha = idx / max(1, steps - 1)
            step_toward(model, data, mujoco, names, start, end, alpha)
            if dense_trace_enabled and idx % dense_trace_sample_every == 0:
                sample(phase, phase_step=idx, phase_progress=alpha, record_dense=True)
        if phase == "pinch_close":
            maybe_render("01_pinch_close")

    contact_gate_success = False
    contact_gate_step = None
    consecutive_contact_samples = 0
    for idx in range(max(1, int(args.contact_gate_max_steps))):
        data.ctrl[:] = broad.ball_demo.ctrl_from_targets(model, mujoco, names, targets["close"])
        mujoco.mj_step(model, data)
        if idx % max(1, int(args.morphology_sample_every)) == 0:
            frame = sample(
                "contact_gate",
                phase_step=idx,
                phase_progress=idx / max(1, int(args.contact_gate_max_steps) - 1),
                record_dense=True,
            )
            morph = frame["morphology"]
            contact_gate_frames.append(morph)
            if bool(morph.get("true_two_tip_pinch", False)):
                consecutive_contact_samples += 1
            else:
                consecutive_contact_samples = 0
            if consecutive_contact_samples >= int(args.contact_gate_required_samples):
                contact_gate_success = True
                contact_gate_step = idx
                break
        elif dense_trace_enabled and idx % dense_trace_sample_every == 0:
            sample(
                "contact_gate",
                phase_step=idx,
                phase_progress=idx / max(1, int(args.contact_gate_max_steps) - 1),
                record_dense=True,
            )
    maybe_render("02_contact_gate")

    if contact_gate_success:
        for idx in range(max(0, int(args.post_contact_settle_steps))):
            data.ctrl[:] = broad.ball_demo.ctrl_from_targets(model, mujoco, names, targets["close"])
            mujoco.mj_step(model, data)
            if dense_trace_enabled and idx % dense_trace_sample_every == 0:
                sample(
                    "post_contact_settle",
                    phase_step=idx,
                    phase_progress=idx / max(1, int(args.post_contact_settle_steps) - 1),
                    record_dense=True,
                )

    preload_level = 0.0
    force_feedback_preload_break_reason = "disabled"
    force_feedback_preload_samples = 0
    if bool(args.enable_force_feedback_lift_gate) and not bool(args.force_feedback_enable_preload):
        force_feedback_preload_break_reason = "preload_disabled"
    if (
        contact_gate_success
        and bool(args.enable_force_feedback_lift_gate)
        and bool(args.force_feedback_enable_preload)
    ):
        force_feedback_preload_break_reason = "steps_exhausted"
        consecutive_preload_ok = 0
        preload_steps = max(1, int(args.force_feedback_preload_steps))
        for idx in range(preload_steps):
            preload_level = min(
                float(args.force_feedback_max_preload_delta),
                float(args.force_feedback_max_preload_delta) * float(idx + 1) / float(preload_steps),
            )
            preload_target = with_pair_preload(targets["close"], preload_level)
            data.ctrl[:] = broad.ball_demo.ctrl_from_targets(model, mujoco, names, preload_target)
            mujoco.mj_step(model, data)
            if idx % max(1, int(args.morphology_sample_every)) == 0:
                frame = sample(
                    "preload",
                    phase_step=idx,
                    phase_progress=idx / max(1, preload_steps - 1),
                    record_dense=True,
                )
                force_feedback_preload_samples += 1
                if pair_force_ok(frame, "slow_lift"):
                    consecutive_preload_ok += 1
                else:
                    consecutive_preload_ok = 0
                if (
                    preload_level >= float(args.force_feedback_min_preload_delta)
                    and consecutive_preload_ok >= int(args.force_feedback_required_samples)
                ):
                    force_feedback_preload_break_reason = "pair_force_window_met"
                    break
            elif dense_trace_enabled and idx % dense_trace_sample_every == 0:
                sample(
                    "preload",
                    phase_step=idx,
                    phase_progress=idx / max(1, preload_steps - 1),
                    record_dense=True,
                )
        targets["close"] = with_pair_preload(targets["close"], preload_level)
        targets["lift"] = with_pair_preload(targets["lift"], preload_level)

    lift_break_reason = "not_started"
    last_lift_target = copy.deepcopy(targets["close"])
    consecutive_lifted_tip_samples = 0
    force_feedback_lift_low_force_samples = 0
    force_feedback_lift_wait_steps = 0
    residual_micro_adjust_level = 0.0
    residual_micro_adjust_quality_bad_samples = 0
    residual_micro_adjust_wait_steps = 0
    residual_micro_adjust_events = 0
    residual_micro_adjust_close_events = 0
    residual_micro_adjust_progress_drop_steps = 0
    residual_micro_adjust_grasp_x_delta_total = 0.0
    residual_micro_adjust_ik_solves = 0
    residual_micro_adjust_prelift_events = 0

    def apply_residual_grasp_x_retarget(delta: float, max_abs_delta: float) -> bool:
        nonlocal residual_micro_adjust_grasp_x_delta_total, residual_micro_adjust_ik_solves, targets
        if float(delta) == 0.0 or abs(float(max_abs_delta)) <= 0.0:
            return False
        old_grasp_x_delta = residual_micro_adjust_grasp_x_delta_total
        residual_micro_adjust_grasp_x_delta_total = float(
            np.clip(
                residual_micro_adjust_grasp_x_delta_total + float(delta),
                -abs(float(max_abs_delta)),
                abs(float(max_abs_delta)),
            )
        )
        if residual_micro_adjust_grasp_x_delta_total == old_grasp_x_delta:
            return False
        adjusted_args = copy.copy(run_args)
        adjusted_args.grasp_offset_x = float(case.grasp_offset_x + residual_micro_adjust_grasp_x_delta_total)
        adjusted_ik = broad.solve_arm_for_tip_pair(model, mujoco, candidate, initial_ball, adjusted_args)
        adjusted_targets = broad.phase_targets(default_targets, adjusted_ik["joints"], candidate)
        targets["close"] = adjusted_targets["close"]
        targets["lift"] = adjusted_targets["lift"]
        if residual_micro_adjust_level > 0.0:
            targets["close"] = with_pair_preload(targets["close"], residual_micro_adjust_level)
            targets["lift"] = with_pair_preload(targets["lift"], residual_micro_adjust_level)
        residual_micro_adjust_ik_solves += 1
        return True

    if (
        contact_gate_success
        and bool(getattr(args, "enable_residual_micro_adjust", False))
        and bool(getattr(args, "residual_micro_adjust_enable_prelift", False))
    ):
        prelift_probe = sample("post_contact_settle", record_dense=False)
        prelift_bad = not frame_lift_quality_ok(prelift_probe, "slow_lift")
        prelift_safe = bool(float(prelift_probe.get("max_penetration_m", 0.0)) <= float(args.max_penetration_m))
        if prelift_bad and prelift_safe:
            changed = apply_residual_grasp_x_retarget(
                float(getattr(args, "residual_micro_adjust_prelift_grasp_x_delta", 0.0)),
                float(getattr(args, "residual_micro_adjust_prelift_max_grasp_x_delta", 0.0)),
            )
            if changed:
                residual_micro_adjust_prelift_events += 1
                for pre_idx in range(max(0, int(getattr(args, "residual_micro_adjust_prelift_steps", 0)))):
                    data.ctrl[:] = broad.ball_demo.ctrl_from_targets(model, mujoco, names, targets["close"])
                    mujoco.mj_step(model, data)
                    if dense_trace_enabled and pre_idx % dense_trace_sample_every == 0:
                        sample(
                            "post_contact_settle",
                            phase_step=pre_idx,
                            phase_progress=pre_idx
                            / max(1, int(getattr(args, "residual_micro_adjust_prelift_steps", 1)) - 1),
                            record_dense=True,
                        )
    if contact_gate_success or not bool(args.require_contact_gate):
        lift_break_reason = "lift_steps_exhausted"
        idx = 0
        progress = 0
        sample_every = max(1, int(args.morphology_sample_every))
        max_lift_steps = max(1, int(candidate.lift_steps)) + (
            int(args.force_feedback_max_lift_wait_steps) if bool(args.enable_force_feedback_lift_gate) else 0
        ) + (
            int(getattr(args, "residual_micro_adjust_max_wait_steps", 0))
            if bool(getattr(args, "enable_residual_micro_adjust", False))
            else 0
        )
        while idx < max_lift_steps and progress < max(1, int(candidate.lift_steps)):
            hold_progress_for_force = False
            hold_progress_for_residual = False
            alpha = progress / max(1, int(candidate.lift_steps) - 1)
            last_lift_target = step_toward(model, data, mujoco, names, targets["close"], targets["lift"], alpha)
            if idx % sample_every == 0:
                frame = sample("slow_lift", phase_step=idx, phase_progress=alpha, record_dense=True)
                morph = frame["morphology"]
                lift_frames.append(morph)
                lift_lifts.append(float(frame["lift_m"]))
                force_ok = pair_force_ok(frame, "slow_lift")
                if not force_ok and bool(args.enable_force_feedback_lift_gate):
                    force_feedback_lift_low_force_samples += 1
                    if progress >= int(args.force_feedback_check_after_lift_steps):
                        hold_progress_for_force = (
                            force_feedback_lift_wait_steps < int(args.force_feedback_max_lift_wait_steps)
                        )
                        if hold_progress_for_force:
                            force_feedback_lift_wait_steps += sample_every
                            if bool(args.force_feedback_enable_preload):
                                preload_level = min(
                                    float(args.force_feedback_max_preload_delta),
                                    preload_level + float(args.force_feedback_lift_wait_close_delta),
                                )
                                targets["close"] = with_pair_preload(targets["close"], preload_level)
                                targets["lift"] = with_pair_preload(targets["lift"], preload_level)
                if bool(getattr(args, "enable_residual_micro_adjust", False)):
                    quality_ok = frame_lift_quality_ok(frame, "slow_lift")
                    if not quality_ok:
                        residual_micro_adjust_quality_bad_samples += 1
                    if (
                        not quality_ok
                        and residual_adjust_eligible(frame)
                        and progress >= int(getattr(args, "residual_micro_adjust_check_after_lift_steps", 0))
                        and residual_micro_adjust_quality_bad_samples
                        >= int(getattr(args, "residual_micro_adjust_required_samples", 1))
                        and residual_micro_adjust_wait_steps
                        < int(getattr(args, "residual_micro_adjust_max_wait_steps", 0))
                    ):
                        hold_progress_for_residual = True
                        residual_micro_adjust_events += 1
                        residual_micro_adjust_wait_steps += sample_every
                        close_delta = float(getattr(args, "residual_micro_adjust_close_delta", 0.0))
                        if close_delta > 0.0:
                            residual_micro_adjust_level = min(
                                float(getattr(args, "residual_micro_adjust_max_close_delta", close_delta)),
                                residual_micro_adjust_level + close_delta,
                            )
                            targets["close"] = with_pair_preload(targets["close"], residual_micro_adjust_level)
                            targets["lift"] = with_pair_preload(targets["lift"], residual_micro_adjust_level)
                            residual_micro_adjust_close_events += 1
                        grasp_x_delta = float(getattr(args, "residual_micro_adjust_grasp_x_delta", 0.0))
                        max_grasp_x_delta = abs(
                            float(getattr(args, "residual_micro_adjust_max_grasp_x_delta", 0.0))
                        )
                        apply_residual_grasp_x_retarget(grasp_x_delta, max_grasp_x_delta)
                        drop_steps = int(getattr(args, "residual_micro_adjust_progress_drop_steps", 0))
                        if drop_steps > 0:
                            old_progress = progress
                            progress = max(0, progress - drop_steps)
                            residual_micro_adjust_progress_drop_steps += int(old_progress - progress)
                lifted_tip = (
                    float(frame["lift_m"]) >= float(case.min_lift_height)
                    and bool(morph.get("true_two_tip_pinch", False))
                    and int(morph.get("floor_contacts", 0)) == 0
                    and force_ok
                )
                consecutive_lifted_tip_samples = consecutive_lifted_tip_samples + 1 if lifted_tip else 0
                if (
                    idx >= int(args.min_lift_steps_before_hold)
                    and consecutive_lifted_tip_samples >= int(args.lifted_contact_required_samples)
                ):
                    lift_break_reason = "lifted_tip_window_met"
                    break
            elif dense_trace_enabled and idx % dense_trace_sample_every == 0:
                sample("slow_lift", phase_step=idx, phase_progress=alpha, record_dense=True)
            if not hold_progress_for_force and not hold_progress_for_residual:
                progress += 1
            idx += 1
    maybe_render("03_slow_lift")

    hold_break_reason = "not_started"
    consecutive_hold_samples = 0
    if lift_break_reason != "not_started":
        hold_break_reason = "hold_steps_exhausted"
        for idx in range(max(1, int(case.hold_steps))):
            data.ctrl[:] = broad.ball_demo.ctrl_from_targets(model, mujoco, names, last_lift_target)
            mujoco.mj_step(model, data)
            if idx % max(1, int(args.morphology_sample_every)) == 0:
                frame = sample(
                    "hold",
                    phase_step=idx,
                    phase_progress=idx / max(1, int(case.hold_steps) - 1),
                    record_dense=True,
                )
                morph = frame["morphology"]
                hold_frames.append(morph)
                hold_lifts.append(float(frame["lift_m"]))
                stable = (
                    float(frame["lift_m"]) >= float(case.min_lift_height)
                    and bool(morph.get("true_two_tip_pinch", False))
                    and int(morph.get("floor_contacts", 0)) == 0
                    and not bool(morph.get("wrap_or_support", False))
                    and pair_force_ok(frame, "hold")
                )
                consecutive_hold_samples = consecutive_hold_samples + 1 if stable else 0
                if (
                    idx >= int(args.min_hold_steps_before_release)
                    and consecutive_hold_samples >= int(args.hold_release_required_samples)
                ):
                    hold_break_reason = "stable_hold_window_met"
                    break
            elif dense_trace_enabled and idx % dense_trace_sample_every == 0:
                sample(
                    "hold",
                    phase_step=idx,
                    phase_progress=idx / max(1, int(case.hold_steps) - 1),
                    record_dense=True,
                )
    maybe_render("04_hold")

    release_target = {**last_lift_target, **broad.hand_targets(candidate, open_hand=True)}
    for idx in range(max(1, int(args.release_steps))):
        alpha = idx / max(1, int(args.release_steps) - 1)
        step_toward(model, data, mujoco, names, last_lift_target, release_target, alpha)
        if dense_trace_enabled and idx % dense_trace_sample_every == 0:
            sample("release_open", phase_step=idx, phase_progress=alpha, record_dense=True)
    maybe_render("05_release_open")
    for idx in range(max(1, int(args.release_settle_steps))):
        data.ctrl[:] = broad.ball_demo.ctrl_from_targets(model, mujoco, names, release_target)
        mujoco.mj_step(model, data)
        if dense_trace_enabled and idx % dense_trace_sample_every == 0:
            sample(
                "release_settle",
                phase_step=idx,
                phase_progress=idx / max(1, int(args.release_settle_steps) - 1),
                record_dense=True,
            )
    maybe_render("06_settle_release")

    final_sample = sample("final")
    final_rows = broad.contact_rows(model, data, mujoco)
    final_morph = broad.frame_morphology(final_rows, candidate)
    hold_summary = broad.summarize_frames(hold_frames)
    lift_summary = broad.summarize_frames(lift_frames)
    gate_summary = broad.summarize_frames(contact_gate_frames)
    hold_lift_max = float(max(hold_lifts) if hold_lifts else 0.0)
    hold_lift_mean = float(np.mean(hold_lifts) if hold_lifts else 0.0)
    lift_lift_max = float(max(lift_lifts) if lift_lifts else 0.0)
    final_ball = broad.ball_position(model, data, mujoco)
    release_success = bool(
        final_morph["floor_contacts"] > 0
        and final_morph["hand_contacts"] == 0
        and abs(float(final_ball[2] - initial_ball[2])) <= float(args.final_height_tolerance)
    )
    lift_success = bool(
        hold_lift_max >= float(case.min_lift_height)
        and hold_summary["floor_contact_fraction"] <= float(args.max_hold_floor_contact_fraction)
    )
    true_pinch_success = bool(
        contact_gate_success
        and lift_success
        and hold_summary["true_two_tip_pinch_fraction"] >= float(args.min_true_pinch_fraction)
        and hold_summary["wrap_frame_fraction"] <= float(args.max_wrap_fraction)
        and hold_summary["non_tip_contact_ratio_mean"] <= float(args.max_non_tip_ratio)
    )
    success = bool(true_pinch_success and release_success)
    if success:
        terminal_reason = "success_event_contact_gated_true_pinch_release_ball"
    elif not contact_gate_success:
        terminal_reason = "contact_gate_failed"
    elif not lift_success:
        terminal_reason = "lift_gate_failed"
    elif not true_pinch_success:
        terminal_reason = "true_pinch_morphology_gate_failed"
    elif not release_success:
        terminal_reason = "release_gate_failed"
    else:
        terminal_reason = "unknown"

    score = (
        9.0 * float(hold_summary["true_two_tip_pinch_fraction"])
        + 4.0 * min(hold_lift_max / max(float(case.min_lift_height), 1e-6), 1.5)
        + 2.0 * min(hold_lift_max / max(float(args.demo_lift_goal), 1e-6), 1.5)
        + 2.0 * float(contact_gate_success)
        + 2.0 * float(release_success)
        + 0.8 * min(float(hold_summary["frames"]) / max(1.0, float(args.hold_release_required_samples)), 1.5)
        - 4.5 * float(hold_summary["wrap_frame_fraction"])
        - 3.0 * float(hold_summary["non_tip_contact_ratio_mean"])
        - 1.0 * float(lift_summary["floor_contact_fraction"])
        - 60.0 * max(0.0, float(max_pen) - float(args.max_penetration_m))
        - 10.0 * min(0.04, float(ik["midpoint_error_m"]))
        - 5.0 * min(0.05, float(ik["tip_separation_error_m"]))
    )

    return {
        "case": {
            "name": case.name,
            "candidate": asdict(candidate),
            "tip_pair_separation_target": case.tip_pair_separation_target,
            "grasp_offset_x": case.grasp_offset_x,
            "grasp_offset_y": case.grasp_offset_y,
            "grasp_offset_z": case.grasp_offset_z,
            "ball_radius": case.ball_radius,
            "ball_mass": case.ball_mass,
            "ball_offset_x": case.ball_offset_x,
            "ball_offset_y": case.ball_offset_y,
            "ball_offset_z": case.ball_offset_z,
            "hold_steps": case.hold_steps,
            "min_lift_height": case.min_lift_height,
        },
        "candidate": asdict(candidate),
        "status": "PASS" if success else "FAIL",
        "success": bool(success),
        "terminal_reason": terminal_reason,
        "score": float(score),
        "contact_gate_success": bool(contact_gate_success),
        "contact_gate_step": contact_gate_step,
        "lift_break_reason": lift_break_reason,
        "hold_break_reason": hold_break_reason,
        "lift_success": bool(lift_success),
        "true_pinch_success": bool(true_pinch_success),
        "release_success": bool(release_success),
        "initial_ball": initial_ball,
        "final_ball": final_ball,
        "max_lift_m": float(max_lift),
        "hold_lift_m_max": float(hold_lift_max),
        "hold_lift_m_mean": float(hold_lift_mean),
        "slow_lift_sample_lift_m_max": float(lift_lift_max),
        "max_penetration_m": float(max_pen),
        "contact_gate_morphology": gate_summary,
        "hold_morphology": hold_summary,
        "lift_morphology": lift_summary,
        "final_morphology": final_morph,
        "final_sample": final_sample,
        "motor_force_feedback_summary": summarize_motor_force_feedback_samples(motor_feedback_samples),
        "force_feedback_gate": {
            "enabled": bool(args.enable_force_feedback_lift_gate),
            "preload_enabled": bool(args.force_feedback_enable_preload),
            "preload_level": float(preload_level),
            "preload_break_reason": force_feedback_preload_break_reason,
            "preload_samples": int(force_feedback_preload_samples),
            "lift_low_force_samples": int(force_feedback_lift_low_force_samples),
            "lift_wait_steps": int(force_feedback_lift_wait_steps),
            "min_slow_lift_pair_tension_n": float(args.force_feedback_min_slow_lift_pair_tension_n),
            "min_hold_pair_tension_n": float(args.force_feedback_min_hold_pair_tension_n),
            "min_pair_balance": float(args.force_feedback_min_pair_balance),
        },
        "residual_micro_adjust": {
            "enabled": bool(getattr(args, "enable_residual_micro_adjust", False)),
            "quality_bad_samples": int(residual_micro_adjust_quality_bad_samples),
            "events": int(residual_micro_adjust_events),
            "close_events": int(residual_micro_adjust_close_events),
            "wait_steps": int(residual_micro_adjust_wait_steps),
            "progress_drop_steps": int(residual_micro_adjust_progress_drop_steps),
            "prelift_events": int(residual_micro_adjust_prelift_events),
            "final_close_level": float(residual_micro_adjust_level),
            "grasp_x_delta_total": float(residual_micro_adjust_grasp_x_delta_total),
            "ik_solves": int(residual_micro_adjust_ik_solves),
            "check_after_lift_steps": int(getattr(args, "residual_micro_adjust_check_after_lift_steps", 0)),
            "max_wait_steps": int(getattr(args, "residual_micro_adjust_max_wait_steps", 0)),
            "close_delta": float(getattr(args, "residual_micro_adjust_close_delta", 0.0)),
            "max_close_delta": float(getattr(args, "residual_micro_adjust_max_close_delta", 0.0)),
            "grasp_x_delta": float(getattr(args, "residual_micro_adjust_grasp_x_delta", 0.0)),
            "max_grasp_x_delta": float(getattr(args, "residual_micro_adjust_max_grasp_x_delta", 0.0)),
        },
        "dense_sensor_trace": dense_sensor_trace,
        "dense_sensor_trace_schema": {
            "enabled": bool(dense_trace_enabled),
            "sample_every": int(dense_trace_sample_every),
            "fields": [
                "dense_step_index",
                "label",
                "phase_step",
                "phase_progress",
                "time_s",
                "ball_position",
                "lift_m",
                "morphology",
                "max_penetration_m",
                "motor_force_feedback",
                "ctrl",
                "qpos",
                "qvel",
            ],
        },
        "ik": ik,
        "material_changes": material_changes,
        "ball_config": ball_config,
        "snapshots": snapshots,
    }


def summarize_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "episodes": int(len(rows)),
        "success_count": int(sum(1 for row in rows if row["success"])),
        "contact_gate_success_count": int(sum(1 for row in rows if row["contact_gate_success"])),
        "lift_success_count": int(sum(1 for row in rows if row["lift_success"])),
        "true_pinch_success_count": int(sum(1 for row in rows if row["true_pinch_success"])),
        "release_success_count": int(sum(1 for row in rows if row["release_success"])),
        "terminal_reason_counts": dict(Counter(str(row["terminal_reason"]) for row in rows)),
        "best_score": float(max([row["score"] for row in rows] + [float("-inf")])),
        "best_case": rows[0]["case"]["name"] if rows else None,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = payload["summary"]
    best = payload.get("best_result", {})
    lines = [
        "# Stage3.11D-B Event Contact-Gated Refinement v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- MuJoCo-only.\n",
        "- Local parameter/action-phase search, not neural-network training.\n",
        "- Provisional diagnostic work; no full-action ACT/DP or hardware promotion.\n\n",
        "## Summary\n\n",
        f"- Cases evaluated: `{s['episodes']}`\n",
        f"- Full event true-pinch-release success: `{s['success_count']} / {s['episodes']}`\n",
        f"- Contact-gate success: `{s['contact_gate_success_count']} / {s['episodes']}`\n",
        f"- Lift gate success: `{s['lift_success_count']} / {s['episodes']}`\n",
        f"- True-pinch morphology success: `{s['true_pinch_success_count']} / {s['episodes']}`\n",
        f"- Release success: `{s['release_success_count']} / {s['episodes']}`\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n\n",
    ]
    if best:
        hm = best.get("hold_morphology", {})
        gm = best.get("contact_gate_morphology", {})
        lines.extend(
            [
                "## Best Case\n\n",
                f"- Name: `{best['case']['name']}`\n",
                f"- Status: `{best['status']}` / `{best['terminal_reason']}`\n",
                f"- Score: `{best['score']:.4f}`\n",
                f"- Contact gate: `{best['contact_gate_success']}` at step `{best.get('contact_gate_step')}`\n",
                f"- Lift break: `{best.get('lift_break_reason')}`\n",
                f"- Hold break: `{best.get('hold_break_reason')}`\n",
                f"- Hold lift max: `{best.get('hold_lift_m_max', 0.0):.5f} m`\n",
                f"- Hold lift mean: `{best.get('hold_lift_m_mean', 0.0):.5f} m`\n",
                f"- Hold true two-tip fraction: `{hm.get('true_two_tip_pinch_fraction', 0.0):.3f}`\n",
                f"- Gate true two-tip fraction: `{gm.get('true_two_tip_pinch_fraction', 0.0):.3f}`\n",
                f"- Hold wrap fraction: `{hm.get('wrap_frame_fraction', 0.0):.3f}`\n",
                f"- Hold non-tip ratio: `{hm.get('non_tip_contact_ratio_mean', 0.0):.3f}`\n",
                f"- Release success: `{best.get('release_success')}`\n",
                f"- Visual contact sheet: `{payload.get('best_contact_sheet')}`\n\n",
            ]
        )
        motor = best.get("motor_force_feedback_summary", {})
        if motor.get("samples", 0):
            phase = motor.get("phase_summaries", {})
            slow_pair = phase.get("slow_lift", {})
            hold_pair = phase.get("hold", {})
            gate = best.get("force_feedback_gate", {})
            lines.extend(
                [
                    "## Best Motor Force Feedback Proxy\n\n",
                    f"- Samples: `{motor.get('samples')}`\n",
                    f"- Max |Iq|: `{motor.get('max_abs_iq_a', 0.0):.4f} A`\n",
                    f"- Mean |Iq|: `{motor.get('mean_abs_iq_a', 0.0):.4f} A`\n",
                    f"- Max output torque proxy: `{motor.get('max_abs_output_torque_nm', 0.0):.5f} Nm`\n",
                    f"- Max tendon tension proxy: `{motor.get('max_tendon_tension_n', 0.0):.4f} N`\n",
                    f"- Max hand-side |Iq| proxy: `{motor.get('max_hand_abs_iq_a', 0.0):.4f} A`\n",
                    f"- Max hand-side tendon tension proxy: `{motor.get('max_hand_tendon_tension_n', 0.0):.4f} N`\n",
                    f"- Active-pair total tension mean/max: `{motor.get('active_pair_total_tension_mean_n', 0.0):.4f}` / "
                    f"`{motor.get('active_pair_total_tension_max_n', 0.0):.4f} N`\n",
                    f"- Active-pair balance mean/min: `{motor.get('active_pair_balance_mean', 0.0):.3f}` / "
                    f"`{motor.get('active_pair_balance_min', 0.0):.3f}`\n",
                    f"- Slow-lift pair tension mean/min/max: `{slow_pair.get('pair_total_tension_mean_n', 0.0):.4f}` / "
                    f"`{slow_pair.get('pair_total_tension_min_n', 0.0):.4f}` / "
                    f"`{slow_pair.get('pair_total_tension_max_n', 0.0):.4f} N`\n",
                    f"- Hold pair tension mean/min/max: `{hold_pair.get('pair_total_tension_mean_n', 0.0):.4f}` / "
                    f"`{hold_pair.get('pair_total_tension_min_n', 0.0):.4f}` / "
                    f"`{hold_pair.get('pair_total_tension_max_n', 0.0):.4f} N`\n",
                    f"- Max bus current proxy: `{motor.get('max_bus_current_a', 0.0):.4f} A`\n",
                    f"- Current saturation sample fraction: `{motor.get('saturation_sample_fraction', 0.0):.3f}`\n\n",
                    "## Best Force-Feedback Gate\n\n",
                    f"- Enabled: `{gate.get('enabled', False)}`\n",
                    f"- Preload level: `{gate.get('preload_level', 0.0):.4f}`\n",
                    f"- Preload break reason: `{gate.get('preload_break_reason', 'n/a')}`\n",
                    f"- Lift low-force samples: `{gate.get('lift_low_force_samples', 0)}`\n",
                    f"- Lift wait steps: `{gate.get('lift_wait_steps', 0)}`\n\n",
                ]
            )
    lines.extend(
        [
            "## Top Cases\n\n",
            "| rank | case | status | score | gate | hold lift | two-tip | wrap | release | reason |\n",
            "|---:|---|---|---:|---|---:|---:|---:|---|---|\n",
        ]
    )
    for idx, row in enumerate(payload["results"][: min(20, len(payload["results"]))], start=1):
        hm = row.get("hold_morphology", {})
        lines.append(
            f"| {idx} | `{row['case']['name']}` | {row['status']} | {row['score']:.3f} | "
            f"`{row['contact_gate_success']}` | {row.get('hold_lift_m_max', 0.0):.4f} | "
            f"{hm.get('true_two_tip_pinch_fraction', 0.0):.3f} | "
            f"{hm.get('wrap_frame_fraction', 0.0):.3f} | "
            f"`{row.get('release_success')}` | `{row['terminal_reason']}` |\n"
        )
    lines.extend(
        [
            "\n## Next\n\n",
            "- If success count widens, run randomized pose/object checks and close-up visual review.\n",
            "- If the pass region remains narrow, branch into fingertip proxy geometry and material/contact modeling.\n",
            "- Do not promote to demo gallery until visual cleanliness and robustness both pass.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Event-driven Stage3.11D-B true-pinch refinement.")
    parser.add_argument("--scene", type=Path, default=DEFAULT_SCENE)
    parser.add_argument("--seed-candidate", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--selected", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--visual-dir", type=Path, default=DEFAULT_VISUAL_DIR)
    parser.add_argument("--max-cases", type=int, default=96)
    parser.add_argument("--render-best", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--render-extra-side-views", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--tip-mu", type=float, default=2.8)
    parser.add_argument("--non-tip-mu", type=float, default=0.10)
    parser.add_argument("--ball-mu", type=float, default=1.35)
    parser.add_argument("--ball-radius", type=float, default=0.018)
    parser.add_argument("--ball-mass", type=float, default=0.010)
    parser.add_argument("--inactive-scale", type=float, default=0.0)
    parser.add_argument("--base-tip-pair-separation-target", type=float, default=0.060)
    parser.add_argument("--base-grasp-offset-z", type=float, default=0.002)
    parser.add_argument("--base-hold-steps", type=int, default=100)
    parser.add_argument("--base-min-lift-height", type=float, default=0.050)
    parser.add_argument("--thumb-abd-values", default="-0.35,-0.30,-0.40,-0.25,-0.45")
    parser.add_argument("--thumb-mcp-values", default="0.28,0.24,0.32,0.20,0.36")
    parser.add_argument("--active-abd-values", default="-0.45,-0.40,-0.50,-0.35,-0.55")
    parser.add_argument("--active-pip-values", default="-0.70,-0.62,-0.78,-0.54,-0.86")
    parser.add_argument("--tip-pair-separation-values", default="0.060,0.056,0.064,0.052,0.068")
    parser.add_argument("--grasp-offset-x", type=float, default=0.0)
    parser.add_argument("--grasp-offset-y", type=float, default=0.0)
    parser.add_argument("--grasp-offset-x-values", default=None)
    parser.add_argument("--grasp-offset-y-values", default=None)
    parser.add_argument("--grasp-offset-z-values", default="0.002,0.001,0.003,0.000,0.004")
    parser.add_argument("--lift-j2-values", default="-0.95,-0.90,-1.00,-0.85,-1.05")
    parser.add_argument("--lift-steps-values", default="520,440,620")
    parser.add_argument("--hold-steps-values", default="120,100,160,80")
    parser.add_argument("--min-lift-height-values", default="0.050,0.040,0.060")
    parser.add_argument("--ik-maxiter", type=int, default=90)
    parser.add_argument("--approach-steps", type=int, default=220)
    parser.add_argument("--preshape-steps", type=int, default=80)
    parser.add_argument("--close-steps", type=int, default=180)
    parser.add_argument("--contact-gate-max-steps", type=int, default=220)
    parser.add_argument("--contact-gate-required-samples", type=int, default=2)
    parser.add_argument("--post-contact-settle-steps", type=int, default=40)
    parser.add_argument("--require-contact-gate", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--min-lift-steps-before-hold", type=int, default=180)
    parser.add_argument("--lifted-contact-required-samples", type=int, default=3)
    parser.add_argument("--min-hold-steps-before-release", type=int, default=60)
    parser.add_argument("--hold-release-required-samples", type=int, default=8)
    parser.add_argument("--demo-lift-goal", type=float, default=0.10)
    parser.add_argument("--release-steps", type=int, default=180)
    parser.add_argument("--release-settle-steps", type=int, default=420)
    parser.add_argument("--morphology-sample-every", type=int, default=5)
    parser.add_argument("--max-hold-floor-contact-fraction", type=float, default=0.05)
    parser.add_argument("--min-true-pinch-fraction", type=float, default=0.50)
    parser.add_argument("--max-wrap-fraction", type=float, default=0.30)
    parser.add_argument("--max-non-tip-ratio", type=float, default=0.45)
    parser.add_argument("--max-penetration-m", type=float, default=0.006)
    parser.add_argument("--final-height-tolerance", type=float, default=0.018)
    parser.add_argument("--enable-motor-force-feedback", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--motor-torque-constant-nm-per-a", type=float, default=0.035)
    parser.add_argument("--motor-gear-ratio", type=float, default=30.0)
    parser.add_argument("--motor-gear-efficiency", type=float, default=0.72)
    parser.add_argument("--motor-spool-radius-m", type=float, default=0.008)
    parser.add_argument("--motor-current-limit-a", type=float, default=4.0)
    parser.add_argument("--motor-bus-voltage-v", type=float, default=24.0)
    parser.add_argument("--motor-current-noise-a", type=float, default=0.025)
    parser.add_argument("--motor-feedback-seed", type=int, default=20260611)
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
    parser.add_argument("--enable-residual-micro-adjust", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--residual-micro-adjust-check-after-lift-steps", type=int, default=80)
    parser.add_argument("--residual-micro-adjust-required-samples", type=int, default=1)
    parser.add_argument("--residual-micro-adjust-max-wait-steps", type=int, default=160)
    parser.add_argument("--residual-micro-adjust-close-delta", type=float, default=0.006)
    parser.add_argument("--residual-micro-adjust-max-close-delta", type=float, default=0.030)
    parser.add_argument("--residual-micro-adjust-grasp-x-delta", type=float, default=0.0)
    parser.add_argument("--residual-micro-adjust-max-grasp-x-delta", type=float, default=0.0)
    parser.add_argument("--residual-micro-adjust-enable-prelift", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--residual-micro-adjust-prelift-steps", type=int, default=40)
    parser.add_argument("--residual-micro-adjust-prelift-grasp-x-delta", type=float, default=0.0)
    parser.add_argument("--residual-micro-adjust-prelift-max-grasp-x-delta", type=float, default=0.0)
    parser.add_argument("--residual-micro-adjust-progress-drop-steps", type=int, default=0)
    parser.add_argument("--residual-micro-adjust-allow-wrap", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--capture-dense-sensor-trace", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--dense-trace-sample-every", type=int, default=1)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    import mujoco

    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)
    cases = local_cases(args)
    results: list[dict[str, Any]] = []
    for idx, case in enumerate(cases):
        model = mujoco.MjModel.from_xml_path(str(scene))
        row = run_event_candidate(model, mujoco, case, args)
        results.append(row)
        hm = row.get("hold_morphology", {})
        print(
            f"{idx + 1:03d}/{len(cases):03d} {row['status']} score={row['score']:.3f} "
            f"gate={row['contact_gate_success']} hold_lift={row.get('hold_lift_m_max', 0.0):.4f} "
            f"two_tip={hm.get('true_two_tip_pinch_fraction', 0.0):.3f} "
            f"wrap={hm.get('wrap_frame_fraction', 0.0):.3f} release={row['release_success']} "
            f"{row['case']['name']}"
        )
    results.sort(key=lambda row: float(row["score"]), reverse=True)
    best = results[0] if results else None
    best_contact_sheet = None
    if best is not None and bool(args.render_best):
        best_case_raw = best["case"]
        best_case = RefineCase(
            name=best_case_raw["name"],
            candidate=broad.BallPinchCandidate(**best_case_raw["candidate"]),
            tip_pair_separation_target=float(best_case_raw["tip_pair_separation_target"]),
            grasp_offset_x=float(best_case_raw["grasp_offset_x"]),
            grasp_offset_y=float(best_case_raw["grasp_offset_y"]),
            grasp_offset_z=float(best_case_raw["grasp_offset_z"]),
            ball_radius=float(best_case_raw["ball_radius"]),
            ball_mass=float(best_case_raw["ball_mass"]),
            ball_offset_x=float(best_case_raw.get("ball_offset_x", 0.0)),
            ball_offset_y=float(best_case_raw.get("ball_offset_y", 0.0)),
            ball_offset_z=float(best_case_raw.get("ball_offset_z", 0.0)),
            hold_steps=int(best_case_raw["hold_steps"]),
            min_lift_height=float(best_case_raw["min_lift_height"]),
        )
        model = mujoco.MjModel.from_xml_path(str(scene))
        render_dir = Path(args.visual_dir) / safe_case_dir_name(best_case.name)
        rendered = run_event_candidate(model, mujoco, best_case, args, render_dir=render_dir)
        best.update({"snapshots": rendered.get("snapshots", {})})
        best_contact_sheet = broad.write_contact_sheet(
            best.get("snapshots", {}),
            Path(args.visual_dir) / f"{best_case.name}_contact_sheet.png",
        )
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.11D-B",
        "scene": str(scene),
        "args": vars(args),
        "summary": summarize_results(results),
        "best_result": best,
        "best_contact_sheet": best_contact_sheet,
        "results": results,
        "boundary": {
            "mujoco_only": True,
            "event_driven_parameter_search_not_neural_training": True,
            "controller_promoted": False,
            "hardware_runtime": False,
            "full_action_act_dp_promoted": False,
        },
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(Path(args.report), json_ready(payload))
    if best is not None:
        args.selected.parent.mkdir(parents=True, exist_ok=True)
        args.selected.write_text(json.dumps(json_ready({"selected_case": best["case"], "result": best}), indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    print(f"Saved selected: {args.selected}")
    if best_contact_sheet:
        print(f"Saved best visual contact sheet: {best_contact_sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
