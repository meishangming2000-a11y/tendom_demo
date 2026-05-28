#!/usr/bin/env python3
"""Render or view a one-episode demo of the experimental Stage2 BC smoke policy."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import torch

from arm_hand_stage1_task_api import CURRENT_LIFT_SCENE, ArmHandStage1TaskAPI
from arm_hand_stage1_v2_bc_common import (
    DEFAULT_CHECKPOINT,
    DEFAULT_DATASET,
    DEFAULT_DEMO_META,
    DEFAULT_DEMO_REPORT,
    DEFAULT_DEMO_VIDEO,
    json_ready,
    load_dataset,
    load_policy,
)
from eval_arm_hand_stage1_v2_bc_smoke import episode_initial_ball, episode_offset, run_policy_episode
from render_arm_hand_lift_ball_video import FrameWriter, setup_side_camera


def write_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    result = payload["result"]
    metrics = result["final_metrics"]
    contact = metrics["contact"]
    lines = [
        "# Arm-Hand Stage1 V2 BC Smoke Demo Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: **{result['status']}**\n",
        f"- Terminal reason: `{result['terminal_reason']}`\n",
        f"- Success: `{result['success']}`\n",
        f"- Checkpoint: `{payload['checkpoint']}`\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Episode: `{result['episode_id']}`\n",
        f"- Video: `{payload['video']}`\n",
        f"- Frames: `{payload['frames']}`\n",
        f"- Steps: `{result['steps']}`\n",
        f"- Ball lift height: `{metrics['ball_lift_height']:.6f} m`\n",
        f"- Ball-hand contacts: `{contact['ball_hand_contact_count']}`\n",
        f"- Ball-floor contacts: `{contact.get('ball_floor_contact_count', 0)}`\n",
        f"- Max penetration: `{contact['max_penetration']:.6f} m`\n",
        f"- Reward: `{result['reward']:.6f}`\n",
        f"- Training ready: **No, experimental BC smoke only**\n\n",
        "## Interpretation\n\n",
        "- This demo runs the learned BC smoke policy online in MuJoCo.\n",
        "- It is a first training artifact, not a promoted baseline.\n",
        "- Compare it with the scripted lift demo when judging whether the next fix should be policy-side or data-side.\n",
    ]
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run/render the experimental Stage2 BC smoke policy demo.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--scene", type=Path, default=CURRENT_LIFT_SCENE)
    parser.add_argument("--episode-id", type=int, default=4)
    parser.add_argument("--max-steps", type=int, default=1230)
    parser.add_argument("--output", type=Path, default=DEFAULT_DEMO_VIDEO)
    parser.add_argument("--report", type=Path, default=DEFAULT_DEMO_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_DEMO_META)
    parser.add_argument("--render-video", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--capture-every", type=int, default=4)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=676)
    parser.add_argument("--action-smoothing", type=float, default=0.0)
    parser.add_argument("--no-train-range-clip", action="store_true")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--viewer-step-sleep", type=float, default=0.01)
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA unavailable; using CPU.")
        args.device = "cpu"
    device = torch.device(args.device)
    data = load_dataset(args.dataset)
    model, checkpoint = load_policy(args.checkpoint, device)
    api = ArmHandStage1TaskAPI(args.scene)

    renderer = None
    writer_ctx = None
    viewer_ctx = None
    viewer = None
    frames = {"count": 0}

    def capture(api_obj: ArmHandStage1TaskAPI, step: int, evaluation):
        if viewer is not None:
            viewer.sync()
            time.sleep(max(0.0, args.viewer_step_sleep))
        if writer_ctx is None or renderer is None:
            return
        if step % max(1, args.capture_every) != 0 and not (evaluation and evaluation.get("done")):
            return
        cam = setup_side_camera(api_obj.model, api_obj.data, api_obj.mujoco)
        renderer.update_scene(api_obj.data, camera=cam)
        writer_ctx.append(renderer.render())
        frames["count"] += 1

    try:
        if args.viewer:
            import mujoco.viewer

            viewer_ctx = mujoco.viewer.launch_passive(api.model, api.data)
            viewer = viewer_ctx.__enter__()
        if args.render_video:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            renderer = api.mujoco.Renderer(api.model, width=args.width, height=args.height)
            writer_ctx = FrameWriter(args.output.resolve(), args.fps).__enter__()
        result = run_policy_episode(
            api=api,
            model=model,
            checkpoint=checkpoint,
            device=device,
            episode_id=args.episode_id,
            initial_ball=episode_initial_ball(data, args.episode_id),
            ball_offset=episode_offset(data, args.episode_id),
            max_steps=args.max_steps,
            clip_to_train_range=not args.no_train_range_clip,
            action_smoothing=args.action_smoothing,
            sample_every=50,
            frame_callback=capture,
        )
    finally:
        if writer_ctx is not None:
            writer_ctx.__exit__(None, None, None)
        if renderer is not None:
            renderer.close()
        if viewer_ctx is not None:
            viewer_ctx.__exit__(None, None, None)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "checkpoint": str(args.checkpoint.resolve()),
        "dataset": str(args.dataset.resolve()),
        "scene": str(args.scene.resolve()),
        "video": str(args.output.resolve()) if args.render_video else None,
        "frames": int(frames["count"]),
        "device": str(device),
        "clip_to_train_range": not args.no_train_range_clip,
        "action_smoothing": float(args.action_smoothing),
        "checkpoint_status": checkpoint.get("status"),
        "result": result,
        "training_ready": False,
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, json_ready(payload))
    print(f"Demo status: {result['status']} / {result['terminal_reason']} success={result['success']}")
    print(f"Video: {payload['video']}")
    print(f"Report: {args.report}")
    print(f"Metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
