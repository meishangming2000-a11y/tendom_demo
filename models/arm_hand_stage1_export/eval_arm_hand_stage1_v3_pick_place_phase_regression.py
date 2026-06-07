#!/usr/bin/env python3
"""Evaluate a v0.7.3 phase-regression pick-place policy online."""

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

from arm_hand_stage1_task_api import ArmHandStage1TaskAPI, json_ready
from arm_hand_stage1_v3_pick_place_task_api import (
    CURRENT_PICK_PLACE_SCENE,
    DEFAULT_REQUIRED_STABLE_STEPS,
    DEFAULT_TARGET_CENTER,
    DEFAULT_TARGET_RADIUS_M,
    TASK_CONTRACT_VERSION,
    compute_pick_place_metrics,
    evaluate_pick_place_state,
)
from collect_arm_hand_stage1_v3_pick_place_dataset_v0_5 import update_counters
from demo_arm_hand_stage1_v3_pick_place_scripted import setup_pick_place_camera
from render_arm_hand_lift_ball_video import FrameWriter
from train_arm_hand_stage1_v3_pick_place_phase_regression import build_features


ROOT = Path(__file__).resolve().parent


def parse_values(raw: str) -> list[float]:
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def parse_target_centers(raw: str) -> list[np.ndarray]:
    rows: list[np.ndarray] = []
    for chunk in raw.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        values = parse_values(chunk)
        if len(values) != 3:
            raise ValueError(f"target center must be x,y,z; got {chunk!r}")
        rows.append(np.asarray(values, dtype=np.float64))
    return rows


def build_target_rows(args) -> list[dict[str, Any]]:
    if args.target_centers:
        return [
            {"episode_id": int(i), "target_offset": np.zeros(3, dtype=np.float64), "target_center": target}
            for i, target in enumerate(parse_target_centers(args.target_centers))
        ]
    base = np.asarray(args.target_center, dtype=np.float64)
    rows = []
    episode_id = 0
    for dx in parse_values(args.x_offsets):
        for dy in parse_values(args.y_offsets):
            offset = np.array([dx, dy, 0.0], dtype=np.float64)
            rows.append({"episode_id": int(episode_id), "target_offset": offset, "target_center": base + offset})
            episode_id += 1
    return rows


def load_policy(path: Path) -> dict[str, Any]:
    data = np.load(path, allow_pickle=False)
    return {
        "path": str(path.resolve()),
        "mode": str(data["mode"][0]),
        "status": str(data["status"][0]),
        "source_dataset": str(data["source_dataset"][0]),
        "action_field": str(data["action_field"][0]),
        "profile_filter": str(data["profile_filter"][0]),
        "phase_names": [str(v) for v in data["phase_names"].tolist()],
        "phase_lengths": data["phase_lengths"].astype(np.int32),
        "feature_names": [str(v) for v in data["feature_names"].tolist()],
        "weights": data["weights"].astype(np.float64),
        "fallback_actions": data["fallback_actions"].astype(np.float64),
        "phase_has_model": data["phase_has_model"].astype(bool),
        "target_centers": data["target_centers"].astype(np.float64),
        "target_offset_centers": data["target_offset_centers"].astype(np.float64),
        "target_drops": data["target_drops"].astype(np.float64),
        "action_min": data["action_min"].astype(np.float64),
        "action_max": data["action_max"].astype(np.float64),
        "rbf_sigma": float(data["rbf_sigma"][0]) if "rbf_sigma" in data.files else 0.075,
        "overall_train_rmse": float(data["overall_train_rmse"][0]),
    }


def choose_drop(policy: dict[str, Any], target_center: np.ndarray) -> float:
    centers = np.asarray(policy["target_centers"], dtype=np.float64)
    if centers.size == 0:
        return 0.02
    distances = np.linalg.norm(centers[:, :2] - target_center[:2], axis=1)
    return float(policy["target_drops"][int(np.argmin(distances))])


