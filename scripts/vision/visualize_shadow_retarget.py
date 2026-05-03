#!/usr/bin/env python3
"""Visualize visual-landmark to Shadow Hand retarget outputs."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from vision.shadow_retarget import SHADOW_ACTUATOR_NAMES


HAND_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (0, 17),
)


ACTION_GROUPS = {
    "wrist": (0, 1),
    "thumb": (2, 3, 4, 5, 6),
    "index": (7, 8, 9, 10),
    "middle": (11, 12, 13, 14),
    "ring": (15, 16, 17, 18),
    "little": (19, 20, 21, 22, 23),
}


def _load_npz_dict(path: Path) -> Dict[str, Any]:
    payload = np.load(path, allow_pickle=True)
    return {key: payload[key] for key in payload.files}


def _metadata_dict(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "metadata" not in payload:
        return {}
    raw = payload["metadata"]
    return dict(raw.item() if hasattr(raw, "item") else raw)


def _json_ready(value):
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def _pick_keyframes(frame_count: int, max_frames: int) -> List[int]:
    frame_count = int(frame_count)
    if frame_count <= 0:
        return []
    max_frames = max(1, int(max_frames))
    if frame_count <= max_frames:
        return list(range(frame_count))
    return sorted({int(round(item)) for item in np.linspace(0, frame_count - 1, max_frames)})


def _import_pyplot():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def plot_landmark_keyframes(landmarks: np.ndarray, out_path: Path, max_frames: int) -> Dict[str, Any]:
    plt = _import_pyplot()
    landmarks = np.asarray(landmarks, dtype=np.float32)
    keyframes = _pick_keyframes(landmarks.shape[0], max_frames)
    if not keyframes:
        return {"path": None, "keyframes": []}

    cols = min(4, len(keyframes))
    rows = int(np.ceil(len(keyframes) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 3.2 * rows), squeeze=False)
    all_xy = landmarks[:, :, :2].reshape(-1, 2)
    xy_min = np.min(all_xy, axis=0)
    xy_max = np.max(all_xy, axis=0)
    span = np.maximum(xy_max - xy_min, 1e-6)
    pad = 0.12 * float(np.max(span))

    for ax in axes.flat:
        ax.axis("off")

    for ax, frame_idx in zip(axes.flat, keyframes):
        lm = landmarks[frame_idx]
        for start, end in HAND_CONNECTIONS:
            ax.plot([lm[start, 0], lm[end, 0]], [-lm[start, 1], -lm[end, 1]], color="#3a5a78", linewidth=1.5)
        ax.scatter(lm[:, 0], -lm[:, 1], s=16, color="#d95f02", zorder=3)
        ax.scatter(lm[0, 0], -lm[0, 1], s=26, color="#1b9e77", zorder=4)
        ax.set_title(f"frame {frame_idx}", fontsize=10)
        ax.set_xlim(float(xy_min[0] - pad), float(xy_max[0] + pad))
        ax.set_ylim(float(-xy_max[1] - pad), float(-xy_min[1] + pad))
        ax.set_aspect("equal", adjustable="box")

    fig.suptitle("Input 21-Landmark Hand Trace", fontsize=13)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return {"path": str(out_path), "keyframes": keyframes}


def plot_action_curves(actions: np.ndarray, actuator_names: Iterable[str], out_path: Path) -> Dict[str, Any]:
    plt = _import_pyplot()
    actions = np.asarray(actions, dtype=np.float32)
    actuator_names = list(actuator_names)
    x = np.arange(actions.shape[0])
    fig, axes = plt.subplots(len(ACTION_GROUPS), 1, figsize=(12, 11), sharex=True)

    for ax, (group_name, indices) in zip(axes, ACTION_GROUPS.items()):
        for idx in indices:
            if idx >= actions.shape[1]:
                continue
            label = actuator_names[idx] if idx < len(actuator_names) else f"actuator_{idx}"
            ax.plot(x, actions[:, idx], linewidth=1.4, label=label)
        ax.set_ylabel(group_name)
        ax.set_ylim(-1.05, 1.05)
        ax.grid(True, alpha=0.25)
        ax.legend(loc="upper right", ncol=min(4, len(indices)), fontsize=7)

    axes[-1].set_xlabel("frame")
    fig.suptitle("Retargeted Shadow Normalized Actions", fontsize=13)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return {"path": str(out_path)}


def plot_rollout_metrics(rollout_path: Path, out_path: Path) -> Dict[str, Any]:
    payload = _load_npz_dict(rollout_path)
    if "episodes" not in payload:
        return {"path": None, "reason": "rollout NPZ missing episodes"}

    episodes = payload["episodes"]
    if len(episodes) == 0:
        return {"path": None, "reason": "rollout NPZ has no episodes"}

    episode = dict(episodes[0])
    rewards = np.asarray(episode.get("rewards", []), dtype=np.float32)
    infos = list(episode.get("infos", []))
    steps = np.arange(len(rewards))
    distances = np.asarray([float(item.get("distance", np.nan)) for item in infos], dtype=np.float32)
    contact = np.asarray([1.0 if item.get("contact") else 0.0 for item in infos], dtype=np.float32)
    grasp_contact = np.asarray([1.0 if item.get("grasp_contact") else 0.0 for item in infos], dtype=np.float32)

    plt = _import_pyplot()
    fig, axes = plt.subplots(3, 1, figsize=(11, 7.5), sharex=True)
    axes[0].plot(steps, rewards, color="#2a6f97")
    axes[0].set_ylabel("reward")
    axes[0].grid(True, alpha=0.25)
    axes[1].plot(steps, distances, color="#7a5195")
    axes[1].set_ylabel("distance")
    axes[1].grid(True, alpha=0.25)
    axes[2].plot(steps, contact, label="any contact", color="#ef5675")
    axes[2].plot(steps, grasp_contact, label="grasp contact", color="#ffa600")
    axes[2].set_ylabel("contact")
    axes[2].set_xlabel("step")
    axes[2].set_ylim(-0.05, 1.05)
    axes[2].grid(True, alpha=0.25)
    axes[2].legend(loc="upper right")
    fig.suptitle("Shadow Replay Rollout Metrics", fontsize=13)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return {
        "path": str(out_path),
        "steps": int(len(rewards)),
        "success": bool(episode.get("success", False)),
        "terminal_success": bool(episode.get("terminal_success", False)),
        "metrics": episode.get("metrics", {}),
    }


def _make_image_sheet(image_paths: List[Path], out_path: Path, columns: int = 3) -> Dict[str, Any]:
    from PIL import Image, ImageDraw

    if not image_paths:
        return {"path": None, "frames": 0}

    images = [Image.open(path).convert("RGB") for path in image_paths]
    thumb_w = max(image.width for image in images)
    thumb_h = max(image.height for image in images)
    columns = min(max(1, columns), len(images))
    rows = int(np.ceil(len(images) / columns))
    label_h = 26
    sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), color=(245, 245, 245))
    draw = ImageDraw.Draw(sheet)

    for idx, (path, image) in enumerate(zip(image_paths, images)):
        row = idx // columns
        col = idx % columns
        x = col * thumb_w
        y = row * (thumb_h + label_h)
        sheet.paste(image, (x, y + label_h))
        draw.text((x + 8, y + 6), path.stem, fill=(30, 30, 30))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return {"path": str(out_path), "frames": len(image_paths)}


def render_mujoco_keyframes(
    actions: np.ndarray,
    out_dir: Path,
    keyframes: List[int],
    placement_mode: str,
    placement_jitter: float,
    camera: str,
    width: int,
    height: int,
) -> Dict[str, Any]:
    from PIL import Image

    from scripts.common.grasp_workflow import place_object
    from src.environments.shadow_grasp_env import ShadowGraspEnv
    import mujoco

    actions = np.asarray(actions, dtype=np.float32)
    if actions.size == 0:
        return {"contact_sheet": None, "frames": []}

    env = ShadowGraspEnv(max_steps=max(len(actions), 1), observation_mode="oracle")
    env.reset()
    place_object(
        env,
        placement_mode=placement_mode,
        placement_jitter=float(placement_jitter),
        verbose=False,
    )

    renderer = mujoco.Renderer(env.model, height=int(height), width=int(width))
    keyframe_set = set(int(item) for item in keyframes)
    frame_paths: List[Path] = []
    render_dir = out_dir / "mujoco_frames"
    render_dir.mkdir(parents=True, exist_ok=True)

    try:
        for step_idx, action in enumerate(actions):
            if step_idx in keyframe_set:
                renderer.update_scene(env.data, camera=camera)
                image = renderer.render()
                path = render_dir / f"shadow_frame_{step_idx:04d}.png"
                Image.fromarray(image).save(path)
                frame_paths.append(path)
            env.step(action.astype(np.float32))

        final_idx = len(actions) - 1
        if final_idx not in keyframe_set:
            renderer.update_scene(env.data, camera=camera)
            image = renderer.render()
            path = render_dir / f"shadow_frame_{final_idx:04d}.png"
            Image.fromarray(image).save(path)
            frame_paths.append(path)
    finally:
        renderer.close()

    sheet = _make_image_sheet(frame_paths, out_dir / "shadow_mujoco_keyframes.png", columns=3)
    return {
        "contact_sheet": sheet.get("path"),
        "frames": [str(path) for path in frame_paths],
        "camera": camera,
        "width": int(width),
        "height": int(height),
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Visualize Shadow retarget outputs")
    parser.add_argument("--retarget", required=True, help="NPZ from retarget_palm_trace_to_shadow.py")
    parser.add_argument("--rollout", default="", help="Optional replay dataset NPZ")
    parser.add_argument("--output-dir", default="", help="Output visualization directory")
    parser.add_argument("--max-keyframes", type=int, default=6, help="Number of keyframes for contact sheets")
    parser.add_argument("--render-mujoco", action="store_true", help="Render fixed-camera Shadow frames")
    parser.add_argument("--camera", default="shadow_front", help="MuJoCo camera name for rendering")
    parser.add_argument("--render-width", type=int, default=960, help="MuJoCo render width")
    parser.add_argument("--render-height", type=int, default=720, help="MuJoCo render height")
    parser.add_argument("--placement-mode", default="demo", choices=["scene", "demo"], help="Object placement for render")
    parser.add_argument("--placement-jitter", type=float, default=0.0, help="Object placement jitter for render")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    retarget_path = Path(args.retarget)
    payload = _load_npz_dict(retarget_path)
    if "actions" not in payload:
        raise ValueError(f"Retarget NPZ is missing actions: {retarget_path}")

    actions = np.asarray(payload["actions"], dtype=np.float32)
    landmarks = np.asarray(payload["landmarks"], dtype=np.float32) if "landmarks" in payload else np.zeros((0, 21, 3), dtype=np.float32)
    actuator_names = (
        [str(item) for item in payload["actuator_names"]]
        if "actuator_names" in payload
        else list(SHADOW_ACTUATOR_NAMES)
    )
    output_dir = Path(args.output_dir) if args.output_dir else Path("artifacts") / "vision_shadow_retarget_visualization" / retarget_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    keyframes = _pick_keyframes(actions.shape[0], args.max_keyframes)
    outputs: Dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "retarget": str(retarget_path),
        "output_dir": str(output_dir),
        "frames": int(actions.shape[0]),
        "action_dim": int(actions.shape[1]) if actions.ndim == 2 else 0,
        "keyframes": keyframes,
        "source_metadata": _metadata_dict(payload),
    }

    outputs["action_curves"] = plot_action_curves(actions, actuator_names, output_dir / "shadow_action_curves.png")
    if landmarks.size:
        outputs["landmark_keyframes"] = plot_landmark_keyframes(
            landmarks,
            output_dir / "input_landmark_keyframes.png",
            args.max_keyframes,
        )
    else:
        outputs["landmark_keyframes"] = {"path": None, "reason": "retarget NPZ missing landmarks"}

    if args.rollout:
        outputs["rollout_metrics"] = plot_rollout_metrics(Path(args.rollout), output_dir / "shadow_rollout_metrics.png")

    if args.render_mujoco:
        outputs["mujoco_keyframes"] = render_mujoco_keyframes(
            actions=actions,
            out_dir=output_dir,
            keyframes=keyframes,
            placement_mode=args.placement_mode,
            placement_jitter=float(args.placement_jitter),
            camera=args.camera,
            width=args.render_width,
            height=args.render_height,
        )

    summary_path = output_dir / "visual_summary.json"
    summary_path.write_text(json.dumps(_json_ready(outputs), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved visualization summary: {summary_path}")
    for key, value in outputs.items():
        if isinstance(value, dict) and value.get("path"):
            print(f"{key}: {value['path']}")
        elif isinstance(value, dict) and value.get("contact_sheet"):
            print(f"{key}: {value['contact_sheet']}")


if __name__ == "__main__":
    main()
