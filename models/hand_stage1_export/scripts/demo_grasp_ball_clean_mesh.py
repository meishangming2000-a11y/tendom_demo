from __future__ import annotations

import argparse
import json
import time

from clean_mesh_common import (
    BALL_POSITION,
    BALL_RADIUS,
    CLEAN_SCENE_XML,
    DOCS_DIR,
    METADATA_DIR,
    VISUAL_CHECK_DIR,
    apply_targets,
    ensure_dirs,
    load_model,
    render_png,
    set_ball_position,
    write_json,
)
from demo_grasp_ball_primitive import CONTROLLED_JOINTS, STAGE_ORDER, STAGE_TARGETS, blend_targets, print_stage


REPORT_MD = DOCS_DIR / "clean_mesh_grasp_visual_report.md"
REPORT_JSON = METADATA_DIR / "clean_mesh_grasp_demo.json"
OUT_DIR = VISUAL_CHECK_DIR / "grasp_demo"
STAGE_TO_FILE = {
    "open_hand": "open_hand.png",
    "approach_pre_shape": "preshape.png",
    "close_four_fingers": "four_fingers_closed.png",
    "close_thumb": "thumb_closed.png",
    "hold": "hold.png",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean mesh hand_stage1 scripted ball-grasp demo.")
    parser.add_argument("--viewer", action="store_true", help="Open an interactive MuJoCo viewer.")
    parser.add_argument("--steps-per-stage", type=int, default=50)
    parser.add_argument("--steps", type=int, default=None, help="Compatibility alias for --steps-per-stage.")
    parser.add_argument("--sleep", type=float, default=0.01)
    parser.add_argument("--ball-x", type=float, default=BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=BALL_POSITION[2])
    parser.add_argument("--no-screenshots", action="store_true")
    args = parser.parse_args()
    steps_per_stage = args.steps if args.steps is not None else args.steps_per_stage
    ball_position = [args.ball_x, args.ball_y, args.ball_z]

    ensure_dirs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        mujoco, model, data = load_model(CLEAN_SCENE_XML)
    except Exception as exc:
        report = {"load_success": False, "error": f"{type(exc).__name__}: {exc}", "scene": str(CLEAN_SCENE_XML)}
        write_outputs(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    viewer = None
    if args.viewer:
        try:
            import mujoco.viewer

            viewer = mujoco.viewer.launch_passive(model, data)
        except Exception as exc:
            print(f"Viewer launch failed; continuing headless. Reason: {type(exc).__name__}: {exc}")

    stage_history = []
    renders = []
    previous_targets = {name: 0.0 for name in CONTROLLED_JOINTS}
    for stage_name in STAGE_ORDER:
        stage_targets = STAGE_TARGETS[stage_name]
        print_stage(stage_name, stage_targets)
        applied = {}
        for step in range(steps_per_stage + 1):
            fraction = step / max(steps_per_stage, 1)
            targets = blend_targets(previous_targets, stage_targets, fraction)
            applied = apply_targets(model, data, mujoco, targets)
            set_ball_position(model, data, mujoco, ball_position)
            mujoco.mj_forward(model, data)
            if viewer is not None:
                viewer.sync()
                time.sleep(args.sleep)
        if not args.no_screenshots:
            filename = STAGE_TO_FILE.get(stage_name, f"{stage_name}.png")
            renders.append(render_png(model, data, mujoco, "full_hand_with_ball", OUT_DIR / filename, width=1200, height=850))
        stage_history.append({"stage": stage_name, "targets": dict(stage_targets), "applied": dict(applied)})
        previous_targets = dict(stage_targets)

    if viewer is not None:
        print("Final clean mesh scripted pose reached. Close the viewer window to exit.")
        while viewer.is_running():
            viewer.sync()
            time.sleep(args.sleep)
        viewer.close()

    report = {
        "scene": str(CLEAN_SCENE_XML),
        "load_success": True,
        "ball_position_configured": ball_position,
        "ball_radius": BALL_RADIUS,
        "stage_order": STAGE_ORDER,
        "stage_history": stage_history,
        "renders": renders,
        "steps_per_stage": steps_per_stage,
        "visual_grasp_status": "pending_visual_review",
        "notes": [
            "This clean mesh demo reuses the primitive staged qpos target logic.",
            "No RL, tendon routing, actuator controller, or joint-tree edits are used.",
            "Clean mesh geoms are visual-only and still require alignment review.",
        ],
    }
    write_outputs(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def write_outputs(report: dict) -> None:
    write_json(REPORT_JSON, report)
    lines = [
        "# Clean Mesh Grasp Visual Report",
        "",
        f"- Scene: `{report.get('scene', CLEAN_SCENE_XML)}`",
        f"- Load success: {'yes' if report.get('load_success') else 'no'}",
    ]
    if report.get("error"):
        lines.append(f"- Error: `{report['error']}`")
    lines.extend(
        [
            f"- Ball position: `{report.get('ball_position_configured', BALL_POSITION)}`",
            f"- Ball radius: {report.get('ball_radius', BALL_RADIUS)} m",
            f"- Visual grasp status: {report.get('visual_grasp_status', 'pending_visual_review')}",
            f"- Steps per stage: {report.get('steps_per_stage', 'unknown')}",
            "",
            "## Rendered Stages",
            "",
        ]
    )
    for item in report.get("renders", []):
        lines.append(f"- `{item['file']}` camera=`{item['camera']}` mean_pixel={item['mean_pixel']:.2f}")
    lines.extend(["", "## Applied Stages", ""])
    for item in report.get("stage_history", []):
        lines.append(f"- `{item['stage']}`")
        for name, value in sorted(item.get("applied", {}).items()):
            lines.append(f"  - `{name}`: {value:.4g} rad")
    lines.extend(["", "## Visual Review", ""])
    lines.extend(
        [
            "- TODO: inspect rendered stage screenshots for ball wrapping, fingertip distance, palm support, thumb opposition, and obvious penetration.",
            "- TODO: if clean mesh alignment is FAIL/BLOCKER, treat this demo as scripted-control-only and do not promote clean mesh visuals.",
        ]
    )
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report.get("notes", []))
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
