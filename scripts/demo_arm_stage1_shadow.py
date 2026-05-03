#!/usr/bin/env python3
"""Visual check demo for the Stage-1 arm plus temporary Shadow hand combo.

This is a structural/debug demo only. It is not a promoted training
environment and does not replace the canonical pre_grasp pipeline.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Dict, Iterable, List

import mujoco
import numpy as np


DEFAULT_MODEL = "models/arm_stage1_shadow_combo/scene.xml"
ARM_ACTUATORS = ("a_j1", "a_j2", "a_j3", "a_j4")
WRIST_ACTUATORS = ("rh_A_WRJ2", "rh_A_WRJ1")
WRAPPER_LOCK_ACTUATORS = ("active_combo_lock_rh_WRJ1", "active_combo_lock_rh_WRJ2")
FINGER_FLEXION_ACTUATORS = (
    "rh_A_THJ5",
    "rh_A_THJ4",
    "rh_A_THJ2",
    "rh_A_THJ1",
    "rh_A_FFJ3",
    "rh_A_FFJ2",
    "rh_A_FFJ1",
    "rh_A_MFJ3",
    "rh_A_MFJ2",
    "rh_A_MFJ1",
    "rh_A_RFJ3",
    "rh_A_RFJ2",
    "rh_A_RFJ1",
    "rh_A_LFJ5",
    "rh_A_LFJ3",
    "rh_A_LFJ2",
    "rh_A_LFJ1",
)
FINGER_SPREAD_ACTUATORS = (
    "rh_A_THJ3",
    "rh_A_FFJ4",
    "rh_A_MFJ4",
    "rh_A_RFJ4",
    "rh_A_LFJ4",
)
TRACKED_BODIES = ("ee_mount", "rh_forearm", "rh_wrist", "rh_palm")
DEFAULT_MOUNT_SITE = "ee_tool_frame_site"
DEFAULT_MOUNT_BODY = "rh_wrist"
DEFAULT_MOUNT_OFFSET = (0.0, 0.0, 0.08)


def actuator_id(model: mujoco.MjModel, name: str) -> int:
    """Return an actuator id, raising a clear error if the model changed."""
    idx = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
    if idx < 0:
        raise KeyError(f"Missing actuator: {name}")
    return idx


def body_id(model: mujoco.MjModel, name: str) -> int:
    """Return a body id, raising a clear error if the model changed."""
    idx = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    if idx < 0:
        raise KeyError(f"Missing body: {name}")
    return idx


def actuator_ids(model: mujoco.MjModel, names: Iterable[str]) -> Dict[str, int]:
    """Resolve a group of actuator names."""
    return {name: actuator_id(model, name) for name in names}


def control_bounds(model: mujoco.MjModel, actuator_index: int) -> np.ndarray:
    """Return a safe control range for an actuator."""
    ctrl_range = np.asarray(model.actuator_ctrlrange[actuator_index], dtype=np.float64)
    if ctrl_range.shape != (2,) or not np.all(np.isfinite(ctrl_range)):
        return np.asarray([-1.0, 1.0], dtype=np.float64)
    low, high = float(ctrl_range[0]), float(ctrl_range[1])
    if high <= low:
        return np.asarray([0.0, 0.0], dtype=np.float64)
    return ctrl_range


def set_named_control(model: mujoco.MjModel, data: mujoco.MjData, name: str, value: float) -> None:
    """Set one named control after clipping to its ctrlrange."""
    idx = actuator_id(model, name)
    low, high = control_bounds(model, idx)
    data.ctrl[idx] = float(np.clip(value, low, high))


def site_id(model: mujoco.MjModel, name: str) -> int:
    """Return a site id, raising a clear error if the model changed."""
    idx = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, name)
    if idx < 0:
        raise KeyError(f"Missing site: {name}")
    return idx


def joint_id(model: mujoco.MjModel, name: str) -> int:
    """Return a joint id, raising a clear error if the model changed."""
    idx = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
    if idx < 0:
        raise KeyError(f"Missing joint: {name}")
    return idx


def equality_id(model: mujoco.MjModel, name: str) -> int:
    """Return an equality constraint id, raising a clear error if the model changed."""
    idx = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_EQUALITY, name)
    if idx < 0:
        raise KeyError(f"Missing equality: {name}")
    return idx


def mat_to_quat(mat: np.ndarray) -> np.ndarray:
    """Convert a 3x3 rotation matrix to a MuJoCo quaternion."""
    quat = np.zeros(4, dtype=np.float64)
    mujoco.mju_mat2Quat(quat, np.asarray(mat, dtype=np.float64).reshape(-1))
    return quat


def quat_to_mat(quat: np.ndarray) -> np.ndarray:
    """Convert a MuJoCo quaternion to a 3x3 rotation matrix."""
    mat = np.zeros(9, dtype=np.float64)
    mujoco.mju_quat2Mat(mat, np.asarray(quat, dtype=np.float64))
    return mat.reshape(3, 3)


def quat_inverse(quat: np.ndarray) -> np.ndarray:
    """Return the inverse of a unit quaternion."""
    out = np.zeros(4, dtype=np.float64)
    mujoco.mju_negQuat(out, quat)
    return out


def quat_multiply(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Multiply two MuJoCo quaternions."""
    out = np.zeros(4, dtype=np.float64)
    mujoco.mju_mulQuat(out, left, right)
    return out


