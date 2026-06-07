#!/usr/bin/env python3
"""Train a phase-specific regression policy for Stage2 pick-place.

This v0.7.3 candidate is intentionally small: each phase gets its own ridge
regressor from schedule/target features to action. It is a trainable baseline,
not action-table playback and not a hardware policy.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_v2_bc_common import json_ready, require_fields, string_list


ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET = (
    ROOT
    / "runs"
    / "stage2_pick_place_v0_7_3_phase_specific"
    / "20260602_010000_seed068"
    / "datasets"
    / "arm_hand_stage1_v3_pick_place_dataset_v0_7_3_release_repair.npz"
)

REQUIRED_FIELDS = [
    "actions",
    "episode_ids",
    "step_ids",
    "phase_ids",
    "phase_step_ids",
    "phase_name_table",
    "target_centers",
    "initial_ball_positions",
    "pre_release_z_drops",
    "behavior_profile_ids",
    "behavior_profile_table",
    "actuator_names",
    "contract_version",
]


PHASE_LENGTH_KEYS = {
    "default_hold": "default_hold_steps",
    "move_to_pre_approach": "move_steps",
    "approach_ball": "approach_steps",
    "preshape": "hand_steps",
    "close_four_fingers": "hand_steps",
    "close_thumb": "close_thumb_steps",
    "close_hold": "close_hold_steps",
    "lift": "lift_steps",
    "hold_lift": "hold_steps",
    "transport": "transport_steps",
    "transport_hold": "transport_hold_steps",
    "descend_to_target": "descend_steps",
    "pre_release_settle": "pre_release_settle_steps",
    "release": "release_steps",
    "post_release_clear": "post_release_clear_steps",
    "retreat": "retreat_steps",
    "settle_on_target": "settle_steps",
}


def phase_lengths_from_config(data) -> list[int]:
    phase_names = string_list(data["phase_name_table"])
    if "phase_step_config_json" in data.files:
        cfg = json.loads(str(data["phase_step_config_json"][0]))
        return [int(cfg.get(PHASE_LENGTH_KEYS.get(name, ""), 0)) for name in phase_names]
    phase_ids = data["phase_ids"].astype(np.int32)
    phase_step_ids = data["phase_step_ids"].astype(np.int32)
    lengths: list[int] = []
    for phase_id in range(len(phase_names)):
        mask = phase_ids == phase_id
        lengths.append(int(np.max(phase_step_ids[mask])) + 1 if np.any(mask) else 0)
    return lengths


def selected_profile_mask(data, profile: str) -> np.ndarray:
    profile_table = string_list(data["behavior_profile_table"])
    if profile == "all":
        return np.ones(data["episode_ids"].shape[0], dtype=bool)
    if profile not in profile_table:
        raise ValueError(f"Unknown profile {profile!r}; available={profile_table}")
    profile_id = profile_table.index(profile)
    return data["behavior_profile_ids"].astype(np.int32) == int(profile_id)


def target_rows(data, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    centers: list[np.ndarray] = []
    offsets: list[np.ndarray] = []
    drops: list[float] = []
    seen: set[tuple[float, float, float]] = set()
    for center, initial, drop in zip(
        data["target_centers"][mask],
        data["initial_ball_positions"][mask],
        data["pre_release_z_drops"][mask],
    ):
        key = tuple(float(v) for v in np.round(center, 9))
        if key in seen:
            continue
        seen.add(key)
        centers.append(np.asarray(center, dtype=np.float64))
        offsets.append(np.asarray(center, dtype=np.float64) - np.asarray(initial, dtype=np.float64))
        drops.append(float(drop))
    return np.asarray(centers, dtype=np.float64), np.asarray(offsets, dtype=np.float64), np.asarray(drops, dtype=np.float64)


def feature_names(num_rbf: int = 0) -> list[str]:
    base = ["1", "target_dx", "target_dy", "target_ux", "target_uy", "drop"]
    out: list[str] = []
    for power in range(4):
        suffix = "" if power == 0 else f"*p^{power}"
        out.extend([name + suffix for name in base])
    out.extend(["target_dx^2", "target_dy^2", "target_dx*target_dy", "drop^2"])
    for center_id in range(num_rbf):
        for power in range(4):
            suffix = "" if power == 0 else f"*p^{power}"
            out.append(f"rbf_target_{center_id}{suffix}")
    return out


def build_features(
    progress: np.ndarray,
    target_offsets: np.ndarray,
    drops: np.ndarray,
    *,
    rbf_centers: np.ndarray | None = None,
    rbf_sigma: float = 0.075,
) -> np.ndarray:
    progress = np.asarray(progress, dtype=np.float64).reshape(-1)
    offsets = np.asarray(target_offsets, dtype=np.float64)
    drops = np.asarray(drops, dtype=np.float64).reshape(-1)
    if offsets.shape[0] != progress.shape[0]:
        raise ValueError("target_offsets and progress must have the same row count")
    dx = offsets[:, 0]
    dy = offsets[:, 1]
    dist = np.maximum(1e-9, np.linalg.norm(offsets[:, :2], axis=1))
    ux = dx / dist
    uy = dy / dist
    base = np.stack([np.ones_like(progress), dx, dy, ux, uy, drops], axis=1)
    parts = [base * (progress[:, None] ** power) for power in range(4)]
    parts.append(np.stack([dx * dx, dy * dy, dx * dy, drops * drops], axis=1))
    if rbf_centers is not None and np.asarray(rbf_centers).size:
        centers = np.asarray(rbf_centers, dtype=np.float64)
        distances = np.linalg.norm(offsets[:, None, :2] - centers[None, :, :2], axis=2)
        rbf = np.exp(-0.5 * (distances / max(1e-6, float(rbf_sigma))) ** 2)
        for power in range(4):
            parts.append(rbf * (progress[:, None] ** power))
    return np.concatenate(parts, axis=1).astype(np.float64)


def fit_ridge(x: np.ndarray, y: np.ndarray, ridge: float) -> np.ndarray:
    xtx = x.T @ x
    reg = np.eye(xtx.shape[0], dtype=np.float64) * float(ridge)
    reg[0, 0] = 0.0
    rhs = x.T @ y
    try:
        return np.linalg.solve(xtx + reg, rhs)
    except np.linalg.LinAlgError:
        return np.linalg.pinv(xtx + reg) @ rhs


def summarize_phase_rmse(pred: np.ndarray, target: np.ndarray) -> float:
    return float(np.sqrt(np.mean((pred - target) ** 2))) if pred.size else float("nan")


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage2 Pick-Place V0.7.3 Phase Regression Train Report\n\n",
        f"Generated: {payload['created_at']}\n\n",
        f"- Status: `{payload['status']}`\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Policy: `{payload['policy']}`\n",
        f"- Metadata: `{payload['metadata']}`\n",
        f"- Action field: `{payload['action_field']}`\n",
        f"- Profile filter: `{payload['profile_filter']}`\n",
        f"- Feature dim: `{payload['feature_dim']}`\n",
        f"- Action dim: `{payload['act_dim']}`\n",
        f"- Ridge: `{payload['ridge']}`\n",
        f"- Samples: `{payload['samples']}`\n",
        f"- Overall train RMSE: `{payload['overall_train_rmse']:.8f}`\n",
        f"- Training ready: **No, online eval still required**\n\n",
        "## Phase Fit\n\n",
        "| phase | samples | rmse |\n",
        "|---|---:|---:|\n",
    ]
    for row in payload["phase_rows"]:
        lines.append(f"| {row['phase']} | {row['samples']} | {row['rmse']:.8f} |\n")
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This is a phase-specific trainable controller candidate.\n",
            "- It uses schedule and target features, not live observation feedback.\n",
            "- Online MuJoCo fixed-target eval is the promotion gate; offline RMSE is only a fit diagnostic.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Train v0.7.3 phase-specific pick-place regression policy.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--action-field", choices=["actions", "expert_actions"], default="actions")
    parser.add_argument("--profile", default="clean_nominal")
    parser.add_argument("--ridge", type=float, default=1e-5)
    parser.add_argument("--rbf-sigma", type=float, default=0.075)
    args = parser.parse_args()

    data_path = Path(args.data).resolve()
    data = np.load(data_path, allow_pickle=False)
    require_fields(data, REQUIRED_FIELDS)
    require_fields(data, [args.action_field])

    selected = selected_profile_mask(data, args.profile)
    actions = data[args.action_field].astype(np.float64)
    phase_ids = data["phase_ids"].astype(np.int32)
    phase_step_ids = data["phase_step_ids"].astype(np.float64)
    phase_names = string_list(data["phase_name_table"])
    phase_lengths = phase_lengths_from_config(data)
    target_offsets = data["target_centers"].astype(np.float64) - data["initial_ball_positions"].astype(np.float64)
    drops = data["pre_release_z_drops"].astype(np.float64)
    act_dim = int(actions.shape[1])
    centers, offset_centers, center_drops = target_rows(data, selected)
    names = feature_names(len(offset_centers))
    feature_dim = len(names)

    weights = np.zeros((len(phase_names), feature_dim, act_dim), dtype=np.float64)
    fallback_actions = np.zeros((len(phase_names), act_dim), dtype=np.float64)
    phase_has_model = np.zeros(len(phase_names), dtype=bool)
    phase_sample_counts = np.zeros(len(phase_names), dtype=np.int32)
    phase_rmse = np.full(len(phase_names), np.nan, dtype=np.float64)
    pred_all = np.zeros_like(actions[selected])
    target_all = actions[selected].copy()
    selected_indices = np.where(selected)[0]

    previous_fallback = np.zeros(act_dim, dtype=np.float64)
    phase_rows = []
    for phase_id, phase_name in enumerate(phase_names):
        mask = selected & (phase_ids == phase_id)
        idx = np.where(mask)[0]
        if idx.size == 0:
            fallback_actions[phase_id] = previous_fallback
            phase_rows.append({"phase": phase_name, "samples": 0, "rmse": float("nan")})
            continue
        denom = max(1.0, float(phase_lengths[phase_id] - 1 if phase_id < len(phase_lengths) else phase_step_ids[idx].max()))
        progress = np.clip(phase_step_ids[idx] / denom, 0.0, 1.0)
        x = build_features(progress, target_offsets[idx], drops[idx], rbf_centers=offset_centers, rbf_sigma=args.rbf_sigma)
        y = actions[idx]
        w = fit_ridge(x, y, args.ridge)
        pred = x @ w
        rmse = summarize_phase_rmse(pred, y)
        weights[phase_id] = w
        fallback_actions[phase_id] = np.mean(y, axis=0)
        previous_fallback = fallback_actions[phase_id]
        phase_has_model[phase_id] = True
        phase_sample_counts[phase_id] = int(idx.size)
        phase_rmse[phase_id] = rmse
        phase_rows.append({"phase": phase_name, "samples": int(idx.size), "rmse": float(rmse)})
        positions = np.searchsorted(selected_indices, idx)
        pred_all[positions] = pred

    overall_rmse = summarize_phase_rmse(pred_all, target_all)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output,
        mode=np.asarray(["phase_regression_v0_7_3"], dtype=str),
        status=np.asarray(["experimental_phase_specific_not_promoted"], dtype=str),
        created_at=np.asarray([datetime.now().isoformat(timespec="seconds")], dtype=str),
        source_dataset=np.asarray([str(data_path)], dtype=str),
        action_field=np.asarray([args.action_field], dtype=str),
        profile_filter=np.asarray([args.profile], dtype=str),
        contract_version=data["contract_version"],
        dataset_version=data["dataset_version"] if "dataset_version" in data.files else np.asarray(["unknown"], dtype=str),
        phase_names=np.asarray(phase_names, dtype=str),
        phase_lengths=np.asarray(phase_lengths, dtype=np.int32),
        feature_names=np.asarray(names, dtype=str),
        weights=weights,
        fallback_actions=fallback_actions,
        phase_has_model=phase_has_model,
        phase_sample_counts=phase_sample_counts,
        phase_rmse=phase_rmse,
        target_centers=centers,
        target_offset_centers=offset_centers,
        target_drops=center_drops,
        action_min=actions[selected].min(axis=0),
        action_max=actions[selected].max(axis=0),
        actuator_names=data["actuator_names"],
        ridge=np.asarray([float(args.ridge)], dtype=np.float64),
        rbf_sigma=np.asarray([float(args.rbf_sigma)], dtype=np.float64),
        overall_train_rmse=np.asarray([overall_rmse], dtype=np.float64),
    )

    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "experimental_phase_specific_not_promoted",
        "dataset": str(data_path),
        "policy": str(output),
        "metadata": str(Path(args.metadata).resolve()),
        "action_field": args.action_field,
        "profile_filter": args.profile,
        "feature_dim": feature_dim,
        "act_dim": act_dim,
        "ridge": float(args.ridge),
        "rbf_sigma": float(args.rbf_sigma),
        "samples": int(selected.sum()),
        "overall_train_rmse": float(overall_rmse),
        "phase_rows": phase_rows,
        "training_ready": False,
    }
    Path(args.metadata).parent.mkdir(parents=True, exist_ok=True)
    Path(args.metadata).write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(Path(args.report), json_ready(payload))
    print(json.dumps({"policy": str(output), "overall_train_rmse": overall_rmse}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
