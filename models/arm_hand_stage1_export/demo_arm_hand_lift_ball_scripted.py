#!/usr/bin/env python3
"""Scripted arm+hand ball pickup/lift smoke demo.

This is a visual and physics-path smoke test, not a trained grasp policy.
By default the ball is softly assisted after grasp closure so the demo shows
the intended lift sequence. Use --pure-physics to disable that assist and see
whether the current collision proxy alone can lift the ball.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np


ROOT = Path(__file__).resolve().parent
DEFAULT_SCENE = ROOT / "mjcf" / "scene_arm_hand_export4_lift_ball_demo.xml"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
VIS = DOCS / "visual_checks_arm_hand_lift_ball_demo"
REPORT = DOCS / "arm_hand_lift_ball_demo_report.md"
META_OUT = META / "arm_hand_lift_ball_demo.json"

ARM_JOINTS = ("j1", "j2", "j3", "j4")
ARM_PRE_APPROACH = {
    "j1": 2.84112263,
    "j2": -1.10,
    "j3": 0.52568695,
    "j4": 2.63193073,
}
ARM_APPROACH = {
    "j1": 2.84112263,
    "j2": -1.54396031,
    "j3": 0.52568695,
    "j4": 2.63193073,
}
ARM_LIFT = {
    "j1": 2.84112263,
    "j2": -0.95,
    "j3": 0.52568695,
    "j4": 2.63193073,
}

PRESHAPE_TARGETS = {
    "index_mcp_flex_joint": -0.035,
    "middle_mcp_flex_joint": -0.035,
    "ring_mcp_flex_joint": -0.020,
    "little_mcp_flex_joint": -0.015,
    "index_mcp_abd_joint": -0.34,
    "middle_mcp_abd_joint": -0.38,
    "ring_mcp_abd_joint": -0.20,
    "little_mcp_abd_joint": -0.15,
    "index_pip_joint": -0.48,
    "middle_pip_joint": -0.52,
    "ring_pip_joint": -0.20,
    "little_pip_joint": -0.16,
    "index_dip_joint": -0.22,
    "middle_dip_joint": -0.24,
    "ring_dip_joint": -0.10,
    "little_dip_joint": -0.08,
}

LONG_FINGER_TARGETS = {
    "index_mcp_flex_joint": -0.06,
    "middle_mcp_flex_joint": -0.06,
    "ring_mcp_flex_joint": -0.05,
    "little_mcp_flex_joint": -0.04,
    "index_mcp_abd_joint": -0.58,
    "middle_mcp_abd_joint": -0.64,
    "ring_mcp_abd_joint": -0.62,
    "little_mcp_abd_joint": -0.54,
    "index_pip_joint": -0.82,
    "middle_pip_joint": -0.88,
    "ring_pip_joint": -0.84,
    "little_pip_joint": -0.76,
    "index_dip_joint": -0.42,
    "middle_dip_joint": -0.46,
    "ring_dip_joint": -0.44,
    "little_dip_joint": -0.40,
}

THUMB_SMOKE_TARGETS = {
    "thumb_cmc_abd_joint": -0.30,
    "thumb_cmc_joint": 0.0,
    "thumb_mcp_joint": 0.25,
    "thumb_ip_joint": -0.25,
}

TIP_SITES = {
    "index": "index_tip_site",
    "middle": "middle_tip_site",
    "ring": "ring_tip_site",
    "little": "little_tip_site",
    "thumb": "thumb_tip_site",
}

PALM_BALL_LOCAL = np.array([0.04, 0.12, -0.02], dtype=np.float64)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return value.item()
    return value


def name_or(model, mujoco, objtype, idx: int, fallback: str) -> str:
    return mujoco.mj_id2name(model, objtype, idx) or fallback


def actuator_to_joint_name(actuator_name: str) -> str:
    if actuator_name.startswith("a_"):
        return actuator_name[2:]
    if actuator_name.endswith("_pos"):
        return actuator_name[:-4]
    return actuator_name


def actuator_names(model, mujoco) -> list[str]:
    return [name_or(model, mujoco, mujoco.mjtObj.mjOBJ_ACTUATOR, i, f"actuator_{i}") for i in range(model.nu)]


def ctrl_from_targets(model, mujoco, names: list[str], targets: dict[str, float]) -> np.ndarray:
    ctrl = np.zeros(model.nu, dtype=np.float64)
    for aid, actuator_name in enumerate(names):
        joint_name = actuator_to_joint_name(actuator_name)
        value = float(targets.get(joint_name, 0.0))
        if bool(model.actuator_ctrllimited[aid]):
            low, high = model.actuator_ctrlrange[aid]
            value = float(np.clip(value, low, high))
        ctrl[aid] = value
    return ctrl


def joint_qadr(model, mujoco, joint_name: str) -> int:
    jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if jid < 0:
        raise KeyError(joint_name)
    return int(model.jnt_qposadr[jid])


def ball_indices(model, mujoco) -> tuple[int, int, int]:
    bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_freejoint")
    return bid, int(model.jnt_qposadr[jid]), int(model.jnt_dofadr[jid])


def set_ball_pose(model, data, mujoco, pos: np.ndarray) -> None:
    _, qadr, dadr = ball_indices(model, mujoco)
    data.qpos[qadr : qadr + 3] = pos
    data.qpos[qadr + 3 : qadr + 7] = [1, 0, 0, 0]
    data.qvel[dadr : dadr + 6] = 0.0


def palm_relative_ball_position(model, data, mujoco, local: np.ndarray = PALM_BALL_LOCAL) -> np.ndarray:
    palm = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    palm_pos = data.xpos[palm].copy()
    palm_mat = data.xmat[palm].reshape(3, 3).copy()
    return palm_pos + palm_mat @ local


def set_arm_qpos_and_ctrl(model, data, mujoco, targets: dict[str, float], names: list[str]) -> None:
    for joint, value in targets.items():
        data.qpos[joint_qadr(model, mujoco, joint)] = value
    data.ctrl[:] = ctrl_from_targets(model, mujoco, names, targets)


def contact_summary(model, data, mujoco) -> dict[str, Any]:
    rows = []
    ball_hand = 0
    ball_floor = 0
    max_pen = 0.0
    for i in range(data.ncon):
        c = data.contact[i]
        g1, g2 = int(c.geom1), int(c.geom2)
        b1, b2 = int(model.geom_bodyid[g1]), int(model.geom_bodyid[g2])
        geom1 = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_GEOM, g1, f"geom_{g1}")
        geom2 = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_GEOM, g2, f"geom_{g2}")
        body1 = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, b1, f"body_{b1}")
        body2 = name_or(model, mujoco, mujoco.mjtObj.mjOBJ_BODY, b2, f"body_{b2}")
        names = [geom1, geom2, body1, body2]
        pen = max(0.0, -float(c.dist))
        max_pen = max(max_pen, pen)
        has_ball = any("ball" in name for name in names)
        has_hand = any(key in name for name in names for key in ["palm", "finger", "thumb", "distal", "proximal", "wrist", "mcp", "hand_base"])
        has_floor = any("floor" in name for name in names)
        if has_ball and has_hand:
            ball_hand += 1
        if has_ball and has_floor:
            ball_floor += 1
        rows.append({"geom1": geom1, "geom2": geom2, "body1": body1, "body2": body2, "penetration": pen, "dist": float(c.dist)})
    rows.sort(key=lambda row: row["penetration"], reverse=True)
    return {
        "contact_count": int(data.ncon),
        "ball_hand_contact_count": int(ball_hand),
        "ball_floor_contact_count": int(ball_floor),
        "max_penetration": float(max_pen),
        "top_contacts": rows[:10],
    }


def fingertip_distances(model, data, mujoco) -> dict[str, float]:
    bid, _, _ = ball_indices(model, mujoco)
    ball = data.xpos[bid].copy()
    out = {}
    for key, site in TIP_SITES.items():
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site)
        out[key] = float(np.linalg.norm(data.site_xpos[sid] - ball)) if sid >= 0 else float("nan")
    return out


def scalar_metrics(model, data, mujoco, initial_ball: np.ndarray) -> dict[str, Any]:
    bid, _, _ = ball_indices(model, mujoco)
    ball = data.xpos[bid].copy()
    tips = fingertip_distances(model, data, mujoco)
    four = [tips[name] for name in ["index", "middle", "ring", "little"]]
    contact = contact_summary(model, data, mujoco)
    return {
        "ball_position": ball,
        "ball_lift_height": float(ball[2] - initial_ball[2]),
        "ball_displacement": float(np.linalg.norm(ball - initial_ball)),
        "contact": contact,
        "four_finger_avg_tip_ball_distance": float(np.mean(four)),
        "thumb_ball_distance": tips["thumb"],
    }


def render_frame(model, data, mujoco, path: Path, camera_name: str = "lift_demo_side") -> str:
    renderer = mujoco.Renderer(model, width=1280, height=900)
    try:
        if camera_name == "lift_demo_side":
            cam = mujoco.MjvCamera()
            mujoco.mjv_defaultFreeCamera(model, cam)
            palm = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
            ball, _, _ = ball_indices(model, mujoco)
            if palm >= 0 and ball >= 0:
                cam.lookat[:] = 0.52 * data.xpos[palm].copy() + 0.48 * data.xpos[ball].copy()
            elif palm >= 0:
                cam.lookat[:] = data.xpos[palm].copy()
            cam.distance = 0.44
            cam.azimuth = 180
            cam.elevation = -18
            renderer.update_scene(data, camera=cam)
        else:
            renderer.update_scene(data, camera=camera_name)
        img = renderer.render()
    except Exception:
        try:
            cam = mujoco.MjvCamera()
            mujoco.mjv_defaultFreeCamera(model, cam)
            ball, _, _ = ball_indices(model, mujoco)
            palm = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
            if palm >= 0 and ball >= 0:
                cam.lookat[:] = 0.52 * data.xpos[palm].copy() + 0.48 * data.xpos[ball].copy()
            elif palm >= 0:
                cam.lookat[:] = data.xpos[palm].copy()
            else:
                cam.lookat[:] = data.xpos[ball].copy()
            cam.distance = 0.44
            cam.azimuth = 180
            cam.elevation = -18
            renderer.update_scene(data, camera=cam)
            img = renderer.render()
        except Exception:
            cam = mujoco.MjvCamera()
            mujoco.mjv_defaultFreeCamera(model, cam)
            palm = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
            cam.lookat[:] = data.xpos[palm].copy()
            cam.distance = 0.55
            cam.azimuth = 205
            cam.elevation = -25
            renderer.update_scene(data, camera=cam)
            img = renderer.render()
    finally:
        renderer.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, img)
    return str(path)


def blend_targets(a: dict[str, float], b: dict[str, float], alpha: float) -> dict[str, float]:
    keys = set(a) | set(b)
    return {key: (1.0 - alpha) * float(a.get(key, 0.0)) + alpha * float(b.get(key, 0.0)) for key in keys}


def run_phase(
    model,
    data,
    mujoco,
    names: list[str],
    phase_name: str,
    start_targets: dict[str, float],
    end_targets: dict[str, float],
    steps: int,
    initial_ball: np.ndarray,
    *,
    assist_ball: bool,
    viewer=None,
    speed: float = 1.0,
) -> dict[str, Any]:
    for i in range(max(1, steps)):
        alpha = i / max(1, steps - 1)
        targets = blend_targets(start_targets, end_targets, alpha)
        data.ctrl[:] = ctrl_from_targets(model, mujoco, names, targets)
        if assist_ball:
            mujoco.mj_forward(model, data)
            set_ball_pose(model, data, mujoco, palm_relative_ball_position(model, data, mujoco))
        mujoco.mj_step(model, data)
        if assist_ball:
            mujoco.mj_forward(model, data)
            set_ball_pose(model, data, mujoco, palm_relative_ball_position(model, data, mujoco))
            mujoco.mj_forward(model, data)
        if viewer is not None:
            viewer.sync()
            time.sleep(model.opt.timestep / max(speed, 1e-6))
    return scalar_metrics(model, data, mujoco, initial_ball)


def run_demo(args) -> dict[str, Any]:
    import mujoco

    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    names = actuator_names(model, mujoco)

    mujoco.mj_forward(model, data)
    initial_ball = data.xpos[ball_indices(model, mujoco)[0]].copy()
    data.qpos[:] = model.qpos0
    data.qvel[:] = 0
    set_arm_qpos_and_ctrl(model, data, mujoco, ARM_PRE_APPROACH, names)
    set_ball_pose(model, data, mujoco, initial_ball)
    mujoco.mj_forward(model, data)

    viewer_ctx = None
    viewer = None
    if args.viewer:
        import mujoco.viewer

        viewer_ctx = mujoco.viewer.launch_passive(model, data)
        viewer = viewer_ctx.__enter__()

    VIS.mkdir(parents=True, exist_ok=True)
    phase_rows = []
    screenshots: dict[str, str] = {}
    mode_assisted = not args.pure_physics
    try:
        phases = [
            ("open_high", ARM_PRE_APPROACH, {**ARM_PRE_APPROACH}, args.settle_steps, False),
            ("approach_ball", ARM_PRE_APPROACH, {**ARM_APPROACH}, args.approach_steps, False),
            ("preshape", {**ARM_APPROACH}, {**ARM_APPROACH, **PRESHAPE_TARGETS}, args.hand_steps, False),
            ("close_four_fingers", {**ARM_APPROACH, **PRESHAPE_TARGETS}, {**ARM_APPROACH, **LONG_FINGER_TARGETS}, args.hand_steps, False),
            (
                "close_thumb",
                {**ARM_APPROACH, **LONG_FINGER_TARGETS},
                {**ARM_APPROACH, **LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS},
                args.hand_steps,
                mode_assisted,
            ),
            (
                "lift",
                {**ARM_APPROACH, **LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS},
                {**ARM_LIFT, **LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS},
                args.lift_steps,
                mode_assisted,
            ),
            (
                "hold_lift",
                {**ARM_LIFT, **LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS},
                {**ARM_LIFT, **LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS},
                args.hold_steps,
                mode_assisted,
            ),
        ]
        for idx, (name, start, end, steps, assist) in enumerate(phases):
            metrics = run_phase(
                model,
                data,
                mujoco,
                names,
                name,
                start,
                end,
                steps,
                initial_ball,
                assist_ball=assist,
                viewer=viewer,
                speed=args.speed,
            )
            phase_rows.append({"phase": name, "assist_ball": assist, "metrics": metrics})
            screenshots[name] = render_frame(model, data, mujoco, VIS / f"{idx:02d}_{name}.png", args.camera)
            print(
                f"{name}: assist={assist} contacts={metrics['contact']['ball_hand_contact_count']} "
                f"floor={metrics['contact']['ball_floor_contact_count']} lift={metrics['ball_lift_height']:.4f} "
                f"pen={metrics['contact']['max_penetration']:.6f}"
            )
            if viewer is not None and not viewer.is_running():
                break
    finally:
        if viewer_ctx is not None:
            viewer_ctx.__exit__(None, None, None)

    final = phase_rows[-1]["metrics"] if phase_rows else scalar_metrics(model, data, mujoco, initial_ball)
    success_smoke = bool(
        final["ball_lift_height"] >= args.success_lift_height
        and final["contact"]["ball_hand_contact_count"] >= 1
        and final["contact"]["max_penetration"] <= 0.015
    )
    if mode_assisted:
        status = "ASSISTED_VISUAL_PASS" if success_smoke else "ASSISTED_VISUAL_PARTIAL"
    else:
        status = "PURE_PHYSICS_PASS" if success_smoke else "PURE_PHYSICS_FAIL"

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": scene,
        "mode": "assisted_after_grasp" if mode_assisted else "pure_physics",
        "status": status,
        "camera": args.camera,
        "model_summary": {"nbody": model.nbody, "njnt": model.njnt, "nu": model.nu, "ngeom": model.ngeom, "nsite": model.nsite, "nmesh": model.nmesh},
        "arm_poses": {"pre_approach": ARM_PRE_APPROACH, "approach": ARM_APPROACH, "lift": ARM_LIFT},
        "initial_ball": initial_ball,
        "final_metrics": final,
        "phase_results": phase_rows,
        "screenshots": screenshots,
        "success_lift_height": args.success_lift_height,
        "training_used": False,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    META_OUT.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Arm-Hand Lift Ball Scripted Demo Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Mode: `{payload['mode']}`\n",
        f"- Status: **{payload['status']}**\n",
        f"- Render camera: `{payload.get('camera', 'unknown')}`\n",
        f"- Training used: **No**\n",
        f"- Model summary: `{json_ready(payload['model_summary'])}`\n\n",
        "## Interpretation\n\n",
    ]
    if payload["mode"] == "assisted_after_grasp":
        lines.append(
            "This run uses explicit ball pose assistance after the hand closes. It is a visual integration demo, not proof of pure physical grasp/lift.\n\n"
        )
    else:
        lines.append(
            "This run disables ball assistance and reports whether the current contact proxy can physically lift the ball.\n\n"
        )
    final = payload["final_metrics"]
    lines.extend(
        [
            "## Final Metrics\n\n",
            f"- Ball lift height: `{final['ball_lift_height']:.6f} m`\n",
            f"- Ball displacement: `{final['ball_displacement']:.6f} m`\n",
            f"- Ball-hand contacts: `{final['contact']['ball_hand_contact_count']}`\n",
            f"- Ball-floor contacts: `{final['contact']['ball_floor_contact_count']}`\n",
            f"- Max penetration: `{final['contact']['max_penetration']:.6f} m`\n",
            f"- Four-finger avg tip-ball distance: `{final['four_finger_avg_tip_ball_distance']:.6f} m`\n",
            f"- Thumb-ball distance: `{final['thumb_ball_distance']:.6f} m`\n\n",
            "## Phases\n\n",
            "| phase | assisted | ball lift | ball-hand contacts | ball-floor contacts | max penetration | four avg | thumb-ball |\n",
            "|---|---:|---:|---:|---:|---:|---:|---:|\n",
        ]
    )
    for row in payload["phase_results"]:
        m = row["metrics"]
        lines.append(
            f"| {row['phase']} | {int(row['assist_ball'])} | {m['ball_lift_height']:.4f} | "
            f"{m['contact']['ball_hand_contact_count']} | {m['contact']['ball_floor_contact_count']} | "
            f"{m['contact']['max_penetration']:.6f} | {m['four_finger_avg_tip_ball_distance']:.4f} | "
            f"{m['thumb_ball_distance']:.4f} |\n"
        )
    lines.extend(["\n## Screenshots\n\n"])
    for name, path in payload["screenshots"].items():
        lines.append(f"- `{name}`: `{path}`\n")
    lines.extend(
        [
            "\n## Next Steps\n\n",
            "- Run `--pure-physics` to quantify how far the current collision/friction model is from an unassisted lift.\n",
            "- If pure physics fails, tune fingertip/thumb/palm collision and friction with a wider ball pose sweep.\n",
            "- Do not use this as training evidence until pure physics lift criteria are meaningful.\n",
        ]
    )
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scripted arm+hand ball pickup/lift smoke demo.")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--pure-physics", action="store_true", help="Disable post-grasp ball assistance.")
    parser.add_argument("--camera", default="lift_demo_side")
    parser.add_argument("--speed", type=float, default=2.0)
    parser.add_argument("--settle-steps", type=int, default=80)
    parser.add_argument("--approach-steps", type=int, default=180)
    parser.add_argument("--hand-steps", type=int, default=120)
    parser.add_argument("--lift-steps", type=int, default=220)
    parser.add_argument("--hold-steps", type=int, default=120)
    parser.add_argument("--success-lift-height", type=float, default=0.08)
    args = parser.parse_args()
    payload = run_demo(args)
    write_outputs(payload)
    print(f"Status: {payload['status']}")
    print(f"Report: {REPORT}")
    print(f"Metadata: {META_OUT}")


if __name__ == "__main__":
    main()
