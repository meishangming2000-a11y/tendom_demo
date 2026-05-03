#!/usr/bin/env python3
"""Run a one-command real-hand video to Shadow-retarget comparison."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


DEFAULT_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)

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


def _simulations_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _repo_root() -> Path:
    return _simulations_root().parent


def _default_video_path() -> Path:
    return _repo_root() / "artifacts" / "vision_real_hand" / "hand_example_20260429" / "source" / "hand-example_video.mp4"


def _default_output_root() -> Path:
    return _repo_root() / "artifacts" / "vision_real_hand" / "hand_example_20260429" / "one_command_compare"


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


def _run(command: List[str], cwd: Path) -> None:
    print("\n> " + " ".join(command))
    subprocess.run(command, cwd=str(cwd), check=True)


def _ensure_hand_landmarker_model(model_path: Path, url: str) -> Path:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    if not model_path.exists():
        print(f"Downloading MediaPipe hand landmarker model to {model_path}")
        urllib.request.urlretrieve(url, model_path)
    return model_path


def _load_npz_metadata(path: Path) -> Dict[str, Any]:
    payload = np.load(path, allow_pickle=True)
    if "metadata" not in payload:
        return {}
    raw = payload["metadata"]
    return dict(raw.item() if hasattr(raw, "item") else raw)


def _load_rollout_summary(path: Path) -> Dict[str, Any]:
    payload = np.load(path, allow_pickle=True)
    episodes = payload["episodes"] if "episodes" in payload else []
    if len(episodes) == 0:
        return {"steps": 0, "success": False, "terminal_success": False, "metrics": {}}
    episode = dict(episodes[0])
    return {
        "steps": int(episode.get("steps", 0)),
        "success": bool(episode.get("success", False)),
        "terminal_success": bool(episode.get("terminal_success", False)),
        "total_reward": float(np.sum(np.asarray(episode.get("rewards", []), dtype=np.float32))),
        "metrics": episode.get("metrics", {}),
    }


def _extract_source_keyframes(video_path: Path, out_dir: Path, max_keyframes: int) -> Path:
    import cv2
    from PIL import Image, ImageDraw

    out_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if frame_count <= 0:
        cap.release()
        raise RuntimeError(f"Could not determine video frame count: {video_path}")

    indices = sorted({int(round(item)) for item in np.linspace(0, frame_count - 1, max(1, int(max_keyframes)))})
    frame_paths: List[Path] = []
    for index in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = cap.read()
        if not ok:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        image.thumbnail((360, 360))
        canvas = Image.new("RGB", (360, 386), (245, 245, 245))
        canvas.paste(image, ((360 - image.width) // 2, 26))
        draw = ImageDraw.Draw(canvas)
        draw.text((8, 6), f"frame {index}/{frame_count}", fill=(20, 20, 20))
        frame_path = out_dir / f"source_frame_{index:04d}.png"
        canvas.save(frame_path)
        frame_paths.append(frame_path)
    cap.release()

    if not frame_paths:
        raise RuntimeError(f"No source frames extracted from video: {video_path}")

    columns = min(4, len(frame_paths))
    rows = int(np.ceil(len(frame_paths) / columns))
    sheet = Image.new("RGB", (columns * 360, rows * 386), (245, 245, 245))
    for idx, frame_path in enumerate(frame_paths):
        image = Image.open(frame_path).convert("RGB")
        sheet.paste(image, ((idx % columns) * 360, (idx // columns) * 386))

    sheet_path = out_dir / "source_video_keyframes.png"
    sheet.save(sheet_path)
    return sheet_path


def _extract_video_keyframes(video_path: Path, out_dir: Path, sheet_name: str, max_keyframes: int) -> Path:
    import cv2
    from PIL import Image, ImageDraw

    out_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open comparison video: {video_path}")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if frame_count <= 0:
        cap.release()
        raise RuntimeError(f"Could not determine frame count: {video_path}")

    indices = sorted({int(round(item)) for item in np.linspace(0, frame_count - 1, max(1, int(max_keyframes)))})
    frame_paths: List[Path] = []
    for index in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = cap.read()
        if not ok:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        image.thumbnail((720, 360))
        canvas = Image.new("RGB", (720, 388), (245, 245, 245))
        canvas.paste(image, ((720 - image.width) // 2, 28))
        draw = ImageDraw.Draw(canvas)
        draw.text((8, 8), f"video frame {index}/{frame_count}", fill=(20, 20, 20))
        frame_path = out_dir / f"{sheet_name}_{index:04d}.png"
        canvas.save(frame_path)
        frame_paths.append(frame_path)
    cap.release()

    if not frame_paths:
        raise RuntimeError(f"No frames extracted from comparison video: {video_path}")

    columns = min(2, len(frame_paths))
    rows = int(np.ceil(len(frame_paths) / columns))
    sheet = Image.new("RGB", (columns * 720, rows * 388), (245, 245, 245))
    for idx, frame_path in enumerate(frame_paths):
        image = Image.open(frame_path).convert("RGB")
        sheet.paste(image, ((idx % columns) * 720, (idx // columns) * 388))

    sheet_path = out_dir / f"{sheet_name}.png"
    sheet.save(sheet_path)
    return sheet_path


def _fit_to_panel(image, size: Tuple[int, int], fill: Tuple[int, int, int] = (242, 244, 247)):
    from PIL import Image

    image = image.convert("RGB")
    panel_w, panel_h = size
    scale = min(panel_w / max(image.width, 1), panel_h / max(image.height, 1))
    resized = image.resize((max(1, int(round(image.width * scale))), max(1, int(round(image.height * scale)))))
    canvas = Image.new("RGB", size, fill)
    canvas.paste(resized, ((panel_w - resized.width) // 2, (panel_h - resized.height) // 2))
    return canvas


def _draw_header(draw, x: int, y: int, title: str, subtitle: str = "") -> None:
    draw.text((x, y), title, fill=(18, 22, 28))
    if subtitle:
        draw.text((x, y + 22), subtitle, fill=(80, 86, 96))


def _landmark_bounds(landmarks: np.ndarray) -> Tuple[float, float, float, float]:
    points = np.asarray(landmarks, dtype=np.float32)
    if points.size == 0:
        return 0.0, 1.0, 0.0, 1.0
    xy = points[:, :, :2].reshape(-1, 2)
    xy_min = np.nanmin(xy, axis=0)
    xy_max = np.nanmax(xy, axis=0)
    span = np.maximum(xy_max - xy_min, 1e-4)
    pad = 0.12 * float(np.max(span))
    return (
        float(xy_min[0] - pad),
        float(xy_max[0] + pad),
        float(xy_min[1] - pad),
        float(xy_max[1] + pad),
    )


def _draw_landmark_panel(landmarks: np.ndarray, size: Tuple[int, int], bounds: Tuple[float, float, float, float]):
    from PIL import Image, ImageDraw

    panel_w, panel_h = size
    margin = 34
    canvas = Image.new("RGB", size, (249, 250, 252))
    draw = ImageDraw.Draw(canvas)
    xmin, xmax, ymin, ymax = bounds
    xspan = max(xmax - xmin, 1e-6)
    yspan = max(ymax - ymin, 1e-6)

    def project(point: np.ndarray) -> Tuple[float, float]:
        x = margin + ((float(point[0]) - xmin) / xspan) * (panel_w - 2 * margin)
        y = margin + ((float(point[1]) - ymin) / yspan) * (panel_h - 2 * margin)
        return x, y

    lm = np.asarray(landmarks, dtype=np.float32)
    draw.rectangle((margin, margin, panel_w - margin, panel_h - margin), outline=(218, 224, 232), width=1)
    for start, end in HAND_CONNECTIONS:
        x0, y0 = project(lm[start])
        x1, y1 = project(lm[end])
        draw.line((x0, y0, x1, y1), fill=(48, 91, 126), width=4)

    for idx, point in enumerate(lm):
        x, y = project(point)
        radius = 5 if idx else 7
        color = (219, 92, 36) if idx else (20, 145, 113)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color, outline=(255, 255, 255), width=2)

    wrist = project(lm[0])
    middle = project(lm[9])
    draw.line((wrist[0], wrist[1], middle[0], middle[1]), fill=(35, 35, 35), width=2)
    draw.text((16, panel_h - 28), "21 landmarks + hand connections", fill=(50, 55, 65))
    return canvas


def _load_rollout_infos(path: Path) -> List[Dict[str, Any]]:
    payload = np.load(path, allow_pickle=True)
    if "episodes" not in payload or len(payload["episodes"]) == 0:
        return []
    episode = dict(payload["episodes"][0])
    return [dict(item) for item in episode.get("infos", [])]


def _draw_metric_strip(draw, x: int, y: int, width: int, step_idx: int, info: Dict[str, Any]) -> None:
    distance = float(info.get("distance", 0.0)) if info else 0.0
    height = float(info.get("object_height", 0.0)) if info else 0.0
    contact = bool(info.get("contact", False)) if info else False
    grasp = bool(info.get("grasp_contact", False)) if info else False
    draw.rectangle((x, y, x + width, y + 72), fill=(235, 240, 246))
    draw.text((x + 14, y + 10), f"step {step_idx}", fill=(25, 30, 35))
    draw.text((x + 14, y + 30), f"contact={contact}  grasp_contact={grasp}", fill=(25, 30, 35))
    draw.text((x + 14, y + 50), f"distance={distance:.4f}  object_height={height:.4f}", fill=(25, 30, 35))


def _make_video_frame(
    source_image,
    landmark_image,
    shadow_image,
    label: str,
    source_frame_idx: int,
    step_idx: int,
    info: Dict[str, Any],
):
    from PIL import Image, ImageDraw

    width, height = 1600, 720
    header_h = 54
    margin = 20
    gap = 14
    source_w = 456
    landmark_w = 456
    shadow_w = width - 2 * margin - 2 * gap - source_w - landmark_w
    panel_h = height - header_h - margin
    canvas = Image.new("RGB", (width, height), (246, 247, 249))
    draw = ImageDraw.Draw(canvas)

    _draw_header(
        draw,
        margin,
        10,
        f"{label}: real hand video -> landmark graph -> Shadow replay",
        f"source frame {source_frame_idx} / retarget step {step_idx}",
    )

    y = header_h
    x = margin
    draw.text((x, y + 6), "source video", fill=(35, 40, 48))
    canvas.paste(_fit_to_panel(source_image, (source_w, panel_h - 28)), (x, y + 28))

    x += source_w + gap
    draw.text((x, y + 6), "intermediate 21-point graph", fill=(35, 40, 48))
    canvas.paste(_fit_to_panel(landmark_image, (landmark_w, panel_h - 28)), (x, y + 28))

    x += landmark_w + gap
    draw.text((x, y + 6), "MuJoCo Shadow replay", fill=(35, 40, 48))
    shadow_panel_h = panel_h - 28
    shadow_canvas = Image.new("RGB", (shadow_w, shadow_panel_h), (242, 244, 247))
    shadow_canvas.paste(_fit_to_panel(shadow_image, (shadow_w, shadow_panel_h - 86)), (0, 0))
    shadow_draw = ImageDraw.Draw(shadow_canvas)
    _draw_metric_strip(shadow_draw, 0, shadow_panel_h - 78, shadow_w, step_idx, info)
    canvas.paste(shadow_canvas, (x, y + 28))
    return canvas


def _make_comparison_video(
    video_path: Path,
    retarget_path: Path,
    rollout_path: Path,
    out_path: Path,
    label: str,
    source_start: int,
    source_stride: int,
    write_stride: int,
    mirror_source: bool,
    placement_mode: str = "demo",
    placement_jitter: float = 0.0,
    camera: str = "shadow_front",
    render_width: int = 640,
    render_height: int = 480,
) -> Dict[str, Any]:
    import cv2
    import mujoco
    from PIL import Image

    from scripts.common.grasp_workflow import place_object
    from src.environments.shadow_grasp_env import ShadowGraspEnv

    payload = np.load(retarget_path, allow_pickle=True)
    actions = np.asarray(payload["actions"], dtype=np.float32)
    landmarks = np.asarray(payload["landmarks"], dtype=np.float32)
    source_frame_indices = (
        np.asarray(payload["source_frame_indices"], dtype=np.float32)
        if "source_frame_indices" in payload
        else np.asarray([], dtype=np.float32)
    )
    infos = _load_rollout_infos(rollout_path)
    source_stride = max(1, int(source_stride))
    write_stride = max(1, int(write_stride))
    if actions.shape[0] == 0:
        raise ValueError(f"Retarget output has no actions: {retarget_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open source video: {video_path}")
    source_fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    output_fps = max(1.0, source_fps / float(source_stride * write_stride))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), output_fps, (1600, 720))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Could not open video writer: {out_path}")

    env = ShadowGraspEnv(max_steps=max(len(actions), 1), observation_mode="oracle")
    env.reset()
    place_object(env, placement_mode=placement_mode, placement_jitter=float(placement_jitter), verbose=False)
    renderer = mujoco.Renderer(env.model, height=int(render_height), width=int(render_width))
    bounds = _landmark_bounds(landmarks)
    written = 0

    try:
        for step_idx, action in enumerate(actions):
            if step_idx % write_stride == 0 or step_idx == len(actions) - 1:
                if source_frame_indices.size > step_idx:
                    source_frame_idx = int(round(float(source_frame_indices[step_idx])))
                else:
                    source_frame_idx = int(source_start + step_idx * source_stride)
                cap.set(cv2.CAP_PROP_POS_FRAMES, source_frame_idx)
                ok, frame = cap.read()
                if not ok:
                    frame = np.zeros((720, 480, 3), dtype=np.uint8)
                if mirror_source:
                    frame = cv2.flip(frame, 1)
                source_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                landmark_image = _draw_landmark_panel(landmarks[step_idx], (456, 638), bounds)
                renderer.update_scene(env.data, camera=camera)
                shadow_image = Image.fromarray(renderer.render())
                info = infos[min(step_idx, len(infos) - 1)] if infos else {}
                combined = _make_video_frame(
                    source_image=source_image,
                    landmark_image=landmark_image,
                    shadow_image=shadow_image,
                    label=label,
                    source_frame_idx=source_frame_idx,
                    step_idx=step_idx,
                    info=info,
                )
                writer.write(cv2.cvtColor(np.asarray(combined), cv2.COLOR_RGB2BGR))
                written += 1
            env.step(action.astype(np.float32))
    finally:
        renderer.close()
        writer.release()
        cap.release()

    return {
        "path": str(out_path),
        "frames_written": int(written),
        "source_fps": float(source_fps),
        "output_fps": float(output_fps),
        "write_stride": int(write_stride),
        "source_start": int(source_start),
        "source_stride": int(source_stride),
    }


def _resize_to_width(image, width: int):
    if image.width == width:
        return image
    height = int(round(image.height * width / max(image.width, 1)))
    return image.resize((width, height))


def _metric_lines(label: str, summary: Dict[str, Any], slice_note: str) -> List[str]:
    metrics = summary.get("metrics", {}) or {}
    return [
        f"{label}",
        f"slice: {slice_note}",
        f"steps: {summary.get('steps', 0)}",
        f"success: {summary.get('success', False)}",
        f"terminal_success: {summary.get('terminal_success', False)}",
        f"grasp_contact_steps: {metrics.get('grasp_contact_steps', 0)}",
        f"max_grasp_contact_duration: {metrics.get('max_grasp_contact_duration', 0)}",
        f"final_distance: {float(metrics.get('final_distance', 0.0)):.4f}",
        f"object_height: {float(metrics.get('object_height', 0.0)):.4f}",
    ]


def _make_comparison_overview(
    source_sheet: Path,
    full_visual_dir: Path,
    segment_visual_dir: Path,
    full_summary: Dict[str, Any],
    segment_summary: Dict[str, Any],
    segment_start: int,
    segment_end: int,
    out_path: Path,
) -> None:
    from PIL import Image, ImageDraw

    width = 1600
    margin = 28
    gap = 18
    text_h = 150
    title_h = 70
    source = _resize_to_width(Image.open(source_sheet).convert("RGB"), width - 2 * margin)
    full = _resize_to_width(Image.open(full_visual_dir / "shadow_mujoco_keyframes.png").convert("RGB"), width - 2 * margin)
    segment = _resize_to_width(
        Image.open(segment_visual_dir / "shadow_mujoco_keyframes.png").convert("RGB"),
        width - 2 * margin,
    )
    metric_h = max(170, text_h)
    height = title_h + source.height + gap + metric_h + full.height + gap + metric_h + segment.height + margin

    canvas = Image.new("RGB", (width, height), (246, 247, 249))
    draw = ImageDraw.Draw(canvas)
    y = 18
    draw.text((margin, y), "Real Hand Video -> Shadow Retarget Comparison", fill=(20, 20, 20))
    y += title_h - 18
    draw.text((margin, y - 24), "source video keyframes", fill=(60, 60, 60))
    canvas.paste(source, (margin, y))
    y += source.height + gap

    full_lines = _metric_lines("FULL VIDEO", full_summary, "all frames")
    draw.rectangle((margin, y, width - margin, y + metric_h), fill=(235, 240, 246))
    for idx, line in enumerate(full_lines):
        draw.text((margin + 16, y + 12 + idx * 17), line, fill=(30, 30, 30))
    y += metric_h
    canvas.paste(full, (margin, y))
    y += full.height + gap

    segment_lines = _metric_lines(
        "SEGMENT",
        segment_summary,
        f"[{segment_start}, {segment_end})",
    )
    draw.rectangle((margin, y, width - margin, y + metric_h), fill=(235, 246, 238))
    for idx, line in enumerate(segment_lines):
        draw.text((margin + 16, y + 12 + idx * 17), line, fill=(30, 30, 30))
    y += metric_h
    canvas.paste(segment, (margin, y))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def _write_run_readme(output_root: Path, command: List[str], summary: Dict[str, Any]) -> None:
    readme = output_root / "README.md"
    text = [
        "# One-Command Real Hand Video Compare",
        "",
        "This folder was generated by `scripts/vision/run_real_hand_video_compare.py`.",
        "",
        "## Command",
        "",
        "```bash",
        " ".join(command),
        "```",
        "",
        "## Main Output",
        "",
        f"- comparison overview: `{Path(summary['comparison_overview']).name}`",
        f"- source video: `{Path(summary['source_video']).relative_to(output_root)}`",
        f"- full visualization: `{Path(summary['full']['visualization_dir']).relative_to(output_root)}`",
        f"- segment visualization: `{Path(summary['segment']['visualization_dir']).relative_to(output_root)}`",
    ]
    full_video = summary["full"].get("comparison_video")
    segment_video = summary["segment"].get("comparison_video")
    if full_video and segment_video:
        text.extend(
            [
                f"- full comparison video: `{Path(full_video['path']).relative_to(output_root)}`",
                f"- segment comparison video: `{Path(segment_video['path']).relative_to(output_root)}`",
                "",
                "The MP4 comparison videos show the source frame, the intermediate",
                "21-point landmark graph, and the synchronized MuJoCo Shadow replay.",
            ]
        )
    text.extend(
        [
            "",
            "## Result",
            "",
            f"- full success: `{summary['full']['rollout_summary'].get('success')}`",
            f"- segment success: `{summary['segment']['rollout_summary'].get('success')}`",
            "",
        ]
    )
    readme.write_text("\n".join(text), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one-command real-hand video retarget comparison")
    parser.add_argument(
        "--video",
        default=str(_default_video_path()),
        help="Input hand video. Defaults to the organized hand-example video.",
    )
    parser.add_argument(
        "--output-root",
        default=str(_default_output_root()),
        help="Experiment output directory.",
    )
    parser.add_argument(
        "--hand-landmarker-model",
        default="",
        help="Optional existing hand_landmarker.task path. A model is downloaded into output-root/models if omitted.",
    )
    parser.add_argument("--model-url", default=DEFAULT_MODEL_URL, help="Download URL for hand_landmarker.task")
    parser.add_argument("--segment-start", type=int, default=0, help="Comparison segment start frame")
    parser.add_argument("--segment-end", type=int, default=430, help="Comparison segment exclusive end frame")
    parser.add_argument("--segment-stride", type=int, default=1, help="Comparison segment frame stride")
    parser.add_argument("--full-smoothing-alpha", type=float, default=0.15, help="Full-video retarget smoothing")
    parser.add_argument("--segment-smoothing-alpha", type=float, default=0.25, help="Segment retarget smoothing")
    parser.add_argument(
        "--retarget-time-scale",
        type=int,
        default=3,
        help="Slow the real-hand motion by inserting N-1 interpolated action steps between visual frames",
    )
    parser.add_argument("--max-keyframes", type=int, default=8, help="Keyframes per visual contact sheet")
    parser.add_argument(
        "--video-frame-stride",
        type=int,
        default=2,
        help="Write every Nth retarget step to comparison MP4 while still stepping every action",
    )
    parser.add_argument(
        "--skip-comparison-video",
        action="store_true",
        help="Skip full/segment MP4 comparison generation",
    )
    parser.add_argument("--mirror", action="store_true", help="Mirror source video before MediaPipe detection")
    parser.add_argument("--mirror-x", action="store_true", help="Mirror landmark x during Shadow retarget")
    parser.add_argument("--force", action="store_true", help="Delete output-root before running")
    parser.add_argument("--open", action="store_true", help="Open the comparison image when complete")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    sim_root = _simulations_root()
    output_root = Path(args.output_root).resolve()
    video_path = Path(args.video).resolve()
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    if args.force and output_root.exists():
        shutil.rmtree(output_root)

    source_dir = output_root / "source"
    model_dir = output_root / "models"
    data_dir = output_root / "data"
    report_dir = output_root / "reports"
    visual_dir = output_root / "visualization"
    for path in (source_dir, model_dir, data_dir, report_dir, visual_dir):
        path.mkdir(parents=True, exist_ok=True)

    copied_video = source_dir / video_path.name
    if video_path != copied_video:
        shutil.copy2(video_path, copied_video)

    model_path = Path(args.hand_landmarker_model).resolve() if args.hand_landmarker_model else model_dir / "hand_landmarker.task"
    model_path = _ensure_hand_landmarker_model(model_path, args.model_url)

    trace_path = data_dir / "real_hand_trace.npz"
    trace_report = report_dir / "real_hand_trace.json"
    collect_cmd = [
        sys.executable,
        "scripts/vision/collect_palm_trace.py",
        "--source",
        str(copied_video),
        "--hand-landmarker-model",
        str(model_path),
        "--output",
        str(trace_path),
        "--report",
        str(trace_report),
        "--source-label",
        copied_video.name,
    ]
    if args.mirror:
        collect_cmd.append("--mirror")
    _run(collect_cmd, cwd=sim_root)

    source_sheet = _extract_source_keyframes(
        copied_video,
        visual_dir / "source_video",
        max_keyframes=args.max_keyframes,
    )

    runs = {
        "full_video": {
            "start": 0,
            "end": 0,
            "stride": 1,
            "smoothing": float(args.full_smoothing_alpha),
            "time_scale": int(args.retarget_time_scale),
        },
        "segment": {
            "start": int(args.segment_start),
            "end": int(args.segment_end),
            "stride": int(args.segment_stride),
            "smoothing": float(args.segment_smoothing_alpha),
            "time_scale": int(args.retarget_time_scale),
        },
    }
    run_summaries: Dict[str, Dict[str, Any]] = {}
    for name, config in runs.items():
        retarget_path = data_dir / f"{name}_shadow_retarget.npz"
        rollout_path = data_dir / f"{name}_shadow_retarget_replay.npz"
        retarget_report = report_dir / f"{name}_shadow_retarget.json"
        retarget_cmd = [
            sys.executable,
            "scripts/vision/retarget_palm_trace_to_shadow.py",
            "--palm-trace",
            str(trace_path),
            "--start-frame",
            str(config["start"]),
            "--end-frame",
            str(config["end"]),
            "--stride",
            str(config["stride"]),
            "--smoothing-alpha",
            str(config["smoothing"]),
            "--action-time-scale",
            str(config["time_scale"]),
            "--output",
            str(retarget_path),
            "--rollout-output",
            str(rollout_path),
            "--report",
            str(retarget_report),
        ]
        if args.mirror_x:
            retarget_cmd.append("--mirror-x")
        _run(retarget_cmd, cwd=sim_root)

        run_visual_dir = visual_dir / name
        visualize_cmd = [
            sys.executable,
            "scripts/vision/visualize_shadow_retarget.py",
            "--retarget",
            str(retarget_path),
            "--rollout",
            str(rollout_path),
            "--output-dir",
            str(run_visual_dir),
            "--render-mujoco",
            "--max-keyframes",
            str(args.max_keyframes),
        ]
        _run(visualize_cmd, cwd=sim_root)

        run_summaries[name] = {
            "config": config,
            "retarget": str(retarget_path),
            "rollout": str(rollout_path),
            "report": str(retarget_report),
            "visualization_dir": str(run_visual_dir),
            "retarget_metadata": _load_npz_metadata(retarget_path),
            "rollout_summary": _load_rollout_summary(rollout_path),
        }

    if not args.skip_comparison_video:
        video_dir = output_root / "videos"
        video_dir.mkdir(parents=True, exist_ok=True)
        for name, label in (("full_video", "FULL VIDEO"), ("segment", "SEGMENT")):
            config = runs[name]
            comparison_video = _make_comparison_video(
                video_path=copied_video,
                retarget_path=Path(run_summaries[name]["retarget"]),
                rollout_path=Path(run_summaries[name]["rollout"]),
                out_path=video_dir / f"{name}_comparison.mp4",
                label=label,
                source_start=int(config["start"]),
                source_stride=int(config["stride"]),
                write_stride=int(args.video_frame_stride),
                mirror_source=bool(args.mirror),
            )
            keyframe_sheet = _extract_video_keyframes(
                Path(comparison_video["path"]),
                visual_dir / name,
                f"{name}_comparison_video_keyframes",
                max_keyframes=args.max_keyframes,
            )
            comparison_video["keyframes"] = str(keyframe_sheet)
            run_summaries[name]["comparison_video"] = comparison_video

    comparison_path = output_root / "comparison_overview.png"
    _make_comparison_overview(
        source_sheet=source_sheet,
        full_visual_dir=visual_dir / "full_video",
        segment_visual_dir=visual_dir / "segment",
        full_summary=run_summaries["full_video"]["rollout_summary"],
        segment_summary=run_summaries["segment"]["rollout_summary"],
        segment_start=int(args.segment_start),
        segment_end=int(args.segment_end),
        out_path=comparison_path,
    )

    command = [sys.executable, str(Path(__file__).relative_to(sim_root))]
    command.extend(sys.argv[1:])
    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_video": str(copied_video),
        "source_keyframes": str(source_sheet),
        "comparison_overview": str(comparison_path),
        "trace": str(trace_path),
        "full": run_summaries["full_video"],
        "segment": run_summaries["segment"],
    }
    summary_path = output_root / "comparison_summary.json"
    summary_path.write_text(json.dumps(_json_ready(summary), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _write_run_readme(output_root, command, summary)

    print("\nComparison complete.")
    print(f"Overview: {comparison_path}")
    print(f"Summary: {summary_path}")
    if not args.skip_comparison_video:
        print(f"Full comparison video: {run_summaries['full_video']['comparison_video']['path']}")
        print(f"Segment comparison video: {run_summaries['segment']['comparison_video']['path']}")
    print(
        "Full vs segment success: "
        f"{run_summaries['full_video']['rollout_summary'].get('success')} -> "
        f"{run_summaries['segment']['rollout_summary'].get('success')}"
    )

    if args.open:
        os.startfile(str(comparison_path))
        if not args.skip_comparison_video:
            os.startfile(str(run_summaries["segment"]["comparison_video"]["path"]))


if __name__ == "__main__":
    main()
