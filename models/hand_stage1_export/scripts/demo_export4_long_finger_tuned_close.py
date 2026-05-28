#!/usr/bin/env python3
"""Animate the export4 long-finger-tuned open/hook/close poses."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENE = ROOT / "mjcf" / "scene_export4_long_finger_tuned.xml"

NATURAL_CLOSE_TARGETS = {
    "index_mcp_flex_joint_pos": -0.06,
    "middle_mcp_flex_joint_pos": -0.06,
    "ring_mcp_flex_joint_pos": -0.05,
    "little_mcp_flex_joint_pos": -0.04,
    "index_mcp_abd_joint_pos": -0.58,
    "middle_mcp_abd_joint_pos": -0.64,
    "ring_mcp_abd_joint_pos": -0.62,
    "little_mcp_abd_joint_pos": -0.54,
    "index_pip_joint_pos": -0.82,
    "middle_pip_joint_pos": -0.88,
    "ring_pip_joint_pos": -0.84,
    "little_pip_joint_pos": -0.76,
    "index_dip_joint_pos": -0.42,
    "middle_dip_joint_pos": -0.46,
    "ring_dip_joint_pos": -0.44,
    "little_dip_joint_pos": -0.40,
}

HOOK_TARGETS = {
    "index_mcp_abd_joint_pos": -0.20,
    "middle_mcp_abd_joint_pos": -0.22,
    "ring_mcp_abd_joint_pos": -0.20,
    "little_mcp_abd_joint_pos": -0.18,
    "index_pip_joint_pos": -0.92,
    "middle_pip_joint_pos": -0.98,
    "ring_pip_joint_pos": -0.92,
    "little_pip_joint_pos": -0.84,
    "index_dip_joint_pos": -0.48,
    "middle_dip_joint_pos": -0.52,
    "ring_dip_joint_pos": -0.50,
    "little_dip_joint_pos": -0.46,
}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animate export4 long-finger tuned close")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--phase-steps", type=int, default=220)
    parser.add_argument("--hold-steps", type=int, default=240)
    parser.add_argument("--pose", choices=("natural", "hook"), default="natural")
    return parser


def _target_vector(model, names, pose: str) -> np.ndarray:
    targets = NATURAL_CLOSE_TARGETS if pose == "natural" else HOOK_TARGETS
    ctrl = np.zeros(model.nu, dtype=np.float64)
    for idx, name in enumerate(names):
        value = float(targets.get(name, 0.0))
        low, high = model.actuator_ctrlrange[idx]
        ctrl[idx] = float(np.clip(value, low, high))
    return ctrl


def main() -> None:
    args = build_arg_parser().parse_args()
    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise FileNotFoundError(scene)

    import mujoco

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, idx) or f"actuator_{idx}"
        for idx in range(model.nu)
    ]
    open_ctrl = np.zeros(model.nu, dtype=np.float64)
    close_ctrl = _target_vector(model, names, args.pose)

    print(f"Loaded: {scene}")
    print(f"pose={args.pose}; bodies={model.nbody}, joints={model.njnt}, actuators={model.nu}")
    print("Close targets:")
    for name, value in zip(names, close_ctrl):
        if abs(float(value)) > 1e-8:
            print(f"  {name}: {value:.4f}")

    viewer = None
    if args.viewer:
        import mujoco.viewer

        viewer = mujoco.viewer.launch_passive(model, data)

    try:
        for step in range(max(1, int(args.phase_steps))):
            phase = step / max(1, int(args.phase_steps) - 1)
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
