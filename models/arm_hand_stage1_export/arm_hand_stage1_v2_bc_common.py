#!/usr/bin/env python3
"""Shared helpers for the Stage2 arm-hand v2 BC smoke experiment.

This module is intentionally scoped to the current dataset-v0 lift-ball smoke
path. It is not a promoted training API for the broader project.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_DATASET = DATA / "arm_hand_stage1_v2_lift_ball_dataset_v0.npz"
DEFAULT_CHECKPOINT = CHECKPOINTS / "bc_arm_hand_stage1_v2_lift_ball_dataset_v0_smoke.pth"
DEFAULT_READINESS_REPORT = DOCS / "arm_hand_stage1_v2_training_readiness_report.md"
DEFAULT_READINESS_META = META / "arm_hand_stage1_v2_training_readiness.json"
DEFAULT_TRAIN_REPORT = DOCS / "arm_hand_stage1_v2_bc_smoke_train_report.md"
DEFAULT_TRAIN_META = META / "arm_hand_stage1_v2_bc_smoke_train.json"
DEFAULT_EVAL_REPORT = DOCS / "arm_hand_stage1_v2_bc_smoke_eval_report.md"
DEFAULT_EVAL_META = META / "arm_hand_stage1_v2_bc_smoke_eval.json"
DEFAULT_DEMO_REPORT = DOCS / "arm_hand_stage1_v2_bc_smoke_demo_report.md"
DEFAULT_DEMO_META = META / "arm_hand_stage1_v2_bc_smoke_demo.json"
DEFAULT_DEMO_VIDEO = DOCS / "visual_checks_arm_hand_stage1_v2_bc_smoke" / "bc_smoke_policy_demo.mp4"

STATUS_EXPERIMENTAL = "experimental_bc_smoke_not_promoted_baseline"


def json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    return value


def load_dataset(path: str | Path = DEFAULT_DATASET):
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    return np.load(path, allow_pickle=False)


def string_list(values: np.ndarray) -> list[str]:
    return [str(item) for item in values.tolist()]


def require_fields(data, fields: list[str]) -> None:
    missing = [field for field in fields if field not in data.files]
    if missing:
        raise KeyError(f"Dataset missing fields: {missing}")


def dataset_phase_lengths(data) -> list[int]:
    phase_names = string_list(data["phase_name_table"])
    phase_ids = data["phase_ids"].astype(np.int32)
    phase_step_ids = data["phase_step_ids"].astype(np.int32)
    lengths: list[int] = []
    for phase_id in range(len(phase_names)):
        mask = phase_ids == phase_id
        if np.any(mask):
            lengths.append(int(np.max(phase_step_ids[mask])) + 1)
        else:
            lengths.append(0)
    return lengths


def episode_lengths(data) -> dict[int, int]:
    out: dict[int, int] = {}
    episode_ids = data["episode_ids"].astype(np.int32)
    for episode_id in sorted(int(v) for v in np.unique(episode_ids)):
        out[episode_id] = int(np.sum(episode_ids == episode_id))
    return out


def feature_config_from_dataset(
    data,
    *,
    include_phase_features: bool = True,
    feature_mode: str = "obs_phase",
) -> dict[str, Any]:
    if feature_mode not in {"obs_phase", "obs_only", "phase_only"}:
        raise ValueError(f"Unknown feature_mode={feature_mode!r}")
    phase_names = string_list(data["phase_name_table"])
    phase_lengths = dataset_phase_lengths(data)
    max_episode_steps = max(episode_lengths(data).values())
    use_obs = feature_mode in {"obs_phase", "obs_only"}
    use_phase = include_phase_features and feature_mode in {"obs_phase", "phase_only"}
    base_dim = int(data["obs"].shape[1]) if use_obs else 0
    phase_dim = len(phase_names) + 2 if use_phase else 0
    return {
        "base_obs_dim": int(data["obs"].shape[1]),
        "feature_dim": int(base_dim + phase_dim),
        "feature_mode": feature_mode,
        "use_observation": bool(use_obs),
        "include_phase_features": bool(use_phase),
        "phase_names": phase_names,
        "phase_lengths": phase_lengths,
        "max_episode_steps": int(max_episode_steps),
        "extra_features": ["phase_one_hot", "phase_progress", "episode_progress"] if use_phase else [],
    }


def phase_for_step(step_id: int, feature_config: dict[str, Any]) -> tuple[int, int]:
    lengths = [int(v) for v in feature_config.get("phase_lengths", [])]
    if not lengths:
        return 0, int(step_id)
    cursor = 0
    last_nonempty = 0
    for phase_id, length in enumerate(lengths):
        if length <= 0:
            continue
        last_nonempty = phase_id
        if step_id < cursor + length:
            return phase_id, int(step_id - cursor)
        cursor += length
    return last_nonempty, max(0, int(step_id - max(0, cursor - max(1, lengths[last_nonempty]))))


def build_single_feature(
    obs_vector: np.ndarray,
    *,
    step_id: int,
    phase_id: int | None,
    phase_step_id: int | None,
    feature_config: dict[str, Any],
) -> np.ndarray:
    if feature_config.get("use_observation", True):
        base = np.asarray(obs_vector, dtype=np.float32)
    else:
        base = np.zeros(0, dtype=np.float32)
    if not feature_config.get("include_phase_features", False):
        return base

    phase_names = list(feature_config.get("phase_names", []))
    phase_lengths = [int(v) for v in feature_config.get("phase_lengths", [])]
    if phase_id is None or phase_step_id is None:
        phase_id, phase_step_id = phase_for_step(step_id, feature_config)
    phase_id = int(np.clip(int(phase_id), 0, max(0, len(phase_names) - 1)))
    phase_step_id = max(0, int(phase_step_id))

    one_hot = np.zeros(len(phase_names), dtype=np.float32)
    if one_hot.size:
        one_hot[phase_id] = 1.0
    denom = max(1, int(phase_lengths[phase_id]) - 1) if phase_id < len(phase_lengths) else 1
    phase_progress = min(1.0, phase_step_id / denom)
    episode_denom = max(1, int(feature_config.get("max_episode_steps", 1)) - 1)
    episode_progress = min(1.0, max(0, int(step_id)) / episode_denom)
    return np.concatenate([base, one_hot, np.array([phase_progress, episode_progress], dtype=np.float32)])


def build_feature_matrix(data, feature_config: dict[str, Any]) -> np.ndarray:
    obs = data["obs"].astype(np.float32)
    if not feature_config.get("include_phase_features", False):
        return obs

    rows = [
        build_single_feature(
            obs[i],
            step_id=int(data["step_ids"][i]),
            phase_id=int(data["phase_ids"][i]),
            phase_step_id=int(data["phase_step_ids"][i]),
            feature_config=feature_config,
        )
        for i in range(obs.shape[0])
    ]
    return np.asarray(rows, dtype=np.float32)


def split_by_episode(episode_ids: np.ndarray, val_fraction: float, seed: int) -> tuple[np.ndarray, np.ndarray, list[int], list[int]]:
    rng = np.random.default_rng(seed)
    episodes = np.unique(episode_ids.astype(np.int32))
    rng.shuffle(episodes)
    val_count = max(1, int(round(len(episodes) * val_fraction))) if len(episodes) > 1 else 0
    val_episodes = sorted(int(v) for v in episodes[:val_count])
    train_episodes = sorted(int(v) for v in episodes[val_count:])
    if not train_episodes and val_episodes:
        train_episodes = [val_episodes.pop()]
    val_set = set(val_episodes)
    train_set = set(train_episodes)
    val_mask = np.asarray([int(v) in val_set for v in episode_ids], dtype=bool)
    train_mask = np.asarray([int(v) in train_set for v in episode_ids], dtype=bool)
    return train_mask, val_mask, train_episodes, val_episodes


def standardize(train_values: np.ndarray, all_values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = train_values.mean(axis=0, keepdims=True).astype(np.float32)
    std = train_values.std(axis=0, keepdims=True).astype(np.float32)
    std = np.where(std < 1e-6, 1.0, std).astype(np.float32)
    return ((all_values - mean) / std).astype(np.float32), mean.squeeze(0), std.squeeze(0)


def rmse(pred: np.ndarray, target: np.ndarray) -> float:
    return float(np.sqrt(np.mean((pred - target) ** 2)))


class BCPolicy(nn.Module):
    def __init__(self, feature_dim: int, act_dim: int, hidden_dim: int, depth: int):
        super().__init__()
        layers: list[nn.Module] = []
        current = int(feature_dim)
        for _ in range(int(depth)):
            layers.append(nn.Linear(current, int(hidden_dim)))
            layers.append(nn.ReLU())
            current = int(hidden_dim)
        layers.append(nn.Linear(current, int(act_dim)))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


def torch_load_checkpoint(path: str | Path, device: torch.device | str = "cpu") -> dict[str, Any]:
    try:
        return torch.load(path, map_location=device, weights_only=False)
    except TypeError:
        return torch.load(path, map_location=device)


def load_policy(path: str | Path, device: torch.device | str = "cpu") -> tuple[BCPolicy, dict[str, Any]]:
    checkpoint = torch_load_checkpoint(path, device)
    model = BCPolicy(
        feature_dim=int(checkpoint["feature_dim"]),
        act_dim=int(checkpoint["act_dim"]),
        hidden_dim=int(checkpoint["hidden_dim"]),
        depth=int(checkpoint["depth"]),
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, checkpoint


def predict_action(
    model: BCPolicy,
    checkpoint: dict[str, Any],
    obs_vector: np.ndarray,
    *,
    step_id: int,
    device: torch.device | str = "cpu",
    clip_to_train_range: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    feature = build_single_feature(
        obs_vector,
        step_id=step_id,
        phase_id=None,
        phase_step_id=None,
        feature_config=checkpoint["feature_config"],
    )
    feature_norm = (feature - checkpoint["feature_mean"]) / checkpoint["feature_std"]
    with torch.no_grad():
        pred_norm = model(torch.from_numpy(feature_norm.astype(np.float32)).to(device)).cpu().numpy()
    action = pred_norm * checkpoint["action_std"] + checkpoint["action_mean"]
    if clip_to_train_range:
        action = np.clip(action, checkpoint["action_min"], checkpoint["action_max"])
    return action.astype(np.float64), pred_norm.astype(np.float32)
