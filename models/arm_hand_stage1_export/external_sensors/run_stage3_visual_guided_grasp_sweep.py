#!/usr/bin/env python3
"""Stage3 visual-guided egg grasp/lift sweep.

Each trial runs two paired episodes:

1. visual: image-derived egg position -> arm IK -> grasp/lift
2. oracle: MuJoCo egg truth -> same arm IK/grasp/lift

The comparison tells us whether the current visual perception path is accurate
enough to guide the mechanical hand, while separating perception errors from
grasp/contact-model failures.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np
from scipy.optimize import minimize


SENSOR_ROOT = Path(__file__).resolve().parent
ROOT = SENSOR_ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import demo_arm_hand_lift_ball_scripted as base
from mujoco_egg_pose_sensor import DEFAULT_SCENE, EggPoseSensorConfig, MujocoEggPoseSensor, json_ready, write_json


DEFAULT_REPORT = SENSOR_ROOT / "reports" / "stage3_visual_guided_grasp_sweep_v0.md"
DEFAULT_METADATA = SENSOR_ROOT / "metadata" / "stage3_visual_guided_grasp_sweep_v0.json"
DEFAULT_VISUAL_DIR = SENSOR_ROOT / "visual_checks" / "stage3_visual_guided_grasp_sweep_v0"

EGG_BODY = "egg"
EGG_JOINT = "egg_freejoint"
DEFAULT_EGG_QUAT = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
DEFAULT_GRASP_LOCAL = np.array([0.04, 0.12, -0.02], dtype=np.float64)
ARM_JOINTS = base.ARM_JOINTS


@dataclass(frozen=True)
class TrialConfig:
    name: str
    offset_xyz: tuple[float, float, float]
    grasp_z_bias_m: float
    lift_delta_m: float
    pre_j2_delta: float
    close_hold_steps: int


def trial_configs() -> list[TrialConfig]:
    return [
        TrialConfig("center_nominal", (0.000, 0.000, 0.000), 0.000, 0.110, 0.42, 90),
        TrialConfig("left_low_nominal", (-0.020, -0.015, 0.000), 0.000, 0.110, 0.42, 90),
        TrialConfig("right_high_nominal", (0.020, 0.015, 0.000), 0.000, 0.110, 0.42, 90),
        TrialConfig("left_high_zplus", (-0.018, 0.014, 0.000), 0.003, 0.115, 0.44, 110),
        TrialConfig("right_low_zminus", (0.018, -0.014, 0.000), -0.003, 0.115, 0.44, 110),
        TrialConfig("front_small_lift", (0.010, 0.000, 0.000), 0.002, 0.095, 0.40, 90),
        TrialConfig("back_large_lift", (-0.010, 0.000, 0.000), -0.002, 0.130, 0.45, 120),
        TrialConfig("lifted_center", (0.000, 0.000, 0.012), 0.000, 0.110, 0.42, 100),
        TrialConfig("lifted_diag", (0.014, -0.010, 0.012), 0.002, 0.120, 0.43, 110),
        TrialConfig("wide_diag", (-0.016, 0.012, 0.006), -0.002, 0.125, 0.45, 120),
    ]


def set_freejoint_pose(model, data, mujoco, joint_name: str, position: np.ndarray, quat: np.ndarray) -> None:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if joint_id < 0:
        raise ValueError(f"Unknown freejoint: {joint_name!r}")
    qadr = int(model.jnt_qposadr[joint_id])
    dadr = int(model.jnt_dofadr[joint_id])
    data.qpos[qadr : qadr + 3] = np.asarray(position, dtype=np.float64).reshape(3)
    data.qpos[qadr + 3 : qadr + 7] = np.asarray(quat, dtype=np.float64).reshape(4)
    data.qvel[dadr : dadr + 6] = 0.0


def egg_body_id(model, mujoco) -> int:
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, EGG_BODY)
    if body_id < 0:
        raise ValueError(f"Unknown egg body: {EGG_BODY!r}")
    return int(body_id)


def reset_episode(model, data, mujoco, egg_position: np.ndarray) -> None:
    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0
    set_freejoint_pose(model, data, mujoco, EGG_JOINT, egg_position, DEFAULT_EGG_QUAT)
    mujoco.mj_forward(model, data)


def proxy_position(model, data, mujoco, grasp_local: np.ndarray) -> np.ndarray:
    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    if palm_id < 0:
        raise ValueError("Missing palm_link body")
    return data.xpos[palm_id].copy() + data.xmat[palm_id].reshape(3, 3).copy() @ np.asarray(grasp_local, dtype=np.float64)


class ArmProxyIkSolver:
    def __init__(self, model, mujoco, grasp_local: np.ndarray):
        self.model = model
        self.mujoco = mujoco
        self.data = mujoco.MjData(model)
        self.grasp_local = np.asarray(grasp_local, dtype=np.float64).reshape(3)
        self.qadr = {joint: base.joint_qadr(model, mujoco, joint) for joint in ARM_JOINTS}
        self.bounds = []
        for joint in ARM_JOINTS:
            jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint)
            self.bounds.append(tuple(float(v) for v in model.jnt_range[jid]))

    def proxy_for_joints(self, joints: np.ndarray) -> np.ndarray:
        self.data.qpos[:] = self.model.qpos0
        self.data.qvel[:] = 0.0
        for idx, joint in enumerate(ARM_JOINTS):
            self.data.qpos[self.qadr[joint]] = float(joints[idx])
        self.mujoco.mj_forward(self.model, self.data)
        return proxy_position(self.model, self.data, self.mujoco, self.grasp_local)

    def solve(self, target_proxy: np.ndarray, *, z_weight: float = 10.0) -> dict[str, Any]:
        seeds = [
            np.asarray([base.ARM_APPROACH[j] for j in ARM_JOINTS], dtype=np.float64),
            np.asarray([base.ARM_LIFT[j] for j in ARM_JOINTS], dtype=np.float64),
            np.array([2.831, -1.506, 0.512, 2.668], dtype=np.float64),
            np.array([2.70, -1.48, 0.58, 2.55], dtype=np.float64),
            np.array([2.95, -1.50, 0.45, 2.78], dtype=np.float64),
        ]
        for j1 in np.linspace(2.45, 3.10, 8):
            seeds.append(np.array([j1, -1.50, 0.52, 2.66], dtype=np.float64))

        target = np.asarray(target_proxy, dtype=np.float64).reshape(3)

        def objective(joints: np.ndarray) -> float:
            err = self.proxy_for_joints(joints) - target
            return float(35.0 * (err[0] * err[0] + err[1] * err[1]) + float(z_weight) * err[2] * err[2])

        best: dict[str, Any] | None = None
        for seed in seeds:
            result = minimize(objective, seed, method="L-BFGS-B", bounds=self.bounds, options={"maxiter": 180})
            joints = np.asarray(result.x, dtype=np.float64)
            proxy = self.proxy_for_joints(joints)
            dxy = float(np.linalg.norm((proxy - target)[:2]))
            dz = abs(float(proxy[2] - target[2]))
            row = {
                "score": dxy + 0.25 * dz,
                "dxy": dxy,
                "dz": dz,
                "joints": joints,
                "proxy": proxy,
                "optimizer_success": bool(result.success),
            }
            if best is None or row["score"] < best["score"]:
                best = row
        assert best is not None
        return best


def arm_dict(solution: dict[str, Any]) -> dict[str, float]:
    joints = np.asarray(solution["joints"], dtype=np.float64)
    return {joint: float(joints[idx]) for idx, joint in enumerate(ARM_JOINTS)}


def blend_targets(a: dict[str, float], b: dict[str, float], alpha: float) -> dict[str, float]:
    keys = set(a) | set(b)
    return {key: (1.0 - alpha) * float(a.get(key, 0.0)) + alpha * float(b.get(key, 0.0)) for key in keys}


def actuator_targets(model, mujoco, actuator_names: list[str], targets: dict[str, float]) -> np.ndarray:
    return base.ctrl_from_targets(model, mujoco, actuator_names, targets)


def run_phase(model, data, mujoco, actuator_names: list[str], start: dict[str, float], end: dict[str, float], steps: int) -> None:
    for idx in range(max(1, int(steps))):
        alpha = idx / max(1, int(steps) - 1)
        targets = blend_targets(start, end, alpha)
        data.ctrl[:] = actuator_targets(model, mujoco, actuator_names, targets)
        mujoco.mj_step(model, data)


def contact_summary(model, data, mujoco) -> dict[str, Any]:
    hand = 0
    floor = 0
    arm = 0
    max_penetration = 0.0
    for idx in range(data.ncon):
        c = data.contact[idx]
        geoms = [int(c.geom1), int(c.geom2)]
        names = []
        for geom_id in geoms:
            body_id = int(model.geom_bodyid[geom_id])
            names.append(mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or "")
            names.append(mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, body_id) or "")
        joined = " ".join(names).lower()
        if "egg" in joined and any(key in joined for key in ["palm", "finger", "thumb", "distal", "proximal", "wrist", "mcp", "hand_base"]):
            hand += 1
        if "egg" in joined and "floor" in joined:
            floor += 1
        if "egg" in joined and any(key in joined for key in ["base_link", "link_1", "link_2", "link_3", "ee_mount"]):
            arm += 1
        max_penetration = max(max_penetration, max(0.0, -float(c.dist)))
    return {
        "egg_hand_contact_count": int(hand),
        "egg_floor_contact_count": int(floor),
        "egg_arm_contact_count": int(arm),
        "max_penetration_m": float(max_penetration),
    }


def render_trial_snapshot(model, data, mujoco, output: Path, lookat: np.ndarray | None = None) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    renderer = mujoco.Renderer(model, width=960, height=720)
    try:
        cam = mujoco.MjvCamera()
        mujoco.mjv_defaultFreeCamera(model, cam)
        if lookat is None:
            egg_id = egg_body_id(model, mujoco)
            palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
            lookat = 0.55 * data.xpos[egg_id].copy() + 0.45 * data.xpos[palm_id].copy()
        cam.lookat[:] = lookat
        cam.distance = 0.42
        cam.azimuth = 180.0
        cam.elevation = -18.0
        renderer.update_scene(data, camera=cam)
        image = renderer.render()
    finally:
        renderer.close()
    imageio.imwrite(output, image)
    return str(output)


def trial_failure_reasons(
    row: dict[str, Any],
    *,
    success_lift_height: float,
    max_penetration: float,
    functional_hit_threshold: float,
) -> list[str]:
    reasons: list[str] = []
    if row.get("sensor_status") not in {"ok", "oracle"}:
        reasons.append("sensor_failed")
    if row.get("ik_approach_dxy_m", math.inf) > 0.006 or row.get("ik_approach_dz_m", math.inf) > 0.006:
        reasons.append("ik_alignment_error")
    if row.get("approach_true_proxy_error_m", math.inf) > float(functional_hit_threshold):
        reasons.append("functional_approach_missed_true_egg")
    if row.get("max_hand_contacts", 0) <= 0:
        reasons.append("no_egg_hand_contact")
    if row.get("final_lift_height_m", -math.inf) < float(success_lift_height):
        reasons.append("insufficient_lift_height")
    if row.get("final_floor_contacts", 0) > 0:
        reasons.append("egg_still_on_floor")
    if row.get("max_penetration_m", math.inf) > float(max_penetration):
        reasons.append("excessive_penetration")
    if not bool(row.get("finite_state", False)):
        reasons.append("non_finite_state")
    return reasons


def run_one_episode(
    model,
    mujoco,
    *,
    trial: TrialConfig,
    target_source: str,
    egg_position: np.ndarray,
    target_position_for_ik: np.ndarray,
    sensor_estimate: dict[str, Any] | None,
    args,
    visual_dir: Path,
) -> dict[str, Any]:
    data = mujoco.MjData(model)
    reset_episode(model, data, mujoco, egg_position)
    actuator_names = base.actuator_names(model, mujoco)
    grasp_local = DEFAULT_GRASP_LOCAL.copy()
    solver = ArmProxyIkSolver(model, mujoco, grasp_local)

    approach_target = np.asarray(target_position_for_ik, dtype=np.float64).copy()
    approach_target[2] += float(trial.grasp_z_bias_m)
    lift_target = approach_target.copy()
    lift_target[2] += float(trial.lift_delta_m)
    approach_solution = solver.solve(approach_target, z_weight=10.0)
    lift_solution = solver.solve(lift_target, z_weight=6.0)
    approach_arm = arm_dict(approach_solution)
    lift_arm = arm_dict(lift_solution)
    pre_arm = dict(approach_arm)
    pre_arm["j2"] = float(np.clip(pre_arm["j2"] + float(trial.pre_j2_delta), -1.5708, 1.5708))

    reset_episode(model, data, mujoco, egg_position)
    for joint, value in pre_arm.items():
        data.qpos[base.joint_qadr(model, mujoco, joint)] = float(value)
    data.ctrl[:] = actuator_targets(model, mujoco, actuator_names, pre_arm)
    mujoco.mj_forward(model, data)
    initial_egg = data.xpos[egg_body_id(model, mujoco)].copy()

    hand_targets = {
        "preshape": {**approach_arm, **base.PRESHAPE_TARGETS},
        "close_fingers": {**approach_arm, **base.LONG_FINGER_TARGETS},
        "close_thumb": {**approach_arm, **base.LONG_FINGER_TARGETS, **base.THUMB_SMOKE_TARGETS},
        "lift": {**lift_arm, **base.LONG_FINGER_TARGETS, **base.THUMB_SMOKE_TARGETS},
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
        run_phase(model, data, mujoco, actuator_names, start, end, int(steps))
        egg_now = data.xpos[egg_body_id(model, mujoco)].copy()
        proxy_now = proxy_position(model, data, mujoco, grasp_local)
        contact = contact_summary(model, data, mujoco)
        max_hand_contacts = max(max_hand_contacts, int(contact["egg_hand_contact_count"]))
        max_penetration_seen = max(max_penetration_seen, float(contact["max_penetration_m"]))
        if phase_name == "approach":
            approach_true_proxy_error = float(np.linalg.norm(proxy_now - initial_egg))
            approach_est_proxy_error = float(np.linalg.norm(proxy_now - approach_target))
        phase_rows.append(
            {
                "phase": phase_name,
                "egg_position": egg_now,
                "egg_lift_height_m": float(egg_now[2] - initial_egg[2]),
                "proxy_position": proxy_now,
                "contact": contact,
            }
        )
        if args.render_snapshots and target_source == "visual" and trial.name in {"center_nominal", "right_high_nominal", "lifted_diag"} and phase_name in {"approach", "close_thumb", "hold_lift"}:
            screenshots[phase_name] = render_trial_snapshot(
                model,
                data,
                mujoco,
                visual_dir / trial.name / f"{target_source}_{phase_name}.png",
            )

    final_egg = data.xpos[egg_body_id(model, mujoco)].copy()
    final_contact = contact_summary(model, data, mujoco)
    finite = bool(np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all())
    final_lift = float(final_egg[2] - initial_egg[2])
    row = {
        "trial": trial.name,
        "target_source": target_source,
        "trial_config": asdict(trial),
        "sensor_status": sensor_estimate.get("status", "oracle") if sensor_estimate is not None else "oracle",
        "sensor_confidence": sensor_estimate.get("confidence") if sensor_estimate is not None else None,
        "sensor_mask_pixels": sensor_estimate.get("mask_pixels") if sensor_estimate is not None else None,
        "egg_initial_position": initial_egg,
        "target_position_for_ik": np.asarray(target_position_for_ik, dtype=np.float64),
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
        "screenshots": screenshots,
    }
    row["precision_hit_pass"] = float(row["approach_true_proxy_error_m"]) <= float(args.precision_hit_threshold)
    row["functional_hit_pass"] = float(row["approach_true_proxy_error_m"]) <= float(args.functional_hit_threshold)
    reasons = trial_failure_reasons(
        row,
        success_lift_height=args.success_lift_height,
        max_penetration=args.max_success_penetration,
        functional_hit_threshold=args.functional_hit_threshold,
    )
    row["success"] = len(reasons) == 0
    row["failure_reasons"] = reasons
    return row


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "episodes": len(rows),
        "successes": int(sum(1 for row in rows if row.get("success"))),
        "failures": int(sum(1 for row in rows if not row.get("success"))),
        "precision_hit_passes": int(sum(1 for row in rows if row.get("precision_hit_pass"))),
        "functional_hit_passes": int(sum(1 for row in rows if row.get("functional_hit_pass"))),
    }
    for key in [
        "final_lift_height_m",
        "approach_true_proxy_error_m",
        "approach_est_proxy_error_m",
        "max_penetration_m",
    ]:
        values = np.asarray([float(row[key]) for row in rows if np.isfinite(float(row[key]))], dtype=np.float64)
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


def pair_summary(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_trial: dict[str, dict[str, dict[str, Any]]] = {}
    for row in results:
        by_trial.setdefault(row["trial"], {})[row["target_source"]] = row
    rows = []
    for trial, items in by_trial.items():
        visual = items.get("visual")
        oracle = items.get("oracle")
        if visual is None or oracle is None:
            continue
        rows.append(
            {
                "trial": trial,
                "visual_success": bool(visual["success"]),
                "oracle_success": bool(oracle["success"]),
                "visual_lift_m": float(visual["final_lift_height_m"]),
                "oracle_lift_m": float(oracle["final_lift_height_m"]),
                "lift_delta_visual_minus_oracle_m": float(visual["final_lift_height_m"] - oracle["final_lift_height_m"]),
                "visual_approach_true_error_m": float(visual["approach_true_proxy_error_m"]),
                "oracle_approach_true_error_m": float(oracle["approach_true_proxy_error_m"]),
                "visual_precision_hit": bool(visual.get("precision_hit_pass")),
                "oracle_precision_hit": bool(oracle.get("precision_hit_pass")),
                "visual_functional_hit": bool(visual.get("functional_hit_pass")),
                "oracle_functional_hit": bool(oracle.get("functional_hit_pass")),
                "visual_failure_reasons": list(visual["failure_reasons"]),
                "oracle_failure_reasons": list(oracle["failure_reasons"]),
            }
        )
    return rows


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Stage3 Visual-Guided Grasp Sweep V0\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "This MuJoCo-only Stage3 test checks whether image-derived egg position can guide the mechanical hand to approach, close on, and lift the egg. Each trial has a paired oracle run that uses MuJoCo egg truth for IK while keeping the same control phases.\n\n",
        "## Inputs\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Perception camera: `{payload['camera']}`\n",
        f"- Trial groups: `{payload['trial_groups']}`\n",
        f"- Episodes: `{payload['summary_all']['episodes']}`\n",
        f"- Success lift threshold: `{payload['thresholds']['success_lift_height_m']:.3f} m`\n",
        f"- Precision hit threshold: `{payload['thresholds']['precision_hit_threshold_m']:.3f} m`\n",
        f"- Functional hit threshold: `{payload['thresholds']['functional_hit_threshold_m']:.3f} m`\n",
        f"- Max success penetration: `{payload['thresholds']['max_success_penetration_m']:.3f} m`\n\n",
        "## Overall Result\n\n",
        f"- Visual episodes: `{payload['summary_visual']['successes']}` / `{payload['summary_visual']['episodes']}` success\n",
        f"- Oracle episodes: `{payload['summary_oracle']['successes']}` / `{payload['summary_oracle']['episodes']}` success\n",
        f"- Visual precision hits: `{payload['summary_visual']['precision_hit_passes']}` / `{payload['summary_visual']['episodes']}`\n",
        f"- Visual functional hits: `{payload['summary_visual']['functional_hit_passes']}` / `{payload['summary_visual']['episodes']}`\n",
        f"- Visual mean final lift: `{payload['summary_visual'].get('final_lift_height_m_mean', float('nan')):.6f} m`\n",
        f"- Oracle mean final lift: `{payload['summary_oracle'].get('final_lift_height_m_mean', float('nan')):.6f} m`\n",
        f"- Visual max approach true error: `{payload['summary_visual'].get('approach_true_proxy_error_m_max', float('nan')):.6f} m`\n",
        f"- Oracle max approach true error: `{payload['summary_oracle'].get('approach_true_proxy_error_m_max', float('nan')):.6f} m`\n\n",
        "## Paired Trial Results\n\n",
        "| trial | visual | oracle | visual lift m | oracle lift m | lift delta m | visual hit 8/15mm | oracle hit 8/15mm | visual approach err m | oracle approach err m | visual failure | oracle failure |\n",
        "|---|---:|---:|---:|---:|---:|---|---|---:|---:|---|---|\n",
    ]
    for row in payload["paired_results"]:
        lines.append(
            f"| {row['trial']} | {int(row['visual_success'])} | {int(row['oracle_success'])} | "
            f"{row['visual_lift_m']:.5f} | {row['oracle_lift_m']:.5f} | "
            f"{row['lift_delta_visual_minus_oracle_m']:.6f} | "
            f"{int(row['visual_precision_hit'])}/{int(row['visual_functional_hit'])} | "
            f"{int(row['oracle_precision_hit'])}/{int(row['oracle_functional_hit'])} | "
            f"{row['visual_approach_true_error_m']:.6f} | {row['oracle_approach_true_error_m']:.6f} | "
            f"`{row['visual_failure_reasons']}` | `{row['oracle_failure_reasons']}` |\n"
        )
    lines.extend(
        [
            "\n## Failure Aggregates\n\n",
            f"- Visual failure reasons: `{payload['summary_visual']['failure_reasons']}`\n",
            f"- Oracle failure reasons: `{payload['summary_oracle']['failure_reasons']}`\n\n",
            "## Interpretation\n\n",
        ]
    )
    if payload["summary_visual"]["successes"] == payload["summary_visual"]["episodes"]:
        lines.append("- Visual-guided grasp/lift passed every tested group under this clean MuJoCo segmentation setup.\n")
    elif payload["summary_visual"]["successes"] == payload["summary_oracle"]["successes"]:
        lines.append("- Visual and oracle outcomes match; remaining failures are likely grasp/contact/control issues rather than perception accuracy.\n")
    else:
        lines.append("- Visual and oracle outcomes differ; perception/visibility should be investigated before expanding the grasp policy.\n")
    lines.extend(
        [
            "- This is not a real-camera test and does not validate Stage4 hardware integration.\n",
            "- The next risk is dynamic occlusion during approach/closure and replacing exact MuJoCo segmentation with a noisier mask provider.\n\n",
            f"Metadata: `{payload['metadata']}`\n",
            f"Visual checks: `{payload['visual_dir']}`\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run paired visual/oracle Stage3 egg grasp sweep.")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
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
    base_egg_position = data.xpos[egg_body_id(model, mujoco)].copy()
    sensor = MujocoEggPoseSensor(
        model,
        mujoco,
        EggPoseSensorConfig(camera_name=args.camera, width=int(args.width), height=int(args.height)),
    )
    results: list[dict[str, Any]] = []
    for trial in trial_configs():
        egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)

        acq_data = mujoco.MjData(model)
        reset_episode(model, acq_data, mujoco, egg_position)
        debug_dir = visual_dir / trial.name / "sensor" if trial.name in {"center_nominal", "right_high_nominal", "lifted_diag"} else None
        estimate = sensor.estimate(acq_data, debug_dir=debug_dir, label=f"{trial.name}_acquire")
        if estimate["status"] == "ok":
            visual_target = np.asarray(estimate["position_world_est"], dtype=np.float64)
            visual_row = run_one_episode(
                model,
                mujoco,
                trial=trial,
                target_source="visual",
                egg_position=egg_position,
                target_position_for_ik=visual_target,
                sensor_estimate=estimate,
                args=args,
                visual_dir=visual_dir,
            )
        else:
            visual_row = {
                "trial": trial.name,
                "target_source": "visual",
                "trial_config": asdict(trial),
                "sensor_status": estimate["status"],
                "sensor_confidence": estimate.get("confidence", 0.0),
                "sensor_mask_pixels": estimate.get("mask_pixels", 0),
                "success": False,
                "failure_reasons": ["sensor_failed"],
            }
        oracle_row = run_one_episode(
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
        results.extend([visual_row, oracle_row])
        print(
            f"{trial.name}: visual={visual_row.get('success')} lift={visual_row.get('final_lift_height_m', float('nan')):.4f} "
            f"oracle={oracle_row.get('success')} lift={oracle_row.get('final_lift_height_m', float('nan')):.4f}"
        )

    visual_rows = [row for row in results if row["target_source"] == "visual"]
    oracle_rows = [row for row in results if row["target_source"] == "oracle"]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(scene),
        "camera": str(args.camera),
        "trial_groups": len(trial_configs()),
        "thresholds": {
            "success_lift_height_m": float(args.success_lift_height),
            "precision_hit_threshold_m": float(args.precision_hit_threshold),
            "functional_hit_threshold_m": float(args.functional_hit_threshold),
            "max_success_penetration_m": float(args.max_success_penetration),
        },
        "results": results,
        "paired_results": pair_summary(results),
        "summary_visual": summarize(visual_rows),
        "summary_oracle": summarize(oracle_rows),
        "summary_all": summarize(results),
        "metadata": str(metadata),
        "visual_dir": str(visual_dir),
    }
    write_json(metadata, payload)
    report_payload = json.loads(json.dumps(json_ready(payload)))
    write_report(report, report_payload)
    print(f"Visual successes: {payload['summary_visual']['successes']} / {payload['summary_visual']['episodes']}")
    print(f"Oracle successes: {payload['summary_oracle']['successes']} / {payload['summary_oracle']['episodes']}")
    print(f"Report: {report}")
    print(f"Metadata: {metadata}")


if __name__ == "__main__":
    main()
