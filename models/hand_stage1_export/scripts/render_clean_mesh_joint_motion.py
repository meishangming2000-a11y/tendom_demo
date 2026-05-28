from __future__ import annotations

import argparse
import json
from pathlib import Path

from clean_mesh_common import CLEAN_SCENE_XML, METADATA_DIR, VISUAL_CHECK_DIR, ensure_dirs, load_model, render_png, set_ball_position, write_json, BALL_POSITION


JOINTS_TO_RENDER = [
    "wrist_1_joint",
    "wrist_2_joint",
    "index_mcp_flex_joint",
    "index_mcp_abd_joint",
    "index_pip_joint",
    "index_dip_joint",
    "middle_mcp_flex_joint",
    "ring_mcp_flex_joint",
    "little_mcp_flex_joint",
    "thumb_cmc_joint",
    "thumb_mcp_joint",
    "thumb_ip_joint",
]

CAMERA_BY_JOINT = {
    "wrist_1_joint": "front",
    "wrist_2_joint": "front",
    "index_mcp_flex_joint": "index_finger_closeup",
    "index_mcp_abd_joint": "index_finger_closeup",
    "index_pip_joint": "index_finger_closeup",
    "index_dip_joint": "index_finger_closeup",
    "middle_mcp_flex_joint": "finger_root_closeup",
    "ring_mcp_flex_joint": "finger_root_closeup",
    "little_mcp_flex_joint": "finger_root_closeup",
    "thumb_cmc_joint": "thumb_root_closeup",
    "thumb_mcp_joint": "thumb_root_closeup",
    "thumb_ip_joint": "thumb_root_closeup",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Render before/after frames for selected clean mesh joints.")
    parser.add_argument("--angle", type=float, default=0.2)
    args = parser.parse_args()

    ensure_dirs()
    out_root = VISUAL_CHECK_DIR / "joint_motion"
    out_root.mkdir(parents=True, exist_ok=True)
    try:
        mujoco, model, data = load_model(CLEAN_SCENE_XML)
    except Exception as exc:
        report = {"load_success": False, "error": f"{type(exc).__name__}: {exc}", "scene": str(CLEAN_SCENE_XML)}
        write_json(METADATA_DIR / "clean_mesh_joint_motion_render_summary.json", report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    neutral_qpos = data.qpos.copy()
    renders = []
    for joint_name in JOINTS_TO_RENDER:
        joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        if joint_id < 0:
            renders.append({"joint": joint_name, "status": "missing_joint"})
            continue
        camera = CAMERA_BY_JOINT.get(joint_name, "front")
        joint_dir = out_root / joint_name
        joint_dir.mkdir(parents=True, exist_ok=True)

        data.qpos[:] = neutral_qpos
        set_ball_position(model, data, mujoco, BALL_POSITION)
        mujoco.mj_forward(model, data)
        before = render_png(model, data, mujoco, camera, joint_dir / "before.png", width=1050, height=760)

        data.qpos[:] = neutral_qpos
        adr = int(model.jnt_qposadr[joint_id])
        lower, upper = [float(v) for v in model.jnt_range[joint_id]]
        target = min(max(args.angle, lower), upper)
        data.qpos[adr] = target
        set_ball_position(model, data, mujoco, BALL_POSITION)
        mujoco.mj_forward(model, data)
        after = render_png(model, data, mujoco, camera, joint_dir / "after_positive_angle.png", width=1050, height=760)

        renders.append(
            {
                "joint": joint_name,
                "camera": camera,
                "target": target,
                "before": before,
                "after_positive_angle": after,
                "status": "rendered",
            }
        )

    report = {
        "scene": str(CLEAN_SCENE_XML),
        "load_success": True,
        "angle": args.angle,
        "renders": renders,
        "notes": [
            "These frames are for visual audit; script does not classify mechanical correctness.",
            "mcp_flex/mcp_abd semantic direction remains TODO and should not be renamed based on this script alone.",
        ],
    }
    write_json(METADATA_DIR / "clean_mesh_joint_motion_render_summary.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