def phase_for_step(policy: dict[str, Any], step_id: int) -> tuple[int, int]:
    cursor = 0
    last = 0
    for phase_id, length in enumerate(policy["phase_lengths"]):
        length = int(length)
        if length <= 0:
            continue
        last = phase_id
        if step_id < cursor + length:
            return int(phase_id), int(step_id - cursor)
        cursor += length
    return int(last), max(0, int(step_id - cursor))


def predict_action(
    policy: dict[str, Any],
    *,
    step_id: int,
    target_offset: np.ndarray,
    target_drop: float,
    clip: bool,
) -> tuple[np.ndarray, str]:
    phase_id, phase_step = phase_for_step(policy, step_id)
    length = int(policy["phase_lengths"][phase_id]) if phase_id < len(policy["phase_lengths"]) else 1
    progress = float(np.clip(phase_step / max(1, length - 1), 0.0, 1.0))
    if not bool(policy["phase_has_model"][phase_id]):
        return policy["fallback_actions"][phase_id].astype(np.float64), policy["phase_names"][phase_id]
    x = build_features(
        np.asarray([progress], dtype=np.float64),
        np.asarray([target_offset], dtype=np.float64),
        np.asarray([target_drop], dtype=np.float64),
        rbf_centers=policy["target_offset_centers"],
        rbf_sigma=policy["rbf_sigma"],
    )
    action = (x @ policy["weights"][phase_id])[0]
    if clip:
        action = np.clip(action, policy["action_min"], policy["action_max"])
    return action.astype(np.float64), policy["phase_names"][phase_id]


def render_frame(renderer, api: ArmHandStage1TaskAPI, target_center: np.ndarray) -> np.ndarray:
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


