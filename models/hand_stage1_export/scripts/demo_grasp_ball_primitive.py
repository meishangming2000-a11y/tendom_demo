from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from demo_grasp_ball_scripted import SCRIPTED_TARGETS, get_joint_map


ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "mjcf" / "scene_ball_primitive.xml"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
BALL_POSITION = [0.01, -0.045, 0.215]
BALL_RADIUS = 0.025

CONTROLLED_JOINTS = sorted(SCRIPTED_TARGETS)
FOUR_FINGER_JOINTS = sorted(name for name in SCRIPTED_TARGETS if not name.startswith("thumb_"))
THUMB_JOINTS = sorted(name for name in SCRIPTED_TARGETS if name.startswith("thumb_"))

STAGE_TARGETS = {
    "open_hand": {name: 0.0 for name in CONTROLLED_JOINTS},
    "approach_pre_shape": {
        **{name: 0.0 for name in CONTROLLED_JOINTS},
        "index_mcp_flex_joint": -0.04,
        "index_mcp_abd_joint": 0.16,
        "middle_mcp_flex_joint": 0.0,
        "middle_mcp_abd_joint": 0.18,
        "ring_mcp_flex_joint": 0.03,
        "ring_mcp_abd_joint": 0.18,
        "little_mcp_flex_joint": 0.06,
        "little_mcp_abd_joint": 0.16,
        "thumb_cmc_joint": 0.12,
        "thumb_mcp_joint": 0.10,
        "thumb_ip_joint": 0.08,
    },
    "close_four_fingers": {
        **{name: 0.0 for name in CONTROLLED_JOINTS},
        **{name: SCRIPTED_TARGETS[name] for name in FOUR_FINGER_JOINTS},
        "thumb_cmc_joint": 0.12,
        "thumb_mcp_joint": 0.10,
        "thumb_ip_joint": 0.08,
    },
    "close_thumb": dict(SCRIPTED_TARGETS),
    "hold": dict(SCRIPTED_TARGETS),
}

STAGE_ORDER = [
    "open_hand",
    "approach_pre_shape",
    "close_four_fingers",
    "close_thumb",
    "hold",
]


def clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def apply_targets(model, data, joint_map: dict[str, int], targets: dict[str, float]) -> dict[str, float]:
    applied = {}
    for name, target in targets.items():
        jid = joint_map.get(name)
        if jid is None:
            continue
        adr = int(model.jnt_qposadr[jid])
        lower, upper = [float(v) for v in model.jnt_range[jid]]
        value = clamp(float(target), lower, upper)
        data.qpos[adr] = value
        applied[name] = value
    return applied


def blend_targets(start: dict[str, float], end: dict[str, float], fraction: float) -> dict[str, float]:
    names = sorted(set(start) | set(end))
    return {
        name: float(start.get(name, 0.0)) + (float(end.get(name, 0.0)) - float(start.get(name, 0.0))) * fraction
        for name in names
    }


def print_stage(stage_name: str, targets: dict[str, float]) -> None:
    print(f"\n[{stage_name}] target joint angles (rad)")
    for name in sorted(targets):
        print(f"  {name}: {targets[name]: .4f}")


