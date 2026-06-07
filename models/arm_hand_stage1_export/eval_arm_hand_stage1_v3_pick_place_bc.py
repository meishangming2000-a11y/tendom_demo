#!/usr/bin/env python3
"""Online fixed-target and target-sweep eval for the Stage2 pick-place BC policy."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np
import torch

from arm_hand_stage1_task_api import ArmHandStage1TaskAPI, json_ready
from arm_hand_stage1_v2_bc_common import load_policy, predict_action
from arm_hand_stage1_v3_pick_place_task_api import (
    CURRENT_PICK_PLACE_SCENE,
    DEFAULT_REQUIRED_STABLE_STEPS,
    DEFAULT_TARGET_CENTER,
    DEFAULT_TARGET_RADIUS_M,
    TASK_CONTRACT_VERSION,
    compute_pick_place_metrics,
    evaluate_pick_place_state,
)
from collect_arm_hand_stage1_v3_pick_place_dataset_v0_5 import extended_observation, update_counters
from demo_arm_hand_stage1_v3_pick_place_scripted import setup_pick_place_camera
from render_arm_hand_lift_ball_video import FrameWriter


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"
DEFAULT_CHECKPOINT = CHECKPOINTS / "bc_arm_hand_stage1_v3_pick_place_dataset_v0_5_obs_phase_target.pth"
DEFAULT_REPORT = DOCS / "arm_hand_stage1_v3_pick_place_bc_v0_5_eval_report.md"
DEFAULT_META = META / "arm_hand_stage1_v3_pick_place_bc_v0_5_eval.json"


def render_policy_frame(renderer, api: ArmHandStage1TaskAPI, target_center: np.ndarray) -> np.ndarray:
    cam = setup_pick_place_camera(api.model, api.data, api.mujoco, target_center)
    renderer.update_scene(api.data, camera=cam)
    return renderer.render()


def write_contact_sheet(path: Path, snapshots: dict[str, str]) -> None:
    from PIL import Image, ImageDraw

    items = list(snapshots.items())
    if not items:
        return
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
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def parse_values(raw: str) -> list[float]:
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def build_target_rows(args) -> list[dict[str, Any]]:
    base = np.asarray(args.target_center, dtype=np.float64)
    rows = []
    episode_id = 0
    for dx in parse_values(args.x_offsets):
        for dy in parse_values(args.y_offsets):
            offset = np.array([dx, dy, 0.0], dtype=np.float64)
            rows.append({"episode_id": int(episode_id), "target_offset": offset, "target_center": base + offset})
            episode_id += 1
    return rows


def run_policy_episode(
    *,
    api: ArmHandStage1TaskAPI,
    model,
    checkpoint: dict[str, Any],
    device: torch.device,
    episode_id: int,
    target_center: np.ndarray,
    target_offset: np.ndarray,
    max_steps: int,
    target_radius: float,
    required_stable_steps: int,
    action_smoothing: float,
    clip_to_train_range: bool,
    sample_every: int,
    renderer=None,
    video_writer: FrameWriter | None = None,
    visual_dir: Path | None = None,
    snapshot_prefix: str = "policy_demo",
    capture_every: int = 4,
) -> dict[str, Any]:
    api.reset_hand_open()
    initial_ball = api.get_ball_pose()["position"].copy()
    counters: dict[str, Any] = {
        "lifted_once": False,
        "release_started": False,
        "transport_floor_contacts": 0,
        "stable_target_steps": 0,
        "step_count": 0,
    }
    prev_action: np.ndarray | None = None
    trace = []
    final_eval: dict[str, Any] | None = None
    action_l2_sum = 0.0
    action_delta_l2_sum = 0.0
    max_action_abs = 0.0
    snapshots: dict[str, str] = {}
    snapshot_phases = {
        "close_thumb",
        "close_hold",
        "lift",
        "hold_lift",
        "transport",
        "transport_hold",
        "descend_to_target",
        "pre_release_settle",
        "release",
        "retreat",
        "settle_on_target",
    }
    if renderer is not None and video_writer is not None:
        video_writer.append(render_policy_frame(renderer, api, target_center))
    for step_id in range(max_steps):
        obs_ext, _ = extended_observation(api, target_center)
        action, pred_norm = predict_action(
            model,
            checkpoint,
            obs_ext,
            step_id=step_id,
            target_center=target_center,
            device=device,
            clip_to_train_range=clip_to_train_range,
        )
        if prev_action is not None and action_smoothing > 0.0:
            smoothing = float(np.clip(action_smoothing, 0.0, 0.99))
            action = smoothing * prev_action + (1.0 - smoothing) * action
        if prev_action is not None:
            action_delta_l2_sum += float(np.linalg.norm(action - prev_action))
        prev_action = action.copy()
        action_l2_sum += float(np.linalg.norm(action))
        max_action_abs = max(max_action_abs, float(np.max(np.abs(action))))
        phase_id, _ = phase_from_checkpoint(checkpoint, step_id)
        phase_name = checkpoint["feature_config"]["phase_names"][phase_id]
        api.step_action(action, n=1, pin_ball=False)
        metrics = update_counters(api, initial_ball, target_center, phase_name, counters, target_radius)
        evaluation = evaluate_pick_place_state(
            api,
            initial_ball,
            target_center=target_center,
            step_count=int(counters["step_count"]),
            max_episode_steps=max_steps,
            lifted_once=bool(counters["lifted_once"]),
            release_started=bool(counters["release_started"]),
            stable_target_steps=int(counters["stable_target_steps"]),
            transport_floor_contacts=int(counters["transport_floor_contacts"]),
            target_radius_m=target_radius,
            required_stable_steps=required_stable_steps,
        )
        final_eval = evaluation
        if renderer is not None and video_writer is not None and step_id % max(1, capture_every) == 0:
            video_writer.append(render_policy_frame(renderer, api, target_center))
        if renderer is not None and visual_dir is not None and phase_name in snapshot_phases and phase_name not in snapshots:
            next_phase_id, _ = phase_from_checkpoint(checkpoint, step_id + 1)
            next_phase_name = checkpoint["feature_config"]["phase_names"][next_phase_id]
            if next_phase_name != phase_name or evaluation["done"]:
                path = visual_dir / f"{snapshot_prefix}_{len(snapshots):02d}_{phase_name}.png"
                imageio.imwrite(path, render_policy_frame(renderer, api, target_center))
                snapshots[phase_name] = str(path)
        if step_id % max(1, sample_every) == 0 or evaluation["done"]:
            contact = metrics["contact"]
            trace.append(
                {
                    "step": int(step_id + 1),
                    "phase": phase_name,
                    "status": evaluation["episode_status"],
                    "reason": evaluation["terminal_reason"],
                    "target_distance_xy": float(metrics["target_distance_xy"]),
                    "lift_height": float(metrics["ball_lift_height"]),
                    "stable_target_steps": int(counters["stable_target_steps"]),
                    "transport_floor_contacts": int(counters["transport_floor_contacts"]),
                    "ball_hand_contacts": int(contact["ball_hand_contact_count"]),
                    "ball_floor_contacts": int(contact.get("ball_floor_contact_count", 0)),
                    "max_penetration": float(contact["max_penetration"]),
                    "action_norm_l2": float(np.linalg.norm(action)),
                    "pred_norm_l2": float(np.linalg.norm(pred_norm)),
                }
            )
        if evaluation["done"]:
            break
    if final_eval is None:
        final_eval = evaluate_pick_place_state(
            api,
            initial_ball,
            target_center=target_center,
            step_count=0,
            max_episode_steps=max_steps,
        )
    final_metrics = compute_pick_place_metrics(api, initial_ball, target_center)
    contact = final_metrics["contact"]
    success = bool(final_eval["success"])
    if success:
        status = "PASS"
    elif final_eval["terminal_reason"] == "timeout":
        status = "FAIL"
    else:
        status = "PARTIAL"
    steps = max(1, int(final_eval["step_count"]))
    return {
        "episode_id": int(episode_id),
        "target_center": target_center,
        "target_offset": target_offset,
        "status": status,
        "terminal_reason": final_eval["terminal_reason"],
        "success": success,
        "failure": bool(final_eval["failure"]),
        "steps": int(final_eval["step_count"]),
        "stable_target_steps": int(counters["stable_target_steps"]),
        "transport_floor_contacts": int(counters["transport_floor_contacts"]),
        "final_target_distance_xy": float(final_metrics["target_distance_xy"]),
        "final_ball_position": final_metrics["ball_position"],
        "final_lift_height": float(final_metrics["ball_lift_height"]),
        "final_hand_contacts": int(contact["ball_hand_contact_count"]),
        "final_floor_contacts": int(contact.get("ball_floor_contact_count", 0)),
        "max_penetration": float(contact["max_penetration"]),
        "action_l2_mean": float(action_l2_sum / steps),
        "action_delta_l2_mean": float(action_delta_l2_sum / steps),
        "max_action_abs": float(max_action_abs),
        "snapshots": snapshots,
        "trace": trace,
    }


def phase_from_checkpoint(checkpoint: dict[str, Any], step_id: int) -> tuple[int, int]:
    lengths = [int(v) for v in checkpoint["feature_config"].get("phase_lengths", [])]
    cursor = 0
    last = 0
    for phase_id, length in enumerate(lengths):
        if length <= 0:
            continue
        last = phase_id
        if step_id < cursor + length:
            return int(phase_id), int(step_id - cursor)
        cursor += length
    return int(last), max(0, int(step_id - cursor))


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    success_count = sum(1 for row in results if row["success"])
    reasons = Counter(str(row["terminal_reason"]) for row in results)
    target_dist = [float(row["final_target_distance_xy"]) for row in results]
    stable_steps = [int(row["stable_target_steps"]) for row in results]
    transport_floor = [int(row["transport_floor_contacts"]) for row in results]
    final_hand = [int(row["final_hand_contacts"]) for row in results]
    status = "PASS" if success_count == len(results) else ("PARTIAL" if success_count else "FAIL")
    return {
        "status": status,
        "episodes": int(len(results)),
        "success_count": int(success_count),
        "terminal_reason_counts": dict(reasons),
        "target_distance_xy_min": float(np.min(target_dist)) if target_dist else None,
        "target_distance_xy_max": float(np.max(target_dist)) if target_dist else None,
        "target_distance_xy_mean": float(np.mean(target_dist)) if target_dist else None,
        "stable_steps_min": int(np.min(stable_steps)) if stable_steps else None,
        "stable_steps_max": int(np.max(stable_steps)) if stable_steps else None,
        "transport_floor_contacts_total": int(np.sum(transport_floor)) if transport_floor else 0,
        "final_hand_contacts_max": int(np.max(final_hand)) if final_hand else 0,
    }


def write_csv(path: Path, results: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "episode_id",
                "target_offset_x",
                "target_offset_y",
                "status",
                "terminal_reason",
                "target_distance_xy",
                "stable_target_steps",
                "transport_floor_contacts",
                "final_hand_contacts",
                "steps",
            ]
        )
        for row in results:
            writer.writerow(
                [
                    row["episode_id"],
                    float(row["target_offset"][0]),
                    float(row["target_offset"][1]),
                    row["status"],
                    row["terminal_reason"],
                    float(row["final_target_distance_xy"]),
                    int(row["stable_target_steps"]),
                    int(row["transport_floor_contacts"]),
                    int(row["final_hand_contacts"]),
                    int(row["steps"]),
                ]
            )


def write_heatmap(path: Path, results: list[dict[str, Any]], target_radius: float) -> None:
    from PIL import Image, ImageDraw

    xs = sorted({float(row["target_offset"][0]) for row in results})
    ys = sorted({float(row["target_offset"][1]) for row in results})
    cell = 92
    margin_left = 70
    margin_top = 50
    width = margin_left + len(xs) * cell + 20
    height = margin_top + len(ys) * cell + 55
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((14, 14), "Pick-place narrow sweep: PASS green, fail red", fill=(0, 0, 0))
    by_key = {(float(row["target_offset"][0]), float(row["target_offset"][1])): row for row in results}
    for ix, x in enumerate(xs):
        draw.text((margin_left + ix * cell + 12, margin_top - 24), f"x={x:+.2f}", fill=(0, 0, 0))
    for iy, y in enumerate(ys):
        y_screen = margin_top + (len(ys) - 1 - iy) * cell
        draw.text((12, y_screen + 32), f"y={y:+.2f}", fill=(0, 0, 0))
        for ix, x in enumerate(xs):
            row = by_key[(x, y)]
            dist = float(row["final_target_distance_xy"])
            ok = bool(row["success"])
            color = (96, 176, 112) if ok else (216, 112, 112)
            if ok and dist > 0.8 * target_radius:
                color = (224, 188, 92)
            x0 = margin_left + ix * cell
            y0 = y_screen
            draw.rectangle([x0, y0, x0 + cell - 6, y0 + cell - 6], fill=color, outline=(80, 80, 80))
            draw.text((x0 + 9, y0 + 12), row["status"], fill=(0, 0, 0))
            draw.text((x0 + 9, y0 + 38), f"{dist:.3f}m", fill=(0, 0, 0))
            draw.text((x0 + 9, y0 + 62), f"s={row['stable_target_steps']}", fill=(0, 0, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = payload["summary"]
    lines = [
        "# Arm-Hand Stage1 V3 Pick-Place BC V0.5 Eval Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Eval name: `{payload['eval_name']}`\n",
        f"- Status: **{s['status']}**\n",
        f"- Checkpoint: `{payload['checkpoint']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Episodes: `{s['episodes']}`\n",
        f"- Success count: `{s['success_count']} / {s['episodes']}`\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n",
        f"- Target radius: `{payload['target_radius']:.3f} m`\n",
        f"- Required stable steps: `{payload['required_stable_steps']}`\n",
        f"- Target distance XY range: `{s['target_distance_xy_min']:.6f} m` to `{s['target_distance_xy_max']:.6f} m`\n",
        f"- Target distance XY mean: `{s['target_distance_xy_mean']:.6f} m`\n",
        f"- Stable steps range: `{s['stable_steps_min']}` to `{s['stable_steps_max']}`\n",
        f"- Transport floor contacts total: `{s['transport_floor_contacts_total']}`\n",
        f"- Final hand contacts max: `{s['final_hand_contacts_max']}`\n",
        f"- Action smoothing: `{payload['action_smoothing']}`\n",
        f"- CSV: `{payload.get('csv')}`\n",
        f"- Heatmap: `{payload.get('heatmap')}`\n\n",
        f"- Demo video: `{payload.get('video')}`\n",
        f"- Demo contact sheet: `{payload.get('contact_sheet')}`\n\n",
        "## Episode Results\n\n",
        "| ep | target offset xy | status | reason | steps | target xy m | stable steps | transport floor | final hand | final floor | max pen m |\n",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for row in payload["results"]:
        lines.append(
            f"| {row['episode_id']} | `{np.round(row['target_offset'][:2], 4).tolist()}` | "
            f"{row['status']} | {row['terminal_reason']} | {row['steps']} | "
            f"{row['final_target_distance_xy']:.6f} | {row['stable_target_steps']} | "
            f"{row['transport_floor_contacts']} | {row['final_hand_contacts']} | "
            f"{row['final_floor_contacts']} | {row['max_penetration']:.6f} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This is online policy evaluation in MuJoCo, not deterministic dataset replay.\n",
            "- Fixed-target PASS answers whether the policy can perform the most familiar pick-place case.\n",
            "- Narrow-sweep PASS is only a tolerance diagnostic because v0.5 was fixed-target data.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def resolve_outputs(args) -> tuple[Path, Path, Path, Path | None, Path | None, Path | None, Path | None]:
    run_dir = Path(args.run_dir).resolve() if args.run_dir else None
    report = args.report
    metadata = args.metadata
    csv_path = args.csv
    heatmap = args.heatmap
    video = args.video
    contact_sheet = args.contact_sheet
    if run_dir:
        (run_dir / "eval").mkdir(parents=True, exist_ok=True)
        (run_dir / "visuals").mkdir(parents=True, exist_ok=True)
        report = report or (run_dir / "eval" / f"{args.eval_name}_eval_report.md")
        metadata = metadata or (run_dir / "eval" / f"{args.eval_name}_summary.json")
        csv_path = csv_path or (run_dir / "eval" / f"{args.eval_name}_target_sweep.csv")
        heatmap = heatmap or (run_dir / "visuals" / f"{args.eval_name}_target_sweep_heatmap.png")
        video = video or (run_dir / "visuals" / f"{args.eval_name}_policy_demo.mp4")
        contact_sheet = contact_sheet or (run_dir / "visuals" / f"{args.eval_name}_policy_contact_sheet.png")
    else:
        report = report or DEFAULT_REPORT
        metadata = metadata or DEFAULT_META
    return (
        Path(report),
        Path(metadata),
        Path(csv_path) if csv_path else None,
        Path(heatmap) if heatmap else None,
        run_dir,
        Path(video) if video else None,
        Path(contact_sheet) if contact_sheet else None,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a Stage2 pick-place BC policy online.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--scene", type=Path, default=CURRENT_PICK_PLACE_SCENE)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--metadata", type=Path, default=None)
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument("--heatmap", type=Path, default=None)
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--contact-sheet", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--eval-name", default="fixed_target")
    parser.add_argument("--target-center", type=lambda raw: np.asarray(parse_values(raw), dtype=np.float64), default=DEFAULT_TARGET_CENTER)
    parser.add_argument("--x-offsets", default="0.0")
    parser.add_argument("--y-offsets", default="0.0")
    parser.add_argument("--target-radius", type=float, default=DEFAULT_TARGET_RADIUS_M)
    parser.add_argument("--required-stable-steps", type=int, default=DEFAULT_REQUIRED_STABLE_STEPS)
    parser.add_argument("--max-steps", type=int, default=4200)
    parser.add_argument("--sample-every", type=int, default=100)
    parser.add_argument("--action-smoothing", type=float, default=0.2)
    parser.add_argument("--render-video", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--render-snapshots", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--render-episode-id", type=int, default=0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--capture-every", type=int, default=4)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=676)
    parser.add_argument("--no-train-range-clip", action="store_true")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA unavailable; using CPU.")
        args.device = "cpu"
    device = torch.device(args.device)
    report_path, metadata_path, csv_path, heatmap_path, run_dir, video_path, contact_sheet_path = resolve_outputs(args)
    model, checkpoint = load_policy(args.checkpoint, device)
    api = ArmHandStage1TaskAPI(args.scene)
    target_rows = build_target_rows(args)
    results = []
    rendered_video: str | None = None
    rendered_contact_sheet: str | None = None
    all_snapshots: dict[str, str] = {}
    for row in target_rows:
        render_this = int(row["episode_id"]) == int(args.render_episode_id) and (args.render_video or args.render_snapshots)
        renderer = None
        writer_ctx = None
        writer = None
        visual_dir = run_dir / "visuals" if run_dir else (report_path.parent / "visuals")
        try:
            if render_this:
                import mujoco

                visual_dir.mkdir(parents=True, exist_ok=True)
                renderer = mujoco.Renderer(api.model, width=args.width, height=args.height)
                if args.render_video:
                    assert video_path is not None
                    video_path.parent.mkdir(parents=True, exist_ok=True)
                    writer_ctx = FrameWriter(video_path.resolve(), args.fps)
                    writer = writer_ctx.__enter__()
            result = run_policy_episode(
                api=api,
                model=model,
                checkpoint=checkpoint,
                device=device,
                episode_id=row["episode_id"],
                target_center=row["target_center"],
                target_offset=row["target_offset"],
                max_steps=args.max_steps,
                target_radius=args.target_radius,
                required_stable_steps=args.required_stable_steps,
                action_smoothing=args.action_smoothing,
                clip_to_train_range=not args.no_train_range_clip,
                sample_every=args.sample_every,
                renderer=renderer,
                video_writer=writer,
                visual_dir=visual_dir if args.render_snapshots else None,
                snapshot_prefix=args.eval_name,
                capture_every=args.capture_every,
            )
        finally:
            if writer_ctx is not None:
                writer_ctx.__exit__(None, None, None)
            if renderer is not None:
                renderer.close()
        if render_this:
            if args.render_video and video_path is not None:
                rendered_video = str(video_path)
            if args.render_snapshots:
                all_snapshots.update({str(k): str(v) for k, v in result.get("snapshots", {}).items()})
                if all_snapshots and contact_sheet_path is not None:
                    write_contact_sheet(contact_sheet_path, all_snapshots)
                    rendered_contact_sheet = str(contact_sheet_path)
        results.append(result)
        print(
            f"ep={result['episode_id']:02d} offset={np.round(result['target_offset'][:2], 4).tolist()} "
            f"{result['status']} reason={result['terminal_reason']} "
            f"dist={result['final_target_distance_xy']:.4f} stable={result['stable_target_steps']}"
        )
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "eval_name": args.eval_name,
        "checkpoint": str(args.checkpoint.resolve()),
        "scene": str(args.scene.resolve()),
        "device": str(device),
        "target_center": np.asarray(args.target_center, dtype=np.float64),
        "x_offsets": parse_values(args.x_offsets),
        "y_offsets": parse_values(args.y_offsets),
        "target_radius": float(args.target_radius),
        "required_stable_steps": int(args.required_stable_steps),
        "max_steps": int(args.max_steps),
        "action_smoothing": float(args.action_smoothing),
        "clip_to_train_range": not args.no_train_range_clip,
        "contract_version": TASK_CONTRACT_VERSION,
        "checkpoint_status": checkpoint.get("status"),
        "checkpoint_final_val_loss": float(checkpoint.get("final_val_loss", float("nan"))),
        "summary": summarize(results),
        "results": results,
        "csv": str(csv_path) if csv_path else None,
        "heatmap": str(heatmap_path) if heatmap_path else None,
        "video": rendered_video,
        "contact_sheet": rendered_contact_sheet,
        "snapshots": all_snapshots,
        "training_ready": False,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    if csv_path:
        write_csv(csv_path, results)
    if heatmap_path:
        write_heatmap(heatmap_path, results, args.target_radius)
    write_report(report_path, json_ready(payload))
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved report: {report_path}")
    print(f"Saved metadata: {metadata_path}")
    if csv_path:
        print(f"Saved CSV: {csv_path}")
    if heatmap_path:
        print(f"Saved heatmap: {heatmap_path}")
    if rendered_video:
        print(f"Saved video: {rendered_video}")
    if rendered_contact_sheet:
        print(f"Saved contact sheet: {rendered_contact_sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
