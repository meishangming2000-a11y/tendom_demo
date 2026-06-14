"""Stage3.11D-A pinch morphology and friction audit.

This MuJoCo-only diagnostic checks whether the current Stage3.8B pinch demo is
really a fingertip pinch or a stable multi-finger enclosure. It deliberately
does not promote a new controller. The output is a report/metadata pair that
can guide Stage3.11D residual-policy work and future material/friction design.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import zlib
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, OBJECT_GEOM_NAME, Stage3Thresholds


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import eval_stage3_pinch_grasp_v0 as pinch
from mujoco_tactile_slip_sensor import MujocoTactileSlipSensor


DEFAULT_SELECTED = META / "stage3_pinch_grasp_training_v0_selected.json"
DEFAULT_REPORT = DOCS / "stage3_11d_a_pinch_morphology_friction_audit_v0_closeout.md"
DEFAULT_METADATA = META / "stage3_11d_a_pinch_morphology_friction_audit_v0.json"

HAND_KEYWORDS = ("palm", "finger", "thumb", "distal", "proximal", "wrist", "mcp", "hand_base")
ARM_KEYWORDS = ("base_link", "link_1", "link_2", "link_3", "ee_mount")
FINGER_REGIONS = ("thumb", "index", "middle", "ring", "little")


def region_from_names(names: list[str]) -> str:
    joined = " ".join(str(name).lower() for name in names)
    for region in FINGER_REGIONS:
        if region in joined:
            return region
    if "palm" in joined or "hand_base" in joined or "wrist" in joined:
        return "palm"
    if "floor" in joined:
        return "support"
    if any(key in joined for key in ARM_KEYWORDS):
        return "arm"
    return "unknown"


def name_for(model, mujoco, obj_type, idx: int, fallback: str) -> str:
    return mujoco.mj_id2name(model, obj_type, int(idx)) or fallback


def load_candidate(path: Path) -> pinch.PinchCandidate:
    if not path.exists():
        raise FileNotFoundError(path)
    return pinch.candidate_from_config(path)


def set_contact_friction(
    model,
    mujoco,
    *,
    egg_sliding_mu: float,
    egg_torsional_mu: float,
    egg_rolling_mu: float,
    hand_sliding_mu: float | None,
) -> dict[str, Any]:
    egg_geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, OBJECT_GEOM_NAME)
    if egg_geom_id < 0:
        raise ValueError(f"Missing object geom {OBJECT_GEOM_NAME!r}")

    original_egg = model.geom_friction[egg_geom_id].copy()
    model.geom_friction[egg_geom_id, :] = np.asarray(
        [float(egg_sliding_mu), float(egg_torsional_mu), float(egg_rolling_mu)],
        dtype=np.float64,
    )

    changed_hand = 0
    if hand_sliding_mu is not None:
        for geom_id in range(model.ngeom):
            name = name_for(model, mujoco, mujoco.mjtObj.mjOBJ_GEOM, geom_id, f"geom_{geom_id}").lower()
            body_id = int(model.geom_bodyid[geom_id])
            body = name_for(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, body_id, f"body_{body_id}").lower()
            joined = f"{name} {body}"
            if any(key in joined for key in HAND_KEYWORDS):
                model.geom_friction[geom_id, 0] = float(hand_sliding_mu)
                changed_hand += 1

    return {
        "egg_geom_id": int(egg_geom_id),
        "original_egg_friction": original_egg,
        "egg_friction": model.geom_friction[egg_geom_id].copy(),
        "hand_sliding_mu": hand_sliding_mu,
        "changed_hand_geoms": int(changed_hand),
    }


def egg_contact_rows(model, data, mujoco, egg_body_id: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx in range(data.ncon):
        c = data.contact[idx]
        geoms = [int(c.geom1), int(c.geom2)]
        names: list[str] = []
        body_ids: list[int] = []
        for geom_id in geoms:
            body_id = int(model.geom_bodyid[geom_id])
            body_ids.append(body_id)
            names.append(name_for(model, mujoco, mujoco.mjtObj.mjOBJ_GEOM, geom_id, f"geom_{geom_id}"))
            names.append(name_for(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, body_id, f"body_{body_id}"))
        joined = " ".join(names).lower()
        has_egg = "egg" in joined or egg_body_id in body_ids
        if not has_egg:
            continue
        hand = any(key in joined for key in HAND_KEYWORDS)
        row = {
            "names": names,
            "region": region_from_names(names),
            "hand": bool(hand),
            "floor": "floor" in joined,
            "arm": any(key in joined for key in ARM_KEYWORDS),
            "tip": "_tip_collision_proxy_sphere" in joined,
            "penetration": max(0.0, -float(c.dist)),
            "dist": float(c.dist),
            "pos": np.asarray(c.pos).copy(),
        }
        rows.append(row)
    return rows


def frame_morphology(rows: list[dict[str, Any]], candidate: pinch.PinchCandidate) -> dict[str, Any]:
    hand_rows = [row for row in rows if bool(row["hand"])]
    desired = {"thumb", *candidate.active_fingers}
    hand_count = len(hand_rows)
    if hand_count == 0:
        return {
            "hand_contact_count": 0,
            "unique_hand_regions": [],
            "tip_contact_ratio": 0.0,
            "non_tip_contact_ratio": 0.0,
            "support_contact_ratio": 0.0,
            "two_finger_tip_pinch": False,
            "three_digit_clamp": False,
            "multi_segment_or_support_wrap": False,
            "wrap_score": 0.0,
        }

    regions = sorted({str(row["region"]) for row in hand_rows if str(row["region"]) not in {"arm", "support"}})
    desired_rows = [row for row in hand_rows if str(row["region"]) in desired]
    support_rows = [row for row in hand_rows if str(row["region"]) not in desired]
    tip_rows = [row for row in hand_rows if bool(row["tip"])]
    desired_tip_regions = sorted({str(row["region"]) for row in desired_rows if bool(row["tip"])})
    active_regions = sorted({str(row["region"]) for row in hand_rows if str(row["region"]) in set(candidate.active_fingers)})
    active_tip_regions = sorted({str(row["region"]) for row in desired_rows if str(row["region"]) in set(candidate.active_fingers) and bool(row["tip"])})
    tip_ratio = float(len(tip_rows) / max(1, hand_count))
    support_ratio = float(len(support_rows) / max(1, hand_count))
    non_tip_ratio = float(1.0 - tip_ratio)
    three_digit = "thumb" in regions and len(active_regions) >= 2
    two_finger_tip = (
        "thumb" in desired_tip_regions
        and len(active_tip_regions) == 1
        and not support_rows
        and tip_ratio >= 0.50
        and not three_digit
    )
    wrap = bool(support_rows) or non_tip_ratio >= 0.50 or three_digit
    wrap_score = min(
        1.0,
        0.45 * non_tip_ratio
        + 0.30 * support_ratio
        + 0.20 * max(0.0, (float(len(regions)) - 2.0) / 3.0)
        + (0.15 if three_digit else 0.0),
    )
    return {
        "hand_contact_count": int(hand_count),
        "unique_hand_regions": regions,
        "tip_contact_ratio": tip_ratio,
        "non_tip_contact_ratio": non_tip_ratio,
        "support_contact_ratio": support_ratio,
        "desired_contact_ratio": float(len(desired_rows) / max(1, hand_count)),
        "desired_tip_regions": desired_tip_regions,
        "active_regions": active_regions,
        "two_finger_tip_pinch": bool(two_finger_tip),
        "three_digit_clamp": bool(three_digit),
        "multi_segment_or_support_wrap": bool(wrap),
        "wrap_score": float(wrap_score),
    }


def summarize_morphology(frames: list[dict[str, Any]]) -> dict[str, Any]:
    if not frames:
        return {
            "hold_frames": 0,
            "two_finger_tip_pinch_fraction": 0.0,
            "three_digit_clamp_fraction": 0.0,
            "wrap_frame_fraction": 0.0,
            "tip_contact_ratio_mean": 0.0,
            "non_tip_contact_ratio_mean": 0.0,
            "support_contact_ratio_mean": 0.0,
            "wrap_score_mean": 0.0,
            "mean_hand_contacts": 0.0,
            "mean_unique_hand_regions": 0.0,
            "region_counts": {},
        }

    def mean(key: str) -> float:
        return float(np.mean([float(frame[key]) for frame in frames]))

    regions = Counter(region for frame in frames for region in frame.get("unique_hand_regions", []))
    return {
        "hold_frames": int(len(frames)),
        "two_finger_tip_pinch_fraction": float(np.mean([bool(frame["two_finger_tip_pinch"]) for frame in frames])),
        "three_digit_clamp_fraction": float(np.mean([bool(frame["three_digit_clamp"]) for frame in frames])),
        "wrap_frame_fraction": float(np.mean([bool(frame["multi_segment_or_support_wrap"]) for frame in frames])),
        "tip_contact_ratio_mean": mean("tip_contact_ratio"),
        "non_tip_contact_ratio_mean": mean("non_tip_contact_ratio"),
        "support_contact_ratio_mean": mean("support_contact_ratio"),
        "wrap_score_mean": mean("wrap_score"),
        "mean_hand_contacts": mean("hand_contact_count"),
        "mean_unique_hand_regions": float(np.mean([len(frame.get("unique_hand_regions", [])) for frame in frames])),
        "region_counts": dict(regions),
    }


def run_audit_episode(
    model,
    mujoco,
    *,
    candidate: pinch.PinchCandidate,
    trial,
    episode_id: int,
    args,
    friction_label: str,
) -> dict[str, Any]:
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    base_egg_position = data.xpos[pinch.sweep.egg_body_id(model, mujoco)].copy()
    egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
    stable_candidate_hash = int(zlib.adler32(candidate.name.encode("utf-8")) % 997)
    rng = np.random.default_rng(int(args.seed) + int(episode_id) * 1009 + stable_candidate_hash)
    if float(args.random_offset_std) > 0.0:
        egg_position = egg_position + rng.normal(0.0, float(args.random_offset_std), size=3)
        egg_position[2] = base_egg_position[2] + np.asarray(trial.offset_xyz, dtype=np.float64)[2]
    pinch.sweep.reset_episode(model, data, mujoco, egg_position)

    initial_vision = pinch.acquire_vision(
        model,
        data,
        mujoco,
        camera_name=str(args.camera),
        width=int(args.width),
        height=int(args.height),
        min_confidence=float(args.min_vision_confidence),
        debug_dir=None,
        label="initial",
    )
    if not bool(initial_vision.get("accepted")):
        return {
            "episode_id": int(episode_id),
            "friction_label": friction_label,
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
            },
            "morphology": summarize_morphology([]),
        }

    plan = pinch.build_pinch_plan(
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
    initial_true_egg = data.xpos[pinch.sweep.egg_body_id(model, mujoco)].copy()
    initial_vision_pos = np.asarray(initial_vision["position_world_est"], dtype=np.float64)
    egg_id = pinch.sweep.egg_body_id(model, mujoco)

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
    hold_morphology_frames: list[dict[str, Any]] = []
    contact_settle_morphology_frames: list[dict[str, Any]] = []
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
            targets = pinch.sweep.blend_targets(start, end, progress)
            action = pinch.collect.clip_action(
                model,
                pinch.sweep.actuator_targets(model, mujoco, plan["actuator_names"], targets),
            )
            data.ctrl[:] = action
            mujoco.mj_step(model, data)
            tactile = tactile_sensor.sample(data)
            pinch.record_phase_metric(phase_metrics, phase_name, tactile)
            region_counts_total.update({str(k): int(v) for k, v in tactile.get("egg_contact_region_counts", {}).items()})
            egg_now = data.xpos[egg_id].copy()
            lift_height = float(egg_now[2] - initial_true_egg[2])

            if phase_name == "approach":
                proxy_now = pinch.sweep.proxy_position(model, data, mujoco, plan["grasp_local"])
                approach_true_proxy_error = float(np.linalg.norm(proxy_now - initial_true_egg))

            if tactile["contact_present"]:
                contact_acquired = True
                if first_contact_phase == "none":
                    first_contact_phase = phase_name
            if phase_name in {"pinch_close", "contact_settle"} and pinch.pinch_contact_ok(tactile, candidate):
                pinch_contact_before_lift = True

            if phase_name == "contact_settle":
                contact_settle_steps_actual += 1
                contact_settle_morphology_frames.append(frame_morphology(egg_contact_rows(model, data, mujoco, egg_id), candidate))
                gate_reasons = pinch.gate_condition_reasons(tactile, args, thresholds)
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
                if pinch.pinch_contact_ok(tactile, candidate):
                    hold_pinch_steps += 1
                hold_purity_sum += pinch.pinch_purity_score(tactile, candidate)
                hold_morphology_frames.append(frame_morphology(egg_contact_rows(model, data, mujoco, egg_id), candidate))

            max_slip = max(max_slip, float(tactile["slip_score"]))
            max_crush = max(max_crush, float(tactile["crush_risk"]))
            max_penetration = max(max_penetration, float(tactile.get("max_penetration", 0.0)))

            if step_count % max(1, int(args.sample_every)) == 0:
                morph = frame_morphology(egg_contact_rows(model, data, mujoco, egg_id), candidate)
                trace.append(
                    {
                        "step": int(step_count),
                        "phase": phase_name,
                        "progress": float(progress),
                        "true_lift_height_m": float(lift_height),
                        "regions": list(tactile.get("contact_regions", [])),
                        "pinch_contact": bool(pinch.pinch_contact_ok(tactile, candidate)),
                        "slip": float(tactile["slip_score"]),
                        "stable": bool(tactile["grip_stable"]),
                        "wrap_score": float(morph["wrap_score"]),
                        "three_digit_clamp": bool(morph["three_digit_clamp"]),
                        "two_finger_tip_pinch": bool(morph["two_finger_tip_pinch"]),
                    }
                )

            local_step += 1
            step_count += 1
            if phase_name == "contact_settle" and gate_release_reason != "not_reached":
                break

    final_tactile = tactile_sensor.sample(data)
    final_true_egg = data.xpos[egg_id].copy()
    final_contact = pinch.sweep.contact_summary(model, data, mujoco)
    final_cameras = [camera.strip() for camera in str(args.final_cameras).split(",") if camera.strip()]
    final_vision, final_vision_all = pinch.best_final_vision(
        model,
        data,
        mujoco,
        cameras=final_cameras,
        width=int(args.width),
        height=int(args.height),
        min_confidence=float(args.min_final_vision_confidence),
        debug_dir=None,
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
    reasons = pinch.classify_failure_reasons(summary, args, thresholds)
    success = len(reasons) == 0
    risks: list[str] = []
    if first_contact_phase == "approach":
        risks.append("early_contact_in_approach")
    if max_slip > thresholds.success_max_slip_score:
        risks.append("transient_slip_high")
    morphology = summarize_morphology(hold_morphology_frames)
    contact_settle_morphology = summarize_morphology(contact_settle_morphology_frames)
    if morphology["wrap_frame_fraction"] >= float(args.wrap_flag_fraction):
        risks.append("pinch_morphology_wrap_or_enclosure")
    if morphology["two_finger_tip_pinch_fraction"] < float(args.min_two_finger_tip_pinch_fraction):
        risks.append("low_true_two_finger_tip_pinch")
    if morphology["three_digit_clamp_fraction"] >= float(args.three_digit_flag_fraction):
        risks.append("three_digit_clamp_dominates")
    if float(morphology["non_tip_contact_ratio_mean"]) >= float(args.non_tip_flag_ratio):
        risks.append("non_tip_contact_dominates")

    terminal_reason = "success_vision_confirmed_pinch_lift_hold" if success else (reasons[0] if reasons else "unknown")
    return {
        "episode_id": int(episode_id),
        "friction_label": friction_label,
        "candidate": candidate.name,
        "candidate_config": candidate.__dict__,
        "trial": trial.name,
        "status": "PASS" if success else "FAIL",
        "success": bool(success),
        "terminal_reason": terminal_reason,
        "failure_reasons": reasons,
        "risk_flags": risks,
        "summary": summary,
        "morphology": morphology,
        "contact_settle_morphology": contact_settle_morphology,
        "trace": trace,
        "final_vision": final_vision,
        "final_vision_all": final_vision_all,
    }


def summarize_numeric(rows: list[dict[str, Any]], path: tuple[str, ...]) -> dict[str, float]:
    values = []
    for row in rows:
        cursor: Any = row
        for key in path:
            cursor = cursor.get(key, {}) if isinstance(cursor, dict) else {}
        try:
            value = float(cursor)
        except (TypeError, ValueError):
            continue
        if np.isfinite(value):
            values.append(value)
    if not values:
        return {}
    arr = np.asarray(values, dtype=np.float64)
    return {"mean": float(np.mean(arr)), "min": float(np.min(arr)), "max": float(np.max(arr))}


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_friction: dict[str, Any] = {}
    for friction_label in sorted({str(row["friction_label"]) for row in rows}):
        subset = [row for row in rows if row["friction_label"] == friction_label]
        by_friction[friction_label] = {
            "episodes": int(len(subset)),
            "success_count": int(sum(1 for row in subset if row["success"])),
            "terminal_reason_counts": dict(Counter(str(row["terminal_reason"]) for row in subset)),
            "failure_reason_counts": dict(Counter(reason for row in subset for reason in row.get("failure_reasons", []))),
            "risk_flag_counts": dict(Counter(flag for row in subset for flag in row.get("risk_flags", []))),
            "true_lift_height_m": summarize_numeric(subset, ("summary", "true_lift_height_m")),
            "hold_max_slip_score": summarize_numeric(subset, ("summary", "hold_max_slip_score")),
            "two_finger_tip_pinch_fraction": summarize_numeric(subset, ("morphology", "two_finger_tip_pinch_fraction")),
            "three_digit_clamp_fraction": summarize_numeric(subset, ("morphology", "three_digit_clamp_fraction")),
            "wrap_frame_fraction": summarize_numeric(subset, ("morphology", "wrap_frame_fraction")),
            "tip_contact_ratio": summarize_numeric(subset, ("morphology", "tip_contact_ratio_mean")),
            "non_tip_contact_ratio": summarize_numeric(subset, ("morphology", "non_tip_contact_ratio_mean")),
            "wrap_score": summarize_numeric(subset, ("morphology", "wrap_score_mean")),
            "mean_hand_contacts": summarize_numeric(subset, ("morphology", "mean_hand_contacts")),
        }
    return {
        "status": "PASS" if all(row["success"] for row in rows) else ("PARTIAL" if any(row["success"] for row in rows) else "FAIL"),
        "episodes": int(len(rows)),
        "success_count": int(sum(1 for row in rows if row["success"])),
        "terminal_reason_counts": dict(Counter(str(row["terminal_reason"]) for row in rows)),
        "failure_reason_counts": dict(Counter(reason for row in rows for reason in row.get("failure_reasons", []))),
        "risk_flag_counts": dict(Counter(flag for row in rows for flag in row.get("risk_flags", []))),
        "by_friction": by_friction,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = payload["summary"]
    lines = [
        "# Stage3.11D-A Pinch Morphology Friction Audit v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "Status: **diagnostic PASS** if the script ran and produced morphology labels. This does not promote a new controller.\n\n",
        "## Purpose\n\n",
        "The current Stage3.8B pinch demo can look like a three-finger clamp or enclosure. This audit measures that morphology under an egg-friction sweep before Stage3.11D trains any safety-conditioned hand/residual policy.\n\n",
        "## Boundary\n\n",
        "- MuJoCo-only.\n",
        "- No real camera, tactile hardware, ultrasound, or hardware runtime.\n",
        "- No full-action ACT/DP promotion.\n",
        "- The current controller is not changed.\n\n",
        "## Summary\n\n",
        f"- Episodes: `{s['episodes']}`\n",
        f"- Success: `{s['success_count']} / {s['episodes']}`\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n",
        f"- Risk flags: `{s['risk_flag_counts']}`\n\n",
        "## Friction Sweep\n\n",
        "| friction case | success | lift mean | hold slip max | two-finger tip pinch | three-digit clamp | wrap frames | tip contact | non-tip contact | wrap score |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for label, row in s["by_friction"].items():
        lines.append(
            f"| {label} | {row['success_count']}/{row['episodes']} | "
            f"{row.get('true_lift_height_m', {}).get('mean', float('nan')):.5f} | "
            f"{row.get('hold_max_slip_score', {}).get('max', float('nan')):.3f} | "
            f"{row.get('two_finger_tip_pinch_fraction', {}).get('mean', float('nan')):.3f} | "
            f"{row.get('three_digit_clamp_fraction', {}).get('mean', float('nan')):.3f} | "
            f"{row.get('wrap_frame_fraction', {}).get('mean', float('nan')):.3f} | "
            f"{row.get('tip_contact_ratio', {}).get('mean', float('nan')):.3f} | "
            f"{row.get('non_tip_contact_ratio', {}).get('mean', float('nan')):.3f} | "
            f"{row.get('wrap_score', {}).get('mean', float('nan')):.3f} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- If three-digit clamp and wrap frames remain high across friction cases, morphology is mainly a controller/objective issue, not only an egg-surface friction issue.\n",
            "- If success or slip changes sharply with egg friction, the material model should become a first-class Stage3.11D/Stage4 design variable.\n",
            "- A future true-pinch gate should require a higher two-finger fingertip-pinch fraction and penalize non-tip/palm/support contacts instead of only checking lift and low hold slip.\n\n",
            "## Episode Details\n\n",
            "| ep | friction | status | lift | hold slip | two-finger tip | three-digit clamp | wrap frames | regions | risks |\n",
            "|---:|---|---|---:|---:|---:|---:|---:|---|---|\n",
        ]
    )
    for row in payload["results"]:
        r = row.get("summary", {})
        m = row.get("morphology", {})
        lines.append(
            f"| {row['episode_id']} | {row['friction_label']} | {row['status']} | "
            f"{r.get('true_lift_height_m', float('nan')):.5f} | "
            f"{r.get('hold_max_slip_score', float('nan')):.3f} | "
            f"{m.get('two_finger_tip_pinch_fraction', float('nan')):.3f} | "
            f"{m.get('three_digit_clamp_fraction', float('nan')):.3f} | "
            f"{m.get('wrap_frame_fraction', float('nan')):.3f} | "
            f"`{m.get('region_counts', {})}` | "
            f"`{row.get('risk_flags', [])}` |\n"
        )
    lines.extend(
        [
            "\n## Next\n\n",
            "Stage3.11D should add morphology-conditioned residual/policy work only after this diagnostic is reviewed. If dense obs/action labels are needed for morphology conditioning, do Stage3.11C2-style dense capture rather than pretending trace-frame labels are dense policy data.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def parse_friction_grid(spec: str) -> list[float]:
    values = []
    for token in str(spec).split(","):
        token = token.strip()
        if not token:
            continue
        values.append(float(token))
    if not values:
        raise ValueError("Empty friction grid")
    return values


def material_modes(spec: str) -> list[str]:
    mode = str(spec).strip().lower()
    if mode == "both":
        return ["egg_only", "matched_hand"]
    if mode in {"egg_only", "matched_hand"}:
        return [mode]
    raise ValueError("material mode must be egg_only, matched_hand, or both")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Stage3.11D-A pinch morphology and friction audit.")
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--candidate-config", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--trial", default="center_nominal")
    parser.add_argument("--episodes-per-friction", type=int, default=1)
    parser.add_argument("--friction-grid", default="0.45,0.75,1.15,1.60")
    parser.add_argument("--material-mode", choices=["egg_only", "matched_hand", "both"], default="both")
    parser.add_argument("--egg-torsional-mu", type=float, default=0.08)
    parser.add_argument("--egg-rolling-mu", type=float, default=0.003)
    parser.add_argument("--hand-sliding-mu", type=float, default=None)
    parser.add_argument("--seed", type=int, default=381)
    parser.add_argument("--random-offset-std", type=float, default=0.0)
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--final-cameras", default="stage3_egg_closeup,stage3_egg_overview")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--min-vision-confidence", type=float, default=0.55)
    parser.add_argument("--min-final-vision-confidence", type=float, default=0.35)
    parser.add_argument("--min-vision-lift-height", type=float, default=0.045)
    parser.add_argument("--min-hold-stable-fraction", type=float, default=0.60)
    parser.add_argument("--min-hold-pinch-fraction", type=float, default=0.55)
    parser.add_argument("--min-hold-pinch-purity", type=float, default=0.55)
    parser.add_argument("--approach-steps", type=int, default=300)
    parser.add_argument("--hand-steps", type=int, default=120)
    parser.add_argument("--pinch-close-steps", type=int, default=220)
    parser.add_argument("--min-contact-settle-steps", type=int, default=120)
    parser.add_argument("--max-contact-settle-steps", type=int, default=360)
    parser.add_argument("--settle-stable-window-steps", type=int, default=70)
    parser.add_argument("--gate-slip-threshold", type=float, default=0.22)
    parser.add_argument("--gate-crush-threshold", type=float, default=0.35)
    parser.add_argument("--gate-penetration-threshold", type=float, default=0.004)
    parser.add_argument("--lift-steps", type=int, default=520)
    parser.add_argument("--hold-steps", type=int, default=900)
    parser.add_argument("--sample-every", type=int, default=240)
    parser.add_argument("--wrap-flag-fraction", type=float, default=0.50)
    parser.add_argument("--three-digit-flag-fraction", type=float, default=0.50)
    parser.add_argument("--min-two-finger-tip-pinch-fraction", type=float, default=0.50)
    parser.add_argument("--non-tip-flag-ratio", type=float, default=0.45)
    parser.add_argument("--render-vision-debug", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    import mujoco

    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)
    candidate = load_candidate(Path(args.candidate_config))
    trial = pinch.selected_trial(str(args.trial))
    friction_grid = parse_friction_grid(str(args.friction_grid))
    modes = material_modes(str(args.material_mode))

    results: list[dict[str, Any]] = []
    friction_settings: list[dict[str, Any]] = []
    episode_id = 0
    for mode in modes:
        for egg_mu in friction_grid:
            friction_label = f"{mode}_egg_mu_{egg_mu:.2f}"
            hand_mu = float(egg_mu) if mode == "matched_hand" else args.hand_sliding_mu
            for _ in range(int(args.episodes_per_friction)):
                model = mujoco.MjModel.from_xml_path(str(scene))
                friction_info = set_contact_friction(
                    model,
                    mujoco,
                    egg_sliding_mu=float(egg_mu),
                    egg_torsional_mu=float(args.egg_torsional_mu),
                    egg_rolling_mu=float(args.egg_rolling_mu),
                    hand_sliding_mu=hand_mu,
                )
                if not any(item.get("label") == friction_label for item in friction_settings):
                    friction_settings.append({"label": friction_label, "material_mode": mode, **friction_info})
                row = run_audit_episode(
                    model,
                    mujoco,
                    candidate=candidate,
                    trial=trial,
                    episode_id=episode_id,
                    args=args,
                    friction_label=friction_label,
                )
                results.append(row)
                m = row.get("morphology", {})
                r = row.get("summary", {})
                print(
                    f"ep={episode_id:03d} friction={friction_label} {row['status']} "
                    f"lift={r.get('true_lift_height_m', float('nan')):.4f} "
                    f"slip={r.get('hold_max_slip_score', float('nan')):.3f} "
                    f"two_tip={m.get('two_finger_tip_pinch_fraction', float('nan')):.3f} "
                    f"three_digit={m.get('three_digit_clamp_fraction', float('nan')):.3f} "
                    f"wrap={m.get('wrap_frame_fraction', float('nan')):.3f}"
                )
                episode_id += 1

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.11D-A",
        "status": "DIAGNOSTIC_PASS",
        "scene": str(scene),
        "candidate": candidate.__dict__,
        "trial": trial.name,
        "friction_settings": friction_settings,
        "morphology_definitions": {
            "two_finger_tip_pinch_fraction": "Hold-frame fraction with thumb tip plus exactly one active fingertip, no support contacts, and tip contacts dominating.",
            "three_digit_clamp_fraction": "Hold-frame fraction with thumb plus at least two active finger regions contacting the egg.",
            "wrap_frame_fraction": "Hold-frame fraction where support/non-tip/multi-digit enclosure evidence is present.",
            "non_tip_contact_ratio": "Mean share of hand contacts that are not fingertip proxy contacts.",
        },
        "args": vars(args),
        "summary": summarize_rows(results),
        "results": results,
        "boundary": {
            "mujoco_only": True,
            "controller_changed": False,
            "full_action_act_dp_promoted": False,
            "hardware_runtime": False,
            "real_camera": False,
            "real_tactile": False,
            "ultrasound_runtime": False,
        },
        "next": "Review morphology. If wrap dominates across friction, Stage3.11D should add a true-pinch morphology gate/objective before training residual policy.",
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
