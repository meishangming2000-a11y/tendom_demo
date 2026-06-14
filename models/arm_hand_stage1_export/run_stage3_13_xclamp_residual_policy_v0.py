#!/usr/bin/env python3
"""Stage3.13 x-clamp residual policy distillation and gate.

This stage turns the Stage3.12C directional x-clamp teacher into a small
bounded residual policy. The policy predicts a grasp-x correction from the
randomized MuJoCo planning context, then the controller applies a safety clamp
before IK. It stays MuJoCo-only and keeps full-action ACT/DP out of scope.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from arm_hand_stage1_task_api import json_ready
import export_stage3_11d_d_dense_sensor_fusion_dataset_v0 as dense
import run_stage3_11d_b_event_contact_gated_robustness_v0 as robustness
import run_stage3_12_autonomous_tuning_batch_v0 as autotune
import train_stage3_11d_b_event_contact_gated_refine_v0 as event


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_SELECTED = META / "stage3_11d_i_demo_quality_static_geometry_selected_v0.json"
DEFAULT_DATASET = DATA / "stage3_13_xclamp_residual_policy_dataset_v0.npz"
DEFAULT_JSONL = DATA / "stage3_13_xclamp_residual_policy_dataset_v0.jsonl"
DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_13_xclamp_residual_policy_v0.pth"
DEFAULT_REPORT = DOCS / "stage3_13_xclamp_residual_policy_v0_report.md"
DEFAULT_METADATA = META / "stage3_13_xclamp_residual_policy_v0.json"
DEFAULT_SUMMARY_CSV = DATA / "stage3_13_xclamp_residual_policy_v0_summary.csv"

STATUS = "stage3_13_xclamp_residual_policy_v0_mujoco_only_teacher_distillation"
TEACHER_X_MIN = -0.0025
TEACHER_X_MAX = 0.0
MAX_ABS_RESIDUAL_M = 0.0015

FEATURE_NAMES = [
    "raw_grasp_offset_x_m",
    "raw_grasp_offset_y_m",
    "raw_grasp_offset_z_m",
    "ball_offset_x_m",
    "ball_offset_y_m",
    "ball_radius_m",
    "ball_mass_kg",
    "tip_mu",
    "ball_mu",
    "non_tip_mu",
    "tip_pair_separation_target_m",
    "lift_steps",
    "hold_steps",
    "min_lift_height_m",
    "gx_margin_to_min_m",
    "gx_margin_to_max_m",
    "gx_below_min_m",
    "gx_above_max_m",
    "object_to_grasp_x_m",
]


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass(frozen=True)
class TrainResult:
    checkpoint: Path
    train_loss: float
    val_loss: float
    val_mae_m: float
    val_max_abs_error_m: float
    train_episodes: list[int]
    val_episodes: list[int]


class ResidualPolicy(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(int(input_dim), int(hidden_dim)),
            nn.LayerNorm(int(hidden_dim)),
            nn.GELU(),
            nn.Dropout(float(dropout)),
            nn.Linear(int(hidden_dim), max(32, int(hidden_dim) // 2)),
            nn.GELU(),
            nn.Dropout(float(dropout)),
            nn.Linear(max(32, int(hidden_dim) // 2), 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def candidate_map() -> dict[str, autotune.Candidate]:
    return {candidate.name: candidate for candidate in autotune.candidate_grid()}


def apply_candidate_overrides(args: argparse.Namespace, candidate_name: str) -> None:
    candidates = candidate_map()
    if candidate_name not in candidates:
        raise ValueError(f"Unknown Stage3.12 candidate: {candidate_name}")
    for key, value in candidates[candidate_name].overrides.items():
        setattr(args, key, value)


def build_rb_args(args: argparse.Namespace, *, seed: int, trials: int | None = None) -> argparse.Namespace:
    rb_args = robustness.build_parser().parse_args([])
    rb_args.scene = Path(args.scene)
    rb_args.selected = Path(args.selected)
    rb_args.seed = int(seed)
    rb_args.trials = int(trials if trials is not None else args.eval_trials)
    rb_args.object_pose_noise_xy_m = float(args.object_pose_noise_xy_m)
    rb_args.grasp_target_noise_xy_m = float(args.grasp_target_noise_xy_m)
    rb_args.grasp_target_noise_z_m = float(args.grasp_target_noise_z_m)
    rb_args.radius_jitter_m = float(args.radius_jitter_m)
    rb_args.mass_jitter_kg = float(args.mass_jitter_kg)
    rb_args.friction_scale_jitter = float(args.friction_scale_jitter)
    rb_args.dense_trace_sample_every = max(1, int(args.dense_trace_sample_every))
    apply_candidate_overrides(rb_args, "baseline_di")
    return dense.fill_from_robustness_defaults(rb_args)


def teacher_x(raw_x: float, *, x_min: float, x_max: float) -> float:
    return float(np.clip(float(raw_x), float(x_min), float(x_max)))


def apply_x_teacher(case: event.RefineCase, *, x_min: float, x_max: float) -> tuple[event.RefineCase, float]:
    updated_x = teacher_x(case.grasp_offset_x, x_min=x_min, x_max=x_max)
    delta = float(updated_x - float(case.grasp_offset_x))
    if delta == 0.0:
        return case, 0.0
    return (
        replace(
            case,
            name=f"{case.name}_gxteacher{updated_x:+.4f}".replace("+", "p").replace("-", "m").replace(".", "p"),
            grasp_offset_x=updated_x,
        ),
        delta,
    )


def case_features(case: event.RefineCase, *, x_min: float, x_max: float) -> np.ndarray:
    gx = float(case.grasp_offset_x)
    margin_min = gx - float(x_min)
    margin_max = gx - float(x_max)
    values = [
        gx,
        float(case.grasp_offset_y),
        float(case.grasp_offset_z),
        float(case.ball_offset_x),
        float(case.ball_offset_y),
        float(case.ball_radius),
        float(case.ball_mass),
        float(case.candidate.tip_sliding_mu),
        float(case.candidate.ball_sliding_mu),
        float(case.candidate.non_tip_sliding_mu),
        float(case.tip_pair_separation_target),
        float(case.candidate.lift_steps),
        float(case.hold_steps),
        float(case.min_lift_height),
        margin_min,
        margin_max,
        min(0.0, margin_min),
        max(0.0, margin_max),
        gx - float(case.ball_offset_x),
    ]
    return np.asarray(values, dtype=np.float32)


def generate_cases(
    args: argparse.Namespace,
    *,
    seed: int,
    count: int,
) -> tuple[list[event.RefineCase], argparse.Namespace, event.RefineCase]:
    rb_args = build_rb_args(args, seed=seed, trials=count)
    base = robustness.apply_base_offsets(robustness.selected_case_from_json(Path(rb_args.selected)), rb_args)
    rng = np.random.default_rng(int(seed))
    cases = [robustness.perturb_case(base, rb_args, rng, idx) for idx in range(max(1, int(count)))]
    return cases, rb_args, base


def export_dataset(args: argparse.Namespace) -> dict[str, Any]:
    cases, rb_args, base = generate_cases(args, seed=int(args.dataset_seed), count=int(args.dataset_episodes))
    x_rows: list[np.ndarray] = []
    y_rows: list[float] = []
    episode_summaries: list[dict[str, Any]] = []
    for episode_idx, case in enumerate(cases):
        teacher_case, delta = apply_x_teacher(case, x_min=args.teacher_x_min, x_max=args.teacher_x_max)
        features = case_features(case, x_min=args.teacher_x_min, x_max=args.teacher_x_max)
        x_rows.append(features)
        y_rows.append(float(delta))
        episode_summaries.append(
            {
                "episode_index": int(episode_idx),
                "raw_grasp_offset_x": float(case.grasp_offset_x),
                "teacher_grasp_offset_x": float(teacher_case.grasp_offset_x),
                "target_residual_x_m": float(delta),
                "residual_active": bool(abs(delta) > 1e-9),
                "ball_offset_x": float(case.ball_offset_x),
                "ball_offset_y": float(case.ball_offset_y),
                "grasp_offset_y": float(case.grasp_offset_y),
                "grasp_offset_z": float(case.grasp_offset_z),
                "ball_radius": float(case.ball_radius),
                "ball_mass": float(case.ball_mass),
                "tip_mu": float(case.candidate.tip_sliding_mu),
                "ball_mu": float(case.candidate.ball_sliding_mu),
                "non_tip_mu": float(case.candidate.non_tip_sliding_mu),
            }
        )
    x = np.asarray(x_rows, dtype=np.float32)
    y = np.asarray(y_rows, dtype=np.float32).reshape(-1, 1)
    episode_ids = np.arange(len(y_rows), dtype=np.int32)
    summary = summarize_dataset_targets(y.reshape(-1))
    metadata = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.13",
        "status": STATUS,
        "dataset": str(Path(args.dataset).resolve()),
        "jsonl": str(Path(args.jsonl).resolve()),
        "source_teacher": "Stage3.12C di_directional_gx_clamp_m0025_p0000",
        "teacher_rule": {
            "grasp_offset_x_min": float(args.teacher_x_min),
            "grasp_offset_x_max": float(args.teacher_x_max),
            "applied_before_ik": True,
        },
        "feature_names": FEATURE_NAMES,
        "target_names": ["target_residual_x_m"],
        "args": json_ready(vars(args)),
        "base_case": {
            "name": base.name,
            "candidate": asdict(base.candidate),
            "tip_pair_separation_target": base.tip_pair_separation_target,
            "grasp_offset_x": base.grasp_offset_x,
            "grasp_offset_y": base.grasp_offset_y,
            "grasp_offset_z": base.grasp_offset_z,
            "ball_radius": base.ball_radius,
            "ball_mass": base.ball_mass,
            "hold_steps": base.hold_steps,
            "min_lift_height": base.min_lift_height,
        },
        "summary": summary,
        "boundary": boundary_payload(),
    }
    args.dataset.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.dataset,
        features=x,
        target_residual_x_m=y,
        episode_ids=episode_ids,
        feature_names=np.asarray(FEATURE_NAMES, dtype=np.str_),
        target_names=np.asarray(["target_residual_x_m"], dtype=np.str_),
        teacher_x_min=np.asarray([float(args.teacher_x_min)], dtype=np.float32),
        teacher_x_max=np.asarray([float(args.teacher_x_max)], dtype=np.float32),
        metadata_json=np.asarray([json.dumps(json_ready(metadata), ensure_ascii=False)], dtype=np.str_),
    )
    args.jsonl.parent.mkdir(parents=True, exist_ok=True)
    with args.jsonl.open("w", encoding="utf-8") as handle:
        for row in episode_summaries:
            handle.write(json.dumps(json_ready(row), ensure_ascii=False) + "\n")
    return {**metadata, "episode_summaries_sample": episode_summaries[:20], "rb_args": json_ready(vars(rb_args))}


def summarize_dataset_targets(targets: np.ndarray) -> dict[str, Any]:
    targets = np.asarray(targets, dtype=np.float32).reshape(-1)
    active = np.abs(targets) > 1e-9
    return {
        "episodes": int(targets.shape[0]),
        "residual_active_count": int(np.sum(active)),
        "residual_active_fraction": float(np.mean(active)) if targets.size else 0.0,
        "target_abs_mean_m": float(np.mean(np.abs(targets))) if targets.size else 0.0,
        "target_abs_max_m": float(np.max(np.abs(targets))) if targets.size else 0.0,
        "target_min_m": float(np.min(targets)) if targets.size else 0.0,
        "target_max_m": float(np.max(targets)) if targets.size else 0.0,
    }


def load_dataset(path: Path) -> np.lib.npyio.NpzFile:
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    return np.load(path, allow_pickle=False)


def split_by_episode(
    episode_ids: np.ndarray,
    *,
    val_fraction: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, list[int], list[int]]:
    unique = np.unique(episode_ids.astype(np.int32))
    if len(unique) <= 2:
        mask = np.ones_like(episode_ids, dtype=bool)
        return mask.copy(), mask.copy(), unique.tolist(), unique.tolist()
    rng = np.random.default_rng(int(seed))
    shuffled = unique.copy()
    rng.shuffle(shuffled)
    val_count = max(1, int(round(len(shuffled) * float(val_fraction))))
    val_eps = set(int(v) for v in shuffled[:val_count])
    val_mask = np.asarray([int(v) in val_eps for v in episode_ids], dtype=bool)
    train_mask = ~val_mask
    if not np.any(train_mask):
        train_mask[:] = True
    return train_mask, val_mask, np.unique(episode_ids[train_mask]).astype(int).tolist(), sorted(val_eps)


def normalize(train_x: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = train_x.mean(axis=0).astype(np.float32)
    std = train_x.std(axis=0).astype(np.float32)
    std = np.maximum(std, 1e-6)
    return ((x - mean.reshape(1, -1)) / std.reshape(1, -1)).astype(np.float32), mean, std


def batch_indices(count: int, batch_size: int, rng: np.random.Generator) -> list[np.ndarray]:
    order = np.arange(int(count), dtype=np.int64)
    rng.shuffle(order)
    return [order[start : start + int(batch_size)] for start in range(0, int(count), int(batch_size))]


def train_policy(args: argparse.Namespace) -> TrainResult:
    data = load_dataset(Path(args.dataset))
    x = np.asarray(data["features"], dtype=np.float32)
    y_m = np.asarray(data["target_residual_x_m"], dtype=np.float32).reshape(-1, 1)
    episode_ids = np.asarray(data["episode_ids"], dtype=np.int32)
    train_mask, val_mask, train_eps, val_eps = split_by_episode(
        episode_ids,
        val_fraction=float(args.val_fraction),
        seed=int(args.train_seed),
    )
    x_norm, mean, std = normalize(x[train_mask], x)
    target_scale = float(args.residual_scale_m)
    y = (y_m / max(target_scale, 1e-9)).astype(np.float32)

    model = ResidualPolicy(x.shape[1], int(args.hidden_dim), float(args.dropout))
    optimizer = optim.AdamW(model.parameters(), lr=float(args.lr), weight_decay=float(args.weight_decay))
    loss_fn = nn.SmoothL1Loss(beta=float(args.smooth_l1_beta))
    rng = np.random.default_rng(int(args.train_seed))

    train_idx = np.flatnonzero(train_mask)
    val_idx = np.flatnonzero(val_mask)
    best_state: dict[str, torch.Tensor] | None = None
    best_val = float("inf")
    best_epoch = -1
    final_train = float("inf")
    for epoch in range(max(1, int(args.epochs))):
        model.train()
        losses: list[float] = []
        for batch in batch_indices(len(train_idx), int(args.batch_size), rng):
            idx = train_idx[batch]
            bx = torch.from_numpy(x_norm[idx])
            by = torch.from_numpy(y[idx])
            pred = model(bx)
            loss = loss_fn(pred, by)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.item()))
        final_train = float(np.mean(losses)) if losses else 0.0
        model.eval()
        with torch.no_grad():
            val_pred = model(torch.from_numpy(x_norm[val_idx]))
            val_loss = float(loss_fn(val_pred, torch.from_numpy(y[val_idx])).item())
        if val_loss <= best_val:
            best_val = val_loss
            best_epoch = epoch
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        pred_m = model(torch.from_numpy(x_norm[val_idx])).cpu().numpy() * target_scale
    err = pred_m - y_m[val_idx]
    val_mae = float(np.mean(np.abs(err))) if err.size else 0.0
    val_max_abs = float(np.max(np.abs(err))) if err.size else 0.0
    checkpoint = {
        "stage": "Stage3.13",
        "status": STATUS,
        "model_state": model.state_dict(),
        "input_dim": int(x.shape[1]),
        "hidden_dim": int(args.hidden_dim),
        "dropout": float(args.dropout),
        "feature_mean": mean,
        "feature_std": std,
        "feature_names": FEATURE_NAMES,
        "target_scale_m": target_scale,
        "teacher_x_min": float(args.teacher_x_min),
        "teacher_x_max": float(args.teacher_x_max),
        "max_abs_residual_m": float(args.max_abs_residual_m),
        "best_epoch": int(best_epoch),
        "best_val_loss": float(best_val),
        "val_mae_m": float(val_mae),
        "val_max_abs_error_m": float(val_max_abs),
        "dataset": str(Path(args.dataset).resolve()),
        "boundary": boundary_payload(),
    }
    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, args.checkpoint)
    return TrainResult(
        checkpoint=Path(args.checkpoint),
        train_loss=float(final_train),
        val_loss=float(best_val),
        val_mae_m=val_mae,
        val_max_abs_error_m=val_max_abs,
        train_episodes=train_eps,
        val_episodes=val_eps,
    )


def load_policy(path: Path) -> dict[str, Any]:
    raw = torch.load(Path(path), map_location="cpu", weights_only=False)
    model = ResidualPolicy(int(raw["input_dim"]), int(raw["hidden_dim"]), float(raw["dropout"]))
    model.load_state_dict(raw["model_state"])
    model.eval()
    raw["model"] = model
    raw["feature_mean"] = np.asarray(raw["feature_mean"], dtype=np.float32)
    raw["feature_std"] = np.asarray(raw["feature_std"], dtype=np.float32)
    return raw


def predict_residual(policy: dict[str, Any], case: event.RefineCase) -> float:
    x = case_features(case, x_min=float(policy["teacher_x_min"]), x_max=float(policy["teacher_x_max"]))
    x_norm = ((x.reshape(1, -1) - policy["feature_mean"].reshape(1, -1)) / policy["feature_std"].reshape(1, -1)).astype(
        np.float32
    )
    with torch.no_grad():
        pred = policy["model"](torch.from_numpy(x_norm)).cpu().numpy()[0, 0]
    delta = float(pred * float(policy["target_scale_m"]))
    return float(np.clip(delta, -float(policy["max_abs_residual_m"]), float(policy["max_abs_residual_m"])))


def apply_policy_case(
    case: event.RefineCase,
    policy: dict[str, Any],
    *,
    safety_clip: bool,
) -> tuple[event.RefineCase, dict[str, Any]]:
    raw_x = float(case.grasp_offset_x)
    predicted_delta = predict_residual(policy, case)
    proposed_x = raw_x + predicted_delta
    applied_x = (
        teacher_x(proposed_x, x_min=float(policy["teacher_x_min"]), x_max=float(policy["teacher_x_max"]))
        if safety_clip
        else float(proposed_x)
    )
    applied_delta = float(applied_x - raw_x)
    out = replace(
        case,
        name=f"{case.name}_xrespol{applied_x:+.4f}".replace("+", "p").replace("-", "m").replace(".", "p"),
        grasp_offset_x=applied_x,
    )
    return (
        out,
        {
            "raw_grasp_offset_x": raw_x,
            "predicted_delta_x_m": predicted_delta,
            "proposed_grasp_offset_x": float(proposed_x),
            "applied_grasp_offset_x": float(applied_x),
            "applied_delta_x_m": applied_delta,
            "safety_clip": bool(safety_clip),
        },
    )


def morphology_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    holds = [row.get("hold_morphology", {}) for row in rows]

    def mean(key: str) -> float:
        values = [float(item.get(key, 0.0)) for item in holds if isinstance(item, dict)]
        return float(np.mean(values)) if values else 0.0

    return {
        "hold_true_two_tip_mean": mean("true_two_tip_pinch_fraction"),
        "hold_non_tip_ratio_mean": mean("non_tip_contact_ratio_mean"),
        "hold_wrap_fraction_mean": mean("wrap_frame_fraction"),
        "hold_floor_contact_fraction_mean": mean("floor_contact_fraction"),
        "max_penetration_m_max": float(max([float(row.get("max_penetration_m", 0.0)) for row in rows] + [0.0])),
    }


def residual_eval_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    residuals = [row.get("stage3_13_residual_policy", {}) for row in rows]
    applied = [float(item.get("applied_delta_x_m", 0.0)) for item in residuals]
    predicted = [float(item.get("predicted_delta_x_m", 0.0)) for item in residuals]
    clipped = [
        abs(float(item.get("proposed_grasp_offset_x", 0.0)) - float(item.get("applied_grasp_offset_x", 0.0))) > 1e-9
        for item in residuals
    ]
    return {
        "residual_active_count": int(sum(abs(value) > 1e-9 for value in applied)),
        "residual_active_fraction": float(np.mean([abs(value) > 1e-9 for value in applied])) if applied else 0.0,
        "predicted_delta_abs_mean_m": float(np.mean(np.abs(predicted))) if predicted else 0.0,
        "applied_delta_abs_mean_m": float(np.mean(np.abs(applied))) if applied else 0.0,
        "safety_clip_count": int(sum(clipped)),
        "safety_clip_fraction": float(np.mean(clipped)) if clipped else 0.0,
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = robustness.summarize(rows)
    summary.update(morphology_summary(rows))
    summary.update(residual_eval_summary(rows))
    return summary


def mode_case(
    mode: str,
    raw_case: event.RefineCase,
    policy: dict[str, Any],
    args: argparse.Namespace,
) -> tuple[event.RefineCase, dict[str, Any]]:
    if mode == "baseline_di":
        return raw_case, {
            "raw_grasp_offset_x": float(raw_case.grasp_offset_x),
            "predicted_delta_x_m": 0.0,
            "proposed_grasp_offset_x": float(raw_case.grasp_offset_x),
            "applied_grasp_offset_x": float(raw_case.grasp_offset_x),
            "applied_delta_x_m": 0.0,
            "safety_clip": False,
        }
    if mode == "teacher_xclamp":
        teacher_case, delta = apply_x_teacher(raw_case, x_min=args.teacher_x_min, x_max=args.teacher_x_max)
        return teacher_case, {
            "raw_grasp_offset_x": float(raw_case.grasp_offset_x),
            "predicted_delta_x_m": float(delta),
            "proposed_grasp_offset_x": float(teacher_case.grasp_offset_x),
            "applied_grasp_offset_x": float(teacher_case.grasp_offset_x),
            "applied_delta_x_m": float(delta),
            "safety_clip": True,
        }
    if mode == "learned_xresidual_safe":
        return apply_policy_case(raw_case, policy, safety_clip=True)
    if mode == "learned_xresidual_raw":
        return apply_policy_case(raw_case, policy, safety_clip=False)
    raise ValueError(f"Unknown eval mode: {mode}")


def run_eval_mode(
    *,
    scene: Path,
    mujoco: Any,
    args: argparse.Namespace,
    policy: dict[str, Any],
    seed: int,
    mode: str,
) -> dict[str, Any]:
    raw_cases, rb_args, _base = generate_cases(args, seed=int(seed), count=int(args.eval_trials))
    ev_args = robustness.event_args_from(rb_args)
    ev_args.capture_dense_sensor_trace = False
    rows: list[dict[str, Any]] = []
    for trial_idx, raw_case in enumerate(raw_cases):
        case, residual_info = mode_case(mode, raw_case, policy, args)
        model = mujoco.MjModel.from_xml_path(str(scene))
        row = event.run_event_candidate(model, mujoco, case, ev_args)
        row["trial_index"] = int(trial_idx)
        row["eval_seed"] = int(seed)
        row["eval_mode"] = mode
        row["stage3_13_residual_policy"] = residual_info
        rows.append(row)
        if bool(args.verbose_trials):
            hm = row.get("hold_morphology", {})
            print(
                f"{mode} seed={seed} {trial_idx + 1:03d}/{args.eval_trials:03d} {row['status']} "
                f"lift={row.get('hold_lift_m_max', 0.0):.4f} "
                f"two_tip={hm.get('true_two_tip_pinch_fraction', 0.0):.3f} "
                f"dx={residual_info.get('applied_delta_x_m', 0.0):+.5f} "
                f"reason={row['terminal_reason']}"
            )
    return {
        "mode": mode,
        "seed": int(seed),
        "trials": int(args.eval_trials),
        "summary": summarize_rows(rows),
        "results": [strip_trace(row) for row in rows],
    }


def strip_trace(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "dense_sensor_trace"}


def aggregate_eval(eval_items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_mode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in eval_items:
        by_mode[str(item["mode"])].extend(item.get("results", []))
    return {mode: summarize_rows(rows) for mode, rows in by_mode.items()}


def eval_policy(args: argparse.Namespace) -> dict[str, Any]:
    import mujoco

    policy = load_policy(Path(args.checkpoint))
    scene = Path(args.scene).resolve()
    modes = [item.strip() for item in str(args.eval_modes).split(",") if item.strip()]
    seeds = [int(item.strip()) for item in str(args.eval_seeds).split(",") if item.strip()]
    eval_items: list[dict[str, Any]] = []
    for seed in seeds:
        for mode in modes:
            print(f"Evaluating {mode} seed={seed} trials={args.eval_trials}")
            eval_items.append(run_eval_mode(scene=scene, mujoco=mujoco, args=args, policy=policy, seed=seed, mode=mode))
    return {
        "items": eval_items,
        "aggregate": aggregate_eval(eval_items),
        "seeds": seeds,
        "modes": modes,
    }


def boundary_payload() -> dict[str, Any]:
    return {
        "mujoco_only": True,
        "teacher_distillation": True,
        "hardware_runtime": False,
        "real_camera": False,
        "real_tactile": False,
        "full_action_act_dp": False,
        "demo_gallery_promotion": False,
    }


def decision_from_aggregate(aggregate: dict[str, dict[str, Any]]) -> dict[str, Any]:
    baseline = aggregate.get("baseline_di", {})
    teacher = aggregate.get("teacher_xclamp", {})
    learned = aggregate.get("learned_xresidual_safe", {})
    b_success = int(baseline.get("success_count", 0))
    t_success = int(teacher.get("success_count", 0))
    l_success = int(learned.get("success_count", 0))
    teacher_morph_fail = int(teacher.get("terminal_reason_counts", {}).get("true_pinch_morphology_gate_failed", 0))
    learned_morph_fail = int(learned.get("terminal_reason_counts", {}).get("true_pinch_morphology_gate_failed", 0))
    if l_success >= t_success and learned_morph_fail <= teacher_morph_fail:
        status = "advance_distilled_policy_candidate"
        text = (
            "The learned bounded residual policy matched or beat the Stage3.12C teacher on the matched gate "
            "without adding true-pinch morphology failures."
        )
    elif l_success > b_success:
        status = "partial_progress_keep_teacher_primary"
        text = (
            "The learned residual policy beat frozen D-I but did not match the Stage3.12C teacher. Keep the "
            "teacher primary and improve the model or safety wrapper."
        )
    else:
        status = "do_not_promote_model"
        text = (
            "The learned residual policy did not beat frozen D-I. Keep Stage3.12C as teacher evidence and move "
            "to dataset/model diagnosis."
        )
    return {
        "status": status,
        "text": text,
        "success_delta_learned_vs_baseline": int(l_success - b_success),
        "success_delta_learned_vs_teacher": int(l_success - t_success),
        "true_pinch_morphology_failures_added_vs_teacher": int(learned_morph_fail - teacher_morph_fail),
    }


def write_summary_csv(path: Path, payload: dict[str, Any]) -> None:
    fields = [
        "scope",
        "mode",
        "seed",
        "success",
        "trials",
        "contact",
        "lift",
        "true_pinch",
        "release",
        "terminal_reasons",
        "hold_true_two_tip_mean",
        "hold_non_tip_ratio_mean",
        "hold_wrap_fraction_mean",
        "hold_floor_contact_fraction_mean",
        "residual_active_fraction",
        "safety_clip_fraction",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in payload["eval"]["items"]:
            s = item["summary"]
            writer.writerow(summary_csv_row("seed", item["mode"], item["seed"], s))
        for mode, s in payload["eval"]["aggregate"].items():
            writer.writerow(summary_csv_row("aggregate", mode, "all", s))


def summary_csv_row(scope: str, mode: str, seed: Any, s: dict[str, Any]) -> dict[str, Any]:
    return {
        "scope": scope,
        "mode": mode,
        "seed": seed,
        "success": s.get("success_count", ""),
        "trials": s.get("trials", ""),
        "contact": s.get("contact_gate_success_count", ""),
        "lift": s.get("lift_success_count", ""),
        "true_pinch": s.get("true_pinch_success_count", ""),
        "release": s.get("release_success_count", ""),
        "terminal_reasons": json.dumps(s.get("terminal_reason_counts", {}), ensure_ascii=False),
        "hold_true_two_tip_mean": f"{float(s.get('hold_true_two_tip_mean', 0.0)):.6f}",
        "hold_non_tip_ratio_mean": f"{float(s.get('hold_non_tip_ratio_mean', 0.0)):.6f}",
        "hold_wrap_fraction_mean": f"{float(s.get('hold_wrap_fraction_mean', 0.0)):.6f}",
        "hold_floor_contact_fraction_mean": f"{float(s.get('hold_floor_contact_fraction_mean', 0.0)):.6f}",
        "residual_active_fraction": f"{float(s.get('residual_active_fraction', 0.0)):.6f}",
        "safety_clip_fraction": f"{float(s.get('safety_clip_fraction', 0.0)):.6f}",
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    dataset = payload["dataset"]
    train = payload["train"]
    aggregate = payload["eval"]["aggregate"]
    decision = payload["decision"]
    lines = [
        "# Stage3.13 X-Clamp Residual Policy v0\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        "## Boundary\n\n",
        "- MuJoCo-only teacher distillation from Stage3.12C x-clamp.\n",
        "- Action surface is a bounded grasp-x residual before IK, not full-action control.\n",
        "- The learned policy is evaluated with a safety clamp around the Stage3.12C corridor.\n",
        "- No hardware runtime, real camera, real tactile, demo-gallery, or full-action ACT/DP promotion.\n\n",
        "## Dataset\n\n",
        f"- Episodes: `{dataset['summary']['episodes']}`\n",
        f"- Residual-active labels: `{dataset['summary']['residual_active_count']}` "
        f"(`{dataset['summary']['residual_active_fraction']:.3f}`)\n",
        f"- Mean/max |target residual|: `{dataset['summary']['target_abs_mean_m']:.6f}` / "
        f"`{dataset['summary']['target_abs_max_m']:.6f} m`\n\n",
        "## Training\n\n",
        f"- Checkpoint: `{train['checkpoint']}`\n",
        f"- Val MAE: `{train['val_mae_m']:.8f} m`\n",
        f"- Val max abs error: `{train['val_max_abs_error_m']:.8f} m`\n\n",
        "## Closed-Loop Gate\n\n",
        "| mode | success | contact | lift | true pinch | release | hold non-tip | wrap | residual active | clip fraction | reasons |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|\n",
    ]
    for mode in payload["eval"]["modes"]:
        s = aggregate.get(mode, {})
        lines.append(
            f"| `{mode}` | {s.get('success_count', 0)}/{s.get('trials', 0)} | "
            f"{s.get('contact_gate_success_count', 0)} | "
            f"{s.get('lift_success_count', 0)} | "
            f"{s.get('true_pinch_success_count', 0)} | "
            f"{s.get('release_success_count', 0)} | "
            f"{float(s.get('hold_non_tip_ratio_mean', 0.0)):.3f} | "
            f"{float(s.get('hold_wrap_fraction_mean', 0.0)):.3f} | "
            f"{float(s.get('residual_active_fraction', 0.0)):.3f} | "
            f"{float(s.get('safety_clip_fraction', 0.0)):.3f} | "
            f"`{s.get('terminal_reason_counts', {})}` |\n"
        )
    lines.extend(
        [
            "\n## Decision\n\n",
            f"- Status: `{decision['status']}`\n",
            f"- {decision['text']}\n",
            f"- Learned vs D-I success delta: `{decision['success_delta_learned_vs_baseline']}`\n",
            f"- Learned vs teacher success delta: `{decision['success_delta_learned_vs_teacher']}`\n",
            f"- True-pinch morphology failures added vs teacher: "
            f"`{decision['true_pinch_morphology_failures_added_vs_teacher']}`\n\n",
            "## Next\n\n",
            "- If success: use this as Stage3.13A distilled residual-policy candidate and broaden to "
            "contact/lift windows only after preserving this matched gate.\n",
            "- If failure: keep Stage3.12C teacher primary, inspect residual prediction errors, and avoid "
            "returning to open-ended D-I parameter tuning.\n\n",
            "## Artifacts\n\n",
            f"- Dataset: `{payload['dataset_path']}`\n",
            f"- JSONL: `{payload['jsonl_path']}`\n",
            f"- Checkpoint: `{payload['checkpoint_path']}`\n",
            f"- Summary CSV: `{payload['summary_csv']}`\n",
            f"- Metadata: `{payload['metadata']}`\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage3.13 x-clamp residual policy distillation and eval.")
    parser.add_argument("--scene", type=Path, default=event.DEFAULT_SCENE)
    parser.add_argument("--selected", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--summary-csv", type=Path, default=DEFAULT_SUMMARY_CSV)
    parser.add_argument("--skip-export", action="store_true")
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-eval", action="store_true")
    parser.add_argument("--dataset-episodes", type=int, default=300)
    parser.add_argument("--dataset-seed", type=int, default=20260614)
    parser.add_argument("--eval-trials", type=int, default=50)
    parser.add_argument("--eval-seeds", default="20260612,20265612,20265613")
    parser.add_argument("--eval-modes", default="baseline_di,teacher_xclamp,learned_xresidual_safe")
    parser.add_argument("--teacher-x-min", type=float, default=TEACHER_X_MIN)
    parser.add_argument("--teacher-x-max", type=float, default=TEACHER_X_MAX)
    parser.add_argument("--max-abs-residual-m", type=float, default=MAX_ABS_RESIDUAL_M)
    parser.add_argument("--residual-scale-m", type=float, default=MAX_ABS_RESIDUAL_M)
    parser.add_argument("--object-pose-noise-xy-m", type=float, default=0.003)
    parser.add_argument("--grasp-target-noise-xy-m", type=float, default=0.002)
    parser.add_argument("--grasp-target-noise-z-m", type=float, default=0.001)
    parser.add_argument("--radius-jitter-m", type=float, default=0.001)
    parser.add_argument("--mass-jitter-kg", type=float, default=0.002)
    parser.add_argument("--friction-scale-jitter", type=float, default=0.08)
    parser.add_argument("--dense-trace-sample-every", type=int, default=25)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=96)
    parser.add_argument("--dropout", type=float, default=0.02)
    parser.add_argument("--lr", type=float, default=2e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--smooth-l1-beta", type=float, default=0.02)
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--train-seed", type=int, default=20260614)
    parser.add_argument("--verbose-trials", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.13",
        "status": STATUS,
        "args": json_ready(vars(args)),
        "dataset_path": str(Path(args.dataset).resolve()),
        "jsonl_path": str(Path(args.jsonl).resolve()),
        "checkpoint_path": str(Path(args.checkpoint).resolve()),
        "summary_csv": str(Path(args.summary_csv).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "report": str(Path(args.report).resolve()),
        "boundary": boundary_payload(),
    }

    if args.skip_export:
        data = load_dataset(Path(args.dataset))
        meta = json.loads(str(data["metadata_json"][0])) if "metadata_json" in data.files else {}
        payload["dataset"] = {
            "summary": summarize_dataset_targets(np.asarray(data["target_residual_x_m"], dtype=np.float32).reshape(-1)),
            "metadata_from_file": meta,
        }
    else:
        payload["dataset"] = export_dataset(args)

    if args.skip_train:
        checkpoint = load_policy(Path(args.checkpoint))
        payload["train"] = {
            "checkpoint": str(Path(args.checkpoint).resolve()),
            "val_mae_m": float(checkpoint.get("val_mae_m", 0.0)),
            "val_max_abs_error_m": float(checkpoint.get("val_max_abs_error_m", 0.0)),
            "best_val_loss": float(checkpoint.get("best_val_loss", 0.0)),
        }
    else:
        train_result = train_policy(args)
        payload["train"] = {
            "checkpoint": str(train_result.checkpoint.resolve()),
            "train_loss": float(train_result.train_loss),
            "val_loss": float(train_result.val_loss),
            "val_mae_m": float(train_result.val_mae_m),
            "val_max_abs_error_m": float(train_result.val_max_abs_error_m),
            "train_episode_count": int(len(train_result.train_episodes)),
            "val_episode_count": int(len(train_result.val_episodes)),
            "train_episodes_sample": train_result.train_episodes[:20],
            "val_episodes_sample": train_result.val_episodes[:20],
        }

    if args.skip_eval:
        payload["eval"] = {"items": [], "aggregate": {}, "seeds": [], "modes": []}
    else:
        payload["eval"] = eval_policy(args)
    payload["decision"] = decision_from_aggregate(payload["eval"]["aggregate"])

    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_summary_csv(Path(args.summary_csv), json_ready(payload))
    write_report(Path(args.report), json_ready(payload))
    print(json.dumps(json_ready(payload["decision"]), indent=2, ensure_ascii=False))
    print(f"Saved dataset: {args.dataset}")
    print(f"Saved checkpoint: {args.checkpoint}")
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
