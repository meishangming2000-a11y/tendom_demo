#!/usr/bin/env python3
"""Open the experimental arm_stage1 + export4 hand assembly in MuJoCo viewer."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_SCENE = ROOT / "mjcf" / "scene_arm_hand_export4_collision_proxy_v2_ball.xml"


def main() -> None:
    parser = argparse.ArgumentParser(description="View the arm + export4 hand assembly.")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE), help="Combined arm-hand scene XML.")
    args = parser.parse_args()

    try:
        import mujoco
        import mujoco.viewer
    except Exception as exc:  # pragma: no cover - depends on local GUI install
        raise SystemExit(f"Failed to import mujoco viewer: {exc}") from exc

    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise SystemExit(f"Scene does not exist: {scene}")

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    joint_names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i) or f"joint_{i}"
        for i in range(model.njnt)
    ]
    actuator_names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) or f"actuator_{i}"
        for i in range(model.nu)
    ]

    print(f"Loaded: {scene}")
    print(
        "Model summary: "
        f"bodies={model.nbody}, joints={model.njnt}, actuators={model.nu}, "
        f"geoms={model.ngeom}, sites={model.nsite}, meshes={model.nmesh}"
    )
    print("Joints:")
    for name in joint_names:
        print(f"  - {name}")
    print("Actuators:")
    for name in actuator_names:
        print(f"  - {name}")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()


if __name__ == "__main__":
    main()
