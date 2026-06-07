#!/usr/bin/env python3
"""Train the first Stage3 sensor-fusion BC baseline.

Input:  Stage3 sensor abstraction `obs`
Target: expert action vector

This is a learning-track smoke baseline, not a promoted policy.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from arm_hand_stage1_task_api import json_ready
from arm_hand_stage1_v2_bc_common import BCPolicy, rmse, split_by_episode, standardize


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_DATASET = DATA / "stage3_sensor_fusion_expert_dataset_v0.npz"
DEFAULT_CHECKPOINT = CHECKPOINTS / "stage3_sensor_fusion_bc_baseline_v0.pth"
DEFAULT_REPORT = DOCS / "stage3_sensor_fusion_bc_baseline_v0_train_report.md"
DEFAULT_METADATA = META / "stage3_sensor_fusion_bc_baseline_v0_train.json"

STATUS = "experimental_stage3_bc_baseline_not_promoted"


def load_dataset(path: Path):
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    return np.load(path, allow_pickle=False)


def require_fields(data, fields: list[str]) -> None:
    missing = [field for field in fields if field not in data.files]
    if missing:
        raise KeyError(f"Dataset missing fields: {missing}")


def string_list(values: np.ndarray) -> list[str]:
    return [str(item) for item in values.tolist()]


def feature_config_from_dataset(data, feature_mode: str) -> dict[str, Any]:
    if feature_mode != "obs_only":
        raise ValueError("Stage3 baseline currently supports only feature_mode=obs_only because obs already contains phase and sensor fields.")
    return {
        "feature_mode": feature_mode,
        "feature_dim": int(data["obs"].shape[1]),
        "base_obs_dim": int(data["obs"].shape[1]),
        "use_observation": True,
        "include_phase_features": False,
        "phase_names": string_list(data["expert_phase_table"]),
        "stage3_phase_names": string_list(data["stage3_phase_table"]),
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage3 Sensor Fusion BC Baseline V0 Train Report\n\n",
        f"Generated: {payload['created_at']}\n\n",
        f"- Status: `{payload['status']}`\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Checkpoint: `{payload['checkpoint']}`\n",
        f"- Feature mode: `{payload['feature_config']['feature_mode']}`\n",
        f"- Feature dim: `{payload['feature_dim']}`\n",
        f"- Action dim: `{payload['act_dim']}`\n",
        f"- Hidden dim: `{payload['hidden_dim']}`\n",
        f"- Depth: `{payload['depth']}`\n",
        f"- Epochs: `{payload['epochs']}`\n",
        f"- Batch size: `{payload['batch_size']}`\n",
        f"- Device: `{payload['device']}`\n",
        f"- Train episodes: `{payload['train_episodes']}`\n",
        f"- Val episodes: `{payload['val_episodes']}`\n",
        f"- Train samples: `{payload['train_samples']}`\n",
        f"- Val samples: `{payload['val_samples']}`\n",
        f"- Final train MSE normalized: `{payload['final_train_loss']:.8f}`\n",
        f"- Final val MSE normalized: `{payload['final_val_loss']:.8f}`\n",
        f"- Train action RMSE raw: `{payload['train_action_rmse_raw']:.8f}`\n",
        f"- Val action RMSE raw: `{payload['val_action_rmse_raw']:.8f}`\n",
        f"- Training ready: **No, closed-loop MuJoCo eval required**\n\n",
        "## Loss Curve\n\n",
        "| epoch | train MSE | val MSE |\n",
        "|---:|---:|---:|\n",
    ]
    for row in payload["loss_history"]:
        lines.append(f"| {row['epoch']} | {row['train_loss']:.8f} | {row['val_loss']:.8f} |\n")
    lines.extend(
        [
            "\n## Per-Action Validation RMSE\n\n",
            "| action | rmse |\n",
            "|---|---:|\n",
        ]
    )
    for name, value in zip(payload["action_names"], payload["val_action_rmse_by_dim"]):
        lines.append(f"| {name} | {value:.8f} |\n")
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This is the first Stage3 sensor-fusion BC baseline.\n",
            "- Low offline error is not task success. The next gate is closed-loop MuJoCo evaluation.\n",
            "- The model uses sensor abstraction `obs`, not ground-truth object state arrays.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Train Stage3 sensor-fusion BC baseline.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--action-field", default="expert_actions")
    parser.add_argument("--feature-mode", default="obs_only")
    parser.add_argument("--epochs", type=int, default=160)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--train-all", action="store_true")
    parser.add_argument("--seed", type=int, default=91)
    parser.add_argument("--no-cuda", action="store_true")
    args = parser.parse_args()

    torch.manual_seed(int(args.seed))
    np.random.seed(int(args.seed))
    data = load_dataset(args.data)
    require_fields(data, ["obs", args.action_field, "episode_ids", "actuator_names", "dataset_version", "contract_version"])
    feature_config = feature_config_from_dataset(data, args.feature_mode)
    features = data["obs"].astype(np.float32)
    actions = data[args.action_field].astype(np.float32)
    episode_ids = data["episode_ids"].astype(np.int32)
    if bool(args.train_all):
        train_mask = np.ones_like(episode_ids, dtype=bool)
        val_mask = train_mask.copy()
        train_episodes = sorted(int(v) for v in np.unique(episode_ids))
        val_episodes = train_episodes.copy()
    else:
        train_mask, val_mask, train_episodes, val_episodes = split_by_episode(episode_ids, args.val_fraction, args.seed)
        if not np.any(val_mask):
            val_mask = train_mask.copy()
            val_episodes = train_episodes.copy()

    feature_norm, feature_mean, feature_std = standardize(features[train_mask], features)
    action_norm, action_mean, action_std = standardize(actions[train_mask], actions)
    x_train = torch.from_numpy(feature_norm[train_mask])
    y_train = torch.from_numpy(action_norm[train_mask])
    x_val = torch.from_numpy(feature_norm[val_mask])
    y_val = torch.from_numpy(action_norm[val_mask])

    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    model = BCPolicy(
        feature_dim=int(features.shape[1]),
        act_dim=int(actions.shape[1]),
        hidden_dim=int(args.hidden_dim),
        depth=int(args.depth),
    ).to(device)
    optimizer = optim.Adam(model.parameters(), lr=float(args.lr))
    loss_fn = nn.MSELoss()
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(x_train, y_train),
        batch_size=int(args.batch_size),
        shuffle=True,
    )
    history = []
    for epoch in range(1, int(args.epochs) + 1):
        model.train()
        total = 0.0
        count = 0
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            loss = loss_fn(model(batch_x), batch_y)
            loss.backward()
            optimizer.step()
            total += float(loss.item()) * int(batch_x.shape[0])
            count += int(batch_x.shape[0])
        train_loss = total / max(1, count)
        model.eval()
        with torch.no_grad():
            val_loss = float(loss_fn(model(x_val.to(device)), y_val.to(device)).item())
        history.append({"epoch": int(epoch), "train_loss": float(train_loss), "val_loss": float(val_loss)})
        if epoch == 1 or epoch == args.epochs or epoch % 20 == 0:
            print(f"epoch {epoch:03d}/{args.epochs} train={train_loss:.8f} val={val_loss:.8f}")

    model.eval()
    with torch.no_grad():
        pred_norm = model(torch.from_numpy(feature_norm).to(device)).cpu().numpy()
    pred_actions = pred_norm * action_std + action_mean
    train_rmse = rmse(pred_actions[train_mask], actions[train_mask])
    val_rmse = rmse(pred_actions[val_mask], actions[val_mask])
    val_rmse_by_dim = np.sqrt(np.mean((pred_actions[val_mask] - actions[val_mask]) ** 2, axis=0)).astype(np.float64)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "status": STATUS,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(Path(args.data).resolve()),
        "dataset_version": str(data["dataset_version"][0]),
        "contract_version": str(data["contract_version"][0]),
        "action_field": str(args.action_field),
        "feature_dim": int(features.shape[1]),
        "base_obs_dim": int(data["obs"].shape[1]),
        "act_dim": int(actions.shape[1]),
        "hidden_dim": int(args.hidden_dim),
        "depth": int(args.depth),
        "feature_mean": feature_mean.astype(np.float32),
        "feature_std": feature_std.astype(np.float32),
        "action_mean": action_mean.astype(np.float32),
        "action_std": action_std.astype(np.float32),
        "action_min": actions[train_mask].min(axis=0).astype(np.float32),
        "action_max": actions[train_mask].max(axis=0).astype(np.float32),
        "feature_config": feature_config,
        "action_names": [str(x) for x in data["actuator_names"].tolist()],
        "train_episodes": train_episodes,
        "val_episodes": val_episodes,
        "loss_history": history,
        "final_train_loss": float(history[-1]["train_loss"]),
        "final_val_loss": float(history[-1]["val_loss"]),
        "train_action_rmse_raw": float(train_rmse),
        "val_action_rmse_raw": float(val_rmse),
        "seed": int(args.seed),
    }
    torch.save(checkpoint, args.output)
    report = {
        **{key: value for key, value in checkpoint.items() if key != "model_state_dict"},
        "checkpoint": str(Path(args.output).resolve()),
        "metadata": str(Path(args.metadata).resolve()),
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "lr": float(args.lr),
        "device": str(device),
        "train_samples": int(train_mask.sum()),
        "val_samples": int(val_mask.sum()),
        "val_action_rmse_by_dim": val_rmse_by_dim,
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(report), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, json_ready(report))
    print(
        json.dumps(
            {
                "checkpoint": str(args.output),
                "final_train_loss": report["final_train_loss"],
                "final_val_loss": report["final_val_loss"],
                "val_action_rmse_raw": report["val_action_rmse_raw"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
