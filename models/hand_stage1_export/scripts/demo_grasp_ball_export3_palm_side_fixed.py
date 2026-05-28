from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import imageio.v2 as imageio

from export3_common import (
    CONTROLLED_JOINTS,
    DOCS_DIR,
    FOUR_FINGER_CLOSE_TARGETS,
    METADATA_DIR,
    STAGE_ORDER,
    STAGE_TO_FILE,
    THUMB_CLOSE_TARGETS,
    actuator_map,
    blend,
    joint_map,
    load_model,
    set_ball_position,
    set_ctrl,
    stage_summary,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]
SCENE_XML = ROOT / "mjcf" / "scene_ball_export3_palm_side_fixed.xml"
BALL_POSITION = [0.0, 0.045, 0.22]
DEFAULT_FINGER_SCALE = 1.30
REPORT_MD = DOCS_DIR / "export3_palm_side_fixed_grasp_report.md"
REPORT_JSON = METADATA_DIR / "export3_palm_side_fixed_grasp.json"
OUT_DIR = DOCS_DIR / "visual_checks_export3_palm_side_fixed_grasp"


FREE_CAMERAS = {
    "palm_side": {"lookat": [0.0, 0.035, 0.21], "distance": 0.34, "azimuth": 180.0, "elevation": -33.0},
    "palm_side_high": {"lookat": [0.0, 0.035, 0.21], "distance": 0.34, "azimuth": 180.0, "elevation": -58.0},
}


def render_free_png(model, data, mujoco, camera_name: str, output: Path, width: int = 1200, height: int = 850) -> dict:
    cfg = FREE_CAMERAS[camera_name]
    output.parent.mkdir(parents=True, exist_ok=True)
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = cfg["lookat"]
    camera.distance = cfg["distance"]
    camera.azimuth = cfg["azimuth"]
    camera.elevation = cfg["elevation"]
    renderer = mujoco.Renderer(model, width=width, height=height)
    try:
        renderer.update_scene(data, camera=camera)
        image = renderer.render()
    finally:
        renderer.close()
    imageio.imwrite(output, image)
    return {
        "file": str(output),
        "camera": camera_name,
        "shape": list(image.shape),
        "min_pixel": int(image.min()),
        "max_pixel": int(image.max()),
        "mean_pixel": float(image.mean()),
    }


def full_stage_targets(stage: str, finger_scale: float) -> dict[str, float]:
    targets = {name: 0.0 for name in CONTROLLED_JOINTS}
    if stage == "open_hand":
        return targets
    if stage == "approach_pre_shape":
        for name, value in FOUR_FINGER_CLOSE_TARGETS.items():
            targets[name] = value * 0.32 * finger_scale
        for name, value in THUMB_CLOSE_TARGETS.items():
            targets[name] = value * 0.20
        return targets
    if stage == "close_four_fingers":
        for name, value in FOUR_FINGER_CLOSE_TARGETS.items():
            targets[name] = value * finger_scale
        for name, value in THUMB_CLOSE_TARGETS.items():
            targets[name] = value * 0.20
        return targets
    if stage in {"close_thumb", "hold"}:
        for name, value in FOUR_FINGER_CLOSE_TARGETS.items():
            targets[name] = value * finger_scale
        targets.update(THUMB_CLOSE_TARGETS)
        return targets
    raise KeyError(stage)