def relative_pose(
    parent_pos: np.ndarray,
    parent_quat: np.ndarray,
    parent_xmat: np.ndarray,
    child_pos: np.ndarray,
    child_quat: np.ndarray,
) -> np.ndarray:
    """Return child pose in the parent body frame as pos + quat."""
    rel_pos = parent_xmat.reshape(3, 3).T @ (child_pos - parent_pos)
    rel_quat = quat_multiply(quat_inverse(parent_quat), child_quat)
    return np.concatenate([rel_pos, rel_quat])


def hide_shadow_forearm_shell(model: mujoco.MjModel) -> List[str]:
    """Hide the temporary Shadow forearm shell for wrist-mount inspection."""
    forearm = body_id(model, "rh_forearm")
    hidden = []
    for geom_idx in range(model.ngeom):
        if int(model.geom_bodyid[geom_idx]) != forearm:
            continue
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_idx) or f"geom_{geom_idx}"
        model.geom_rgba[geom_idx, 3] = 0.0
        model.geom_contype[geom_idx] = 0
        model.geom_conaffinity[geom_idx] = 0
        hidden.append(name)
    return hidden


def parse_vec3(text: str, name: str) -> np.ndarray:
    """Parse a comma-separated xyz vector."""
    try:
        values = [float(item.strip()) for item in text.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{name} must contain three floats") from exc
    if len(values) != 3:
        raise argparse.ArgumentTypeError(f"{name} must contain three floats")
    return np.asarray(values, dtype=np.float64)


def configure_shadow_mount(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    mount_site: str,
    mount_body: str,
    mount_offset: np.ndarray,
    mount_weld: str = "active_arm_shadow_mount_weld",
) -> Dict[str, object]:
    """Initialize the temporary Shadow hand at the selected arm mount site.

    The XML combo weld is intentionally a bridge. If the Shadow freejoint starts
    at its source-model origin, MuJoCo preserves that initial offset. For this
    debug demo we reset the freejoint and weld relpose so the visible target
    body is actually mounted at the arm-side tool site.
    """
    mujoco.mj_forward(model, data)

    ee_body = body_id(model, "ee_mount")
    root_joint = joint_id(model, "combo_shadow_root_freejoint")
    root_body = body_id(model, "rh_forearm")
    target_body = body_id(model, mount_body)
    site = site_id(model, mount_site)
    weld = equality_id(model, mount_weld)

    root_qpos = int(model.jnt_qposadr[root_joint])
    root_qvel = int(model.jnt_dofadr[root_joint])

    root_to_target_pos = data.xmat[root_body].reshape(3, 3).T @ (data.xpos[target_body] - data.xpos[root_body])
    root_to_target_quat = quat_multiply(quat_inverse(data.xquat[root_body]), data.xquat[target_body])

    site_xmat = data.site_xmat[site].reshape(3, 3).copy()
    target_pos = data.site_xpos[site] + site_xmat @ np.asarray(mount_offset, dtype=np.float64)
    target_quat = mat_to_quat(site_xmat)
    root_quat = quat_multiply(target_quat, quat_inverse(root_to_target_quat))
    root_xmat = quat_to_mat(root_quat)
    root_pos = target_pos - root_xmat @ root_to_target_pos

    data.qpos[root_qpos: root_qpos + 3] = root_pos
    data.qpos[root_qpos + 3: root_qpos + 7] = root_quat
    data.qvel[root_qvel: root_qvel + 6] = 0.0
    mujoco.mj_forward(model, data)

    model.eq_data[weld, 3:10] = relative_pose(
        parent_pos=data.xpos[ee_body],
        parent_quat=data.xquat[ee_body],
        parent_xmat=data.xmat[ee_body],
        child_pos=data.xpos[root_body],
        child_quat=data.xquat[root_body],
    )
    mujoco.mj_forward(model, data)

    return {
        "mount_site": mount_site,
        "mount_body": mount_body,
        "mount_offset": np.asarray(mount_offset, dtype=np.float64).round(6).tolist(),
        "mount_weld": mount_weld,
        "root_body": "rh_forearm",
        "mount_error": float(np.linalg.norm(target_pos - data.xpos[target_body])),
        "root_mount_error": float(np.linalg.norm(data.site_xpos[site] - data.xpos[root_body])),
        "root_world_position": data.xpos[root_body].astype(float).round(6).tolist(),
        "target_body_world_position": data.xpos[target_body].astype(float).round(6).tolist(),
        "target_mount_position": target_pos.astype(float).round(6).tolist(),
        "site_world_position": data.site_xpos[site].astype(float).round(6).tolist(),
        "weld_relpose": model.eq_data[weld, 3:10].astype(float).round(6).tolist(),
    }


def drive_demo_controls(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    groups: Dict[str, Dict[str, int]],
    sim_time: float,
    arm_scale: float,
    hand_close: float,
) -> None:
    """Drive a gentle inspection motion for the arm and temporary hand."""
    data.ctrl[:] = 0.0

    arm_pattern = (
        0.35 * math.sin(0.55 * sim_time),
        0.22 * math.sin(0.40 * sim_time + 0.7),
        -0.18 + 0.18 * math.sin(0.35 * sim_time + 1.4),
        0.28 * math.sin(0.65 * sim_time + 2.0),
    )
    for name, target in zip(ARM_ACTUATORS, arm_pattern):
        set_named_control(model, data, name, float(arm_scale) * target)

    for name in WRIST_ACTUATORS:
        set_named_control(model, data, name, 0.0)
    for name in WRAPPER_LOCK_ACTUATORS:
        set_named_control(model, data, name, 0.0)

    close = 0.5 - 0.5 * math.cos(0.95 * sim_time)
    close *= float(np.clip(hand_close, 0.0, 1.0))

    for name, idx in groups["finger_flexion"].items():
        low, high = control_bounds(model, idx)
        open_target = low if low >= 0.0 else 0.0
        close_target = open_target + (high - open_target) * 0.55
        data.ctrl[idx] = float(open_target + (close_target - open_target) * close)

    spread = 0.35 * math.sin(0.75 * sim_time)
    for name, idx in groups["finger_spread"].items():
        low, high = control_bounds(model, idx)
        data.ctrl[idx] = float(np.clip(spread * max(abs(low), abs(high)) * 0.35, low, high))


def tracked_body_positions(model: mujoco.MjModel, data: mujoco.MjData) -> Dict[str, List[float]]:
    """Return positions for key mount bodies."""
    return {
        name: data.xpos[body_id(model, name)].astype(float).round(6).tolist()
        for name in TRACKED_BODIES
    }


def configure_viewer_camera(viewer, model: mujoco.MjModel, data: mujoco.MjData) -> None:
    """Aim the passive viewer at the temporary mount area."""
    points = np.vstack([
        data.xpos[body_id(model, "ee_mount")],
        data.xpos[body_id(model, "rh_wrist")],
        data.xpos[body_id(model, "rh_palm")],
    ])
    center = points.mean(axis=0)
    extent = float(max(0.35, np.linalg.norm(points.max(axis=0) - points.min(axis=0)) * 1.7))
    viewer.cam.lookat[:] = center
    viewer.cam.distance = extent
    viewer.cam.azimuth = 215
    viewer.cam.elevation = -25


def build_summary(
    model_path: Path,
    model: mujoco.MjModel,
    data: mujoco.MjData,
    steps: int,
    elapsed: float,
    mount_info: Dict[str, object],
) -> Dict[str, object]:
    """Build a compact machine-readable run summary."""
    current_mount_error = 0.0
    mount_site = str(mount_info.get("mount_site", ""))
    mount_body = str(mount_info.get("mount_body", "rh_forearm"))
    mount_offset = np.asarray(mount_info.get("mount_offset", [0.0, 0.0, 0.0]), dtype=np.float64)
    if mount_site:
        site_xmat = data.site_xmat[site_id(model, mount_site)].reshape(3, 3)
        target_pos = data.site_xpos[site_id(model, mount_site)] + site_xmat @ mount_offset
        current_mount_error = float(
            np.linalg.norm(target_pos - data.xpos[body_id(model, mount_body)])
        )
    return {
        "model": str(model_path),
        "steps": int(steps),
        "elapsed_seconds": float(elapsed),
        "counts": {
            "nq": int(model.nq),
            "nv": int(model.nv),
            "nu": int(model.nu),
            "nbody": int(model.nbody),
            "neq": int(model.neq),
        },
        "tracked_body_positions": tracked_body_positions(model, data),
        "ctrl_min": float(np.min(data.ctrl)) if model.nu else 0.0,
        "ctrl_max": float(np.max(data.ctrl)) if model.nu else 0.0,
        "qpos_min": float(np.min(data.qpos)) if model.nq else 0.0,
        "qpos_max": float(np.max(data.qpos)) if model.nq else 0.0,
        "mount_info": mount_info,
        "current_mount_error": current_mount_error,
    }


def run_demo(args: argparse.Namespace) -> Dict[str, object]:
    """Run the combo inspection demo."""
    model_path = Path(args.model).resolve()
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    hidden_forearm_geoms = hide_shadow_forearm_shell(model) if args.hide_shadow_forearm else []
    mount_offset = parse_vec3(args.mount_offset, "--mount-offset")
    mount_info = configure_shadow_mount(model, data, args.mount_site, args.mount_body, mount_offset)
    mount_info["hidden_shadow_forearm_geoms"] = hidden_forearm_geoms

    groups = {
        "arm": actuator_ids(model, ARM_ACTUATORS),
        "finger_flexion": actuator_ids(model, FINGER_FLEXION_ACTUATORS),
        "finger_spread": actuator_ids(model, FINGER_SPREAD_ACTUATORS),
        "wrist": actuator_ids(model, WRIST_ACTUATORS),
        "wrapper_lock": actuator_ids(model, WRAPPER_LOCK_ACTUATORS),
    }
    for body_name in TRACKED_BODIES:
        body_id(model, body_name)

    viewer = None
    if not args.no_viewer:
        from mujoco import viewer as mujoco_viewer

        viewer = mujoco_viewer.launch_passive(model, data)
        configure_viewer_camera(viewer, model, data)
        print("Viewer started. Close the viewer window or press Ctrl+C to stop.")

    print("=" * 60)
    print("Stage-1 Arm + Shadow Combo Demo")
    print("=" * 60)
    print(f"Model: {model_path}")
    print(f"Steps: {args.steps}")
    print(f"Viewer: {'off' if args.no_viewer else 'on'}")
    print(
        f"Mount: {mount_info['mount_body']} -> {mount_info['mount_site']} "
        f"offset={mount_info['mount_offset']} | error={mount_info['mount_error']:.6f} m"
    )
    print(f"Shadow forearm shell: {'hidden' if args.hide_shadow_forearm else 'visible'}")
    print(f"Mount solve mode: {'kinematic visual re-project' if args.kinematic_mount else 'dynamic equality'}")
    print(f"Actuators: arm={len(groups['arm'])}, hand={len(groups['finger_flexion']) + len(groups['finger_spread'])}")
    print("Scope: structural motion check only, not a promoted training environment.")

    start = time.time()
    try:
        for step in range(args.steps):
            sim_time = step * model.opt.timestep
            drive_demo_controls(
                model,
                data,
                groups,
                sim_time=sim_time,
                arm_scale=args.arm_scale,
                hand_close=args.hand_close,
            )
            mujoco.mj_step(model, data)
            if args.kinematic_mount:
                configure_shadow_mount(model, data, args.mount_site, args.mount_body, mount_offset)

            if args.print_interval > 0 and (step == 0 or (step + 1) % args.print_interval == 0):
                positions = tracked_body_positions(model, data)
                print(
                    f"step={step + 1:5d} "
                    f"ctrl=[{float(np.min(data.ctrl)):.3f}, {float(np.max(data.ctrl)):.3f}] "
                    f"ee={positions['ee_mount']} palm={positions['rh_palm']}"
                )

            if viewer is not None:
                viewer.sync()
                if args.realtime:
                    time.sleep(max(0.0, model.opt.timestep / max(args.speed, 1e-6)))
    finally:
        if viewer is not None:
            viewer.close()

    elapsed = time.time() - start
    summary = build_summary(model_path, model, data, args.steps, elapsed, mount_info)
    print("\nSummary:")
    print(json.dumps(summary, indent=2))

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"Saved report: {report_path}")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage-1 arm plus Shadow hand combo demo")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Combo MJCF path")
    parser.add_argument("--steps", type=int, default=1200, help="Simulation steps")
    parser.add_argument("--no-viewer", action="store_true", help="Run without opening the viewer")
    parser.set_defaults(realtime=True)
    parser.add_argument("--realtime", dest="realtime", action="store_true", help="Sleep by model timestep when viewer is enabled")
    parser.add_argument("--no-realtime", dest="realtime", action="store_false", help="Run the viewer loop as fast as possible")
    parser.add_argument("--speed", type=float, default=1.0, help="Realtime speed scale")
    parser.add_argument("--arm-scale", type=float, default=1.0, help="Scale the arm inspection motion")
    parser.add_argument("--hand-close", type=float, default=1.0, help="Scale the hand open-close motion")
    parser.add_argument("--mount-site", default=DEFAULT_MOUNT_SITE, help="Arm-side site used to initialize the Shadow target body")
    parser.add_argument("--mount-body", default=DEFAULT_MOUNT_BODY, help="Shadow body aligned to the arm-side mount site")
    parser.add_argument(
        "--mount-offset",
        default=",".join(str(item) for item in DEFAULT_MOUNT_OFFSET),
        help="xyz offset in mount-site frame from site to target body",
    )
    parser.set_defaults(hide_shadow_forearm=True)
    parser.add_argument("--hide-shadow-forearm", dest="hide_shadow_forearm", action="store_true", help="Hide the temporary Shadow forearm shell")
    parser.add_argument("--show-shadow-forearm", dest="hide_shadow_forearm", action="store_false", help="Show the temporary Shadow forearm shell")
    parser.set_defaults(kinematic_mount=True)
    parser.add_argument("--kinematic-mount", dest="kinematic_mount", action="store_true", help="Re-project the temporary mount each step for visual inspection")
    parser.add_argument("--dynamic-mount", dest="kinematic_mount", action="store_false", help="Let the equality constraint solve the mount dynamically")
    parser.add_argument("--print-interval", type=int, default=100, help="Progress print interval; 0 disables")
    parser.add_argument("--report", default="", help="Optional JSON report path")
    args = parser.parse_args()

    run_demo(args)


if __name__ == "__main__":
    main()
