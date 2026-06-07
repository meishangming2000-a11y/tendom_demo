#!/usr/bin/env python3
"""Evaluate a phase-aware target mixture policy for Stage2 pick-place.

This v0.8 Gate1 candidate stores one action schedule per target and blends the
nearest schedules with an RBF gate. It is intentionally phase-gated and
target-conditioned: the goal is to repair local transport interpolation without
returning to monolithic live-observation BC.
"""

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


ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET = (
    ROOT
    / "runs"
    / "stage2_pick_place_v0_8_gate1_target_generalization"
    / "20260603_000000_seed071"
    / "datasets"
    / "arm_hand_stage1_v3_pick_place_dataset_v0_8_gate1_m165_local_repair.npz"
)


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


def save_policy(
    path: Path,
    entries: list[dict[str, Any]],
    data,
    *,
    action_field: str,
    profile_id: int,
    top_k: int,
    rbf_sigma: float,
    exact_epsilon: float,
    blend_phases: list[str],
) -> None:
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
        mode=np.asarray(["phase_moe_target_schedule_v0_8_gate1"], dtype=str),
        source_dataset=np.asarray(
            [str(Path(data.filename).resolve())] if hasattr(data, "filename") else ["unknown"], dtype=str
        ),
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
        required_stable_steps=(
            data["required_stable_steps"]
            if "required_stable_steps" in data
            else np.asarray([DEFAULT_REQUIRED_STABLE_STEPS], dtype=np.int32)
        ),
        top_k=np.asarray([int(top_k)], dtype=np.int32),
        rbf_sigma=np.asarray([float(rbf_sigma)], dtype=np.float64),
        exact_epsilon=np.asarray([float(exact_epsilon)], dtype=np.float64),
        blend_phase_names=np.asarray(blend_phases, dtype=str),
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
        "required_stable_steps": int(data["required_stable_steps"][0])
        if "required_stable_steps" in data.files
        else DEFAULT_REQUIRED_STABLE_STEPS,
        "top_k": int(data["top_k"][0]) if "top_k" in data.files else 4,
        "rbf_sigma": float(data["rbf_sigma"][0]) if "rbf_sigma" in data.files else 0.01,
        "exact_epsilon": float(data["exact_epsilon"][0]) if "exact_epsilon" in data.files else 1e-9,
        "blend_phase_names": string_list(data["blend_phase_names"]) if "blend_phase_names" in data.files else [],
    }


def choose_experts(
    policy: dict[str, Any],
    target_center: np.ndarray,
    *,
    top_k: int | None = None,
    rbf_sigma: float | None = None,
    exact_epsilon: float | None = None,
) -> dict[str, Any]:
    centers = np.asarray(policy["target_centers"], dtype=np.float64)
    distances = np.linalg.norm(centers[:, :2] - target_center[:2], axis=1)
    nearest = int(np.argmin(distances))
    eps = float(policy["exact_epsilon"] if exact_epsilon is None else exact_epsilon)
    k = max(1, int(policy["top_k"] if top_k is None else top_k))
    sigma = float(policy["rbf_sigma"] if rbf_sigma is None else rbf_sigma)
    if float(distances[nearest]) <= eps or sigma <= 0.0 or k <= 1:
        idxs = np.asarray([nearest], dtype=np.int32)
        weights = np.asarray([1.0], dtype=np.float64)
    else:
        idxs = np.argsort(distances)[: min(k, len(distances))].astype(np.int32)
        local = distances[idxs]
        scaled = -0.5 * (local / max(1e-9, sigma)) ** 2
        scaled -= float(np.max(scaled))
        weights = np.exp(scaled)
        weights /= max(1e-12, float(np.sum(weights)))
    return {
        "indices": idxs,
        "weights": weights,
        "nearest_index": nearest,
        "nearest_target_distance_xy": float(distances[nearest]),
        "source_episode_ids": [int(policy["episode_ids"][int(i)]) for i in idxs],
        "source_target_centers": centers[idxs],
    }


