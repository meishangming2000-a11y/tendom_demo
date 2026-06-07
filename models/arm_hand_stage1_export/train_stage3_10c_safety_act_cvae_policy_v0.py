#!/usr/bin/env python3
"""Train Stage3.10C safety-aware ACT/CVAE-style action chunk baseline.

This is the first Stage3.10C offline model-training entrypoint. It reads the
Stage3.10B-full safety-labeled dense sequence dataset and trains an ACT/CVAE-
style chunk predictor:

    obs_t + skill_id + phase_id + safety_label_t -> action[t:t+H]

The model also predicts the safety labels over the same horizon as an auxiliary
head. This is still an offline baseline. Closed-loop MuJoCo evaluation is a
separate gate before promotion.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from arm_hand_stage1_task_api import json_ready


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_DATASET = DATA / "stage3_10b_safety_labeled_act_dp_dataset_full_success_v0.npz"
DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_10c_safety_act_cvae_policy_v0.pth"
DEFAULT_REPORT = DOCS / "stage3_10c_safety_act_cvae_policy_v0_train_report.md"
DEFAULT_METADATA = META / "stage3_10c_safety_act_cvae_policy_v0_train.json"

STATUS = "stage3_10c_safety_act_cvae_policy_v0_offline_trained_not_closed_loop_promoted"


@dataclass(frozen=True)
class WindowArrays:
    obs: np.ndarray
    skill_ids: np.ndarray
    phase_ids: np.ndarray
    safety_now: np.ndarray
    action_chunks: np.ndarray
    safety_chunks: np.ndarray


def load_dataset(path: Path) -> np.lib.npyio.NpzFile:
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    return np.load(path, allow_pickle=False)


def require_fields(data: np.lib.npyio.NpzFile, fields: list[str]) -> None:
    missing = [field for field in fields if field not in data.files]
    if missing:
        raise KeyError(f"Dataset missing fields: {missing}")


def string_list(values: np.ndarray) -> list[str]:
    return [str(item) for item in values.tolist()]


def parse_metadata_json(data: np.lib.npyio.NpzFile) -> dict[str, Any]:
    if "metadata_json" not in data.files:
        return {}
    return json.loads(str(data["metadata_json"][0]))


def split_episodes_by_skill(
    episode_skill_ids: np.ndarray,
    *,
    val_fraction: float,
    seed: int,
    train_all: bool,
) -> tuple[np.ndarray, np.ndarray, list[int], list[int]]:
    episode_ids = np.arange(len(episode_skill_ids), dtype=np.int32)
    if train_all:
        mask = np.ones_like(episode_ids, dtype=bool)
        return mask.copy(), mask.copy(), episode_ids.tolist(), episode_ids.tolist()

    rng = np.random.default_rng(int(seed))
    train_mask = np.ones_like(episode_ids, dtype=bool)
    val_mask = np.zeros_like(episode_ids, dtype=bool)
    for skill_id in sorted(int(v) for v in np.unique(episode_skill_ids)):
        group = episode_ids[episode_skill_ids == skill_id]
        shuffled = group.copy()
        rng.shuffle(shuffled)
        val_count = max(1, int(round(len(shuffled) * float(val_fraction))))
        val_ids = shuffled[:val_count]
        val_mask[val_ids] = True
        train_mask[val_ids] = False
    if not np.any(train_mask):
        train_mask[:] = True
    return train_mask, val_mask, episode_ids[train_mask].tolist(), episode_ids[val_mask].tolist()


def collect_window_index(
    episode_lengths: np.ndarray,
    episode_allowed: np.ndarray,
    *,
    horizon: int,
    stride: int,
) -> np.ndarray:
    rows: list[tuple[int, int]] = []
    for episode_id, length in enumerate(episode_lengths.astype(np.int32).tolist()):
        if not bool(episode_allowed[episode_id]):
            continue
        if int(length) < int(horizon):
            continue
        for start in range(0, int(length) - int(horizon) + 1, int(stride)):
            rows.append((int(episode_id), int(start)))
    return np.asarray(rows, dtype=np.int32)


def subsample_windows(index: np.ndarray, *, max_windows: int, seed: int) -> np.ndarray:
    if int(max_windows) <= 0 or len(index) <= int(max_windows):
        return index
    rng = np.random.default_rng(int(seed))
    chosen = rng.choice(len(index), size=int(max_windows), replace=False)
    chosen.sort()
    return index[chosen]


def make_episode_aux(
    flat: np.ndarray,
    *,
    row_starts: np.ndarray,
    row_counts: np.ndarray,
    max_len: int,
    fill_value: float | int = 0,
) -> np.ndarray:
    flat = np.asarray(flat)
    if flat.ndim == 1:
        out = np.full((len(row_starts), int(max_len)), fill_value, dtype=flat.dtype)
        for episode_id, (start, count) in enumerate(zip(row_starts, row_counts, strict=False)):
            out[episode_id, : int(count)] = flat[int(start) : int(start) + int(count)]
        return out

    out_shape = (len(row_starts), int(max_len), *flat.shape[1:])
    out = np.full(out_shape, fill_value, dtype=flat.dtype)
    for episode_id, (start, count) in enumerate(zip(row_starts, row_counts, strict=False)):
        out[episode_id, : int(count)] = flat[int(start) : int(start) + int(count)]
    return out


def materialize_windows(
    episode_obs: np.ndarray,
    episode_actions: np.ndarray,
    episode_skill_ids: np.ndarray,
    episode_phase_ids: np.ndarray,
    episode_safety_labels: np.ndarray,
    window_index: np.ndarray,
    *,
    horizon: int,
    obs_mean: np.ndarray,
    obs_std: np.ndarray,
    action_mean: np.ndarray,
    action_std: np.ndarray,
) -> WindowArrays:
    count = int(len(window_index))
    obs_dim = int(episode_obs.shape[2])
    action_dim = int(episode_actions.shape[2])
    safety_dim = int(episode_safety_labels.shape[2])
    obs = np.empty((count, obs_dim), dtype=np.float32)
    skill_ids = np.empty((count,), dtype=np.int64)
    phase_ids = np.empty((count,), dtype=np.int64)
    safety_now = np.empty((count, safety_dim), dtype=np.float32)
    action_chunks = np.empty((count, int(horizon), action_dim), dtype=np.float32)
    safety_chunks = np.empty((count, int(horizon), safety_dim), dtype=np.float32)
    obs_std_safe = np.maximum(obs_std.astype(np.float32), 1e-6)
    action_std_safe = np.maximum(action_std.astype(np.float32), 1e-6)

    for row_id, (episode_id, start) in enumerate(window_index.tolist()):
        obs[row_id] = (episode_obs[episode_id, start].astype(np.float32) - obs_mean) / obs_std_safe
        skill_ids[row_id] = int(episode_skill_ids[episode_id])
        phase_ids[row_id] = int(episode_phase_ids[episode_id, start])
        safety_now[row_id] = episode_safety_labels[episode_id, start].astype(np.float32)
        chunk = episode_actions[episode_id, start : start + int(horizon)].astype(np.float32)
        action_chunks[row_id] = (chunk - action_mean.reshape(1, -1)) / action_std_safe.reshape(1, -1)
        safety_chunks[row_id] = episode_safety_labels[episode_id, start : start + int(horizon)].astype(np.float32)

    return WindowArrays(
        obs=obs,
        skill_ids=skill_ids,
        phase_ids=phase_ids,
        safety_now=safety_now,
        action_chunks=action_chunks,
        safety_chunks=safety_chunks,
    )


class SafetyACTCVAEChunkPolicy(nn.Module):
    def __init__(
        self,
        *,
        obs_dim: int,
        action_dim: int,
        safety_dim: int,
        horizon: int,
        skill_count: int,
        phase_count: int,
        d_model: int,
        nhead: int,
        num_layers: int,
        latent_dim: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.action_dim = int(action_dim)
        self.safety_dim = int(safety_dim)
        self.horizon = int(horizon)
        self.latent_dim = int(latent_dim)
        self.skill_embedding = nn.Embedding(int(skill_count), int(d_model))
        self.phase_embedding = nn.Embedding(int(phase_count), int(d_model))
        self.obs_proj = nn.Linear(int(obs_dim), int(d_model))
        self.safety_now_proj = nn.Linear(int(safety_dim), int(d_model))
        self.action_proj = nn.Linear(int(action_dim), int(d_model))
        self.context_norm = nn.LayerNorm(int(d_model))

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=int(d_model),
            nhead=int(nhead),
            dim_feedforward=int(d_model) * 4,
            dropout=float(dropout),
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.posterior_encoder = nn.TransformerEncoder(encoder_layer, num_layers=int(num_layers))
        self.posterior_pos = nn.Parameter(torch.zeros(1, int(horizon) + 2, int(d_model)))
        self.mu_head = nn.Linear(int(d_model), int(latent_dim))
        self.logvar_head = nn.Linear(int(d_model), int(latent_dim))

        self.latent_proj = nn.Linear(int(latent_dim), int(d_model))
        self.query_embed = nn.Parameter(torch.zeros(1, int(horizon), int(d_model)))
        decoder_layer = nn.TransformerEncoderLayer(
            d_model=int(d_model),
            nhead=int(nhead),
            dim_feedforward=int(d_model) * 4,
            dropout=float(dropout),
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.decoder = nn.TransformerEncoder(decoder_layer, num_layers=int(num_layers))
        self.decoder_pos = nn.Parameter(torch.zeros(1, int(horizon) + 1, int(d_model)))
        self.action_head = nn.Linear(int(d_model), int(action_dim))
        self.safety_head = nn.Linear(int(d_model), int(safety_dim))
        self._reset_parameters()

    def _reset_parameters(self) -> None:
        for param in (self.posterior_pos, self.query_embed, self.decoder_pos):
            nn.init.normal_(param, mean=0.0, std=0.02)

    def context_tokens(
        self,
        obs: torch.Tensor,
        skill_ids: torch.Tensor,
        phase_ids: torch.Tensor,
        safety_now: torch.Tensor,
    ) -> torch.Tensor:
        context = (
            self.obs_proj(obs)
            + self.skill_embedding(skill_ids.long())
            + self.phase_embedding(phase_ids.long())
            + self.safety_now_proj(safety_now)
        )
        return self.context_norm(context)

    def posterior(
        self,
        obs: torch.Tensor,
        skill_ids: torch.Tensor,
        phase_ids: torch.Tensor,
        safety_now: torch.Tensor,
        action_chunks: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        context = self.context_tokens(obs, skill_ids, phase_ids, safety_now).unsqueeze(1)
        action_tokens = self.action_proj(action_chunks)
        tokens = torch.cat([context, action_tokens], dim=1) + self.posterior_pos[:, : action_chunks.shape[1] + 1]
        encoded = self.posterior_encoder(tokens)
        pooled = encoded[:, 0]
        return self.mu_head(pooled), self.logvar_head(pooled)

    @staticmethod
    def reparameterize(mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        if not torch.is_grad_enabled():
            return mu
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(
        self,
        obs: torch.Tensor,
        skill_ids: torch.Tensor,
        phase_ids: torch.Tensor,
        safety_now: torch.Tensor,
        latent: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        context = self.context_tokens(obs, skill_ids, phase_ids, safety_now) + self.latent_proj(latent)
        context = context.unsqueeze(1)
        queries = self.query_embed.expand(obs.shape[0], -1, -1)
        tokens = torch.cat([context, queries], dim=1) + self.decoder_pos
        decoded = self.decoder(tokens)[:, 1:]
        return self.action_head(decoded), self.safety_head(decoded)

    def forward(
        self,
        obs: torch.Tensor,
        skill_ids: torch.Tensor,
        phase_ids: torch.Tensor,
        safety_now: torch.Tensor,
        action_chunks: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        mu, logvar = self.posterior(obs, skill_ids, phase_ids, safety_now, action_chunks)
        latent = self.reparameterize(mu, logvar)
        pred_actions, pred_safety = self.decode(obs, skill_ids, phase_ids, safety_now, latent)
        return pred_actions, pred_safety, mu, logvar

    def predict(
        self,
        obs: torch.Tensor,
        skill_ids: torch.Tensor,
        phase_ids: torch.Tensor,
        safety_now: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        latent = torch.zeros((obs.shape[0], self.latent_dim), dtype=obs.dtype, device=obs.device)
        return self.decode(obs, skill_ids, phase_ids, safety_now, latent)


def kl_divergence(mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
    return -0.5 * torch.mean(1.0 + logvar - mu.pow(2) - logvar.exp())


def weighted_action_mse(
    pred: torch.Tensor,
    target: torch.Tensor,
    *,
    action_weights: torch.Tensor,
) -> torch.Tensor:
    return torch.mean((pred - target).pow(2) * action_weights.view(1, 1, -1))


def make_action_weights(action_dim: int, *, hand_start_index: int, arm_loss_weight: float, hand_loss_weight: float) -> torch.Tensor:
    weights = torch.full((int(action_dim),), float(arm_loss_weight), dtype=torch.float32)
    weights[int(hand_start_index) :] = float(hand_loss_weight)
    return weights


def denormalize_actions(chunks: np.ndarray, *, action_mean: np.ndarray, action_std: np.ndarray) -> np.ndarray:
    return chunks * action_std.reshape(1, 1, -1) + action_mean.reshape(1, 1, -1)


def raw_rmse(pred_raw: np.ndarray, target_raw: np.ndarray) -> float:
    return float(np.sqrt(np.mean((pred_raw - target_raw) ** 2)))


def binary_metrics(logits: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    probs = 1.0 / (1.0 + np.exp(-logits))
    pred = probs >= 0.5
    label_bool = labels >= 0.5
    accuracy = float((pred == label_bool).mean())
    positives = int(label_bool.sum())
    predicted_positives = int(pred.sum())
    true_positives = int(np.logical_and(pred, label_bool).sum())
    precision = float(true_positives / max(1, predicted_positives))
    recall = float(true_positives / max(1, positives))
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "positive_labels": positives,
        "predicted_positive_labels": predicted_positives,
    }


def per_skill_window_counts(index: np.ndarray, episode_skill_ids: np.ndarray, skill_table: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {name: 0 for name in skill_table}
    for episode_id, _ in index.tolist():
        name = skill_table[int(episode_skill_ids[int(episode_id)])]
        counts[name] = counts.get(name, 0) + 1
    return counts


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Stage3.10C Safety ACT/CVAE Policy v0 Train Report\n\n",
        f"- 生成时间：`{payload['created_at']}`\n",
        f"- 状态：`{payload['status']}`\n",
        f"- 数据集：`{payload['dataset']}`\n",
        f"- checkpoint：`{payload['checkpoint']}`\n",
        f"- metadata：`{payload['metadata']}`\n",
        f"- 模型：`{payload['model_type']}`\n",
        f"- horizon：`{payload['horizon']}`\n",
        f"- stride：`{payload['stride']}`\n",
        f"- obs dim：`{payload['obs_dim']}`\n",
        f"- action dim：`{payload['action_dim']}`\n",
        f"- safety dim：`{payload['safety_dim']}`\n",
        f"- d_model：`{payload['d_model']}`\n",
        f"- latent dim：`{payload['latent_dim']}`\n",
        f"- epochs：`{payload['epochs']}`\n",
        f"- batch size：`{payload['batch_size']}`\n",
        f"- device：`{payload['device']}`\n\n",
        "## 训练数据\n\n",
        f"- train episodes：`{payload['train_episodes']}`\n",
        f"- val episodes：`{payload['val_episodes']}`\n",
        f"- train windows：`{payload['train_windows']}`\n",
        f"- val windows：`{payload['val_windows']}`\n",
        f"- Stage3.10B train ready：`{payload['source_stage3_10b_train_ready']}`\n\n",
        "## 训练结果\n\n",
        f"- best epoch：`{payload['best_epoch']}`\n",
        f"- best val prior action loss：`{payload['best_val_prior_action_loss']:.8f}`\n",
        f"- final train action loss：`{payload['final_train_action_loss']:.8f}`\n",
        f"- final val prior action loss：`{payload['final_val_prior_action_loss']:.8f}`\n",
        f"- train raw RMSE：`{payload['train_prior_rmse_raw']:.8f}`\n",
        f"- val raw RMSE：`{payload['val_prior_rmse_raw']:.8f}`\n",
        f"- train hand raw RMSE：`{payload['train_prior_hand_rmse_raw']:.8f}`\n",
        f"- val hand raw RMSE：`{payload['val_prior_hand_rmse_raw']:.8f}`\n",
        f"- val safety accuracy：`{payload['val_safety_metrics']['accuracy']:.6f}`\n",
        f"- val safety precision：`{payload['val_safety_metrics']['precision']:.6f}`\n",
        f"- val safety recall：`{payload['val_safety_metrics']['recall']:.6f}`\n\n",
        "## 技能窗口分布\n\n",
        "| split | skill | windows |\n",
        "| --- | --- | ---: |\n",
    ]
    for split, counts in (("train", payload["train_window_counts_by_skill"]), ("val", payload["val_window_counts_by_skill"])):
        for skill, count in counts.items():
            lines.append(f"| {split} | `{skill}` | {count} |\n")

    lines.extend(["\n## Loss Curve\n\n", "| epoch | train action | val prior action | val safety BCE | KL |\n", "| ---: | ---: | ---: | ---: | ---: |\n"])
    for row in payload["loss_history"]:
        lines.append(
            f"| {row['epoch']} | {row['train_action_loss']:.8f} | {row['val_prior_action_loss']:.8f} | "
            f"{row['val_safety_loss']:.8f} | {row['train_kl_loss']:.8f} |\n"
        )

    lines.extend(
        [
            "\n## 这一步说明什么\n\n",
            "这一步说明 Stage3.10B-full 的安全标签数据已经能被模型训练入口直接读取，并能训练出一个带 latent 的 action chunk baseline。它比旧 ACT-lite 多了 phase 输入、safety-label 输入和 safety-label 辅助预测头。\n\n",
            "## 重要边界\n\n",
            "- 这是 offline 训练结果，不是闭环 MuJoCo 成功。\n",
            "- 这个模型仍然不能被描述为 full-action ACT/DP 已经学会抓鸡蛋。\n",
            "- 下一步必须做 Stage3.10C-B closed-loop eval，并和 Stage3.10A safety layer 同场景对比。\n\n",
            "## 如果成功\n\n",
            "进入 Stage3.10C-B：写闭环评估器，用 `scripted_arm_predicted_hand` 方式先评估 hand/finger chunk，再报告 success、hold slip、crush、penetration、floor contact 和 final vision。\n\n",
            "## 如果失败\n\n",
            "先检查 skill/phase 分层、action loss 权重、safety auxiliary head 的正负样本不平衡，以及是否需要分技能模型头；不要放宽抓取成功阈值。\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--horizon", type=int, default=16)
    parser.add_argument("--stride", type=int, default=8)
    parser.add_argument("--max-train-windows", type=int, default=24000)
    parser.add_argument("--max-val-windows", type=int, default=6000)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--d-model", type=int, default=128)
    parser.add_argument("--nhead", type=int, default=4)
    parser.add_argument("--num-layers", type=int, default=2)
    parser.add_argument("--latent-dim", type=int, default=32)
    parser.add_argument("--dropout", type=float, default=0.05)
    parser.add_argument("--lr", type=float, default=4e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    parser.add_argument("--kl-weight", type=float, default=1e-4)
    parser.add_argument("--safety-loss-weight", type=float, default=0.05)
    parser.add_argument("--prior-loss-weight", type=float, default=0.50)
    parser.add_argument("--arm-loss-weight", type=float, default=0.20)
    parser.add_argument("--hand-loss-weight", type=float, default=1.00)
    parser.add_argument("--hand-start-index", type=int, default=6)
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--train-all", action="store_true")
    parser.add_argument("--seed", type=int, default=31010)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()

    torch.manual_seed(int(args.seed))
    np.random.seed(int(args.seed))
    data = load_dataset(args.data)
    require_fields(
        data,
        [
            "episode_obs",
            "episode_actions",
            "episode_lengths",
            "episode_success",
            "episode_skill_ids",
            "episode_row_starts",
            "episode_row_counts",
            "skill_table",
            "phase_table",
            "phase_ids",
            "safety_labels",
            "obs_mean",
            "obs_std",
            "action_mean",
            "action_std",
            "action_min",
            "action_max",
            "metadata_json",
        ],
    )
    source_metadata = parse_metadata_json(data)
    if not bool(source_metadata.get("stage3_10b_train_ready", False)):
        raise RuntimeError("Stage3.10B source dataset is not marked stage3_10b_train_ready=True.")

    horizon = int(args.horizon)
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    max_len = int(data["episode_obs"].shape[1])
    episode_phase_ids = make_episode_aux(
        data["phase_ids"],
        row_starts=data["episode_row_starts"].astype(np.int32),
        row_counts=data["episode_row_counts"].astype(np.int32),
        max_len=max_len,
        fill_value=0,
    ).astype(np.int64)
    episode_safety_labels = make_episode_aux(
        data["safety_labels"],
        row_starts=data["episode_row_starts"].astype(np.int32),
        row_counts=data["episode_row_counts"].astype(np.int32),
        max_len=max_len,
        fill_value=0.0,
    ).astype(np.float32)

    episode_success = data["episode_success"].astype(bool)
    episode_skill_ids = data["episode_skill_ids"].astype(np.int32)
    train_episode_mask, val_episode_mask, train_episodes, val_episodes = split_episodes_by_skill(
        episode_skill_ids,
        val_fraction=float(args.val_fraction),
        seed=int(args.seed),
        train_all=bool(args.train_all),
    )
    train_episode_mask &= episode_success
    val_episode_mask &= episode_success

    train_index = collect_window_index(data["episode_lengths"], train_episode_mask, horizon=horizon, stride=max(1, int(args.stride)))
    val_index = collect_window_index(data["episode_lengths"], val_episode_mask, horizon=horizon, stride=max(1, int(args.stride)))
    if len(train_index) == 0 or len(val_index) == 0:
        raise RuntimeError(f"No train/val windows: train={len(train_index)} val={len(val_index)}")
    train_index = subsample_windows(train_index, max_windows=int(args.max_train_windows), seed=int(args.seed) + 1)
    val_index = subsample_windows(val_index, max_windows=int(args.max_val_windows), seed=int(args.seed) + 2)

    episode_obs = data["episode_obs"].astype(np.float32)
    episode_actions = data["episode_actions"].astype(np.float32)
    obs_mean = data["obs_mean"].astype(np.float32)
    obs_std = np.maximum(data["obs_std"].astype(np.float32), 1e-6)
    action_mean = data["action_mean"].astype(np.float32)
    action_std = np.maximum(data["action_std"].astype(np.float32), 1e-6)

    train = materialize_windows(
        episode_obs,
        episode_actions,
        episode_skill_ids,
        episode_phase_ids,
        episode_safety_labels,
        train_index,
        horizon=horizon,
        obs_mean=obs_mean,
        obs_std=obs_std,
        action_mean=action_mean,
        action_std=action_std,
    )
    val = materialize_windows(
        episode_obs,
        episode_actions,
        episode_skill_ids,
        episode_phase_ids,
        episode_safety_labels,
        val_index,
        horizon=horizon,
        obs_mean=obs_mean,
        obs_std=obs_std,
        action_mean=action_mean,
        action_std=action_std,
    )

    if str(args.device) == "cuda":
        device = torch.device("cuda")
    elif str(args.device) == "cpu":
        device = torch.device("cpu")
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = SafetyACTCVAEChunkPolicy(
        obs_dim=int(train.obs.shape[1]),
        action_dim=int(train.action_chunks.shape[2]),
        safety_dim=int(train.safety_now.shape[1]),
        horizon=horizon,
        skill_count=int(len(data["skill_table"])),
        phase_count=int(len(data["phase_table"])),
        d_model=int(args.d_model),
        nhead=int(args.nhead),
        num_layers=int(args.num_layers),
        latent_dim=int(args.latent_dim),
        dropout=float(args.dropout),
    ).to(device)

    action_weights = make_action_weights(
        int(train.action_chunks.shape[2]),
        hand_start_index=int(args.hand_start_index),
        arm_loss_weight=float(args.arm_loss_weight),
        hand_loss_weight=float(args.hand_loss_weight),
    ).to(device)
    optimizer = optim.AdamW(model.parameters(), lr=float(args.lr), weight_decay=float(args.weight_decay))
    safety_loss_fn = nn.BCEWithLogitsLoss()
    train_ds = torch.utils.data.TensorDataset(
        torch.from_numpy(train.obs),
        torch.from_numpy(train.skill_ids),
        torch.from_numpy(train.phase_ids),
        torch.from_numpy(train.safety_now),
        torch.from_numpy(train.action_chunks),
        torch.from_numpy(train.safety_chunks),
    )
    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=int(args.batch_size), shuffle=True)

    val_tensors = tuple(
        item.to(device)
        for item in (
            torch.from_numpy(val.obs),
            torch.from_numpy(val.skill_ids),
            torch.from_numpy(val.phase_ids),
            torch.from_numpy(val.safety_now),
            torch.from_numpy(val.action_chunks),
            torch.from_numpy(val.safety_chunks),
        )
    )

    history: list[dict[str, float]] = []
    best_state: dict[str, torch.Tensor] | None = None
    best_val_prior_action = float("inf")
    best_epoch = 0
    for epoch in range(1, int(args.epochs) + 1):
        model.train()
        totals = {"action": 0.0, "prior_action": 0.0, "safety": 0.0, "kl": 0.0, "total": 0.0}
        seen = 0
        for batch in train_loader:
            batch = tuple(item.to(device) for item in batch)
            obs_b, skill_b, phase_b, safety_now_b, action_b, safety_b = batch
            optimizer.zero_grad(set_to_none=True)
            pred_action, pred_safety, mu, logvar = model(obs_b, skill_b, phase_b, safety_now_b, action_b)
            prior_action, prior_safety = model.predict(obs_b, skill_b, phase_b, safety_now_b)
            action_loss = weighted_action_mse(pred_action, action_b, action_weights=action_weights)
            prior_action_loss = weighted_action_mse(prior_action, action_b, action_weights=action_weights)
            safety_loss = 0.5 * (safety_loss_fn(pred_safety, safety_b) + safety_loss_fn(prior_safety, safety_b))
            kl_loss = kl_divergence(mu, logvar)
            loss = (
                action_loss
                + float(args.prior_loss_weight) * prior_action_loss
                + float(args.safety_loss_weight) * safety_loss
                + float(args.kl_weight) * kl_loss
            )
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()
            batch_count = int(obs_b.shape[0])
            seen += batch_count
            totals["action"] += float(action_loss.item()) * batch_count
            totals["prior_action"] += float(prior_action_loss.item()) * batch_count
            totals["safety"] += float(safety_loss.item()) * batch_count
            totals["kl"] += float(kl_loss.item()) * batch_count
            totals["total"] += float(loss.item()) * batch_count

        train_metrics = {key: value / max(1, seen) for key, value in totals.items()}
        model.eval()
        with torch.no_grad():
            obs_v, skill_v, phase_v, safety_now_v, action_v, safety_v = val_tensors
            pred_action_v, pred_safety_v, mu_v, logvar_v = model(obs_v, skill_v, phase_v, safety_now_v, action_v)
            prior_action_v, prior_safety_v = model.predict(obs_v, skill_v, phase_v, safety_now_v)
            val_action_loss = float(weighted_action_mse(pred_action_v, action_v, action_weights=action_weights).item())
            val_prior_action_loss = float(weighted_action_mse(prior_action_v, action_v, action_weights=action_weights).item())
            val_safety_loss = float(safety_loss_fn(prior_safety_v, safety_v).item())
            val_kl_loss = float(kl_divergence(mu_v, logvar_v).item())

        row = {
            "epoch": int(epoch),
            "train_total_loss": float(train_metrics["total"]),
            "train_action_loss": float(train_metrics["action"]),
            "train_prior_action_loss": float(train_metrics["prior_action"]),
            "train_safety_loss": float(train_metrics["safety"]),
            "train_kl_loss": float(train_metrics["kl"]),
            "val_action_loss": float(val_action_loss),
            "val_prior_action_loss": float(val_prior_action_loss),
            "val_safety_loss": float(val_safety_loss),
            "val_kl_loss": float(val_kl_loss),
        }
        history.append(row)
        if val_prior_action_loss < best_val_prior_action:
            best_val_prior_action = val_prior_action_loss
            best_epoch = int(epoch)
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        if epoch == 1 or epoch == int(args.epochs) or epoch % max(1, int(args.epochs) // 4) == 0:
            print(
                f"epoch {epoch:03d}/{args.epochs} "
                f"train_action={row['train_action_loss']:.8f} "
                f"val_prior_action={row['val_prior_action_loss']:.8f} "
                f"val_safety={row['val_safety_loss']:.8f} kl={row['train_kl_loss']:.8f}"
            )

    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        train_pred_action_t, train_pred_safety_t = model.predict(
            torch.from_numpy(train.obs).to(device),
            torch.from_numpy(train.skill_ids).to(device),
            torch.from_numpy(train.phase_ids).to(device),
            torch.from_numpy(train.safety_now).to(device),
        )
        val_pred_action_t, val_pred_safety_t = model.predict(
            torch.from_numpy(val.obs).to(device),
            torch.from_numpy(val.skill_ids).to(device),
            torch.from_numpy(val.phase_ids).to(device),
            torch.from_numpy(val.safety_now).to(device),
        )
    train_pred_action = train_pred_action_t.cpu().numpy()
    val_pred_action = val_pred_action_t.cpu().numpy()
    train_pred_safety = train_pred_safety_t.cpu().numpy()
    val_pred_safety = val_pred_safety_t.cpu().numpy()

    train_pred_raw = denormalize_actions(train_pred_action, action_mean=action_mean, action_std=action_std)
    val_pred_raw = denormalize_actions(val_pred_action, action_mean=action_mean, action_std=action_std)
    train_target_raw = denormalize_actions(train.action_chunks, action_mean=action_mean, action_std=action_std)
    val_target_raw = denormalize_actions(val.action_chunks, action_mean=action_mean, action_std=action_std)
    hand_start = int(args.hand_start_index)
    train_rmse = raw_rmse(train_pred_raw, train_target_raw)
    val_rmse = raw_rmse(val_pred_raw, val_target_raw)
    train_hand_rmse = raw_rmse(train_pred_raw[:, :, hand_start:], train_target_raw[:, :, hand_start:])
    val_hand_rmse = raw_rmse(val_pred_raw[:, :, hand_start:], val_target_raw[:, :, hand_start:])
    train_safety_metrics = binary_metrics(train_pred_safety, train.safety_chunks)
    val_safety_metrics = binary_metrics(val_pred_safety, val.safety_chunks)

    skill_table = string_list(data["skill_table"])
    phase_table = string_list(data["phase_table"])
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "status": STATUS,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "model_type": "SafetyACTCVAEChunkPolicy",
        "dataset": str(Path(args.data).resolve()),
        "dataset_version": str(data["dataset_version"][0]),
        "experiment_name": str(data["experiment_name"][0]),
        "horizon": int(horizon),
        "stride": int(args.stride),
        "obs_dim": int(train.obs.shape[1]),
        "action_dim": int(train.action_chunks.shape[2]),
        "safety_dim": int(train.safety_now.shape[1]),
        "skill_count": int(len(skill_table)),
        "phase_count": int(len(phase_table)),
        "skill_table": skill_table,
        "phase_table": phase_table,
        "d_model": int(args.d_model),
        "nhead": int(args.nhead),
        "num_layers": int(args.num_layers),
        "latent_dim": int(args.latent_dim),
        "dropout": float(args.dropout),
        "hand_start_index": hand_start,
        "arm_loss_weight": float(args.arm_loss_weight),
        "hand_loss_weight": float(args.hand_loss_weight),
        "obs_mean": obs_mean,
        "obs_std": obs_std,
        "action_mean": action_mean,
        "action_std": action_std,
        "action_min": data["action_min"].astype(np.float32),
        "action_max": data["action_max"].astype(np.float32),
        "train_episodes": [int(v) for v in train_episodes],
        "val_episodes": [int(v) for v in val_episodes],
        "train_windows": int(len(train_index)),
        "val_windows": int(len(val_index)),
        "loss_history": history,
        "best_epoch": int(best_epoch),
        "best_val_prior_action_loss": float(best_val_prior_action),
        "final_train_action_loss": float(history[-1]["train_action_loss"]),
        "final_val_prior_action_loss": float(history[-1]["val_prior_action_loss"]),
        "train_prior_rmse_raw": float(train_rmse),
        "val_prior_rmse_raw": float(val_rmse),
        "train_prior_hand_rmse_raw": float(train_hand_rmse),
        "val_prior_hand_rmse_raw": float(val_hand_rmse),
        "train_safety_metrics": train_safety_metrics,
        "val_safety_metrics": val_safety_metrics,
        "source_stage3_10b_train_ready": bool(source_metadata.get("stage3_10b_train_ready", False)),
        "source_safety_checks": source_metadata.get("safety_checks", {}),
        "source_readiness_checks": source_metadata.get("readiness_checks", {}),
        "seed": int(args.seed),
        "closed_loop_eval_completed": False,
        "promoted_policy": False,
        "boundary": "Offline safety-aware ACT/CVAE-style chunk model; not closed-loop promoted and not hardware integration.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, args.output)

    report_payload = {
        **{key: value for key, value in checkpoint.items() if key != "model_state_dict"},
        "checkpoint": str(Path(args.output).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "report": str(Path(args.report).resolve()),
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "lr": float(args.lr),
        "weight_decay": float(args.weight_decay),
        "kl_weight": float(args.kl_weight),
        "safety_loss_weight": float(args.safety_loss_weight),
        "prior_loss_weight": float(args.prior_loss_weight),
        "device": str(device),
        "train_window_counts_by_skill": per_skill_window_counts(train_index, episode_skill_ids, skill_table),
        "val_window_counts_by_skill": per_skill_window_counts(val_index, episode_skill_ids, skill_table),
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(report_payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(args.report, json_ready(report_payload))
    print(
        json.dumps(
            {
                "status": STATUS,
                "checkpoint": str(Path(args.output).resolve()),
                "report": str(Path(args.report).resolve()),
                "best_epoch": int(best_epoch),
                "best_val_prior_action_loss": float(best_val_prior_action),
                "final_train_action_loss": float(history[-1]["train_action_loss"]),
                "final_val_prior_action_loss": float(history[-1]["val_prior_action_loss"]),
                "train_prior_rmse_raw": float(train_rmse),
                "val_prior_rmse_raw": float(val_rmse),
                "train_prior_hand_rmse_raw": float(train_hand_rmse),
                "val_prior_hand_rmse_raw": float(val_hand_rmse),
                "val_safety_metrics": val_safety_metrics,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
