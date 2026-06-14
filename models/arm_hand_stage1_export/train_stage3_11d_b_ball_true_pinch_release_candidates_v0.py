#!/usr/bin/env python3
"""Stage3.11D-B small-ball true-pinch-and-release candidate search.

This is MuJoCo-only parameter search, not neural-network training.  It is the
first bridge from "the hand can lift a ball" toward "the hand visibly pinches a
small ball with fingertips, then lets it go".
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np
from scipy.optimize import minimize

import demo_arm_hand_lift_ball_scripted as ball_demo
from arm_hand_stage1_task_api import json_ready
from demo_arm_hand_lift_ball_from_default import actuated_joint_targets_from_qpos


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DEFAULT_SCENE = ROOT / "mjcf" / "scene_arm_hand_export4_lift_ball_demo.xml"
DEFAULT_REPORT = DOCS / "stage3_11d_b_ball_true_pinch_release_candidates_v0_report.md"
DEFAULT_METADATA = META / "stage3_11d_b_ball_true_pinch_release_candidates_v0.json"
DEFAULT_SELECTED = META / "stage3_11d_b_ball_true_pinch_release_selected_v0.json"
DEFAULT_VISUAL_DIR = DOCS / "visual_checks_stage3_11d_b_ball_true_pinch_release_v0"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


HAND_KEYWORDS = ("palm", "finger", "thumb", "distal", "proximal", "wrist", "mcp", "hand_base")
FINGER_REGIONS = ("thumb", "index", "middle", "ring", "little")
ARM_JOINTS = ball_demo.ARM_JOINTS


@dataclass(frozen=True)
class BallPinchCandidate:
    name: str
    active_finger: str
    thumb_cmc_abd: float
    thumb_cmc: float
    thumb_mcp: float
    thumb_ip: float
    active_mcp_flex: float
    active_mcp_abd: float
    active_pip: float
    active_dip: float
    inactive_scale: float = 0.0
    tip_sliding_mu: float = 2.6
    non_tip_sliding_mu: float = 0.12
    ball_sliding_mu: float = 1.35
    lift_j2: float = -0.95
    lift_steps: int = 420


def name_for(model, mujoco, obj_type, idx: int, fallback: str) -> str:
    return mujoco.mj_id2name(model, obj_type, int(idx)) or fallback


def joint_qadr(model, mujoco, joint_name: str) -> int | None:
    jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if jid < 0:
        return None
    return int(model.jnt_qposadr[jid])


def set_joint_qpos(model, data, mujoco, joint_name: str, value: float) -> None:
    qadr = joint_qadr(model, mujoco, joint_name)
    if qadr is not None:
        data.qpos[qadr] = float(value)


def ball_ids(model, mujoco) -> tuple[int, int, int]:
    return ball_demo.ball_indices(model, mujoco)


def ball_position(model, data, mujoco) -> np.ndarray:
    body_id, _, _ = ball_ids(model, mujoco)
    return data.xpos[body_id].copy()


def set_contact_materials(model, mujoco, candidate: BallPinchCandidate) -> dict[str, Any]:
    changed = Counter()
    for geom_id in range(model.ngeom):
        geom = name_for(model, mujoco, mujoco.mjtObj.mjOBJ_GEOM, geom_id, f"geom_{geom_id}").lower()
        body_id = int(model.geom_bodyid[geom_id])
        body = name_for(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, body_id, f"body_{body_id}").lower()
        joined = f"{geom} {body}"
        if "ball_geom" in joined:
            model.geom_friction[geom_id, 0] = float(candidate.ball_sliding_mu)
            changed["ball"] += 1
        elif "tip_collision_proxy_sphere" in joined:
            model.geom_friction[geom_id, 0] = float(candidate.tip_sliding_mu)
            changed["tip"] += 1
        elif any(key in joined for key in HAND_KEYWORDS):
            model.geom_friction[geom_id, 0] = float(candidate.non_tip_sliding_mu)
            changed["non_tip_hand"] += 1
    return dict(changed)


def configure_ball_model(model, mujoco, args) -> dict[str, Any]:
    ball_geom = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
    ball_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    floor_geom = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "floor")
    if ball_geom < 0 or ball_body < 0:
        return {"configured": False}
    original_radius = float(model.geom_size[ball_geom, 0])
    original_body_mass = float(model.body_mass[ball_body])
    radius = float(args.ball_radius)
    if radius > 0:
        model.geom_size[ball_geom, 0] = radius
    if float(args.ball_mass) > 0:
        model.body_mass[ball_body] = float(args.ball_mass)
    floor_z = float(model.geom_pos[floor_geom, 2]) if floor_geom >= 0 else -0.09338044
    return {
        "configured": True,
        "original_radius_m": original_radius,
        "radius_m": float(model.geom_size[ball_geom, 0]),
        "original_body_mass_kg": original_body_mass,
        "body_mass_kg": float(model.body_mass[ball_body]),
        "floor_z_m": floor_z,
    }


def hand_targets(candidate: BallPinchCandidate, *, open_hand: bool = False) -> dict[str, float]:
    if open_hand:
        out = {
            "thumb_cmc_abd_joint": -0.12,
            "thumb_cmc_joint": 0.0,
            "thumb_mcp_joint": 0.02,
            "thumb_ip_joint": -0.02,
        }
        for finger in ("index", "middle", "ring", "little"):
            out.update(
                {
                    f"{finger}_mcp_flex_joint": 0.0,
                    f"{finger}_mcp_abd_joint": 0.0,
                    f"{finger}_pip_joint": 0.0,
                    f"{finger}_dip_joint": 0.0,
                }
            )
        return out

    out = {
        "thumb_cmc_abd_joint": candidate.thumb_cmc_abd,
        "thumb_cmc_joint": candidate.thumb_cmc,
        "thumb_mcp_joint": candidate.thumb_mcp,
        "thumb_ip_joint": candidate.thumb_ip,
    }
    for finger in ("index", "middle", "ring", "little"):
        if finger == candidate.active_finger:
            out.update(
                {
                    f"{finger}_mcp_flex_joint": candidate.active_mcp_flex,
                    f"{finger}_mcp_abd_joint": candidate.active_mcp_abd,
                    f"{finger}_pip_joint": candidate.active_pip,
                    f"{finger}_dip_joint": candidate.active_dip,
                }
            )
        else:
            scale = float(candidate.inactive_scale)
            out.update(
                {
                    f"{finger}_mcp_flex_joint": -0.02 * scale,
                    f"{finger}_mcp_abd_joint": -0.08 * scale,
                    f"{finger}_pip_joint": -0.10 * scale,
                    f"{finger}_dip_joint": -0.05 * scale,
                }
            )
    return out


def apply_hand_qpos(model, data, mujoco, targets: dict[str, float]) -> None:
    for joint, value in targets.items():
        set_joint_qpos(model, data, mujoco, joint, value)


def site_pos(model, data, mujoco, site_name: str) -> np.ndarray:
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
    if sid < 0:
        raise ValueError(f"Missing site {site_name!r}")
    return data.site_xpos[sid].copy()


def active_tip_site(candidate: BallPinchCandidate) -> str:
    return f"{candidate.active_finger}_tip_site"


def solve_arm_for_tip_pair(model, mujoco, candidate: BallPinchCandidate, initial_ball: np.ndarray, args) -> dict[str, Any]:
    data = mujoco.MjData(model)
    qadr = {joint: joint_qadr(model, mujoco, joint) for joint in ARM_JOINTS}
    bounds = []
    for joint in ARM_JOINTS:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint)
        bounds.append(tuple(float(v) for v in model.jnt_range[jid]))

    close_hand = hand_targets(candidate)
    target = np.asarray(initial_ball, dtype=np.float64).reshape(3) + np.asarray(
        [float(args.grasp_offset_x), float(args.grasp_offset_y), float(args.grasp_offset_z)],
        dtype=np.float64,
    )
    sep_target = float(args.tip_pair_separation_target)

    def set_pose(joints: np.ndarray) -> None:
        data.qpos[:] = model.qpos0
        data.qvel[:] = 0.0
        for idx, joint in enumerate(ARM_JOINTS):
            if qadr[joint] is not None:
                data.qpos[qadr[joint]] = float(joints[idx])
        apply_hand_qpos(model, data, mujoco, close_hand)
        mujoco.mj_forward(model, data)

    def objective(joints: np.ndarray) -> float:
        set_pose(joints)
        thumb = site_pos(model, data, mujoco, "thumb_tip_site")
        active = site_pos(model, data, mujoco, active_tip_site(candidate))
        mid = 0.5 * (thumb + active)
        sep = float(np.linalg.norm(thumb - active))
        z_split = float(abs(thumb[2] - active[2]))
        center_err = float(np.linalg.norm(mid - target))
        return float(160.0 * center_err * center_err + 60.0 * (sep - sep_target) ** 2 + 4.0 * z_split * z_split)

    seeds = [
        np.asarray([ball_demo.ARM_APPROACH[joint] for joint in ARM_JOINTS], dtype=np.float64),
        np.asarray([2.78, -1.54, 0.57, 2.60], dtype=np.float64),
        np.asarray([2.43, -1.5707, 0.12, 2.60], dtype=np.float64),
    ]
    best: dict[str, Any] | None = None
    for seed in seeds:
        result = minimize(objective, seed, method="L-BFGS-B", bounds=bounds, options={"maxiter": int(args.ik_maxiter)})
        joints = np.asarray(result.x, dtype=np.float64)
        set_pose(joints)
        thumb = site_pos(model, data, mujoco, "thumb_tip_site")
        active = site_pos(model, data, mujoco, active_tip_site(candidate))
        mid = 0.5 * (thumb + active)
        sep = float(np.linalg.norm(thumb - active))
        row = {
            "score": float(np.linalg.norm(mid - target) + abs(sep - sep_target)),
            "objective": float(result.fun),
            "optimizer_success": bool(result.success),
            "joints": {joint: float(joints[idx]) for idx, joint in enumerate(ARM_JOINTS)},
            "midpoint": mid,
            "target": target,
            "midpoint_error_m": float(np.linalg.norm(mid - target)),
            "tip_separation_m": float(sep),
            "tip_separation_error_m": float(abs(sep - sep_target)),
            "thumb_tip": thumb,
            "active_tip": active,
        }
        if best is None or row["score"] < best["score"]:
            best = row
    assert best is not None
    return best


def contact_rows(model, data, mujoco) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ball_body, _, _ = ball_ids(model, mujoco)
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
        if "ball" not in joined and ball_body not in body_ids:
            continue
        region = "unknown"
        for item in FINGER_REGIONS:
            if item in joined:
                region = item
                break
        if "palm" in joined or "hand_base" in joined or "wrist" in joined:
            region = "palm"
        rows.append(
            {
                "names": names,
                "region": region,
                "hand": bool(any(key in joined for key in HAND_KEYWORDS)),
                "floor": bool("floor" in joined),
                "tip": bool("tip_collision_proxy_sphere" in joined),
                "penetration": float(max(0.0, -float(c.dist))),
                "dist": float(c.dist),
            }
        )
    return rows


def frame_morphology(rows: list[dict[str, Any]], candidate: BallPinchCandidate) -> dict[str, Any]:
    hand_rows = [row for row in rows if bool(row["hand"])]
    floor_rows = [row for row in rows if bool(row["floor"])]
    hand_count = len(hand_rows)
    if hand_count == 0:
        return {
            "hand_contacts": 0,
            "floor_contacts": len(floor_rows),
            "regions": [],
            "tip_contact_ratio": 0.0,
            "non_tip_contact_ratio": 0.0,
            "true_two_tip_pinch": False,
            "wrap_or_support": False,
        }
    regions = sorted({str(row["region"]) for row in hand_rows})
    tip_regions = sorted({str(row["region"]) for row in hand_rows if bool(row["tip"])})
    desired = {"thumb", candidate.active_finger}
    support_regions = set(regions) - desired
    tip_ratio = float(sum(1 for row in hand_rows if bool(row["tip"])) / max(1, hand_count))
    non_tip_ratio = float(1.0 - tip_ratio)
    true_two_tip = bool(
        "thumb" in tip_regions
        and candidate.active_finger in tip_regions
        and not support_regions
        and tip_ratio >= float(0.66)
    )
    wrap = bool(support_regions) or non_tip_ratio > 0.34 or len(regions) > 2
    return {
        "hand_contacts": int(hand_count),
        "floor_contacts": int(len(floor_rows)),
        "regions": regions,
        "tip_regions": tip_regions,
        "support_regions": sorted(support_regions),
        "tip_contact_ratio": tip_ratio,
        "non_tip_contact_ratio": non_tip_ratio,
        "true_two_tip_pinch": bool(true_two_tip),
        "wrap_or_support": bool(wrap),
    }


def summarize_frames(frames: list[dict[str, Any]]) -> dict[str, Any]:
    if not frames:
        return {
            "frames": 0,
            "true_two_tip_pinch_fraction": 0.0,
            "wrap_frame_fraction": 0.0,
            "floor_contact_fraction": 0.0,
            "tip_contact_ratio_mean": 0.0,
            "non_tip_contact_ratio_mean": 0.0,
            "mean_hand_contacts": 0.0,
            "region_counts": {},
        }
    region_counts = Counter(region for frame in frames for region in frame.get("regions", []))
    return {
        "frames": int(len(frames)),
        "true_two_tip_pinch_fraction": float(np.mean([bool(frame["true_two_tip_pinch"]) for frame in frames])),
        "wrap_frame_fraction": float(np.mean([bool(frame["wrap_or_support"]) for frame in frames])),
        "floor_contact_fraction": float(np.mean([int(frame.get("floor_contacts", 0)) > 0 for frame in frames])),
        "tip_contact_ratio_mean": float(np.mean([float(frame.get("tip_contact_ratio", 0.0)) for frame in frames])),
        "non_tip_contact_ratio_mean": float(np.mean([float(frame.get("non_tip_contact_ratio", 0.0)) for frame in frames])),
        "mean_hand_contacts": float(np.mean([float(frame.get("hand_contacts", 0)) for frame in frames])),
        "region_counts": dict(region_counts),
    }


def phase_targets(default_targets: dict[str, float], approach_arm: dict[str, float], candidate: BallPinchCandidate) -> dict[str, dict[str, float]]:
    open_hand = hand_targets(candidate, open_hand=True)
    close_hand = hand_targets(candidate, open_hand=False)
    pre_arm = dict(approach_arm)
    pre_arm["j2"] = float(np.clip(pre_arm["j2"] + 0.32, -1.5708, 1.5708))
    lift_arm = dict(approach_arm)
    lift_arm["j2"] = float(candidate.lift_j2)
    return {
        "pre": {**default_targets, **pre_arm, **open_hand},
        "approach": {**default_targets, **approach_arm, **open_hand},
        "preshape": {**default_targets, **approach_arm, **open_hand},
        "close": {**default_targets, **approach_arm, **close_hand},
        "lift": {**default_targets, **lift_arm, **close_hand},
        "release": {**default_targets, **lift_arm, **open_hand},
    }


def run_phase(model, data, mujoco, names: list[str], start: dict[str, float], end: dict[str, float], steps: int) -> None:
    for idx in range(max(1, int(steps))):
        alpha = idx / max(1, int(steps) - 1)
        targets = ball_demo.blend_targets(start, end, alpha)
        data.ctrl[:] = ball_demo.ctrl_from_targets(model, mujoco, names, targets)
        mujoco.mj_step(model, data)


def run_candidate(model, mujoco, candidate: BallPinchCandidate, args, *, render_dir: Path | None = None) -> dict[str, Any]:
    data = mujoco.MjData(model)
    ball_config = configure_ball_model(model, mujoco, args)
    mujoco.mj_forward(model, data)
    initial_ball = ball_position(model, data, mujoco)
    if ball_config.get("configured"):
        initial_ball = initial_ball.copy()
        initial_ball[2] = float(ball_config["floor_z_m"]) + float(ball_config["radius_m"])
    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    ball_demo.set_ball_pose(model, data, mujoco, initial_ball)
    mujoco.mj_forward(model, data)

    names = ball_demo.actuator_names(model, mujoco)
    default_targets = actuated_joint_targets_from_qpos(model, data, mujoco, names)
    material_changes = set_contact_materials(model, mujoco, candidate)
    ik = solve_arm_for_tip_pair(model, mujoco, candidate, initial_ball, args)
    targets = phase_targets(default_targets, ik["joints"], candidate)

    for joint, value in targets["pre"].items():
        qadr = joint_qadr(model, mujoco, joint)
        if qadr is not None:
            data.qpos[qadr] = float(value)
    data.ctrl[:] = ball_demo.ctrl_from_targets(model, mujoco, names, targets["pre"])
    ball_demo.set_ball_pose(model, data, mujoco, initial_ball)
    mujoco.mj_forward(model, data)

    hold_frames: list[dict[str, Any]] = []
    lift_frames: list[dict[str, Any]] = []
    hold_lifts: list[float] = []
    lift_lifts: list[float] = []
    max_lift = 0.0
    max_pen = 0.0
    snapshots: dict[str, str] = {}

    def sample(label: str) -> dict[str, Any]:
        nonlocal max_lift, max_pen
        rows = contact_rows(model, data, mujoco)
        morph = frame_morphology(rows, candidate)
        ball = ball_position(model, data, mujoco)
        lift = float(ball[2] - initial_ball[2])
        max_lift = max(max_lift, lift)
        max_pen = max(max_pen, max([float(row["penetration"]) for row in rows] + [0.0]))
        return {
            "label": label,
            "ball_position": ball,
            "lift_m": lift,
            "morphology": morph,
            "max_penetration_m": float(max([float(row["penetration"]) for row in rows] + [0.0])),
        }

    def maybe_render(label: str) -> None:
        if render_dir is None:
            return
        path = render_dir / f"{label}.png"
        snapshots[label] = render_frame(model, data, mujoco, candidate, path, sample(label))

    phases = [
        ("approach", targets["pre"], targets["approach"], int(args.approach_steps)),
        ("preshape", targets["approach"], targets["preshape"], int(args.preshape_steps)),
        ("pinch_close", targets["preshape"], targets["close"], int(args.close_steps)),
        ("contact_settle", targets["close"], targets["close"], int(args.settle_steps)),
        ("slow_lift", targets["close"], targets["lift"], int(candidate.lift_steps)),
        ("hold", targets["lift"], targets["lift"], int(args.hold_steps)),
        ("release_open", targets["lift"], targets["release"], int(args.release_steps)),
        ("settle_release", targets["release"], targets["release"], int(args.release_settle_steps)),
    ]

    maybe_render("00_start")
    for phase, start, end, steps in phases:
        for idx in range(max(1, int(steps))):
            alpha = idx / max(1, int(steps) - 1)
            phase_target = ball_demo.blend_targets(start, end, alpha)
            data.ctrl[:] = ball_demo.ctrl_from_targets(model, mujoco, names, phase_target)
            mujoco.mj_step(model, data)
            if phase in {"slow_lift", "hold"} and idx % max(1, int(args.morphology_sample_every)) == 0:
                frame = sample(phase)
                if phase == "hold":
                    hold_frames.append(frame["morphology"])
                    hold_lifts.append(float(frame["lift_m"]))
                else:
                    lift_frames.append(frame["morphology"])
                    lift_lifts.append(float(frame["lift_m"]))
        if phase in {"pinch_close", "contact_settle", "slow_lift", "hold", "release_open", "settle_release"}:
            maybe_render(f"{len(snapshots):02d}_{phase}")

    final_sample = sample("final")
    final_rows = contact_rows(model, data, mujoco)
    final_morph = frame_morphology(final_rows, candidate)
    hold_summary = summarize_frames(hold_frames)
    lift_summary = summarize_frames(lift_frames)
    hold_lift_max = float(max(hold_lifts) if hold_lifts else 0.0)
    hold_lift_mean = float(np.mean(hold_lifts) if hold_lifts else 0.0)
    lift_lift_max = float(max(lift_lifts) if lift_lifts else 0.0)
    final_ball = ball_position(model, data, mujoco)
    release_success = bool(
        final_morph["floor_contacts"] > 0
        and final_morph["hand_contacts"] == 0
        and abs(float(final_ball[2] - initial_ball[2])) <= float(args.final_height_tolerance)
    )
    lift_success = bool(
        hold_lift_max >= float(args.min_lift_height)
        and hold_summary["floor_contact_fraction"] <= float(args.max_hold_floor_contact_fraction)
    )
    true_pinch_success = bool(
        lift_success
        and hold_summary["true_two_tip_pinch_fraction"] >= float(args.min_true_pinch_fraction)
        and hold_summary["wrap_frame_fraction"] <= float(args.max_wrap_fraction)
        and hold_summary["non_tip_contact_ratio_mean"] <= float(args.max_non_tip_ratio)
    )
    success = bool(true_pinch_success and release_success)
    if success:
        terminal_reason = "success_true_pinch_lift_release_ball"
    elif not lift_success:
        terminal_reason = "lift_gate_failed"
    elif not true_pinch_success:
        terminal_reason = "true_pinch_morphology_gate_failed"
    elif not release_success:
        terminal_reason = "release_gate_failed"
    else:
        terminal_reason = "unknown"

    score = (
        8.0 * float(hold_summary["true_two_tip_pinch_fraction"])
        + 4.0 * min(hold_lift_max / max(float(args.min_lift_height), 1e-6), 1.5)
        + 1.0 * min(lift_lift_max / max(float(args.min_lift_height), 1e-6), 1.5)
        + 2.0 * float(release_success)
        - 4.0 * float(hold_summary["wrap_frame_fraction"])
        - 3.0 * float(hold_summary["non_tip_contact_ratio_mean"])
        - 1.0 * float(lift_summary["floor_contact_fraction"])
        - 60.0 * max(0.0, float(max_pen) - float(args.max_penetration_m))
        - 10.0 * min(0.04, float(ik["midpoint_error_m"]))
        - 5.0 * min(0.05, float(ik["tip_separation_error_m"]))
    )

    return {
        "candidate": asdict(candidate),
        "status": "PASS" if success else "FAIL",
        "success": bool(success),
        "terminal_reason": terminal_reason,
        "score": float(score),
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
        "hold_morphology": hold_summary,
        "lift_morphology": lift_summary,
        "final_morphology": final_morph,
        "ik": ik,
        "material_changes": material_changes,
        "ball_config": ball_config,
        "snapshots": snapshots,
    }


def render_frame(
    model,
    data,
    mujoco,
    candidate: BallPinchCandidate,
    path: Path,
    row: dict[str, Any],
    *,
    camera_view: dict[str, float] | None = None,
) -> str:
    from PIL import Image, ImageDraw

    renderer = mujoco.Renderer(model, width=960, height=720)
    try:
        cam = mujoco.MjvCamera()
        mujoco.mjv_defaultFreeCamera(model, cam)
        bpos = ball_position(model, data, mujoco)
        palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
        palm = data.xpos[palm_id].copy() if palm_id >= 0 else bpos
        cam.lookat[:] = 0.62 * bpos + 0.38 * palm
        cam.lookat[2] += 0.015
        view = camera_view or {}
        cam.lookat[0] += float(view.get("lookat_dx", 0.0))
        cam.lookat[1] += float(view.get("lookat_dy", 0.0))
        cam.lookat[2] += float(view.get("lookat_dz", 0.0))
        cam.distance = float(view.get("distance", 0.35))
        cam.azimuth = float(view.get("azimuth", 176.0))
        cam.elevation = float(view.get("elevation", -18.0))
        renderer.update_scene(data, camera=cam)
        img = renderer.render().copy()
    finally:
        renderer.close()
    pil = Image.fromarray(img).convert("RGB")
    draw = ImageDraw.Draw(pil)
    morph = row.get("morphology", {})
    lines = [
        f"{row.get('label', '')} {candidate.name}",
        f"lift={float(row.get('lift_m', 0.0)):.4f} hand={morph.get('hand_contacts', 0)} floor={morph.get('floor_contacts', 0)}",
        f"regions={','.join(morph.get('regions', [])) or 'none'} true2tip={morph.get('true_two_tip_pinch', False)}",
        f"tip={float(morph.get('tip_contact_ratio', 0.0)):.2f} non_tip={float(morph.get('non_tip_contact_ratio', 0.0)):.2f} wrap={morph.get('wrap_or_support', False)}",
    ]
    width = int(max([draw.textlength(line) for line in lines] + [1])) + 20
    height = 18 * len(lines) + 12
    draw.rectangle((0, 0, width, height), fill=(255, 255, 255))
    for idx, line in enumerate(lines):
        draw.text((10, 7 + 18 * idx), line, fill=(0, 0, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    pil.save(path)
    return str(path)


def write_contact_sheet(paths: dict[str, str], out: Path) -> str | None:
    if not paths:
        return None
    from PIL import Image, ImageDraw

    items = list(paths.items())
    thumbs = []
    for label, filename in items:
        img = Image.open(filename).convert("RGB")
        img.thumbnail((360, 270))
        canvas = Image.new("RGB", (380, 306), (245, 245, 245))
        canvas.paste(img, ((380 - img.width) // 2, 28))
        ImageDraw.Draw(canvas).text((12, 8), label, fill=(0, 0, 0))
        thumbs.append(canvas)
    cols = 3
    rows = int(math.ceil(len(thumbs) / cols))
    sheet = Image.new("RGB", (cols * 380, rows * 306), (255, 255, 255))
    for idx, img in enumerate(thumbs):
        sheet.paste(img, ((idx % cols) * 380, (idx // cols) * 306))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return str(out)


def candidate_grid(args) -> list[BallPinchCandidate]:
    rows: list[BallPinchCandidate] = []
    for active in ("index", "middle"):
        for active_abd in (-0.45, -0.65, -0.85):
            for active_pip in (-0.45, -0.70, -0.95):
                for thumb_abd in (-0.35, -0.50, -0.65):
                    for thumb_mcp in (0.28, 0.42):
                        name = (
                            f"thumb_{active}_tip_mu{float(args.tip_mu):.1f}"
                            f"_abd{active_abd:+.2f}_pip{active_pip:+.2f}"
                            f"_tabd{thumb_abd:+.2f}_tmcp{thumb_mcp:+.2f}"
                        )
                        rows.append(
                            BallPinchCandidate(
                                name=name.replace("+", "p").replace("-", "m").replace(".", "p"),
                                active_finger=active,
                                thumb_cmc_abd=float(thumb_abd),
                                thumb_cmc=0.02,
                                thumb_mcp=float(thumb_mcp),
                                thumb_ip=-0.32,
                                active_mcp_flex=-0.04,
                                active_mcp_abd=float(active_abd),
                                active_pip=float(active_pip),
                                active_dip=float(active_pip * 0.45),
                                inactive_scale=float(args.inactive_scale),
                                tip_sliding_mu=float(args.tip_mu),
                                non_tip_sliding_mu=float(args.non_tip_mu),
                                ball_sliding_mu=float(args.ball_mu),
                                lift_j2=float(args.lift_j2),
                                lift_steps=int(args.lift_steps),
                            )
                        )
    return rows[: max(1, int(args.max_candidates))]


def summarize_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "episodes": int(len(rows)),
        "success_count": int(sum(1 for row in rows if row["success"])),
        "lift_success_count": int(sum(1 for row in rows if row["lift_success"])),
        "true_pinch_success_count": int(sum(1 for row in rows if row["true_pinch_success"])),
        "release_success_count": int(sum(1 for row in rows if row["release_success"])),
        "terminal_reason_counts": dict(Counter(str(row["terminal_reason"]) for row in rows)),
        "best_score": float(max([row["score"] for row in rows] + [float("-inf")])),
        "best_candidate": rows[0]["candidate"]["name"] if rows else None,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = payload["summary"]
    best = payload.get("best_result", {})
    lines = [
        "# Stage3.11D-B Ball True-Pinch Release Candidate Search v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- MuJoCo-only.\n",
        "- Parameter search, not neural-network training.\n",
        "- No hardware, real camera, tactile hardware, ultrasound, or full-action ACT/DP promotion.\n\n",
        "## Goal\n\n",
        "Find a small-ball demo candidate that separates lift success from true fingertip pinch and release success.\n\n",
        "## Summary\n\n",
        f"- Candidates evaluated: `{s['episodes']}`\n",
        f"- Full true-pinch-release success: `{s['success_count']} / {s['episodes']}`\n",
        f"- Lift gate success: `{s['lift_success_count']} / {s['episodes']}`\n",
        f"- True-pinch morphology gate success: `{s['true_pinch_success_count']} / {s['episodes']}`\n",
        f"- Release gate success: `{s['release_success_count']} / {s['episodes']}`\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n\n",
    ]
    if best:
        hm = best.get("hold_morphology", {})
        lines.extend(
            [
                "## Best Candidate\n\n",
                f"- Name: `{best['candidate']['name']}`\n",
                f"- Active finger: `{best['candidate']['active_finger']}`\n",
                f"- Score: `{best['score']:.4f}`\n",
                f"- Status: `{best['status']}` / `{best['terminal_reason']}`\n",
        f"- Max transient lift: `{best['max_lift_m']:.5f} m`\n",
        f"- Hold lift max: `{best.get('hold_lift_m_max', 0.0):.5f} m`\n",
        f"- Hold lift mean: `{best.get('hold_lift_m_mean', 0.0):.5f} m`\n",
                f"- Hold true two-tip fraction: `{hm.get('true_two_tip_pinch_fraction', 0.0):.3f}`\n",
                f"- Hold wrap fraction: `{hm.get('wrap_frame_fraction', 0.0):.3f}`\n",
                f"- Hold non-tip ratio: `{hm.get('non_tip_contact_ratio_mean', 0.0):.3f}`\n",
                f"- Release success: `{best.get('release_success')}`\n",
                f"- Visual contact sheet: `{payload.get('best_contact_sheet')}`\n\n",
            ]
        )
    lines.extend(
        [
            "## Top Candidates\n\n",
            "| rank | candidate | active | status | score | hold lift | transient lift | two-tip | wrap | non-tip | release | reason |\n",
            "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---|---|\n",
        ]
    )
    for idx, row in enumerate(payload["results"][: min(20, len(payload["results"]))], start=1):
        hm = row.get("hold_morphology", {})
        lines.append(
            f"| {idx} | `{row['candidate']['name']}` | `{row['candidate']['active_finger']}` | "
            f"{row['status']} | {row['score']:.3f} | {row.get('hold_lift_m_max', 0.0):.4f} | "
            f"{row['max_lift_m']:.4f} | "
            f"{hm.get('true_two_tip_pinch_fraction', 0.0):.3f} | "
            f"{hm.get('wrap_frame_fraction', 0.0):.3f} | "
            f"{hm.get('non_tip_contact_ratio_mean', 0.0):.3f} | "
            f"`{row.get('release_success')}` | `{row['terminal_reason']}` |\n"
        )
    lines.extend(
        [
            "\n## Next\n\n",
            "- If a full success appears, promote it only as a Stage3.11D-B true-pinch-release candidate after visual review and randomized pose checks.\n",
            "- If lift succeeds but morphology fails, continue morphology/material/approach search before neural training.\n",
            "- If true two-tip frames remain zero, treat current proxy geometry/approach orientation as the blocker and add a geometry/material branch.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search small-ball true-pinch-and-release candidates.")
    parser.add_argument("--scene", type=Path, default=DEFAULT_SCENE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--selected", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--visual-dir", type=Path, default=DEFAULT_VISUAL_DIR)
    parser.add_argument("--max-candidates", type=int, default=36)
    parser.add_argument("--render-best", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--tip-mu", type=float, default=2.8)
    parser.add_argument("--non-tip-mu", type=float, default=0.10)
    parser.add_argument("--ball-mu", type=float, default=1.35)
    parser.add_argument("--ball-radius", type=float, default=0.028)
    parser.add_argument("--ball-mass", type=float, default=0.025)
    parser.add_argument("--inactive-scale", type=float, default=0.0)
    parser.add_argument("--grasp-offset-x", type=float, default=0.0)
    parser.add_argument("--grasp-offset-y", type=float, default=0.0)
    parser.add_argument("--grasp-offset-z", type=float, default=0.002)
    parser.add_argument("--tip-pair-separation-target", type=float, default=0.070)
    parser.add_argument("--ik-maxiter", type=int, default=90)
    parser.add_argument("--approach-steps", type=int, default=220)
    parser.add_argument("--preshape-steps", type=int, default=80)
    parser.add_argument("--close-steps", type=int, default=180)
    parser.add_argument("--settle-steps", type=int, default=120)
    parser.add_argument("--hold-steps", type=int, default=260)
    parser.add_argument("--release-steps", type=int, default=180)
    parser.add_argument("--release-settle-steps", type=int, default=420)
    parser.add_argument("--lift-j2", type=float, default=-0.95)
    parser.add_argument("--lift-steps", type=int, default=420)
    parser.add_argument("--morphology-sample-every", type=int, default=10)
    parser.add_argument("--min-lift-height", type=float, default=0.050)
    parser.add_argument("--max-hold-floor-contact-fraction", type=float, default=0.05)
    parser.add_argument("--min-true-pinch-fraction", type=float, default=0.50)
    parser.add_argument("--max-wrap-fraction", type=float, default=0.30)
    parser.add_argument("--max-non-tip-ratio", type=float, default=0.45)
    parser.add_argument("--max-penetration-m", type=float, default=0.006)
    parser.add_argument("--final-height-tolerance", type=float, default=0.018)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    import mujoco

    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)

    results: list[dict[str, Any]] = []
    candidates = candidate_grid(args)
    for idx, candidate in enumerate(candidates):
        model = mujoco.MjModel.from_xml_path(str(scene))
        row = run_candidate(model, mujoco, candidate, args)
        results.append(row)
        hm = row.get("hold_morphology", {})
        print(
            f"{idx + 1:03d}/{len(candidates):03d} {row['status']} score={row['score']:.3f} "
            f"hold_lift={row.get('hold_lift_m_max', 0.0):.4f} transient={row['max_lift_m']:.4f} "
            f"two_tip={hm.get('true_two_tip_pinch_fraction', 0.0):.3f} "
            f"wrap={hm.get('wrap_frame_fraction', 0.0):.3f} release={row['release_success']} "
            f"{row['candidate']['name']}"
        )

    results.sort(key=lambda row: float(row["score"]), reverse=True)
    best = results[0] if results else None
    best_contact_sheet = None
    if best is not None and bool(args.render_best):
        best_candidate = BallPinchCandidate(**best["candidate"])
        model = mujoco.MjModel.from_xml_path(str(scene))
        render_dir = Path(args.visual_dir) / best_candidate.name
        best_rendered = run_candidate(model, mujoco, best_candidate, args, render_dir=render_dir)
        best.update({"snapshots": best_rendered.get("snapshots", {})})
        best_contact_sheet = write_contact_sheet(
            best.get("snapshots", {}),
            Path(args.visual_dir) / f"{best_candidate.name}_contact_sheet.png",
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
            "parameter_search_not_neural_training": True,
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
        args.selected.write_text(json.dumps(json_ready({"selected_candidate": best["candidate"], "result": best}), indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    print(f"Saved selected: {args.selected}")
    if best_contact_sheet:
        print(f"Saved best visual contact sheet: {best_contact_sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