def predict_action(
    policy: dict[str, Any],
    selected: dict[str, Any],
    step_id: int,
    blend_phases: set[str],
) -> tuple[np.ndarray, str]:
    actions = policy["actions"]
    phase_ids = policy["phase_ids"]
    starts = policy["starts"]
    lengths = policy["lengths"]
    phase_names = policy["phase_names"]
    nearest = int(selected["nearest_index"])
    nearest_start = int(starts[nearest])
    nearest_length = int(lengths[nearest])
    nearest_step = min(int(step_id), max(0, nearest_length - 1))
    nearest_row = nearest_start + nearest_step
    nearest_phase_name = phase_names[int(phase_ids[nearest_row])]
    if nearest_phase_name not in blend_phases:
        return actions[nearest_row].astype(np.float64), nearest_phase_name

    blended = np.zeros(actions.shape[1], dtype=np.float64)
    for idx, weight in zip(selected["indices"], selected["weights"]):
        entry_id = int(idx)
        start = int(starts[entry_id])
        length = int(lengths[entry_id])
        table_step = min(int(step_id), max(0, length - 1))
        row = start + table_step
        blended += float(weight) * actions[row]
    return blended, nearest_phase_name


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
    top_k: int | None,
    rbf_sigma: float | None,
    exact_epsilon: float | None,
    blend_phases: set[str],
    renderer=None,
    video_writer: FrameWriter | None = None,
    visual_dir: Path | None = None,
    snapshot_prefix: str = "phase_moe",
    capture_every: int = 8,
) -> dict[str, Any]:
    selected = choose_experts(policy, target_center, top_k=top_k, rbf_sigma=rbf_sigma, exact_epsilon=exact_epsilon)
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
        action, phase_name = predict_action(policy, selected, step_id, blend_phases)
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
            _, next_phase_name = predict_action(policy, selected, step_id + 1, blend_phases)
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
        "target_offset": target_offset,
        "source_episode_ids": selected["source_episode_ids"],
        "source_weights": selected["weights"],
        "nearest_target_distance_xy": float(selected["nearest_target_distance_xy"]),
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
                "source_episode_ids",
                "source_weights",
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
                    "source_episode_ids": json.dumps(row["source_episode_ids"]),
                    "source_weights": json.dumps(np.round(row["source_weights"], 6).tolist()),
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
        "# Arm-Hand Stage1 V3 Pick-Place Phase MoE Policy Eval\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Eval name: `{payload['eval_name']}`\n",
        f"- Policy: `{payload['policy']}`\n",
        f"- Policy mode: `{payload['policy_mode']}`\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Action field: `{payload['action_field']}`\n",
        f"- Profile id: `{payload['profile_id']}`\n",
        f"- Top-k: `{payload['top_k']}`\n",
        f"- RBF sigma: `{payload['rbf_sigma']}`\n",
        f"- Exact epsilon: `{payload['exact_epsilon']}`\n",
        f"- Blend phases: `{payload['blend_phases']}`\n",
        f"- Status: **{s['status']}**\n",
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
        "## Episodes\n\n",
        "| ep | sources | weights | status | reason | steps | final xy | stable | floor | hand |\n",
        "|---:|---|---|---|---|---:|---:|---:|---:|---:|\n",
    ]
    for row in payload["results"]:
        weights = np.round(row["source_weights"], 3).tolist()
        lines.append(
            f"| {row['episode_id']} | `{row['source_episode_ids']}` | `{weights}` | {row['status']} | "
            f"{row['terminal_reason']} | {row['steps']} | {row['final_target_distance_xy']:.6f} | "
            f"{row['stable_target_steps']} | {row['transport_floor_contacts']} | {row['final_hand_contacts']} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This policy is a phase-aware mixture over target-conditioned action schedules.\n",
            "- It is not monolithic live-observation BC and should be judged as a staged-control/interpolation candidate.\n",
            "- Exact training targets may use a single expert; held-out target eval should show whether local interpolation is useful.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def resolve_paths(args) -> dict[str, Path | None]:
    run_dir = Path(args.run_dir).resolve() if args.run_dir else None
    if run_dir:
        (run_dir / "checkpoints").mkdir(parents=True, exist_ok=True)
        (run_dir / "eval").mkdir(parents=True, exist_ok=True)
        (run_dir / "visuals").mkdir(parents=True, exist_ok=True)
        sigma_tag = str(args.rbf_sigma).replace(".", "p")
        policy = args.policy or (run_dir / "checkpoints" / f"phase_moe_policy_v0_8_gate1_top{args.top_k}_sigma{sigma_tag}.npz")
        report = args.report or (run_dir / "eval" / f"{args.eval_name}_eval_report.md")
        metadata = args.metadata or (run_dir / "eval" / f"{args.eval_name}_summary.json")
        csv_path = args.csv or (run_dir / "eval" / f"{args.eval_name}_episodes.csv")
        video = args.video or (run_dir / "visuals" / f"{args.eval_name}_policy_demo.mp4")
        contact_sheet = args.contact_sheet or (run_dir / "visuals" / f"{args.eval_name}_policy_contact_sheet.png")
    else:
        policy = args.policy
        report = args.report or (ROOT / "docs" / f"{args.eval_name}_phase_moe_eval_report.md")
        metadata = args.metadata or (ROOT / "metadata" / f"{args.eval_name}_phase_moe_eval.json")
        csv_path = args.csv
        video = args.video
        contact_sheet = args.contact_sheet
    return {
        "run_dir": run_dir,
        "policy": Path(policy) if policy else None,
        "report": Path(report),
        "metadata": Path(metadata),
        "csv": Path(csv_path) if csv_path else None,
        "video": Path(video) if video else None,
        "contact_sheet": Path(contact_sheet) if contact_sheet else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate v0.8 Gate1 phase-aware MoE pick-place policy.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--scene", type=Path, default=CURRENT_PICK_PLACE_SCENE)
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--metadata", type=Path, default=None)
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--contact-sheet", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--eval-name", default="v0_8_gate1_phase_moe_eval")
    parser.add_argument("--action-field", choices=["actions", "expert_actions"], default="actions")
    parser.add_argument("--profile-id", type=int, default=0)
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--rbf-sigma", type=float, default=0.008)
    parser.add_argument("--exact-epsilon", type=float, default=1e-9)
    parser.add_argument(
        "--blend-phases",
        default="transport,transport_hold,descend_to_target,pre_release_settle",
        help="Comma-separated phase names where action schedules are blended. Other phases use the nearest expert.",
    )
    parser.add_argument(
        "--target-center",
        type=lambda raw: np.asarray(parse_values(raw), dtype=np.float64),
        default=DEFAULT_TARGET_CENTER,
    )
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
    blend_phase_names = [item.strip() for item in args.blend_phases.split(",") if item.strip()]
    entries = episode_entries(data, profile_id=args.profile_id, action_field=args.action_field)
    save_policy(
        policy_path,
        entries,
        data,
        action_field=args.action_field,
        profile_id=args.profile_id,
        top_k=args.top_k,
        rbf_sigma=args.rbf_sigma,
        exact_epsilon=args.exact_epsilon,
        blend_phases=blend_phase_names,
    )
    policy = load_policy(policy_path)
    blend_phases = set(blend_phase_names or policy["blend_phase_names"])

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
                top_k=args.top_k,
                rbf_sigma=args.rbf_sigma,
                exact_epsilon=args.exact_epsilon,
                blend_phases=blend_phases,
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
            f"ep={result['episode_id']:02d} sources={result['source_episode_ids']} "
            f"weights={np.round(result['source_weights'], 3).tolist()} "
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
        "top_k": int(args.top_k),
        "rbf_sigma": float(args.rbf_sigma),
        "exact_epsilon": float(args.exact_epsilon),
        "blend_phases": sorted(blend_phases),
        "contract_version": TASK_CONTRACT_VERSION,
        "summary": summarize(results),
        "results": results,
        "csv": str(paths["csv"]) if paths["csv"] else None,
        "video": rendered_video,
        "contact_sheet": rendered_contact_sheet,
        "snapshots": all_snapshots,
    }
    paths["metadata"].parent.mkdir(parents=True, exist_ok=True)  # type: ignore[union-attr]
    paths["metadata"].write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")  # type: ignore[union-attr]
    if paths["csv"] is not None:
        write_csv(paths["csv"], json_ready(results))
    write_report(paths["report"], json_ready(payload))  # type: ignore[arg-type]
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved policy: {policy_path}")
    print(f"Saved report: {paths['report']}")
    print(f"Saved metadata: {paths['metadata']}")
    if paths["csv"] is not None:
        print(f"Saved CSV: {paths['csv']}")
    if rendered_video:
        print(f"Saved video: {rendered_video}")
    if rendered_contact_sheet:
        print(f"Saved contact sheet: {rendered_contact_sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
