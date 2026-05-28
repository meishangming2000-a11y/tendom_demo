from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "mjcf" / "scene_ball.xml"
DOCS_DIR = ROOT / "docs"
METADATA_DIR = ROOT / "metadata"
BALL_POSITION = [0.01, -0.045, 0.215]
BALL_RADIUS = 0.025


SCRIPTED_TARGETS = {
    "index_mcp_flex_joint": -0.08,
    "index_mcp_abd_joint": 0.45,
    "index_pip_joint": 0.65,
    "index_dip_joint": 0.35,
    "middle_mcp_flex_joint": 0.0,
    "middle_mcp_abd_joint": 0.50,
    "middle_pip_joint": 0.70,
    "middle_dip_joint": 0.38,
    "ring_mcp_flex_joint": 0.04,
    "ring_mcp_abd_joint": 0.50,
    "ring_pip_joint": 0.70,
    "ring_dip_joint": 0.38,
    "little_mcp_flex_joint": 0.08,
    "little_mcp_abd_joint": 0.45,
    "little_pip_joint": 0.65,
    "little_dip_joint": 0.35,
    "thumb_cmc_joint": 0.25,
    "thumb_mcp_joint": 0.45,
    "thumb_ip_joint": 0.35,
}


def clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def get_joint_map(model, mujoco) -> dict[str, int]:
    mapping = {}
    for jid in range(model.njnt):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
        if name:
            mapping[name] = jid
    return mapping


def apply_fraction(model, data, joint_map: dict[str, int], targets: dict[str, float], fraction: float) -> dict[str, float]:
    applied = {}
    for name, target in targets.items():
        jid = joint_map.get(name)
        if jid is None:
            continue
        adr = int(model.jnt_qposadr[jid])
        lower, upper = [float(v) for v in model.jnt_range[jid]]
        value = clamp(target * fraction, lower, upper)
        data.qpos[adr] = value
        applied[name] = value
    return applied


def main() -> int:
    parser = argparse.ArgumentParser(description="Scripted hand_stage1 ball grasp demo.")
    parser.add_argument("--viewer", action="store_true", help="Open an interactive MuJoCo viewer while closing.")
    parser.add_argument("--steps", type=int, default=160, help="Number of interpolation steps.")
    parser.add_argument("--sleep", type=float, default=0.01, help="Sleep between viewer frames.")
    args = parser.parse_args()

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
        report = {"load_success": False, "error": f"scene load failed: {type(exc).__name__}: {exc}"}
        write_report(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    joint_map = get_joint_map(model, mujoco)
    missing_targets = sorted(set(SCRIPTED_TARGETS) - set(joint_map))
    applied_targets = {}

    viewer = None
    if args.viewer:
        try:
            import mujoco.viewer

            viewer = mujoco.viewer.launch_passive(model, data)
        except Exception as exc:
            print(f"Viewer launch failed; continuing headless. Reason: {type(exc).__name__}: {exc}")
            viewer = None

    for step in range(args.steps + 1):
        fraction = step / max(args.steps, 1)
        applied_targets = apply_fraction(model, data, joint_map, SCRIPTED_TARGETS, fraction)
        mujoco.mj_forward(model, data)
        if viewer is not None:
            viewer.sync()
            time.sleep(args.sleep)

    if viewer is not None:
        print("Final scripted grasp pose reached. Close the viewer window to exit.")
        while viewer.is_running():
            viewer.sync()
            time.sleep(args.sleep)
        viewer.close()

    ball_body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ball")
    ball_xpos = data.xpos[ball_body_id].tolist() if ball_body_id >= 0 else None
    report = {
        "scene": str(SCENE_XML),
        "load_success": True,
        "viewer_requested": args.viewer,
        "ball_position_configured": BALL_POSITION,
        "ball_radius": BALL_RADIUS,
        "ball_xpos_after_forward": ball_xpos,
        "target_angles_requested": SCRIPTED_TARGETS,
        "target_angles_applied": applied_targets,
        "missing_target_joints": missing_targets,
        "visual_grasp_status": "approximate_wrap_visible_in_primitive_skeleton_renders",
        "notes": [
            "No RL, tendon routing, or actuator controller is used; the demo directly interpolates qpos.",
            "The pose uses small MCP side-motion values and moderate PIP/DIP closure to avoid explosive motion.",
            "Default scene uses primitive skeleton geoms because the exported STL meshes appear unsuitable as clean per-link visuals.",
            "See docs/renders/scripted_close_front.png, scripted_close_side.png, and scripted_close_top.png for fixed-camera checks.",
            "CAD/URDF current names mcp_flex and mcp_abd may need later review against actual motion-axis semantics.",
            "TODO: confirm whether any target signs should be flipped after visual inspection.",
            "TODO: tune ball position after viewing real palm/finger alignment.",
        ],
    }
    write_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def write_report(report: dict) -> None:
    (METADATA_DIR / "scripted_grasp_ball.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Scripted Grasp Ball Report",
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
            "",
            "## Applied Joint Targets",
            "",
        ]
    )
    for name, value in sorted(report.get("target_angles_applied", {}).items()):
        lines.append(f"- `{name}`: {value:.4g} rad")
    if report.get("missing_target_joints"):
        lines.extend(["", "## Missing Target Joints", ""])
        lines.extend(f"- `{name}`" for name in report["missing_target_joints"])
    lines.extend(["", "## Possible Direction/Axis Issues", ""])
    lines.extend(
        [
            "- TODO: visually confirm whether MCP flex/abd signs are correct; current names may not match actual motion semantics.",
            "- TODO: visually confirm whether any PIP/DIP axes are reversed.",
            "- TODO: visually confirm whether any link origin/scale causes penetration or offset around the ball.",
        ]
    )
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report.get("notes", []))
    lines.append("")
    (DOCS_DIR / "scripted_grasp_ball_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