def set_ball_position(model, data, mujoco, position: list[float]) -> None:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_freejoint")
    if joint_id < 0:
        return
    adr = int(model.jnt_qposadr[joint_id])
    data.qpos[adr : adr + 3] = position
    data.qpos[adr + 3 : adr + 7] = [1.0, 0.0, 0.0, 0.0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Primitive hand_stage1 scripted ball-grasp demo.")
    parser.add_argument("--viewer", action="store_true", help="Open an interactive MuJoCo viewer.")
    parser.add_argument("--steps-per-stage", type=int, default=50, help="Interpolation steps for each scripted stage.")
    parser.add_argument("--steps", type=int, default=None, help="Compatibility alias for --steps-per-stage.")
    parser.add_argument("--sleep", type=float, default=0.01, help="Sleep between viewer frames.")
    parser.add_argument("--ball-x", type=float, default=BALL_POSITION[0], help="Ball x position in world coordinates.")
    parser.add_argument("--ball-y", type=float, default=BALL_POSITION[1], help="Ball y position in world coordinates.")
    parser.add_argument("--ball-z", type=float, default=BALL_POSITION[2], help="Ball z position in world coordinates.")
    args = parser.parse_args()
    steps_per_stage = args.steps if args.steps is not None else args.steps_per_stage
    ball_position = [args.ball_x, args.ball_y, args.ball_z]

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        import mujoco
    except Exception as exc:
        report = {"load_success": False, "error": f"mujoco import failed: {type(exc).__name__}: {exc}"}
        write_report(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    try:
        model = mujoco.MjModel.from_xml_path(str(SCENE_XML))
        data = mujoco.MjData(model)
    except Exception as exc:
        report = {"load_success": False, "error": f"primitive scene load failed: {type(exc).__name__}: {exc}"}
        write_report(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    joint_map = get_joint_map(model, mujoco)
    missing_targets = sorted(set(SCRIPTED_TARGETS) - set(joint_map))
    applied_targets = {}
    set_ball_position(model, data, mujoco, ball_position)
    viewer = None
    if args.viewer:
        try:
            import mujoco.viewer

            viewer = mujoco.viewer.launch_passive(model, data)
        except Exception as exc:
            print(f"Viewer launch failed; continuing headless. Reason: {type(exc).__name__}: {exc}")

    stage_history = []
    previous_targets = {name: 0.0 for name in CONTROLLED_JOINTS}
    for stage_name in STAGE_ORDER:
        stage_targets = STAGE_TARGETS[stage_name]
        print_stage(stage_name, stage_targets)
        for step in range(steps_per_stage + 1):
            fraction = step / max(steps_per_stage, 1)
            targets = blend_targets(previous_targets, stage_targets, fraction)
            applied_targets = apply_targets(model, data, joint_map, targets)
            set_ball_position(model, data, mujoco, ball_position)
            mujoco.mj_forward(model, data)
            if viewer is not None:
                viewer.sync()
                time.sleep(args.sleep)
        stage_history.append({"stage": stage_name, "targets": dict(stage_targets), "applied": dict(applied_targets)})
        previous_targets = dict(stage_targets)

    if viewer is not None:
        print("Final primitive scripted grasp pose reached. Close the viewer window to exit.")
        while viewer.is_running():
            viewer.sync()
            time.sleep(args.sleep)
        viewer.close()

    ball_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    ball_xpos = data.xpos[ball_id].tolist() if ball_id >= 0 else None
    site_names = [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_SITE, sid) or f"site_{sid}"
        for sid in range(model.nsite)
    ]
    report = {
        "scene": str(SCENE_XML),
        "load_success": True,
        "viewer_requested": args.viewer,
        "ball_position_configured": ball_position,
        "ball_radius": BALL_RADIUS,
        "ball_xpos_after_forward": ball_xpos,
        "target_angles_requested": SCRIPTED_TARGETS,
        "target_angles_applied": applied_targets,
        "stage_order": STAGE_ORDER,
        "stage_history": stage_history,
        "steps_per_stage": steps_per_stage,
        "missing_target_joints": missing_targets,
        "site_names": site_names,
        "visual_grasp_status": "approximate_wrap_visible_in_primitive_skeleton",
        "notes": [
            "This primitive demo does not use suspicious STL meshes.",
            "No RL, tendon routing, or actuator controller is used; qpos is interpolated directly through scripted stages.",
            "The demo validates joint-tree and scripted pose logic only, not final CAD appearance.",
            "TODO: manually confirm MCP flex/abd semantics and thumb opposition direction.",
        ],
    }
    write_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def write_report(report: dict) -> None:
    (METADATA_DIR / "primitive_scripted_grasp_ball.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Primitive Scripted Grasp Ball Report",
        "",
        f"- Scene: `{report.get('scene', SCENE_XML)}`",
        f"- Load success: {'yes' if report.get('load_success') else 'no'}",
    ]
    if report.get("error"):
        lines.append(f"- Error: `{report['error']}`")
    lines.extend(
        [
            f"- Ball position: `{report.get('ball_position_configured', BALL_POSITION)}`",
            f"- Ball radius: {report.get('ball_radius', BALL_RADIUS)} m",
            f"- Visual grasp status: {report.get('visual_grasp_status', 'not_checked')}",
            f"- Steps per stage: {report.get('steps_per_stage', 'unknown')}",
            "",
            "## Stages",
            "",
        ]
    )
    for item in report.get("stage_history", []):
        lines.append(f"- `{item['stage']}`")
        for name, value in sorted(item.get("applied", {}).items()):
            lines.append(f"  - `{name}`: {value:.4g} rad")
    lines.extend(
        [
            "",
            "## Applied Joint Targets",
            "",
        ]
    )
    for name, value in sorted(report.get("target_angles_applied", {}).items()):
        lines.append(f"- `{name}`: {value:.4g} rad")
    lines.extend(["", "## Fingertip Sites", ""])
    lines.extend(f"- `{name}`" for name in report.get("site_names", []))
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report.get("notes", []))
    lines.append("")
    (DOCS_DIR / "primitive_scripted_grasp_ball_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