def run_episode(
    *,
    api: ArmHandStage1TaskAPI,
    policy: dict[str, Any],
    episode_id: int,
    target_center: np.ndarray,
    target_offset_request: np.ndarray,
    max_steps: int,
    target_radius: float,
    required_stable_steps: int,
    sample_every: int,
    action_smoothing: float,
    clip: bool,
    renderer=None,
    writer=None,
    visual_dir: Path | None = None,
    snapshot_prefix: str = "phase_regression",
    capture_every: int = 8,
) -> dict[str, Any]:
    api.reset_hand_open()
    initial_ball = api.get_ball_pose()["position"].copy()
    target_offset = np.asarray(target_center, dtype=np.float64) - initial_ball
    target_drop = choose_drop(policy, target_center)
    counters: dict[str, Any] = {
        "lifted_once": False,
        "release_started": False,
        "transport_floor_contacts": 0,
        "stable_target_steps": 0,
        "step_count": 0,
    }
    trace = []
    snapshots: dict[str, str] = {}
    prev_action: np.ndarray | None = None
    final_eval: dict[str, Any] | None = None
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
    if renderer is not None and writer is not None:
        writer.append(render_frame(renderer, api, target_center))
    for step_id in range(max_steps):
        action, phase_name = predict_action(
            policy,
            step_id=step_id,
            target_offset=target_offset,
            target_drop=target_drop,
            clip=clip,
        )
        if prev_action is not None and action_smoothing > 0.0:
            smoothing = float(np.clip(action_smoothing, 0.0, 0.99))
            action = smoothing * prev_action + (1.0 - smoothing) * action
        prev_action = action.copy()
        api.step_action(action, n=1, pin_ball=False)
        metrics = update_counters(api, initial_ball, target_center, phase_name, counters, target_radius)
        final_eval = evaluate_pick_place_state(
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
        if renderer is not None and writer is not None and step_id % max(1, capture_every) == 0:
            writer.append(render_frame(renderer, api, target_center))
        if renderer is not None and visual_dir is not None and phase_name in snapshot_phases and phase_name not in snapshots:
            next_action, next_phase_name = predict_action(
                policy,
                step_id=step_id + 1,
                target_offset=target_offset,
                target_drop=target_drop,
                clip=clip,
            )
            del next_action
            if next_phase_name != phase_name or final_eval["done"]:
                path = visual_dir / f"{snapshot_prefix}_{len(snapshots):02d}_{phase_name}.png"
                imageio.imwrite(path, render_frame(renderer, api, target_center))
                snapshots[phase_name] = str(path)
        if step_id % max(1, sample_every) == 0 or final_eval["done"]:
            contact = metrics["contact"]
            trace.append(
                {
                    "step": int(step_id + 1),
                    "phase": phase_name,
                    "status": final_eval["episode_status"],
                    "reason": final_eval["terminal_reason"],
                    "target_distance_xy": float(metrics["target_distance_xy"]),
                    "lift_height": float(metrics["ball_lift_height"]),
                    "stable_target_steps": int(counters["stable_target_steps"]),
                    "transport_floor_contacts": int(counters["transport_floor_contacts"]),
                    "ball_hand_contacts": int(contact["ball_hand_contact_count"]),
                    "ball_floor_contacts": int(contact.get("ball_floor_contact_count", 0)),
                    "max_penetration": float(contact["max_penetration"]),
                }
            )
        if final_eval["done"]:
            break
    if final_eval is None:
        final_eval = evaluate_pick_place_state(api, initial_ball, target_center=target_center, step_count=0)
    final_metrics = compute_pick_place_metrics(api, initial_ball, target_center)
    contact = final_metrics["contact"]
    status = "PASS" if final_eval["success"] else ("FAIL" if final_eval["terminal_reason"] == "timeout" else "PARTIAL")
    return {
        "episode_id": int(episode_id),
        "target_center": target_center,
        "target_offset": target_offset_request,
        "policy_target_offset": target_offset,
        "target_drop": float(target_drop),
        "status": status,
        "terminal_reason": final_eval["terminal_reason"],
        "success": bool(final_eval["success"]),
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
        "snapshots": snapshots,
        "trace": trace,
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    success_count = sum(1 for row in results if row["success"])
    target_dist = [float(row["final_target_distance_xy"]) for row in results]
    stable_steps = [int(row["stable_target_steps"]) for row in results]
    transport_floor = [int(row["transport_floor_contacts"]) for row in results]
    final_hand = [int(row["final_hand_contacts"]) for row in results]
    reasons = Counter(str(row["terminal_reason"]) for row in results)
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
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "episode_id",
                "status",
                "terminal_reason",
                "success",
                "steps",
                "target_drop",
                "target_x",
                "target_y",
                "target_z",
                "final_target_distance_xy",
                "stable_target_steps",
                "transport_floor_contacts",
                "final_hand_contacts",
                "final_floor_contacts",
                "max_penetration",
            ],
        )
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    "episode_id": row["episode_id"],
                    "status": row["status"],
                    "terminal_reason": row["terminal_reason"],
                    "success": row["success"],
                    "steps": row["steps"],
                    "target_drop": row["target_drop"],
                    "target_x": float(row["target_center"][0]),
                    "target_y": float(row["target_center"][1]),
                    "target_z": float(row["target_center"][2]),
                    "final_target_distance_xy": row["final_target_distance_xy"],
                    "stable_target_steps": row["stable_target_steps"],
                    "transport_floor_contacts": row["transport_floor_contacts"],
                    "final_hand_contacts": row["final_hand_contacts"],
                    "final_floor_contacts": row["final_floor_contacts"],
                    "max_penetration": row["max_penetration"],
                }
            )


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = payload["summary"]
    lines = [
        "# Stage2 Pick-Place V0.7.3 Phase Regression Eval Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Eval name: `{payload['eval_name']}`\n",
        f"- Status: **{s['status']}**\n",
        f"- Policy: `{payload['policy']}`\n",
        f"- Policy mode: `{payload['policy_mode']}`\n",
        f"- Source dataset: `{payload['source_dataset']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Episodes: `{s['episodes']}`\n",
        f"- Success count: `{s['success_count']} / {s['episodes']}`\n",
        f"- Terminal reasons: `{s['terminal_reason_counts']}`\n",
        f"- Target distance XY range: `{s['target_distance_xy_min']:.6f} m` to `{s['target_distance_xy_max']:.6f} m`\n",
        f"- Target distance XY mean: `{s['target_distance_xy_mean']:.6f} m`\n",
        f"- Stable steps range: `{s['stable_steps_min']}` to `{s['stable_steps_max']}`\n",
        f"- Transport floor contacts total: `{s['transport_floor_contacts_total']}`\n",
        f"- Final hand contacts max: `{s['final_hand_contacts_max']}`\n",
        f"- CSV: `{payload.get('csv')}`\n",
        f"- Video: `{payload.get('video')}`\n",
        f"- Contact sheet: `{payload.get('contact_sheet')}`\n\n",
        "## Episode Results\n\n",
        "| ep | drop | status | reason | steps | target xy m | stable | transport floor | final hand | final floor | max pen m |\n",
        "|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for row in payload["results"]:
        lines.append(
            f"| {row['episode_id']} | {row['target_drop']:.3f} | {row['status']} | {row['terminal_reason']} | "
            f"{row['steps']} | {row['final_target_distance_xy']:.6f} | {row['stable_target_steps']} | "
            f"{row['transport_floor_contacts']} | {row['final_hand_contacts']} | "
            f"{row['final_floor_contacts']} | {row['max_penetration']:.6f} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This is online MuJoCo evaluation of a trainable phase-specific policy.\n",
            "- PASS on fixed targets means this candidate closes the fixed-angle gate only; it is not a target-general claim.\n",
            "- Failed targets should drive phase/dataset repair before broader sweeps.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def resolve_paths(args) -> dict[str, Path | None]:
    run_dir = Path(args.run_dir).resolve() if args.run_dir else None
    if run_dir:
        (run_dir / "eval").mkdir(parents=True, exist_ok=True)
        (run_dir / "visuals").mkdir(parents=True, exist_ok=True)
        report = args.report or (run_dir / "eval" / f"{args.eval_name}_eval_report.md")
        metadata = args.metadata or (run_dir / "eval" / f"{args.eval_name}_summary.json")
        csv_path = args.csv or (run_dir / "eval" / f"{args.eval_name}_episodes.csv")
        video = args.video or (run_dir / "visuals" / f"{args.eval_name}_policy_demo.mp4")
        contact_sheet = args.contact_sheet or (run_dir / "visuals" / f"{args.eval_name}_policy_contact_sheet.png")
    else:
        report = args.report
        metadata = args.metadata
        csv_path = args.csv
        video = args.video
        contact_sheet = args.contact_sheet
    return {
        "run_dir": run_dir,
        "report": Path(report) if report else None,
        "metadata": Path(metadata) if metadata else None,
        "csv": Path(csv_path) if csv_path else None,
        "video": Path(video) if video else None,
        "contact_sheet": Path(contact_sheet) if contact_sheet else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate v0.7.3 phase-regression pick-place policy.")
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--scene", type=Path, default=CURRENT_PICK_PLACE_SCENE)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--metadata", type=Path, default=None)
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--contact-sheet", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--eval-name", default="v0_7_3_phase_regression_fixed_targets")
    parser.add_argument("--target-center", type=lambda raw: np.asarray(parse_values(raw), dtype=np.float64), default=DEFAULT_TARGET_CENTER)
    parser.add_argument("--target-centers", default="")
    parser.add_argument("--x-offsets", default="0.0")
    parser.add_argument("--y-offsets", default="0.0")
    parser.add_argument("--target-radius", type=float, default=DEFAULT_TARGET_RADIUS_M)
    parser.add_argument("--required-stable-steps", type=int, default=DEFAULT_REQUIRED_STABLE_STEPS)
    parser.add_argument("--max-steps", type=int, default=8200)
    parser.add_argument("--sample-every", type=int, default=100)
    parser.add_argument("--action-smoothing", type=float, default=0.0)
    parser.add_argument("--render-video", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--render-snapshots", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--render-episode-id", type=int, default=0)
    parser.add_argument("--capture-every", type=int, default=8)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=676)
    parser.add_argument("--no-clip", action="store_true")
    args = parser.parse_args()

    paths = resolve_paths(args)
    if paths["report"] is None or paths["metadata"] is None:
        raise ValueError("--report and --metadata are required unless --run-dir is provided")

    policy = load_policy(args.policy)
    api = ArmHandStage1TaskAPI(args.scene)
    target_rows = build_target_rows(args)
    results = []
    rendered_video = None
    rendered_contact_sheet = None
    all_snapshots: dict[str, str] = {}
    for row in target_rows:
        render_this = int(row["episode_id"]) == int(args.render_episode_id) and (args.render_video or args.render_snapshots)
        renderer = None
        writer_ctx = None
        writer = None
        visual_dir = (paths["run_dir"] / "visuals") if paths["run_dir"] else paths["report"].parent / "visuals"  # type: ignore[union-attr]
        try:
            if render_this:
                import mujoco

                renderer = mujoco.Renderer(api.model, width=args.width, height=args.height)
                if args.render_video:
                    assert paths["video"] is not None
                    paths["video"].parent.mkdir(parents=True, exist_ok=True)
                    writer_ctx = FrameWriter(paths["video"].resolve(), args.fps)
                    writer = writer_ctx.__enter__()
            result = run_episode(
                api=api,
                policy=policy,
                episode_id=int(row["episode_id"]),
                target_center=row["target_center"],
                target_offset_request=row["target_offset"],
                max_steps=args.max_steps,
                target_radius=args.target_radius,
                required_stable_steps=args.required_stable_steps,
                sample_every=args.sample_every,
                action_smoothing=args.action_smoothing,
                clip=not args.no_clip,
                renderer=renderer,
                writer=writer,
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
            if args.render_video and paths["video"] is not None:
                rendered_video = str(paths["video"])
            if args.render_snapshots:
                all_snapshots.update({str(k): str(v) for k, v in result.get("snapshots", {}).items()})
                if all_snapshots and paths["contact_sheet"] is not None:
                    write_contact_sheet(paths["contact_sheet"], all_snapshots)
                    rendered_contact_sheet = str(paths["contact_sheet"])
        results.append(result)
        print(
            f"ep={result['episode_id']:02d} drop={result['target_drop']:.3f} "
            f"{result['status']} reason={result['terminal_reason']} "
            f"dist={result['final_target_distance_xy']:.4f} stable={result['stable_target_steps']}"
        )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "eval_name": args.eval_name,
        "policy": str(Path(args.policy).resolve()),
        "policy_mode": policy["mode"],
        "policy_status": policy["status"],
        "source_dataset": policy["source_dataset"],
        "scene": str(Path(args.scene).resolve()),
        "contract_version": TASK_CONTRACT_VERSION,
        "target_radius": float(args.target_radius),
        "required_stable_steps": int(args.required_stable_steps),
        "max_steps": int(args.max_steps),
        "action_smoothing": float(args.action_smoothing),
        "clip": not args.no_clip,
        "summary": summarize(results),
        "results": results,
        "csv": str(paths["csv"]) if paths["csv"] else None,
        "video": rendered_video,
        "contact_sheet": rendered_contact_sheet,
        "snapshots": all_snapshots,
        "training_ready": False,
    }
    paths["metadata"].parent.mkdir(parents=True, exist_ok=True)  # type: ignore[union-attr]
    paths["metadata"].write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")  # type: ignore[union-attr]
    if paths["csv"]:
        write_csv(paths["csv"], results)
    write_report(paths["report"], json_ready(payload))  # type: ignore[arg-type]
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved report: {paths['report']}")
    print(f"Saved metadata: {paths['metadata']}")
    if paths["csv"]:
        print(f"Saved CSV: {paths['csv']}")
    if rendered_video:
        print(f"Saved video: {rendered_video}")
    if rendered_contact_sheet:
        print(f"Saved contact sheet: {rendered_contact_sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
