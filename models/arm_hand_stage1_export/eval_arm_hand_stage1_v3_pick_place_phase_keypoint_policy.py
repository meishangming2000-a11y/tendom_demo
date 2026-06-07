#!/usr/bin/env python3
"""Train/evaluate a phase-keypoint target policy for Stage2 pick-place.

The policy learns start/end action keypoints for each phase as a function of
target offset, then executes a linear phase schedule online. This is meant to
repair the v0.8 Gate1 transport representation without fitting dense raw action
samples directly.
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
from train_arm_hand_stage1_v3_pick_place_phase_regression import (
    fit_ridge,
    phase_lengths_from_config,
    selected_profile_mask,
    string_list,
    target_rows,
)


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


def target_feature_names(num_rbf: int) -> list[str]:
    names = ["1", "target_dx", "target_dy", "target_ux", "target_uy", "drop"]
    names.extend(["target_dx^2", "target_dy^2", "target_dx*target_dy", "drop^2"])
    names.extend([f"rbf_target_{i}" for i in range(num_rbf)])
    return names


def target_features(
    target_offsets: np.ndarray,
    drops: np.ndarray,
    *,
    rbf_centers: np.ndarray,
    rbf_sigma: float,
) -> np.ndarray:
    offsets = np.asarray(target_offsets, dtype=np.float64)
    drops = np.asarray(drops, dtype=np.float64).reshape(-1)
    dx = offsets[:, 0]
    dy = offsets[:, 1]
    dist = np.maximum(1e-9, np.linalg.norm(offsets[:, :2], axis=1))
    ux = dx / dist
    uy = dy / dist
    parts = [
        np.stack([np.ones_like(dx), dx, dy, ux, uy, drops], axis=1),
        np.stack([dx * dx, dy * dy, dx * dy, drops * drops], axis=1),
    ]
    centers = np.asarray(rbf_centers, dtype=np.float64)
    if centers.size:
        distances = np.linalg.norm(offsets[:, None, :2] - centers[None, :, :2], axis=2)
        parts.append(np.exp(-0.5 * (distances / max(1e-9, float(rbf_sigma))) ** 2))
    return np.concatenate(parts, axis=1).astype(np.float64)


def choose_drop(policy: dict[str, Any], target_center: np.ndarray) -> float:
    centers = np.asarray(policy["target_centers"], dtype=np.float64)
    if centers.size == 0:
        return 0.02
    distances = np.linalg.norm(centers[:, :2] - target_center[:2], axis=1)
    return float(policy["target_drops"][int(np.argmin(distances))])


def train_policy(
    data_path: Path,
    *,
    action_field: str,
    profile: str,
    ridge: float,
    rbf_sigma: float,
    feature_mode: str,
    local_center: np.ndarray | None,
    local_radius: float,
) -> dict[str, Any]:
    data = np.load(data_path, allow_pickle=False)
    selected = selected_profile_mask(data, profile)
    schedule_selected = selected.copy()
    if local_center is not None:
        target_centers_all = data["target_centers"].astype(np.float64)
        local_dist = np.linalg.norm(target_centers_all[:, :2] - np.asarray(local_center, dtype=np.float64)[:2], axis=1)
        selected = selected & (local_dist <= float(local_radius))
    actions = data[action_field].astype(np.float64)
    phase_ids = data["phase_ids"].astype(np.int32)
    episode_ids = data["episode_ids"].astype(np.int32)
    phase_names = string_list(data["phase_name_table"])
    phase_lengths = phase_lengths_from_config(data)
    centers, offset_centers, center_drops = target_rows(data, selected)
    if feature_mode == "affine":
        feature_offset_centers = np.zeros((0, 3), dtype=np.float64)
    elif feature_mode == "rbf":
        feature_offset_centers = offset_centers
    else:
        raise ValueError(f"Unknown feature mode {feature_mode!r}")
    feature_names = target_feature_names(len(offset_centers))
    if feature_mode == "affine":
        feature_names = target_feature_names(0)
    feature_dim = len(feature_names)
    act_dim = int(actions.shape[1])
    start_weights = np.zeros((len(phase_names), feature_dim, act_dim), dtype=np.float64)
    end_weights = np.zeros_like(start_weights)
    fallback_start = np.zeros((len(phase_names), act_dim), dtype=np.float64)
    fallback_end = np.zeros_like(fallback_start)
    phase_has_model = np.zeros(len(phase_names), dtype=bool)
    phase_sample_counts = np.zeros(len(phase_names), dtype=np.int32)
    phase_rows = []

    selected_episodes = sorted(int(v) for v in np.unique(episode_ids[selected]))
    for phase_id, phase_name in enumerate(phase_names):
        xs = []
        ys0 = []
        ys1 = []
        for episode_id in selected_episodes:
            ep_mask = selected & (episode_ids == episode_id)
            idx = np.where(ep_mask & (phase_ids == phase_id))[0]
            if idx.size == 0:
                continue
            first = int(idx[0])
            last = int(idx[-1])
            target_offset = data["target_centers"][first].astype(np.float64) - data["initial_ball_positions"][first].astype(np.float64)
            drop = float(data["pre_release_z_drops"][first])
            xs.append((target_offset, drop))
            ys0.append(actions[first])
            ys1.append(actions[last])
        if not xs:
            if phase_id > 0:
                fallback_start[phase_id] = fallback_end[phase_id - 1]
                fallback_end[phase_id] = fallback_end[phase_id - 1]
            phase_rows.append({"phase": phase_name, "samples": 0, "start_rmse": float("nan"), "end_rmse": float("nan")})
            continue
        offsets = np.asarray([row[0] for row in xs], dtype=np.float64)
        drops = np.asarray([row[1] for row in xs], dtype=np.float64)
        x = target_features(offsets, drops, rbf_centers=feature_offset_centers, rbf_sigma=rbf_sigma)
        y0 = np.asarray(ys0, dtype=np.float64)
        y1 = np.asarray(ys1, dtype=np.float64)
        w0 = fit_ridge(x, y0, ridge)
        w1 = fit_ridge(x, y1, ridge)
        pred0 = x @ w0
        pred1 = x @ w1
        start_weights[phase_id] = w0
        end_weights[phase_id] = w1
        fallback_start[phase_id] = np.mean(y0, axis=0)
        fallback_end[phase_id] = np.mean(y1, axis=0)
        phase_has_model[phase_id] = True
        phase_sample_counts[phase_id] = int(x.shape[0])
        phase_rows.append(
            {
                "phase": phase_name,
                "samples": int(x.shape[0]),
                "start_rmse": float(np.sqrt(np.mean((pred0 - y0) ** 2))),
                "end_rmse": float(np.sqrt(np.mean((pred1 - y1) ** 2))),
            }
        )
    return {
        "mode": "phase_keypoint_target_policy_v0_8_gate1",
        "source_dataset": str(data_path.resolve()),
        "action_field": action_field,
        "profile_filter": profile,
        "phase_names": phase_names,
        "phase_lengths": np.asarray(phase_lengths, dtype=np.int32),
        "feature_names": feature_names,
        "start_weights": start_weights,
        "end_weights": end_weights,
        "fallback_start": fallback_start,
        "fallback_end": fallback_end,
        "phase_has_model": phase_has_model,
        "phase_sample_counts": phase_sample_counts,
        "target_centers": centers,
        "target_offset_centers": feature_offset_centers,
        "fit_target_centers": centers,
        "fit_target_drops": center_drops,
        "target_drops": center_drops,
        "action_min": actions[selected].min(axis=0),
        "action_max": actions[selected].max(axis=0),
        "actuator_names": data["actuator_names"],
        "contract_version": data["contract_version"],
        "dataset_version": data["dataset_version"] if "dataset_version" in data.files else np.asarray(["unknown"], dtype=str),
        "ridge": float(ridge),
        "rbf_sigma": float(rbf_sigma),
        "feature_mode": feature_mode,
        "local_center": np.asarray(local_center, dtype=np.float64) if local_center is not None else np.asarray([], dtype=np.float64),
        "local_radius": float(local_radius),
        "phase_rows": phase_rows,
        "schedule": build_exact_schedule(data, schedule_selected, action_field=action_field),
    }


def build_exact_schedule(data, selected: np.ndarray, *, action_field: str) -> dict[str, np.ndarray]:
    episode_ids = data["episode_ids"].astype(np.int32)
    starts = []
    lengths = []
    actions = []
    phases = []
    centers = []
    out_episode_ids = []
    cursor = 0
    for episode_id in sorted(int(v) for v in np.unique(episode_ids[selected])):
        idx = np.where(selected & (episode_ids == episode_id))[0]
        if idx.size == 0:
            continue
        arr = data[action_field][idx].astype(np.float64)
        phase_ids = data["phase_ids"][idx].astype(np.int32)
        starts.append(cursor)
        lengths.append(arr.shape[0])
        actions.append(arr)
        phases.append(phase_ids)
        centers.append(data["target_centers"][idx[0]].astype(np.float64))
        out_episode_ids.append(int(episode_id))
        cursor += arr.shape[0]
    return {
        "schedule_episode_ids": np.asarray(out_episode_ids, dtype=np.int32),
        "schedule_target_centers": np.asarray(centers, dtype=np.float64),
        "schedule_starts": np.asarray(starts, dtype=np.int32),
        "schedule_lengths": np.asarray(lengths, dtype=np.int32),
        "schedule_actions": np.concatenate(actions, axis=0),
        "schedule_phase_ids": np.concatenate(phases, axis=0),
    }


def save_policy(path: Path, policy: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        mode=np.asarray([policy["mode"]], dtype=str),
        created_at=np.asarray([datetime.now().isoformat(timespec="seconds")], dtype=str),
        source_dataset=np.asarray([policy["source_dataset"]], dtype=str),
        action_field=np.asarray([policy["action_field"]], dtype=str),
        profile_filter=np.asarray([policy["profile_filter"]], dtype=str),
        phase_names=np.asarray(policy["phase_names"], dtype=str),
        phase_lengths=policy["phase_lengths"],
        feature_names=np.asarray(policy["feature_names"], dtype=str),
        start_weights=policy["start_weights"],
        end_weights=policy["end_weights"],
        fallback_start=policy["fallback_start"],
        fallback_end=policy["fallback_end"],
        phase_has_model=policy["phase_has_model"],
        phase_sample_counts=policy["phase_sample_counts"],
        target_centers=policy["target_centers"],
        target_offset_centers=policy["target_offset_centers"],
        fit_target_centers=policy["fit_target_centers"],
        fit_target_drops=policy["fit_target_drops"],
        target_drops=policy["target_drops"],
        action_min=policy["action_min"],
        action_max=policy["action_max"],
        actuator_names=policy["actuator_names"],
        contract_version=policy["contract_version"],
        dataset_version=policy["dataset_version"],
        ridge=np.asarray([policy["ridge"]], dtype=np.float64),
        rbf_sigma=np.asarray([policy["rbf_sigma"]], dtype=np.float64),
        feature_mode=np.asarray([policy["feature_mode"]], dtype=str),
        local_center=np.asarray(policy["local_center"], dtype=np.float64),
        local_radius=np.asarray([policy["local_radius"]], dtype=np.float64),
        phase_rows_json=np.asarray([json.dumps(json_ready(policy["phase_rows"]), ensure_ascii=False)], dtype=str),
        **policy["schedule"],
    )


def load_policy(path: Path) -> dict[str, Any]:
    data = np.load(path, allow_pickle=False)
    return {
        "path": str(path.resolve()),
        "mode": str(data["mode"][0]),
        "source_dataset": str(data["source_dataset"][0]),
        "action_field": str(data["action_field"][0]),
        "profile_filter": str(data["profile_filter"][0]),
        "phase_names": string_list(data["phase_names"]),
        "phase_lengths": data["phase_lengths"].astype(np.int32),
        "feature_names": string_list(data["feature_names"]),
        "start_weights": data["start_weights"].astype(np.float64),
        "end_weights": data["end_weights"].astype(np.float64),
        "fallback_start": data["fallback_start"].astype(np.float64),
        "fallback_end": data["fallback_end"].astype(np.float64),
        "phase_has_model": data["phase_has_model"].astype(bool),
        "target_centers": data["target_centers"].astype(np.float64),
        "target_offset_centers": data["target_offset_centers"].astype(np.float64),
        "fit_target_centers": data["fit_target_centers"].astype(np.float64) if "fit_target_centers" in data.files else data["target_centers"].astype(np.float64),
        "fit_target_drops": data["fit_target_drops"].astype(np.float64) if "fit_target_drops" in data.files else data["target_drops"].astype(np.float64),
        "target_drops": data["target_drops"].astype(np.float64),
        "action_min": data["action_min"].astype(np.float64),
        "action_max": data["action_max"].astype(np.float64),
        "rbf_sigma": float(data["rbf_sigma"][0]),
        "feature_mode": str(data["feature_mode"][0]) if "feature_mode" in data.files else "rbf",
        "local_center": data["local_center"].astype(np.float64) if "local_center" in data.files else np.asarray([], dtype=np.float64),
        "local_radius": float(data["local_radius"][0]) if "local_radius" in data.files else 0.0,
        "schedule_episode_ids": data["schedule_episode_ids"].astype(np.int32),
        "schedule_target_centers": data["schedule_target_centers"].astype(np.float64),
        "schedule_starts": data["schedule_starts"].astype(np.int32),
        "schedule_lengths": data["schedule_lengths"].astype(np.int32),
        "schedule_actions": data["schedule_actions"].astype(np.float64),
        "schedule_phase_ids": data["schedule_phase_ids"].astype(np.int32),
    }


def choose_exact_schedule(policy: dict[str, Any], target_center: np.ndarray, exact_epsilon: float) -> dict[str, Any] | None:
    centers = np.asarray(policy["schedule_target_centers"], dtype=np.float64)
    distances = np.linalg.norm(centers[:, :2] - target_center[:2], axis=1)
    if not distances.size:
        return None
    idx = int(np.argmin(distances))
    if float(distances[idx]) > float(exact_epsilon):
        return None
    return {
        "index": idx,
        "episode_id": int(policy["schedule_episode_ids"][idx]),
        "start": int(policy["schedule_starts"][idx]),
        "length": int(policy["schedule_lengths"][idx]),
        "distance": float(distances[idx]),
    }


def predict_schedule_action(policy: dict[str, Any], exact_schedule: dict[str, Any], step_id: int) -> tuple[np.ndarray, str]:
    table_step = min(int(step_id), max(0, int(exact_schedule["length"]) - 1))
    row = int(exact_schedule["start"]) + table_step
    phase_id = int(policy["schedule_phase_ids"][row])
    return policy["schedule_actions"][row].astype(np.float64), policy["phase_names"][phase_id]


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
    alpha = float(np.clip(phase_step / max(1, length - 1), 0.0, 1.0))
    if not bool(policy["phase_has_model"][phase_id]):
        start = policy["fallback_start"][phase_id]
        end = policy["fallback_end"][phase_id]
    else:
        x = target_features(
            np.asarray([target_offset], dtype=np.float64),
            np.asarray([target_drop], dtype=np.float64),
            rbf_centers=policy["target_offset_centers"],
            rbf_sigma=policy["rbf_sigma"],
        )
        start = (x @ policy["start_weights"][phase_id])[0]
        end = (x @ policy["end_weights"][phase_id])[0]
    action = (1.0 - alpha) * start + alpha * end
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
    clip: bool,
    exact_epsilon: float,
    renderer=None,
    writer=None,
    visual_dir: Path | None = None,
    snapshot_prefix: str = "phase_keypoint",
    capture_every: int = 8,
) -> dict[str, Any]:
    api.reset_hand_open()
    initial_ball = api.get_ball_pose()["position"].copy()
    target_offset = np.asarray(target_center, dtype=np.float64) - initial_ball
    target_drop = choose_drop(policy, target_center)
    exact_schedule = choose_exact_schedule(policy, target_center, exact_epsilon)
    counters: dict[str, Any] = {
        "lifted_once": False,
        "release_started": False,
        "transport_floor_contacts": 0,
        "stable_target_steps": 0,
        "step_count": 0,
    }
    trace = []
    snapshots: dict[str, str] = {}
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
        if exact_schedule is not None:
            action, phase_name = predict_schedule_action(policy, exact_schedule, step_id)
        else:
            action, phase_name = predict_action(
                policy,
                step_id=step_id,
                target_offset=target_offset,
                target_drop=target_drop,
                clip=clip,
            )
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
            if exact_schedule is not None:
                _, next_phase_name = predict_schedule_action(policy, exact_schedule, step_id + 1)
            else:
                _, next_phase_name = predict_action(
                    policy,
                    step_id=step_id + 1,
                    target_offset=target_offset,
                    target_drop=target_drop,
                    clip=clip,
                )
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
        "exact_schedule_episode_id": None if exact_schedule is None else int(exact_schedule["episode_id"]),
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
        "# Arm-Hand Stage1 V3 Pick-Place Phase Keypoint Policy Eval\n\n",
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
        f"- RBF sigma: `{payload['rbf_sigma']}`\n",
        f"- Ridge: `{payload['ridge']}`\n",
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
            "- This is a phase-keypoint target-conditioned policy.\n",
            "- It learns phase endpoint actions from demonstrations and executes a phase schedule online.\n",
            "- PASS on held-out local targets is stronger evidence than nearest-neighbor phase-table replay, but it is still a staged-control policy, not hardware-ready runtime integration.\n",
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
        policy = args.policy or (run_dir / "checkpoints" / f"phase_keypoint_policy_v0_8_gate1_sigma{sigma_tag}.npz")
        report = args.report or (run_dir / "eval" / f"{args.eval_name}_eval_report.md")
        metadata = args.metadata or (run_dir / "eval" / f"{args.eval_name}_summary.json")
        csv_path = args.csv or (run_dir / "eval" / f"{args.eval_name}_episodes.csv")
        video = args.video or (run_dir / "visuals" / f"{args.eval_name}_policy_demo.mp4")
        contact_sheet = args.contact_sheet or (run_dir / "visuals" / f"{args.eval_name}_policy_contact_sheet.png")
    else:
        policy = args.policy
        report = args.report
        metadata = args.metadata
        csv_path = args.csv
        video = args.video
        contact_sheet = args.contact_sheet
    return {
        "run_dir": run_dir,
        "policy": Path(policy) if policy else None,
        "report": Path(report) if report else None,
        "metadata": Path(metadata) if metadata else None,
        "csv": Path(csv_path) if csv_path else None,
        "video": Path(video) if video else None,
        "contact_sheet": Path(contact_sheet) if contact_sheet else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate v0.8 Gate1 phase-keypoint pick-place policy.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--scene", type=Path, default=CURRENT_PICK_PLACE_SCENE)
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--metadata", type=Path, default=None)
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--contact-sheet", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--eval-name", default="v0_8_gate1_phase_keypoint_eval")
    parser.add_argument("--action-field", choices=["actions", "expert_actions"], default="actions")
    parser.add_argument("--profile", default="clean_nominal")
    parser.add_argument("--ridge", type=float, default=1e-6)
    parser.add_argument("--rbf-sigma", type=float, default=0.012)
    parser.add_argument("--feature-mode", choices=["affine", "rbf"], default="rbf")
    parser.add_argument("--fit-local-center", type=lambda raw: np.asarray(parse_values(raw), dtype=np.float64), default=None)
    parser.add_argument("--fit-local-radius", type=float, default=0.031)
    parser.add_argument("--exact-epsilon", type=float, default=1e-9)
    parser.add_argument("--target-center", type=lambda raw: np.asarray(parse_values(raw), dtype=np.float64), default=DEFAULT_TARGET_CENTER)
    parser.add_argument("--target-centers", default="")
    parser.add_argument("--x-offsets", default="0.0")
    parser.add_argument("--y-offsets", default="0.0")
    parser.add_argument("--target-radius", type=float, default=DEFAULT_TARGET_RADIUS_M)
    parser.add_argument("--required-stable-steps", type=int, default=DEFAULT_REQUIRED_STABLE_STEPS)
    parser.add_argument("--max-steps", type=int, default=8200)
    parser.add_argument("--sample-every", type=int, default=100)
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
    if paths["policy"] is None or paths["report"] is None or paths["metadata"] is None:
        raise ValueError("--policy, --report, and --metadata are required unless --run-dir is provided")
    dataset_path = Path(args.dataset).resolve()
    trained = train_policy(
        dataset_path,
        action_field=args.action_field,
        profile=args.profile,
        ridge=args.ridge,
        rbf_sigma=args.rbf_sigma,
        feature_mode=args.feature_mode,
        local_center=args.fit_local_center,
        local_radius=args.fit_local_radius,
    )
    save_policy(paths["policy"], trained)
    policy = load_policy(paths["policy"])

    api = ArmHandStage1TaskAPI(args.scene)
    target_rows_eval = build_target_rows(args)
    results = []
    rendered_video = None
    rendered_contact_sheet = None
    all_snapshots: dict[str, str] = {}
    for row in target_rows_eval:
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
                clip=not args.no_clip,
                exact_epsilon=args.exact_epsilon,
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
        "policy": str(paths["policy"].resolve()),
        "policy_mode": policy["mode"],
        "source_dataset": policy["source_dataset"],
        "scene": str(Path(args.scene).resolve()),
        "contract_version": TASK_CONTRACT_VERSION,
        "target_radius": float(args.target_radius),
        "required_stable_steps": int(args.required_stable_steps),
        "max_steps": int(args.max_steps),
        "clip": not args.no_clip,
        "ridge": float(args.ridge),
        "rbf_sigma": float(args.rbf_sigma),
        "feature_mode": args.feature_mode,
        "fit_local_center": None if args.fit_local_center is None else args.fit_local_center,
        "fit_local_radius": float(args.fit_local_radius),
        "exact_epsilon": float(args.exact_epsilon),
        "phase_rows": trained["phase_rows"],
        "summary": summarize(results),
        "results": results,
        "csv": str(paths["csv"]) if paths["csv"] else None,
        "video": rendered_video,
        "contact_sheet": rendered_contact_sheet,
        "snapshots": all_snapshots,
        "training_ready": False,
    }
    paths["metadata"].parent.mkdir(parents=True, exist_ok=True)
    paths["metadata"].write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    if paths["csv"] is not None:
        write_csv(paths["csv"], json_ready(results))
    write_report(paths["report"], json_ready(payload))
    print(json.dumps(json_ready(payload["summary"]), indent=2, ensure_ascii=False))
    print(f"Saved policy: {paths['policy']}")
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
