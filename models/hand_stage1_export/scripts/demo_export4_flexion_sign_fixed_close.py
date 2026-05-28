#!/usr/bin/env python3
"""Animate the experimental export4 flexion-sign-fixed open/close pose."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENE = ROOT / "mjcf" / "scene_export4_flexion_sign_fixed.xml"

FLEXION_ACTUATOR_KEYWORDS = (
    "_mcp_abd_joint_pos",
    "_pip_joint_pos",
    "_dip_joint_pos",
    "thumb_ip_joint_pos",
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animate export4 sign-fixed close pose")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--viewer", action="store_true", help="Open MuJoCo viewer")
    parser.add_argument("--steps", type=int, default=360)
    parser.add_argument("--hold-steps", type=int, default=240)
    parser.add_argument("--close-scale", type=float, default=0.75)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)

    import mujoco

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    actuator_names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, idx) or f"actuator_{idx}"
        for idx in range(model.nu)
    ]

    open_ctrl = np.zeros(model.nu, dtype=np.float64)
    close_ctrl = np.zeros(model.nu, dtype=np.float64)
    for idx, name in enumerate(actuator_names):
        low, high = model.actuator_ctrlrange[idx]
        if any(keyword in name for keyword in FLEXION_ACTUATOR_KEYWORDS):
            # In the sign-fixed model, long-finger closing ranges end at zero
            # and close toward the negative lower bound.
            close_ctrl[idx] = float(low) * float(args.close_scale) if low < 0.0 else float(high) * float(args.close_scale)
        elif name in {"thumb_cmc_abd_joint_pos", "thumb_cmc_joint_pos", "thumb_mcp_joint_pos"}:
            close_ctrl[idx] = 0.0

    print(f"Loaded: {scene}")
    print(f"bodies={model.nbody}, joints={model.njnt}, actuators={model.nu}, geoms={model.ngeom}, sites={model.nsite}")
    print("Non-zero close targets:")
    for name, value in zip(actuator_names, close_ctrl):
        if abs(float(value)) > 1e-8:
            print(f"  {name}: {value:.4f}")

    viewer = None
    if args.viewer:
        import mujoco.viewer

        viewer = mujoco.viewer.launch_passive(model, data)

    try:
        for step in range(max(1, int(args.steps))):
            phase = step / max(1, int(args.steps) - 1)
            data.ctrl[:] = (1.0 - phase) * open_ctrl + phase * close_ctrl
            mujoco.mj_step(model, data)
            if viewer:
                viewer.sync()
                time.sleep(0.01)
        for _ in range(max(0, int(args.hold_steps))):
            data.ctrl[:] = close_ctrl
            mujoco.mj_step(model, data)
            if viewer:
                viewer.sync()
                time.sleep(0.01)
    finally:
        if viewer:
            viewer.close()


if __name__ == "__main__":
    main()
