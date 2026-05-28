#!/usr/bin/env python3
"""Arm+hand lift-ball demo starting from the model default posture.

This is a scripted smoke demo. It uses the current arm+hand collision proxy v2
scene and position actuators, then renders a video by default.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np

import demo_arm_hand_lift_ball_scripted as base
from render_arm_hand_lift_ball_video import FrameWriter, setup_side_camera


ROOT = Path(__file__).resolve().parent
SCENE = ROOT / "mjcf" / "scene_arm_hand_export4_lift_ball_demo.xml"
VIS = ROOT / "docs" / "visual_checks_arm_hand_lift_from_default"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
REPORT = DOCS / "arm_hand_lift_from_default_report.md"
META_OUT = META / "arm_hand_lift_from_default.json"
VIDEO = VIS / "arm_hand_lift_from_default_pure_physics.mp4"


def actuated_joint_targets_from_qpos(model, data, mujoco, names: list[str]) -> dict[str, float]:
    targets = {}
    for actuator_name in names:
        joint_name = base.actuator_to_joint_name(actuator_name)
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        if jid < 0:
            continue
        qadr = int(model.jnt_qposadr[jid])
        targets[joint_name] = float(data.qpos[qadr])
    return targets


def render_with_side_camera(model, data, mujoco, path: Path) -> str:
    renderer = mujoco.Renderer(model, width=1280, height=900)
    try:
        cam = setup_side_camera(model, data, mujoco)
        renderer.update_scene(data, camera=cam)
        img = renderer.render()
    finally:
        renderer.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, img)
    return str(path)


def append_video_frame(writer: FrameWriter, renderer, model, data, mujoco) -> None:
    cam = setup_side_camera(model, data, mujoco)
    renderer.update_scene(data, camera=cam)
    writer.append(renderer.render())


def run_interpolated_phase(
    model,
    data,
    mujoco,
    names: list[str],
    start_targets: dict[str, float],
    end_targets: dict[str, float],
    steps: int,
    *,
    assist_ball: bool,
    viewer=None,
    speed: float = 1.0,
    video_writer: FrameWriter | None = None,
    renderer=None,
    capture_every: int = 4,
) -> None:
    for i in range(max(1, steps)):
        alpha = i / max(1, steps - 1)
        targets = base.blend_targets(start_targets, end_targets, alpha)
        data.ctrl[:] = base.ctrl_from_targets(model, mujoco, names, targets)
        if assist_ball:
            mujoco.mj_forward(model, data)
            base.set_ball_pose(model, data, mujoco, base.palm_relative_ball_position(model, data, mujoco))
        mujoco.mj_step(model, data)
        if assist_ball:
            mujoco.mj_forward(model, data)
            base.set_ball_pose(model, data, mujoco, base.palm_relative_ball_position(model, data, mujoco))
            mujoco.mj_forward(model, data)
        if viewer is not None:
            viewer.sync()
            time.sleep(model.opt.timestep / max(speed, 1e-6))
        if video_writer is not None and renderer is not None and i % max(1, capture_every) == 0:
            append_video_frame(video_writer, renderer, model, data, mujoco)


def write_contact_sheet(screenshots: dict[str, str]) -> str:
    from PIL import Image, ImageDraw

    items = list(screenshots.items())
    thumbs = []
    for label, filename in items:
        img = Image.open(filename).convert("RGB")
        img.thumbnail((360, 253))
        canvas = Image.new("RGB", (380, 290), (245, 245, 245))
        canvas.paste(img, ((380 - img.width) // 2, 28))
        ImageDraw.Draw(canvas).text((12, 8), label, fill=(0, 0, 0))
        thumbs.append(canvas)
    rows = int(np.ceil(len(thumbs) / 3))
    sheet = Image.new("RGB", (3 * 380, rows * 290), (255, 255, 255))
    for i, img in enumerate(thumbs):
        sheet.paste(img, ((i % 3) * 380, (i // 3) * 290))
    out = VIS / "arm_hand_lift_from_default_contact_sheet.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return str(out)


def run_demo(args) -> dict[str, Any]:
    import mujoco

    scene = Path(args.scene).resolve()
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    names = base.actuator_names(model, mujoco)

    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)
    initial_ball = data.xpos[base.ball_indices(model, mujoco)[0]].copy()
    base.set_ball_pose(model, data, mujoco, initial_ball)
    mujoco.mj_forward(model, data)

    default_targets = actuated_joint_targets_from_qpos(model, data, mujoco, names)
    pre_approach = {**default_targets, **base.ARM_PRE_APPROACH}
    approach = {**default_targets, **base.ARM_APPROACH}
    preshape = {**approach, **base.PRESHAPE_TARGETS}
    close_fingers = {**approach, **base.LONG_FINGER_TARGETS}
    close_thumb = {**close_fingers, **base.THUMB_SMOKE_TARGETS}
    lift = {**close_thumb, **base.ARM_LIFT}

    phases = [
        ("default_hold", default_targets, default_targets, args.default_hold_steps, False),
        ("move_to_pre_approach", default_targets, pre_approach, args.move_steps, False),
        ("approach_ball", pre_approach, approach, args.approach_steps, False),
        ("preshape", approach, preshape, args.hand_steps, False),
        ("close_four_fingers", preshape, close_fingers, args.hand_steps, False),
        ("close_thumb", close_fingers, close_thumb, args.hand_steps, args.assist_after_grasp),
        ("lift", close_thumb, lift, args.lift_steps, args.assist_after_grasp),
        ("hold_lift", lift, lift, args.hold_steps, args.assist_after_grasp),
    ]

    viewer_ctx = None
    viewer = None
    if args.viewer:
        import mujoco.viewer

        viewer_ctx = mujoco.viewer.launch_passive(model, data)
        viewer = viewer_ctx.__enter__()

    VIS.mkdir(parents=True, exist_ok=True)
    screenshots: dict[str, str] = {}
    phase_rows = []
    renderer = None
    writer_ctx = None
    video_path = str(Path(args.output).resolve()) if args.render_video else None
    try:
        if args.render_video:
            renderer = mujoco.Renderer(model, width=args.width, height=args.height)
            writer_ctx = FrameWriter(Path(args.output).resolve(), args.fps)
            writer = writer_ctx.__enter__()
            append_video_frame(writer, renderer, model, data, mujoco)
        else:
            writer = None

        for idx, (phase, start, end, steps, assist) in enumerate(phases):
            run_interpolated_phase(
                model,
                data,
                mujoco,
                names,
                start,
                end,
                steps,
                assist_ball=assist,
                viewer=viewer,
                speed=args.speed,
                video_writer=writer,
                renderer=renderer,
                capture_every=args.capture_every,
            )
            metrics = base.scalar_metrics(model, data, mujoco, initial_ball)
            phase_rows.append({"phase": phase, "assist_ball": assist, "metrics": metrics})
            screenshots[phase] = render_with_side_camera(model, data, mujoco, VIS / f"{idx:02d}_{phase}.png")
            print(
                f"{phase}: assist={assist} contacts={metrics['contact']['ball_hand_contact_count']} "
                f"floor={metrics['contact']['ball_floor_contact_count']} lift={metrics['ball_lift_height']:.4f} "
                f"pen={metrics['contact']['max_penetration']:.6f}"
            )
            if viewer is not None and not viewer.is_running():
                break
    finally:
        if writer_ctx is not None:
            writer_ctx.__exit__(None, None, None)
        if renderer is not None:
            renderer.close()
        if viewer_ctx is not None:
            viewer_ctx.__exit__(None, None, None)

    contact_sheet = write_contact_sheet(screenshots)
    final = phase_rows[-1]["metrics"]
    success = bool(
        final["ball_lift_height"] >= args.success_lift_height
        and final["contact"]["ball_hand_contact_count"] >= 1
        and final["contact"]["ball_floor_contact_count"] == 0
        and final["contact"]["max_penetration"] <= 0.015
    )
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(scene),
        "mode": "assisted_after_grasp" if args.assist_after_grasp else "pure_physics",
        "status": "PASS" if success else "PARTIAL",
        "training_used": False,
        "video": video_path,
        "screenshots": screenshots,
        "contact_sheet": contact_sheet,
        "model_summary": {
            "nbody": model.nbody,
            "njnt": model.njnt,
            "nu": model.nu,
            "ngeom": model.ngeom,
            "nsite": model.nsite,
            "nmesh": model.nmesh,
        },
        "initial_ball": initial_ball,
        "phase_results": phase_rows,
        "final_metrics": final,
    }


def json_ready(value: Any) -> Any:
    return base.json_ready(value)


def write_outputs(payload: dict[str, Any]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    META_OUT.write_text(json.dumps(json_ready(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    final = payload["final_metrics"]
    lines = [
        "# Arm-Hand Lift From Default Demo Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Mode: `{payload['mode']}`\n",
        f"- Status: **{payload['status']}**\n",
        f"- Training used: **No**\n",
        f"- Video: `{payload['video']}`\n",
        f"- Contact sheet: `{payload['contact_sheet']}`\n\n",
        "## Final Metrics\n\n",
        f"- Ball lift height: `{final['ball_lift_height']:.6f} m`\n",
        f"- Ball displacement: `{final['ball_displacement']:.6f} m`\n",
        f"- Ball-hand contacts: `{final['contact']['ball_hand_contact_count']}`\n",
        f"- Ball-floor contacts: `{final['contact']['ball_floor_contact_count']}`\n",
        f"- Max penetration: `{final['contact']['max_penetration']:.6f} m`\n",
        f"- Four-finger avg tip-ball distance: `{final['four_finger_avg_tip_ball_distance']:.6f} m`\n",
        f"- Thumb-ball distance: `{final['thumb_ball_distance']:.6f} m`\n\n",
        "## Phase Metrics\n\n",
        "| phase | assisted | ball lift | ball-hand contacts | ball-floor contacts | max penetration | four avg | thumb-ball |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for row in payload["phase_results"]:
        m = row["metrics"]
        lines.append(
            f"| {row['phase']} | {int(row['assist_ball'])} | {m['ball_lift_height']:.4f} | "
            f"{m['contact']['ball_hand_contact_count']} | {m['contact']['ball_floor_contact_count']} | "
            f"{m['contact']['max_penetration']:.6f} | {m['four_finger_avg_tip_ball_distance']:.4f} | "
            f"{m['thumb_ball_distance']:.4f} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "This demo starts from the model default posture, moves the arm to a pre-approach pose, approaches the ball, closes the fingers, and lifts. It is still scripted position control using collision proxy v2, not a learned policy.\n\n",
            "The floor/table plane is the same raised demo plane used by the previous lift-ball smoke scene, chosen to keep the ball inside the current arm workspace.\n\n",
        ]
    )
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Arm+hand lift-ball demo starting from default posture.")
    parser.add_argument("--scene", default=str(SCENE))
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--render-video", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--output", default=str(VIDEO))
    parser.add_argument("--assist-after-grasp", action="store_true")
    parser.add_argument("--speed", type=float, default=2.0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--capture-every", type=int, default=4)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=676)
    parser.add_argument("--default-hold-steps", type=int, default=90)
    parser.add_argument("--move-steps", type=int, default=260)
    parser.add_argument("--approach-steps", type=int, default=180)
    parser.add_argument("--hand-steps", type=int, default=120)
    parser.add_argument("--lift-steps", type=int, default=220)
    parser.add_argument("--hold-steps", type=int, default=120)
    parser.add_argument("--success-lift-height", type=float, default=0.08)
    args = parser.parse_args()

    payload = run_demo(args)
    write_outputs(payload)
    print(f"Status: {payload['status']}")
    print(f"Video: {payload['video']}")
    print(f"Report: {REPORT}")
    print(f"Metadata: {META_OUT}")


if __name__ == "__main__":
    main()