def write_outputs(report: dict) -> None:
    write_json(REPORT_JSON, report)
    lines = [
        "# Export3 Palm-Side Fixed Grasp Report",
        "",
        f"- Scene: `{report.get('scene')}`",
        f"- Load success: {'yes' if report.get('load_success') else 'no'}",
    ]
    if report.get("error"):
        lines.append(f"- Error: `{report['error']}`")
    lines.extend(
        [
            f"- Ball position: `{report.get('ball_position')}`",
            f"- Finger close scale: {report.get('finger_scale')}",
            f"- Actuator count: {report.get('actuator_count')}",
            f"- Missing actuators: {report.get('missing_actuators') or 'None'}",
            "",
            "## Stage Summary",
            "",
            "| Stage | Contacts | Max penetration (m) | Mean 4-tip dist (m) | Thumb-ball (m) | Thumb-index (m) |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for stage in report.get("stage_order", []):
        item = report.get("stage_reports", {}).get(stage, {})
        lines.append(
            f"| {stage} | {item.get('ball_contact_count', 'N/A')} | {item.get('max_penetration', 0.0):.6f} | "
            f"{item.get('mean_four_tip_distance', 0.0):.6f} | {item.get('thumb_to_ball', 0.0):.6f} | {item.get('thumb_to_index', 0.0):.6f} |"
        )
    lines.extend(["", "## Renders", ""])
    for item in report.get("renders", []):
        lines.append(f"- `{item['file']}` camera=`{item['camera']}` mean_pixel={item['mean_pixel']:.2f}")
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {line}" for line in report.get("interpretation", []))
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def interpret(report: dict) -> list[str]:
    lines = [
        "This run uses the palm-side fixed export3 scene: ball at positive Y and long-finger closure axes negated in the experimental hand MJCF.",
        "The default ball is not the full mirror Y=+0.1; a small sweep found Y=+0.045, Z=0.22 to be inside the four-finger wrap region.",
        "CAD, STL files, link tree, and joint names were not changed.",
        "Thumb tuning remains intentionally conservative in this run; the goal is to verify palm-side ball placement and long-finger closure direction.",
    ]
    stages = report.get("stage_reports", {})
    open_stage = stages.get("open_hand", {})
    hold = stages.get("hold", {})
    if open_stage.get("ball_contact_count", 0) == 0:
        lines.append("Open hand has no initial ball overlap at the corrected palm-side ball position.")
    else:
        lines.append("Open hand starts with ball contact; ball position or collision proxy still needs adjustment.")
    if hold.get("mean_four_tip_distance") is not None:
        lines.append(f"Hold mean four-fingertip distance is {hold['mean_four_tip_distance']:.4f} m.")
    if hold.get("ball_contact_count", 0) > 0:
        lines.append("The corrected scene produces ball contact during hold, so it is usable for the next visual sanity check.")
    else:
        lines.append("The corrected scene did not produce ball contact; inspect axis signs or ball position before continuing scripted grasp work.")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Export3 palm-side fixed position-control scripted ball grasp.")
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--ball-x", type=float, default=BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=BALL_POSITION[2])
    parser.add_argument("--finger-scale", type=float, default=DEFAULT_FINGER_SCALE)
    parser.add_argument("--scene", type=Path, default=SCENE_XML)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--hold-steps", type=int, default=300)
    parser.add_argument("--no-screenshots", action="store_true")
    args = parser.parse_args()

    ball_position = [args.ball_x, args.ball_y, args.ball_z]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        mujoco, model, data = load_model(args.scene)
    except Exception as exc:
        report = {"load_success": False, "scene": str(args.scene), "error": f"{type(exc).__name__}: {exc}"}
        write_outputs(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    model.opt.gravity[:] = 0.0
    act_map = actuator_map(model, mujoco)
    joints = joint_map(model, mujoco)
    missing_actuators = sorted(set(CONTROLLED_JOINTS) - set(act_map))
    set_ball_position(model, data, mujoco, ball_position)
    set_ctrl(model, data, full_stage_targets("open_hand", args.finger_scale), act_map)
    mujoco.mj_forward(model, data)

    viewer = None
    if args.viewer:
        try:
            import mujoco.viewer

            viewer = mujoco.viewer.launch_passive(model, data)
        except Exception as exc:
            print(f"Viewer launch failed; continuing headless. Reason: {type(exc).__name__}: {exc}")

    stage_steps = max(20, int(400 / max(args.speed, 0.05)))
    previous = full_stage_targets("open_hand", args.finger_scale)
    stage_reports = {}
    renders = []
    for stage in STAGE_ORDER:
        targets = full_stage_targets(stage, args.finger_scale)
        steps = args.hold_steps if stage == "hold" else stage_steps
        applied = {}
        print(f"\n[{stage}] target joint angles (rad)")
        for name in CONTROLLED_JOINTS:
            print(f"  {name}: {targets.get(name, 0.0): .4f}")
        for step in range(steps):
            command = blend(previous, targets, (step + 1) / max(steps, 1))
            applied = set_ctrl(model, data, command, act_map)
            set_ball_position(model, data, mujoco, ball_position)
            mujoco.mj_step(model, data)
            if viewer is not None:
                viewer.sync()
                time.sleep(0.002)
        set_ball_position(model, data, mujoco, ball_position)
        mujoco.mj_forward(model, data)
        stage_reports[stage] = stage_summary(model, data, mujoco, joints, targets, applied)
        if not args.no_screenshots:
            renders.append(render_free_png(model, data, mujoco, "palm_side", OUT_DIR / STAGE_TO_FILE[stage], width=1200, height=850))
            if stage in {"close_four_fingers", "hold"}:
                renders.append(render_free_png(model, data, mujoco, "palm_side_high", OUT_DIR / f"{stage}_palm_high.png", width=1200, height=850))
        previous = targets

    if viewer is not None:
        print("Palm-side fixed demo reached hold stage. Close the viewer window to exit.")
        while viewer.is_running():
            viewer.sync()
            time.sleep(0.01)
        viewer.close()

    report = {
        "load_success": True,
        "scene": str(args.scene),
        "ball_position": ball_position,
        "finger_scale": float(args.finger_scale),
        "actuator_count": int(model.nu),
        "missing_actuators": missing_actuators,
        "stage_order": STAGE_ORDER,
        "stage_reports": stage_reports,
        "renders": renders,
    }
    report["interpretation"] = interpret(report)
    write_outputs(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
