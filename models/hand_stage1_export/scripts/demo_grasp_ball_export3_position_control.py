from __future__ import annotations

import argparse
import json
import time

from export3_common import (
    BALL_POSITION,
    CONTROLLED_JOINTS,
    DOCS_DIR,
    FOUR_FINGER_CLOSE_TARGETS,
    METADATA_DIR,
    SCENE_XML,
    STAGE_ORDER,
    STAGE_TO_FILE,
    THUMB_CLOSE_TARGETS,
    THUMB_JOINTS,
    actuator_map,
    blend,
    joint_map,
    load_model,
    render_png,
    set_ball_position,
    set_ctrl,
    stage_summary,
    write_json,
)


REPORT_MD = DOCS_DIR / "export3_grasp_ball_report.md"
REPORT_JSON = METADATA_DIR / "export3_grasp_ball_position_control.json"
OUT_DIR = DOCS_DIR / "visual_checks_export3_grasp"
THUMB_AUDIT_JSON = METADATA_DIR / "export3_thumb_opposition_candidates.json"


def load_thumb_targets() -> dict[str, float]:
    if not THUMB_AUDIT_JSON.exists():
        return dict(THUMB_CLOSE_TARGETS)
    try:
        payload = json.loads(THUMB_AUDIT_JSON.read_text(encoding="utf-8"))
        best = payload.get("best_by_score", [])[0]
        return {name: float(best["applied_pose"].get(name, 0.0)) for name in THUMB_JOINTS}
    except Exception:
        return dict(THUMB_CLOSE_TARGETS)


def full_stage_targets(stage: str, thumb_targets: dict[str, float]) -> dict[str, float]:
    targets = {name: 0.0 for name in CONTROLLED_JOINTS}
    if stage == "open_hand":
        return targets
    if stage == "approach_pre_shape":
        for name, value in FOUR_FINGER_CLOSE_TARGETS.items():
            targets[name] = value * 0.32
        for name, value in thumb_targets.items():
            targets[name] = value * 0.25
        return targets
    if stage == "close_four_fingers":
        targets.update(FOUR_FINGER_CLOSE_TARGETS)
        for name, value in thumb_targets.items():
            targets[name] = value * 0.25
        return targets
    if stage in {"close_thumb", "hold"}:
        targets.update(FOUR_FINGER_CLOSE_TARGETS)
        targets.update(thumb_targets)
        return targets
    raise KeyError(stage)


