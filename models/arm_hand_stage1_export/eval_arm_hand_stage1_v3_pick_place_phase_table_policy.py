#!/usr/bin/env python3
"""Evaluate a phase-gated target table policy for Stage2 pick-place.

This is a diagnostic v0.7.2 bridge, not a promoted general policy.  It stores
one demonstration action schedule per target and replays the nearest schedule
for a requested target.  The purpose is to separate "teacher trajectory can
close the fixed-angle gate" from "a neural BC can generalize that trajectory".
"""

from __future__ import annotations

import argparse
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


ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET = ROOT / "data" / "arm_hand_stage1_v3_pick_place_dataset_v0_7_1.npz"


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


def string_list(values: np.ndarray) -> list[str]:
    return [str(item) for item in values.tolist()]


def build_target_rows(args) -> list[dict[str, Any]]:
    if args.target_centers:
        return [
            {
                "episode_id": int(i),
                "target_offset": np.zeros(3, dtype=np.float64),
                "target_center": target,
            }
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


def episode_entries(data, *, profile_id: int, action_field: str) -> list[dict[str, Any]]:
    episode_ids = data["episode_ids"].astype(np.int32)
    profile_ids = data["behavior_profile_ids"].astype(np.int32)
    entries = []
    for episode_id in sorted(int(v) for v in np.unique(episode_ids)):
        idxs = np.where(episode_ids == episode_id)[0]
        if len(idxs) == 0:
            continue
        if int(profile_ids[idxs[0]]) != int(profile_id):
            continue
        entries.append(
            {
                "episode_id": int(episode_id),
                "target_center": data["target_centers"][idxs[0]].astype(np.float64),
                "actions": data[action_field][idxs].astype(np.float64),
                "phase_ids": data["phase_ids"][idxs].astype(np.int32),
            }
        )
    if not entries:
        raise RuntimeError(f"No episodes found for profile_id={profile_id}")
    return entries


def save_policy(path: Path, entries: list[dict[str, Any]], data, *, action_field: str, profile_id: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    starts = []
    lengths = []
    actions = []
    phases = []
    cursor = 0
    for entry in entries:
        arr = np.asarray(entry["actions"], dtype=np.float64)
        phase_ids = np.asarray(entry["phase_ids"], dtype=np.int32)
        starts.append(cursor)
        lengths.append(arr.shape[0])
        actions.append(arr)
        phases.append(phase_ids)
        cursor += arr.shape[0]
    np.savez_compressed(
        path,
        mode=np.asarray(["phase_table_nearest_target_v0_7_2"], dtype=str),
        source_dataset=np.asarray([str(Path(data.filename).resolve())], dtype=str) if hasattr(data, "filename") else np.asarray(["unknown"], dtype=str),
        action_field=np.asarray([action_field], dtype=str),
        profile_id=np.asarray([int(profile_id)], dtype=np.int32),
        target_centers=np.asarray([entry["target_center"] for entry in entries], dtype=np.float64),
        episode_ids=np.asarray([entry["episode_id"] for entry in entries], dtype=np.int32),
        starts=np.asarray(starts, dtype=np.int32),
        lengths=np.asarray(lengths, dtype=np.int32),
        actions=np.concatenate(actions, axis=0),
        phase_ids=np.concatenate(phases, axis=0),
        phase_name_table=data["phase_name_table"],
        target_radius=data["target_radius"] if "target_radius" in data else np.asarray([DEFAULT_TARGET_RADIUS_M], dtype=np.float64),
        required_stable_steps=data["required_stable_steps"] if "required_stable_steps" in data else np.asarray([DEFAULT_REQUIRED_STABLE_STEPS], dtype=np.int32),
    )


def load_policy(path: Path) -> dict[str, Any]:
    data = np.load(path, allow_pickle=False)
    return {
        "path": str(path.resolve()),
        "mode": str(data["mode"][0]),
        "source_dataset": str(data["source_dataset"][0]),
        "action_field": str(data["action_field"][0]),
        "profile_id": int(data["profile_id"][0]),
        "target_centers": data["target_centers"].astype(np.float64),
        "episode_ids": data["episode_ids"].astype(np.int32),
        "starts": data["starts"].astype(np.int32),
        "lengths": data["lengths"].astype(np.int32),
        "actions": data["actions"].astype(np.float64),
        "phase_ids": data["phase_ids"].astype(np.int32),
        "phase_names": string_list(data["phase_name_table"]),
        "target_radius": float(data["target_radius"][0]) if "target_radius" in data.files else DEFAULT_TARGET_RADIUS_M,
        "required_stable_steps": int(data["required_stable_steps"][0]) if "required_stable_steps" in data.files else DEFAULT_REQUIRED_STABLE_STEPS,
    }


def choose_entry(policy: dict[str, Any], target_center: np.ndarray) -> dict[str, Any]:
    centers = np.asarray(policy["target_centers"], dtype=np.float64)
    dist = np.linalg.norm(centers[:, :2] - target_center[:2], axis=1)
    idx = int(np.argmin(dist))
    start = int(policy["starts"][idx])
    length = int(policy["lengths"][idx])
    return {
        "table_index": idx,
        "source_episode_id": int(policy["episode_ids"][idx]),
        "source_target_center": centers[idx],
        "target_distance_xy": float(dist[idx]),
        "actions": policy["actions"][start : start + length],
        "phase_ids": policy["phase_ids"][start : start + length],
    }


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
    target_offset: np.ndarray,
    max_steps: int,
    sample_every: int,
    renderer=None,
    video_writer: FrameWriter | None = None,
    visual_dir: Path | None = None,
    snapshot_prefix: str = "phase_table",
    capture_every: int = 8,
) -> dict[str, Any]:
    entry = choose_entry(policy, target_center)
    actions = entry["actions"]
    phase_ids = entry["phase_ids"]
    phase_names = policy["phase_names"]
    target_radius = float(policy["target_radius"])
    required_stable_steps = int(policy["required_stable_steps"])

    api.reset_hand_open()
    initial_ball = api.get_ball_pose()["position"].copy()
    counters: dict[str, Any] = {
        "lifted_once": False,
        "release_started": False,
        "transport_floor_contacts": 0,
        "stable_target_steps": 0,
        "step_count": 0,
    }
    trace = []
    snapshots: dict[str, str] = {}
    final_eval = None
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
        video_writer.append(render_frame(renderer, api, target_center))

    for step_id in range(max_steps):
        table_step = min(step_id, actions.shape[0] - 1)
        action = actions[table_step]
        phase_id = int(phase_ids[table_step])
        phase_name = phase_names[phase_id]
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
        if renderer is not None and video_writer is not None and step_id % max(1, capture_every) == 0:
            video_writer.append(render_frame(renderer, api, target_center))
        if renderer is not None and visual_dir is not None and phase_name in snapshot_phases and phase_name not in snapshots:
            next_step = min(table_step + 1, actions.shape[0] - 1)
            next_phase_name = phase_names[int(phase_ids[next_step])]
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
    status = "PASS" if final_eval["success"] else ("FAIL" if final_eval["terminal_reason"] == "timeout" else "PARTIAL")
    return {
        "episode_id": int(episode_id),
        "target_center": target_center,
        "target_offset": target_offset,
        "selected_source_episode_id": int(entry["source_episode_id"]),
        "selected_source_target_center": entry["source_target_center"],
        "nearest_target_distance_xy": float(entry["target_distance_xy"]),
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
        "final_hand_contacts": int(final_metrics["contact"]["ball_hand_contact_count"]),
        "final_floor_contacts": int(final_metrics["contact"].get("ball_floor_contact_count", 0)),
        "max_penetration": float(final_metrics["contact"]["max_penetration"]),
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


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Arm-Hand Stage1 V3 Pick-Place Phase Table Policy Eval\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Eval name: `{payload['eval_name']}`\n",
        f"- Policy: `{payload['policy']}`\n",
        f"- Policy mode: `{payload['policy_mode']}`\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Action field: `{payload['action_field']}`\n",
        f"- Profile id: `{payload['profile_id']}`\n",
        f"- Summary: `{payload['summary']}`\n",
        f"- Video: `{payload['video']}`\n",
        f"- Contact sheet: `{payload['contact_sheet']}`\n\n",
        "## Episodes\n\n",
        "| ep | source ep | nearest xy | status | reason | steps | final xy | stable | floor | hand |\n",
        "|---:|---:|---:|---|---|---:|---:|---:|---:|---:|\n",
    ]
    for row in payload["results"]:
        lines.append(
            f"| {row['episode_id']} | {row['selected_source_episode_id']} | "
            f"{row['nearest_target_distance_xy']:.6f} | {row['status']} | {row['terminal_reason']} | "
            f"{row['steps']} | {row['final_target_distance_xy']:.6f} | "
            f"{row['stable_target_steps']} | {row['transport_floor_contacts']} | {row['final_hand_contacts']} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This phase-table policy is a diagnostic bridge, not a promoted general policy.\n",
            "- PASS on exact fixed targets means the phase-gated/static teacher schedule can close the gate when target lookup is exact.\n",
            "- Unseen target behavior is nearest-neighbor only and must not be overclaimed as smooth target generalization.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def resolve_paths(args) -> dict[str, Path | None]:
    run_dir = Path(args.run_dir).resolve() if args.run_dir else None
    if run_dir:
        (run_dir / "checkpoints").mkdir(parents=True, exist_ok=True)
        (run_dir / "eval").mkdir(parents=True, exist_ok=True)
        (run_dir / "visuals").mkdir(parents=True, exist_ok=True)
        policy = args.policy or (run_dir / "checkpoints" / "phase_table_policy_v0_7_2_clean_actions.npz")
        report = args.report or (run_dir / "eval" / f"{args.eval_name}_eval_report.md")
        metadata = args.metadata or (run_dir / "eval" / f"{args.eval_name}_summary.json")
        video = args.video or (run_dir / "visuals" / f"{args.eval_name}_policy_demo.mp4")
        contact_sheet = args.contact_sheet or (run_dir / "visuals" / f"{args.eval_name}_policy_contact_sheet.png")
    else:
        policy = args.policy
        report = args.report or (ROOT / "docs" / f"{args.eval_name}_phase_table_eval_report.md")
        metadata = args.metadata or (ROOT / "metadata" / f"{args.eval_name}_phase_table_eval.json")
        video = args.video
        contact_sheet = args.contact_sheet
    return {
        "run_dir": run_dir,
        "policy": Path(policy) if policy else None,
        "report": Path(report),
        "metadata": Path(metadata),
        "video": Path(video) if video else None,
        "contact_sheet": Path(contact_sheet) if contact_sheet else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate v0.7.2 phase-table pick-place policy.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--scene", type=Path, default=CURRENT_PICK_PLACE_SCENE)
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--metadata", type=Path, default=None)
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--contact-sheet", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--eval-name", default="v0_7_2_phase_table_fixed_targets")
    parser.add_argument("--action-field", choices=["actions", "expert_actions"], default="actions")
    parser.add_argument("--profile-id", type=int, default=0)
    parser.add_argument("--target-center", type=lambda raw: np.asarray(parse_values(raw), dtype=np.float64), default=DEFAULT_TARGET_CENTER)
    parser.add_argument("--target-centers", default="")
    parser.add_argument("--x-offsets", default="0.0")
    parser.add_argument("--y-offsets", default="0.0")
    parser.add_argument("--max-steps", type=int, default=8200)
    parser.add_argument("--sample-every", type=int, default=100)
    parser.add_argument("--render-video", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--render-snapshots", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--render-episode-id", type=int, default=0)
    parser.add_argument("--capture-every", type=int, default=8)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=676)
    args = parser.parse_args()

    paths = resolve_paths(args)
    dataset_path = Path(args.dataset).resolve()
    data = np.load(dataset_path, allow_pickle=False)
    policy_path = paths["policy"]
    assert policy_path is not None
    entries = episode_entries(data, profile_id=args.profile_id, action_field=args.action_field)
    save_policy(policy_path, entries, data, action_field=args.action_field, profile_id=args.profile_id)
    policy = load_policy(policy_path)

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
                target_offset=row["target_offset"],
                max_steps=args.max_steps,
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
            if args.render_video and paths["video"] is not None:
                rendered_video = str(paths["video"])
            if args.render_snapshots:
                all_snapshots.update({str(k): str(v) for k, v in result.get("snapshots", {}).items()})
                if all_snapshots and paths["contact_sheet"] is not None:
                    write_contact_sheet(paths["contact_sheet"], all_snapshots)
                    rendered_contact_sheet = str(paths["contact_sheet"])
        results.append(result)
        print(
            f"ep={result['episode_id']:02d} source={result['selected_source_episode_id']} "
            f"{result['status']} reason={result['terminal_reason']} "
            f"dist={result['final_target_distance_xy']:.4f} stable={result['stable_target_steps']}"
        )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "eval_name": args.eval_name,
        "policy": str(policy_path.resolve()),
        "policy_mode": policy["mode"],
        "dataset": str(dataset_path),
        "scene": str(Path(args.scene).resolve()),
        "action_field": args.action_field,
        "profile_id": int(args.profile_id),
        "contract_version": TASK_CONTRACT_VERSION,
        "summary": summarize(results),
        "results": results,
        "video": rendered_video,
        "contact_sheet": rendered_contact_sheet,
        "snapshots": all_snapshots,
    }
    paths["metadata"].parent.mkdir(parents=True, exist_ok=True)  # type: ignore[union-attr]
    paths["metadata"].write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")  # type: ignore[union-attr]
    write_report(paths["report"], json_ready(payload))  # type: ignore[arg-type]
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved policy: {policy_path}")
    print(f"Saved report: {paths['report']}")
    print(f"Saved metadata: {paths['metadata']}")
    if rendered_video:
        print(f"Saved video: {rendered_video}")
    if rendered_contact_sheet:
        print(f"Saved contact sheet: {rendered_contact_sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
