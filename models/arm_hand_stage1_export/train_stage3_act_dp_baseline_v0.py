#!/usr/bin/env python3
"""Train the first Stage3 ACT/DP-style action-chunk baseline.

This is an ACT-lite smoke baseline, not a promoted closed-loop policy:

    input:  obs_t + learned skill embedding
    target: future action chunk a[t:t+H]

It uses the Stage3.9B3 dense obs/action dataset and trains a lightweight MLP
chunk predictor. The purpose is to verify the ACT/DP training surface before
adding heavier transformer/CVAE or diffusion-policy machinery.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
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

DEFAULT_DATASET = DATA / "stage3_skill_act_dp_sequence_dataset_v0.npz"
DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_act_lite_chunk_policy_v0.pth"
DEFAULT_REPORT = DOCS / "stage3_act_lite_chunk_policy_v0_train_report.md"
DEFAULT_METADATA = META / "stage3_act_lite_chunk_policy_v0_train.json"

STATUS = "stage3_act_lite_chunk_policy_v0_trained_offline_not_closed_loop_promoted"


def load_dataset(path: Path) -> np.lib.npyio.NpzFile:
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    return np.load(path, allow_pickle=True)


def require_fields(data: np.lib.npyio.NpzFile, fields: list[str]) -> None:
    missing = [field for field in fields if field not in data.files]
    if missing:
        raise KeyError(f"Dataset missing fields: {missing}")


def string_list(values: np.ndarray) -> list[str]:
    return [str(item) for item in values.tolist()]


def split_episodes_by_skill(
    episode_skill_ids: np.ndarray,
    *,
    val_fraction: float,
    seed: int,
    train_all: bool,
) -> tuple[np.ndarray, np.ndarray, list[int], list[int]]:
    episode_ids = np.arange(len(episode_skill_ids), dtype=np.int32)
    if train_all:
        return np.ones_like(episode_ids, dtype=bool), np.ones_like(episode_ids, dtype=bool), episode_ids.tolist(), episode_ids.tolist()

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
        if length < horizon:
            continue
        for start in range(0, int(length) - int(horizon) + 1, int(stride)):
            rows.append((episode_id, start))
    return np.asarray(rows, dtype=np.int32)


def subsample_windows(index: np.ndarray, *, max_windows: int, seed: int) -> np.ndarray:
    if int(max_windows) <= 0 or len(index) <= int(max_windows):
        return index
    rng = np.random.default_rng(int(seed))
    chosen = rng.choice(len(index), size=int(max_windows), replace=False)
    chosen.sort()
    return index[chosen]


def materialize_windows(
    episode_obs: np.ndarray,
    episode_actions: np.ndarray,
    episode_skill_ids: np.ndarray,
    window_index: np.ndarray,
    *,
    horizon: int,
    obs_mean: np.ndarray,
    obs_std: np.ndarray,
    action_mean: np.ndarray,
    action_std: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    count = int(len(window_index))
    obs_dim = int(episode_obs.shape[2])
    action_dim = int(episode_actions.shape[2])
    obs = np.empty((count, obs_dim), dtype=np.float32)
    skill_ids = np.empty((count,), dtype=np.int64)
    chunks = np.empty((count, int(horizon) * action_dim), dtype=np.float32)
    obs_std_safe = np.maximum(obs_std.astype(np.float32), 1e-6)
    action_std_safe = np.maximum(action_std.astype(np.float32), 1e-6)
    for row_id, (episode_id, start) in enumerate(window_index.tolist()):
        obs[row_id] = (episode_obs[episode_id, start].astype(np.float32) - obs_mean) / obs_std_safe
        skill_ids[row_id] = int(episode_skill_ids[episode_id])
        chunk = episode_actions[episode_id, start : start + int(horizon)].astype(np.float32)
        chunks[row_id] = ((chunk - action_mean) / action_std_safe).reshape(-1)
    return obs, skill_ids, chunks


class ACTLiteChunkPolicy(nn.Module):
    def __init__(
        self,
        *,
        obs_dim: int,
        action_dim: int,
        horizon: int,
        skill_count: int,
        skill_embed_dim: int,
        hidden_dim: int,
        depth: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.skill_embedding = nn.Embedding(int(skill_count), int(skill_embed_dim))
        layers: list[nn.Module] = []
        in_dim = int(obs_dim) + int(skill_embed_dim)
        for _ in range(max(1, int(depth))):
            layers.append(nn.Linear(in_dim, int(hidden_dim)))
            layers.append(nn.LayerNorm(int(hidden_dim)))
            layers.append(nn.GELU())
            if float(dropout) > 0.0:
                layers.append(nn.Dropout(float(dropout)))
            in_dim = int(hidden_dim)
        layers.append(nn.Linear(in_dim, int(horizon) * int(action_dim)))
        self.net = nn.Sequential(*layers)

    def forward(self, obs: torch.Tensor, skill_ids: torch.Tensor) -> torch.Tensor:
        skill = self.skill_embedding(skill_ids.long())
        return self.net(torch.cat([obs, skill], dim=-1))


def normalized_to_raw_chunk(pred: np.ndarray, *, horizon: int, action_dim: int, action_mean: np.ndarray, action_std: np.ndarray) -> np.ndarray:
    chunk = pred.reshape(-1, int(horizon), int(action_dim))
    return chunk * action_std.reshape(1, 1, -1) + action_mean.reshape(1, 1, -1)


def raw_rmse(pred_raw: np.ndarray, target_raw: np.ndarray) -> float:
    return float(np.sqrt(np.mean((pred_raw - target_raw) ** 2)))


def per_skill_window_counts(index: np.ndarray, episode_skill_ids: np.ndarray, skill_table: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {name: 0 for name in skill_table}
    for episode_id, _ in index.tolist():
        name = skill_table[int(episode_skill_ids[int(episode_id)])]
        counts[name] = counts.get(name, 0) + 1
    return counts


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage3 ACT-lite Chunk Policy v0 训练报告\n\n",
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
        f"- output dim：`{payload['output_dim']}`\n",
        f"- skill count：`{payload['skill_count']}`\n",
        f"- hidden dim：`{payload['hidden_dim']}`\n",
        f"- depth：`{payload['depth']}`\n",
        f"- epochs：`{payload['epochs']}`\n",
        f"- batch size：`{payload['batch_size']}`\n",
        f"- device：`{payload['device']}`\n",
        f"- train episodes：`{payload['train_episodes']}`\n",
        f"- val episodes：`{payload['val_episodes']}`\n",
        f"- train windows：`{payload['train_windows']}`\n",
        f"- val windows：`{payload['val_windows']}`\n",
        f"- final train MSE normalized：`{payload['final_train_loss']:.8f}`\n",
        f"- final val MSE normalized：`{payload['final_val_loss']:.8f}`\n",
        f"- train chunk RMSE raw：`{payload['train_chunk_rmse_raw']:.8f}`\n",
        f"- val chunk RMSE raw：`{payload['val_chunk_rmse_raw']:.8f}`\n",
        f"- best val epoch：`{payload['best_epoch']}`\n",
        f"- best val MSE normalized：`{payload['best_val_loss']:.8f}`\n",
        "\n## 这次训练到底是什么\n\n",
        "这是第一版 ACT-lite action chunk 训练：给当前 `obs_t` 和 `skill_id`，预测未来 `H` 步 actuator action chunk。它验证 ACT/DP 训练入口，但还不是完整 ACT CVAE/Transformer，也不是 Diffusion Policy。\n\n",
        "## 技能窗口分布\n\n",
        "| split | skill | windows |\n",
        "| --- | --- | ---: |\n",
    ]
    for split, counts in (("train", payload["train_window_counts_by_skill"]), ("val", payload["val_window_counts_by_skill"])):
        for skill, count in counts.items():
            lines.append(f"| {split} | `{skill}` | {count} |\n")
    lines.extend(["\n## Loss Curve\n\n", "| epoch | train MSE | val MSE |\n", "| ---: | ---: | ---: |\n"])
    for row in payload["loss_history"]:
        lines.append(f"| {row['epoch']} | {row['train_loss']:.8f} | {row['val_loss']:.8f} |\n")
    lines.extend(
        [
            "\n## 如果成功\n\n",
            "下一步做 MuJoCo closed-loop eval：把 chunk policy 接到 Stage3 技能执行器里，和 scripted SkillZoo baseline 对比成功率、滑移、挤压和穿透。\n\n",
            "## 如果失败\n\n",
            "先不要扩大模型。优先检查窗口切分、phase/skill 条件、action chunk horizon、以及 full-hand/pinch 混合训练是否需要分技能头。\n\n",
            "## 重要边界\n\n",
            "- 这个 checkpoint 只能说明 offline action chunk learning 已跑通。\n",
            "- 不能说机械手已经由 ACT/DP 学会抓鸡蛋；闭环 MuJoCo eval 还没做。\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Train Stage3 ACT-lite action chunk policy from B3 dense obs/action data.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--horizon", type=int, default=16)
    parser.add_argument("--stride", type=int, default=8)
    parser.add_argument("--max-train-windows", type=int, default=60000)
    parser.add_argument("--max-val-windows", type=int, default=12000)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--skill-embed-dim", type=int, default=16)
    parser.add_argument("--dropout", type=float, default=0.03)
    parser.add_argument("--lr", type=float, default=8e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--train-all", action="store_true")
    parser.add_argument("--seed", type=int, default=239)
    parser.add_argument("--no-cuda", action="store_true")
    args = parser.parse_args()

    torch.manual_seed(int(args.seed))
    np.random.seed(int(args.seed))
    data = load_dataset(args.data)
    require_fields(
        data,
        [
            "episode_obs",
            "episode_actions",
            "episode_mask",
            "episode_lengths",
            "episode_success",
            "episode_skill_ids",
            "skill_table",
            "obs_mean",
            "obs_std",
            "action_mean",
            "action_std",
            "act_dp_ready",
            "dataset_version",
            "contract_version",
        ],
    )
    if not bool(data["act_dp_ready"][0]):
        raise RuntimeError("Dataset is not marked act_dp_ready; run B3 export first.")

    horizon = int(args.horizon)
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    stride = max(1, int(args.stride))
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

    train_index = collect_window_index(data["episode_lengths"], train_episode_mask, horizon=horizon, stride=stride)
    val_index = collect_window_index(data["episode_lengths"], val_episode_mask, horizon=horizon, stride=stride)
    if len(train_index) == 0 or len(val_index) == 0:
        raise RuntimeError(f"No windows for training/validation: train={len(train_index)} val={len(val_index)}")
    train_index = subsample_windows(train_index, max_windows=int(args.max_train_windows), seed=int(args.seed) + 1)
    val_index = subsample_windows(val_index, max_windows=int(args.max_val_windows), seed=int(args.seed) + 2)

    episode_obs = data["episode_obs"].astype(np.float32)
    episode_actions = data["episode_actions"].astype(np.float32)
    obs_mean = data["obs_mean"].astype(np.float32)
    obs_std = data["obs_std"].astype(np.float32)
    action_mean = data["action_mean"].astype(np.float32)
    action_std = data["action_std"].astype(np.float32)

    x_train, skill_train, y_train = materialize_windows(
        episode_obs,
        episode_actions,
        episode_skill_ids,
        train_index,
        horizon=horizon,
        obs_mean=obs_mean,
        obs_std=obs_std,
        action_mean=action_mean,
        action_std=action_std,
    )
    x_val, skill_val, y_val = materialize_windows(
        episode_obs,
        episode_actions,
        episode_skill_ids,
        val_index,
        horizon=horizon,
        obs_mean=obs_mean,
        obs_std=obs_std,
        action_mean=action_mean,
        action_std=action_std,
    )

    device = torch.device("cuda" if torch.cuda.is_available() and not bool(args.no_cuda) else "cpu")
    model = ACTLiteChunkPolicy(
        obs_dim=int(x_train.shape[1]),
        action_dim=int(episode_actions.shape[2]),
        horizon=horizon,
        skill_count=int(len(data["skill_table"])),
        skill_embed_dim=int(args.skill_embed_dim),
        hidden_dim=int(args.hidden_dim),
        depth=int(args.depth),
        dropout=float(args.dropout),
    ).to(device)
    optimizer = optim.AdamW(model.parameters(), lr=float(args.lr), weight_decay=float(args.weight_decay))
    loss_fn = nn.MSELoss()
    train_ds = torch.utils.data.TensorDataset(
        torch.from_numpy(x_train),
        torch.from_numpy(skill_train),
        torch.from_numpy(y_train),
    )
    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=int(args.batch_size), shuffle=True)
    x_val_t = torch.from_numpy(x_val).to(device)
    skill_val_t = torch.from_numpy(skill_val).to(device)
    y_val_t = torch.from_numpy(y_val).to(device)

    history: list[dict[str, float]] = []
    best_state: dict[str, torch.Tensor] | None = None
    best_val = float("inf")
    best_epoch = 0
    for epoch in range(1, int(args.epochs) + 1):
        model.train()
        total = 0.0
        count = 0
        for batch_obs, batch_skill, batch_target in train_loader:
            batch_obs = batch_obs.to(device)
            batch_skill = batch_skill.to(device)
            batch_target = batch_target.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(batch_obs, batch_skill), batch_target)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()
            total += float(loss.item()) * int(batch_obs.shape[0])
            count += int(batch_obs.shape[0])
        train_loss = total / max(1, count)
        model.eval()
        with torch.no_grad():
            val_loss = float(loss_fn(model(x_val_t, skill_val_t), y_val_t).item())
        history.append({"epoch": int(epoch), "train_loss": float(train_loss), "val_loss": float(val_loss)})
        if val_loss < best_val:
            best_val = val_loss
            best_epoch = int(epoch)
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        if epoch == 1 or epoch == int(args.epochs) or epoch % max(1, int(args.epochs) // 5) == 0:
            print(f"epoch {epoch:03d}/{args.epochs} train={train_loss:.8f} val={val_loss:.8f}")

    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        pred_train = model(torch.from_numpy(x_train).to(device), torch.from_numpy(skill_train).to(device)).cpu().numpy()
        pred_val = model(x_val_t, skill_val_t).cpu().numpy()
    action_dim = int(episode_actions.shape[2])
    target_train_raw = normalized_to_raw_chunk(y_train, horizon=horizon, action_dim=action_dim, action_mean=action_mean, action_std=action_std)
    target_val_raw = normalized_to_raw_chunk(y_val, horizon=horizon, action_dim=action_dim, action_mean=action_mean, action_std=action_std)
    pred_train_raw = normalized_to_raw_chunk(pred_train, horizon=horizon, action_dim=action_dim, action_mean=action_mean, action_std=action_std)
    pred_val_raw = normalized_to_raw_chunk(pred_val, horizon=horizon, action_dim=action_dim, action_mean=action_mean, action_std=action_std)
    train_rmse = raw_rmse(pred_train_raw, target_train_raw)
    val_rmse = raw_rmse(pred_val_raw, target_val_raw)

    skill_table = string_list(data["skill_table"])
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "status": STATUS,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "model_type": "ACT-lite MLP action chunk predictor",
        "dataset": str(Path(args.data).resolve()),
        "dataset_version": str(data["dataset_version"][0]),
        "contract_version": str(data["contract_version"][0]),
        "horizon": int(horizon),
        "stride": int(stride),
        "obs_dim": int(x_train.shape[1]),
        "action_dim": int(action_dim),
        "output_dim": int(horizon * action_dim),
        "skill_count": int(len(skill_table)),
        "skill_table": skill_table,
        "phase_table": string_list(data["phase_table"]) if "phase_table" in data.files else [],
        "hidden_dim": int(args.hidden_dim),
        "depth": int(args.depth),
        "skill_embed_dim": int(args.skill_embed_dim),
        "dropout": float(args.dropout),
        "obs_mean": obs_mean,
        "obs_std": np.maximum(obs_std, 1e-6),
        "action_mean": action_mean,
        "action_std": np.maximum(action_std, 1e-6),
        "action_min": data["action_min"].astype(np.float32),
        "action_max": data["action_max"].astype(np.float32),
        "train_episodes": [int(v) for v in train_episodes],
        "val_episodes": [int(v) for v in val_episodes],
        "train_windows": int(len(train_index)),
        "val_windows": int(len(val_index)),
        "loss_history": history,
        "best_epoch": int(best_epoch),
        "best_val_loss": float(best_val),
        "final_train_loss": float(history[-1]["train_loss"]),
        "final_val_loss": float(history[-1]["val_loss"]),
        "train_chunk_rmse_raw": float(train_rmse),
        "val_chunk_rmse_raw": float(val_rmse),
        "seed": int(args.seed),
        "note": "Offline action-chunk training only; closed-loop MuJoCo eval is required before promotion.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, args.output)

    report = {
        **{key: value for key, value in checkpoint.items() if key != "model_state_dict"},
        "checkpoint": str(Path(args.output).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "report": str(Path(args.report).resolve()),
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "lr": float(args.lr),
        "weight_decay": float(args.weight_decay),
        "device": str(device),
        "train_window_counts_by_skill": per_skill_window_counts(train_index, episode_skill_ids, skill_table),
        "val_window_counts_by_skill": per_skill_window_counts(val_index, episode_skill_ids, skill_table),
        "readiness": {
            "offline_training_completed": True,
            "closed_loop_eval_completed": False,
            "promoted_policy": False,
        },
        "next_step_if_success_zh": "接入 MuJoCo closed-loop eval，与 scripted SkillZoo baseline 比较。",
        "next_step_if_failure_zh": "先检查 horizon、skill 条件、分技能头和动作归一化，不急着上更大的模型。",
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(report), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, json_ready(report))
    print(
        json.dumps(
            {
                "status": STATUS,
                "checkpoint": str(Path(args.output).resolve()),
                "report": str(Path(args.report).resolve()),
                "best_epoch": int(best_epoch),
                "best_val_loss": float(best_val),
                "final_train_loss": float(history[-1]["train_loss"]),
                "final_val_loss": float(history[-1]["val_loss"]),
                "train_chunk_rmse_raw": float(train_rmse),
                "val_chunk_rmse_raw": float(val_rmse),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