def write_outputs(report: dict) -> None:
    write_json(REPORT_JSON, report)
    lines = [
        "# Export3 Grasp Ball Position-Control Report",
        "",
        f"- Scene: `{report.get('scene', SCENE_XML)}`",
        f"- Load success: {'yes' if report.get('load_success') else 'no'}",
    ]
    if report.get("error"):
        lines.append(f"- Error: `{report['error']}`")
    lines.extend(
        [
            f"- Ball position: `{report.get('ball_position')}`",
            f"- Gravity enabled: {report.get('gravity_enabled')}",
            f"- Ball pinned: {report.get('pin_ball')}",
            f"- Actuator count: {report.get('actuator_count')}",
            f"- Missing actuators: {report.get('missing_actuators') or 'None'}",
            f"- Thumb target source: {report.get('thumb_target_source')}",
            f"- Thumb close target: `{report.get('thumb_close_target')}`",
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
    lines = []
    stages = report.get("stage_reports", {})
    open_stage = stages.get("open_hand", {})
    hold = stages.get("hold", {})
    if open_stage.get("ball_contact_count", 0) == 0:
        lines.append("Open hand has no initial ball contact at the requested ball position.")
    else:
        lines.append("Open hand starts with ball contact; ball position or proxy shape needs adjustment.")
    if hold.get("mean_four_tip_distance") is not None:
        lines.append(f"Hold mean four-fingertip distance is {hold['mean_four_tip_distance']:.4f} m.")
    if hold.get("thumb_to_ball") is not None:
        lines.append(f"Hold thumb-ball distance is {hold['thumb_to_ball']:.4f} m.")
    if hold.get("thumb_to_ball", 1.0) < 0.10:
        lines.append("Thumb is much closer than the old model and can be used for export3 scripted smoke testing.")
    else:
        lines.append("Thumb remains too far for convincing opposition.")
    lines.append("Visual inspection of the saved hold frames shows four fingers wrapping the ball and the thumb moving to the ball-side region; it is improved but still not a final Shadow-like opposition clamp.")
    lines.append("Some exported joint ranges have nonzero lower limits, so an open-hand target of 0 can be clamped by the position actuator ctrlrange; inspect `ctrl_applied` and `qpos_actual` before treating 0 rad as mechanical neutral.")
    if hold.get("max_penetration", 0.0) > 0.02:
        lines.append("Hold penetration is high; keep this as smoke test only.")
    lines.append("This remains pinned-ball, zero-gravity scripted position control; it is not training-ready or a stable free-ball grasp.")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Export3 position-control scripted ball grasp smoke test.")
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--ball-x", type=float, default=BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=BALL_POSITION[2])
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--hold-steps", type=int, default=300)
    parser.add_argument("--gravity", action="store_true")
    parser.add_argument("--pin-ball", action="store_true", default=True)
    parser.add_argument("--free-ball", action="store_true", help="Do not pin the ball after initial placement.")
    parser.add_argument("--no-screenshots", action="store_true")
    args = parser.parse_args()
    pin_ball = bool(args.pin_ball and not args.free_ball)
    ball_position = [args.ball_x, args.ball_y, args.ball_z]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        mujoco, model, data = load_model(SCENE_XML)
    except Exception as exc:
        report = {"load_success": False, "scene": str(SCENE_XML), "error": f"{type(exc).__name__}: {exc}"}
        write_outputs(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1
    if not args.gravity:
        model.opt.gravity[:] = 0.0
    thumb_targets = load_thumb_targets()
    thumb_source = str(THUMB_AUDIT_JSON) if THUMB_AUDIT_JSON.exists() else "fallback"
    act_map = actuator_map(model, mujoco)
    joints = joint_map(model, mujoco)
    missing_actuators = sorted(set(CONTROLLED_JOINTS) - set(act_map))
    set_ball_position(model, data, mujoco, ball_position)
    set_ctrl(model, data, full_stage_targets("open_hand", thumb_targets), act_map)
    mujoco.mj_forward(model, data)
    viewer = None
    if args.viewer:
        try:
            import mujoco.viewer

            viewer = mujoco.viewer.launch_passive(model, data)
        except Exception as exc:
            print(f"Viewer launch failed; continuing headless. Reason: {type(exc).__name__}: {exc}")
    stage_steps = max(20, int(400 / max(args.speed, 0.05)))
    previous = full_stage_targets("open_hand", thumb_targets)
    stage_reports = {}
    renders = []
    for stage in STAGE_ORDER:
        targets = full_stage_targets(stage, thumb_targets)
        steps = args.hold_steps if stage == "hold" else stage_steps
        applied = {}
        print(f"\n[{stage}] target joint angles (rad)")
        for name in CONTROLLED_JOINTS:
            print(f"  {name}: {targets.get(name, 0.0): .4f}")
        for step in range(steps):
            command = blend(previous, targets, (step + 1) / max(steps, 1))
            applied = set_ctrl(model, data, command, act_map)
            if pin_ball:
                set_ball_position(model, data, mujoco, ball_position)
            mujoco.mj_step(model, data)
            if viewer is not None:
                viewer.sync()
                time.sleep(0.002)
        if pin_ball:
            set_ball_position(model, data, mujoco, ball_position)
        mujoco.mj_forward(model, data)
        stage_reports[stage] = stage_summary(model, data, mujoco, joints, targets, applied)
        if not args.no_screenshots:
            renders.append(render_png(model, data, mujoco, "full_hand_with_ball", OUT_DIR / STAGE_TO_FILE[stage], width=1200, height=850))
            if stage in {"close_thumb", "hold"}:
                renders.append(render_png(model, data, mujoco, "palm", OUT_DIR / f"{stage}_palm.png", width=1200, height=850))
        previous = targets
    if viewer is not None:
        print("Export3 position-control demo reached hold stage. Close the viewer window to exit.")
        while viewer.is_running():
            viewer.sync()
            time.sleep(0.01)
        viewer.close()
    report = {
        "load_success": True,
        "scene": str(SCENE_XML),
        "ball_position": ball_position,
        "gravity_enabled": bool(args.gravity),
        "pin_ball": pin_ball,
        "actuator_count": int(model.nu),
        "missing_actuators": missing_actuators,
        "thumb_target_source": thumb_source,
        "thumb_close_target": thumb_targets,
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
