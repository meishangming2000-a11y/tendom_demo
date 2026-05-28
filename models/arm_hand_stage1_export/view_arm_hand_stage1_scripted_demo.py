#!/usr/bin/env python3
"""Interactive scripted close demo for the arm + export4 hand v1 scene.

The plain viewer is intentionally passive: gravity acts on the ball and no
hand target is applied. This demo pins the ball by default and drives the
position actuators through a small staged close sequence so the hand motion is
visible and repeatable.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
DEFAULT_SCENE = ROOT / "mjcf" / "scene_arm_hand_export4_collision_proxy_v2_ball.xml"

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

PHASES = [
    ("open_hand", {}),
    ("preshape", PRESHAPE_TARGETS),
    ("close_four_fingers", LONG_FINGER_TARGETS),
    ("close_thumb_smoke", {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}),
    ("hold", {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}),
]

TIP_SITES = {
    "index": "index_tip_site",
    "middle": "middle_tip_site",
    "ring": "ring_tip_site",
    "little": "little_tip_site",
    "thumb": "thumb_tip_site",
}


def names(model, mujoco, objtype, count: int, fallback: str) -> list[str]:
    return [mujoco.mj_id2name(model, objtype, i) or f"{fallback}_{i}" for i in range(count)]


def actuator_to_joint_name(actuator_name: str) -> str:
    if actuator_name.startswith("a_"):
        return actuator_name[2:]
    if actuator_name.endswith("_pos"):
        return actuator_name[:-4]
    return actuator_name


def ctrl_from_targets(model, mujoco, actuator_names: list[str], targets: dict[str, float]) -> np.ndarray:
    ctrl = np.zeros(model.nu, dtype=np.float64)
    for aid, actuator_name in enumerate(actuator_names):
        joint_name = actuator_to_joint_name(actuator_name)
        value = float(targets.get(joint_name, 0.0))
        if bool(model.actuator_ctrllimited[aid]):
            low, high = model.actuator_ctrlrange[aid]
            value = float(np.clip(value, low, high))
        ctrl[aid] = value
    return ctrl


def set_ball_pose(model, data, mujoco, ball_joint_id: int, ball_pos: np.ndarray) -> None:
    if ball_joint_id < 0:
        return
    qadr = int(model.jnt_qposadr[ball_joint_id])
    dadr = int(model.jnt_dofadr[ball_joint_id])
    data.qpos[qadr : qadr + 3] = ball_pos
    data.qpos[qadr + 3 : qadr + 7] = [1.0, 0.0, 0.0, 0.0]
    data.qvel[dadr : dadr + 6] = 0.0


def contact_summary(model, data, mujoco) -> tuple[int, int, float]:
    ball_hand = 0
    max_pen = 0.0
    for i in range(data.ncon):
        c = data.contact[i]
        geom_names = [
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(c.geom1)) or "",
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(c.geom2)) or "",
        ]
        body_names = [
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[int(c.geom1)])) or "",
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[int(c.geom2)])) or "",
        ]
        names_all = geom_names + body_names
        max_pen = max(max_pen, max(0.0, -float(c.dist)))
        if any("ball" in name for name in names_all) and any(
            key in name for name in names_all for key in ["palm", "finger", "thumb", "distal", "proximal", "wrist", "mcp", "hand_base"]
        ):
            ball_hand += 1
    return int(data.ncon), int(ball_hand), float(max_pen)


def fingertip_distances(model, data, mujoco, ball_body_id: int) -> dict[str, float]:
    if ball_body_id < 0:
        return {}
    ball = data.xpos[ball_body_id]
    out = {}
    for key, site_name in TIP_SITES.items():
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
        out[key] = float(np.linalg.norm(data.site_xpos[sid] - ball)) if sid >= 0 else float("nan")
    return out


def print_phase_status(model, data, mujoco, phase: str, ball_body_id: int) -> None:
    contacts, ball_hand, max_pen = contact_summary(model, data, mujoco)
    distances = fingertip_distances(model, data, mujoco, ball_body_id)
    four = [distances.get(name, np.nan) for name in ["index", "middle", "ring", "little"]]
    print(
        f"{phase}: contacts={contacts}, ball_hand={ball_hand}, "
        f"max_pen={max_pen:.6f}, four_avg={np.nanmean(four):.6f}, "
        f"thumb_ball={distances.get('thumb', float('nan')):.6f}"
    )


def run_demo(args) -> None:
    import mujoco

    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise SystemExit(f"Scene does not exist: {scene}")

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    actuator_names = names(model, mujoco, mujoco.mjtObj.mjOBJ_ACTUATOR, model.nu, "actuator")
    ball_joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_freejoint")
    ball_body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    mujoco.mj_forward(model, data)
    scene_ball = data.xpos[ball_body_id].copy() if ball_body_id >= 0 else np.zeros(3, dtype=np.float64)
    ball_pos = np.array(
        [
            scene_ball[0] if args.ball_x is None else args.ball_x,
            scene_ball[1] if args.ball_y is None else args.ball_y,
            scene_ball[2] if args.ball_z is None else args.ball_z,
        ],
        dtype=np.float64,
    )

    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0
    set_ball_pose(model, data, mujoco, ball_joint_id, ball_pos)
    mujoco.mj_forward(model, data)

    print(f"Loaded: {scene}")
    print(
        "Model summary: "
        f"bodies={model.nbody}, joints={model.njnt}, actuators={model.nu}, "
        f"geoms={model.ngeom}, sites={model.nsite}, meshes={model.nmesh}"
    )
    print(f"Ball pose: {ball_pos.tolist()}  pin_ball={not args.free_ball}")
    print("Actuators:")
    for name in actuator_names:
        print(f"  - {name}")

    viewer_ctx = None
    viewer = None
    if not args.no_viewer:
        import mujoco.viewer

        viewer_ctx = mujoco.viewer.launch_passive(model, data)
        viewer = viewer_ctx.__enter__()

    try:
        while True:
            for phase_name, targets in PHASES:
                target_ctrl = ctrl_from_targets(model, mujoco, actuator_names, targets)
                start_ctrl = data.ctrl.copy()
                seconds = args.hold_seconds if phase_name == "hold" else args.phase_seconds
                steps = max(1, int(seconds / max(model.opt.timestep, 1e-4)))
                print(f"\nPhase: {phase_name}")
                if targets:
                    for joint_name, value in sorted(targets.items()):
                        print(f"  {joint_name}: {value:+.3f}")
                for step in range(steps):
                    alpha = step / max(1, steps - 1)
                    data.ctrl[:] = (1.0 - alpha) * start_ctrl + alpha * target_ctrl
                    if not args.free_ball:
                        set_ball_pose(model, data, mujoco, ball_joint_id, ball_pos)
                    mujoco.mj_step(model, data)
                    if not args.free_ball:
                        set_ball_pose(model, data, mujoco, ball_joint_id, ball_pos)
                        mujoco.mj_forward(model, data)
                    if viewer is not None:
                        viewer.sync()
                        time.sleep(model.opt.timestep / max(args.speed, 1e-6))
                print_phase_status(model, data, mujoco, phase_name, ball_body_id)
                if viewer is not None and not viewer.is_running():
                    return
            if not args.loop or args.no_viewer:
                return
    finally:
        if viewer_ctx is not None:
            viewer_ctx.__exit__(None, None, None)


def main() -> None:
    parser = argparse.ArgumentParser(description="View a staged arm-hand scripted close on collision proxy v1.")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--ball-x", type=float, default=None, help="Override scene ball x position.")
    parser.add_argument("--ball-y", type=float, default=None, help="Override scene ball y position.")
    parser.add_argument("--ball-z", type=float, default=None, help="Override scene ball z position.")
    parser.add_argument("--speed", type=float, default=2.0, help="Playback speed multiplier.")
    parser.add_argument("--phase-seconds", type=float, default=1.0)
    parser.add_argument("--hold-seconds", type=float, default=2.0)
    parser.add_argument("--free-ball", action="store_true", help="Let gravity act on the ball instead of pinning it.")
    parser.add_argument("--loop", action="store_true", help="Loop phases until the viewer closes.")
    parser.add_argument("--no-viewer", action="store_true", help="Run once without opening a GUI.")
    args = parser.parse_args()
    run_demo(args)


if __name__ == "__main__":
    main()
