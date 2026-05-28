#!/usr/bin/env python3
"""Render the scripted arm+hand lift-ball smoke demo to a video file."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

import demo_arm_hand_lift_ball_scripted as demo


ROOT = Path(__file__).resolve().parent
VIS = ROOT / "docs" / "visual_checks_arm_hand_lift_ball_demo"
DEFAULT_VIDEO = VIS / "arm_hand_lift_ball_demo_pure_physics.mp4"


def setup_side_camera(model, data, mujoco) -> object:
    cam = mujoco.MjvCamera()
    mujoco.mjv_defaultFreeCamera(model, cam)
    palm = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    ball, _, _ = demo.ball_indices(model, mujoco)
    if palm >= 0 and ball >= 0:
        cam.lookat[:] = 0.52 * data.xpos[palm].copy() + 0.48 * data.xpos[ball].copy()
    elif palm >= 0:
        cam.lookat[:] = data.xpos[palm].copy()
    cam.distance = 0.44
    cam.azimuth = 180
    cam.elevation = -18
    return cam


def append_frame(writer, renderer, model, data, mujoco) -> None:
    cam = setup_side_camera(model, data, mujoco)
    renderer.update_scene(data, camera=cam)
    writer.append_data(renderer.render())


class FrameWriter:
    def __init__(self, output: Path, fps: int):
        self.output = output
        self.fps = fps
        self.count = 0
        self.writer = None
        self.frame_dir: Path | None = None
        self.ffmpeg = shutil.which("ffmpeg.exe") or shutil.which("ffmpeg")

    def __enter__(self):
        if self.output.suffix.lower() == ".mp4" and self.ffmpeg:
            self.frame_dir = self.output.with_name(self.output.stem + "_frames_tmp")
            if self.frame_dir.exists():
                shutil.rmtree(self.frame_dir)
            self.frame_dir.mkdir(parents=True, exist_ok=True)
        else:
            fallback = self.output
            if fallback.suffix.lower() == ".mp4":
                fallback = fallback.with_suffix(".gif")
                self.output = fallback
            self.writer = imageio.get_writer(fallback, fps=self.fps)
        return self

    def append(self, img: np.ndarray) -> None:
        if self.frame_dir is not None:
            imageio.imwrite(self.frame_dir / f"frame_{self.count:05d}.png", img)
        else:
            assert self.writer is not None
            self.writer.append_data(img)
        self.count += 1

    def __exit__(self, exc_type, exc, tb):
        if self.writer is not None:
            self.writer.close()
        if exc_type is not None:
            return False
        if self.frame_dir is not None:
            cmd = [
                self.ffmpeg,
                "-y",
                "-framerate",
                str(self.fps),
                "-i",
                str(self.frame_dir / "frame_%05d.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(self.output),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            shutil.rmtree(self.frame_dir)
        return False


def append_frame_to_sink(sink: FrameWriter, renderer, model, data, mujoco) -> None:
    cam = setup_side_camera(model, data, mujoco)
    renderer.update_scene(data, camera=cam)
    sink.append(renderer.render())


def main() -> None:
    parser = argparse.ArgumentParser(description="Render arm+hand lift-ball smoke demo to MP4.")
    parser.add_argument("--scene", default=str(demo.DEFAULT_SCENE))
    parser.add_argument("--output", default=str(DEFAULT_VIDEO))
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--capture-every", type=int, default=4)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=676)
    parser.add_argument("--assisted", action="store_true", help="Use post-grasp ball assistance; default is pure physics.")
    args = parser.parse_args()

    import mujoco

    scene = Path(args.scene).resolve()
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    names = demo.actuator_names(model, mujoco)

    mujoco.mj_forward(model, data)
    initial_ball = data.xpos[demo.ball_indices(model, mujoco)[0]].copy()
    data.qpos[:] = model.qpos0
    data.qvel[:] = 0
    demo.set_arm_qpos_and_ctrl(model, data, mujoco, demo.ARM_PRE_APPROACH, names)
    demo.set_ball_pose(model, data, mujoco, initial_ball)
    mujoco.mj_forward(model, data)

    mode_assisted = bool(args.assisted)
    phases = [
        ("open_high", demo.ARM_PRE_APPROACH, {**demo.ARM_PRE_APPROACH}, 80, False),
        ("approach_ball", demo.ARM_PRE_APPROACH, {**demo.ARM_APPROACH}, 180, False),
        ("preshape", {**demo.ARM_APPROACH}, {**demo.ARM_APPROACH, **demo.PRESHAPE_TARGETS}, 120, False),
        ("close_four_fingers", {**demo.ARM_APPROACH, **demo.PRESHAPE_TARGETS}, {**demo.ARM_APPROACH, **demo.LONG_FINGER_TARGETS}, 120, False),
        (
            "close_thumb",
            {**demo.ARM_APPROACH, **demo.LONG_FINGER_TARGETS},
            {**demo.ARM_APPROACH, **demo.LONG_FINGER_TARGETS, **demo.THUMB_SMOKE_TARGETS},
            120,
            mode_assisted,
        ),
        (
            "lift",
            {**demo.ARM_APPROACH, **demo.LONG_FINGER_TARGETS, **demo.THUMB_SMOKE_TARGETS},
            {**demo.ARM_LIFT, **demo.LONG_FINGER_TARGETS, **demo.THUMB_SMOKE_TARGETS},
            220,
            mode_assisted,
        ),
        (
            "hold_lift",
            {**demo.ARM_LIFT, **demo.LONG_FINGER_TARGETS, **demo.THUMB_SMOKE_TARGETS},
            {**demo.ARM_LIFT, **demo.LONG_FINGER_TARGETS, **demo.THUMB_SMOKE_TARGETS},
            120,
            mode_assisted,
        ),
    ]

    renderer = mujoco.Renderer(model, width=args.width, height=args.height)
    frame_count = 0
    try:
        with FrameWriter(out, args.fps) as writer:
            append_frame_to_sink(writer, renderer, model, data, mujoco)
            frame_count += 1
            for phase, start, end, steps, assist in phases:
                print(f"rendering {phase}...")
                for i in range(max(1, steps)):
                    alpha = i / max(1, steps - 1)
                    targets = demo.blend_targets(start, end, alpha)
                    data.ctrl[:] = demo.ctrl_from_targets(model, mujoco, names, targets)
                    if assist:
                        mujoco.mj_forward(model, data)
                        demo.set_ball_pose(model, data, mujoco, demo.palm_relative_ball_position(model, data, mujoco))
                    mujoco.mj_step(model, data)
                    if assist:
                        mujoco.mj_forward(model, data)
                        demo.set_ball_pose(model, data, mujoco, demo.palm_relative_ball_position(model, data, mujoco))
                        mujoco.mj_forward(model, data)
                    if i % max(1, args.capture_every) == 0:
                        append_frame_to_sink(writer, renderer, model, data, mujoco)
                        frame_count += 1
    finally:
        renderer.close()

    metrics = demo.scalar_metrics(model, data, mujoco, initial_ball)
    print(f"Saved video: {out}")
    print(f"Frames: {frame_count}")
    print(f"Final lift: {metrics['ball_lift_height']:.4f} m")
    print(f"Ball-hand contacts: {metrics['contact']['ball_hand_contact_count']}")
    print(f"Max penetration: {metrics['contact']['max_penetration']:.6f} m")


if __name__ == "__main__":
    main()
