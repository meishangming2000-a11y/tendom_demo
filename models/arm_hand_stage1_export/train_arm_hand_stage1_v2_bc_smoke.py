#!/usr/bin/env python3
"""Train the first experimental BC smoke policy on Stage2 dataset v0."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from arm_hand_stage1_v2_bc_common import (
    BCPolicy,
    DEFAULT_CHECKPOINT,
    DEFAULT_DATASET,
    DEFAULT_TRAIN_META,
    DEFAULT_TRAIN_REPORT,
    STATUS_EXPERIMENTAL,
    build_feature_matrix,
    feature_config_from_dataset,
    json_ready,
    load_dataset,
    require_fields,
    rmse,
    split_by_episode,
    standardize,
)


REQUIRED_FIELDS = [
    "obs",
    "actions",
    "episode_ids",
    "step_ids",
    "phase_ids",
    "phase_step_ids",
    "phase_name_table",
    "actuator_names",
    "contract_version",
]


def write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Arm-Hand Stage1 V2 BC Smoke Train Report\n\n",
        f"Generated: {report['created_at']}\n\n",
        f"- Status: `{report['status']}`\n",
        f"- Dataset: `{report['dataset']}`\n",
        f"- Checkpoint: `{report['checkpoint']}`\n",
        f"- Metadata: `{report['metadata']}`\n",
        f"- Contract: `{report['contract_version']}`\n",
        f"- Feature dim: `{report['feature_dim']}`\n",
        f"- Feature mode: `{report['feature_config']['feature_mode']}`\n",
        f"- Base obs dim: `{report['base_obs_dim']}`\n",
        f"- Action field: `{report['action_field']}`\n",
        f"- Action dim: `{report['act_dim']}`\n",
        f"- Phase features: `{report['feature_config']['include_phase_features']}`\n",
        f"- Hidden dim: `{report['hidden_dim']}`\n",
        f"- Depth: `{report['depth']}`\n",
        f"- Epochs: `{report['epochs']}`\n",
        f"- Batch size: `{report['batch_size']}`\n",
        f"- Device: `{report['device']}`\n",
        f"- Normalized obs noise std: `{report['normalized_obs_noise_std']}`\n",
        f"- Obs dropout prob: `{report['obs_dropout_prob']}`\n",
        f"- Train episodes: `{report['train_episodes']}`\n",
        f"- Val episodes: `{report['val_episodes']}`\n",
        f"- Train samples: `{report['train_samples']}`\n",
        f"- Val samples: `{report['val_samples']}`\n",
        f"- Final train MSE normalized: `{report['final_train_loss']:.8f}`\n",
        f"- Final val MSE normalized: `{report['final_val_loss']:.8f}`\n",
        f"- Val action RMSE raw units: `{report['val_action_rmse_raw']:.8f}`\n",
        f"- Train action RMSE raw units: `{report['train_action_rmse_raw']:.8f}`\n",
        f"- Training ready: **No, experimental BC smoke only**\n\n",
        "## Loss Curve\n\n",
        "| epoch | train MSE | val MSE |\n",
        "|---:|---:|---:|\n",
    ]
    for row in report["loss_history"]:
        lines.append(f"| {row['epoch']} | {row['train_loss']:.8f} | {row['val_loss']:.8f} |\n")
    lines.extend(
        [
            "\n## Per-Action Validation RMSE\n\n",
            "| action | rmse |\n",
            "|---|---:|\n",
        ]
    )
    for name, value in zip(report["action_names"], report["val_action_rmse_by_dim"]):
        lines.append(f"| {name} | {value:.8f} |\n")
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This checkpoint only proves that the tiny scripted dataset is learnable offline.\n",
            "- Online rollout against MuJoCo is the next gate; low validation loss alone is not enough.\n",
            "- The checkpoint is intentionally marked as experimental and not promoted to a maintained baseline.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Train experimental BC smoke policy on arm-hand Stage2 dataset v0.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--report", type=Path, default=DEFAULT_TRAIN_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_TRAIN_META)
    parser.add_argument("--action-field", default="actions", help="Dataset field to use as the BC target.")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--val-fraction", type=float, default=0.22)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--normalized-obs-noise-std", type=float, default=0.0)
    parser.add_argument("--obs-dropout-prob", type=float, default=0.0)
    parser.add_argument(
        "--feature-mode",
        choices=["obs_phase", "obs_only", "phase_only"],
        default="obs_phase",
        help="obs_phase is the first BC attempt; phase_only is the schedule-conditioned repair mode.",
    )
    parser.add_argument("--no-phase-features", action="store_true")
    parser.add_argument("--no-cuda", action="store_true")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    data = load_dataset(args.data)
    require_fields(data, REQUIRED_FIELDS)
    require_fields(data, [args.action_field])
    feature_config = feature_config_from_dataset(
        data,
        include_phase_features=not args.no_phase_features,
        feature_mode=args.feature_mode,
    )
    features = build_feature_matrix(data, feature_config)
    actions = data[args.action_field].astype(np.float32)
    episode_ids = data["episode_ids"].astype(np.int32)
    train_mask, val_mask, train_episodes, val_episodes = split_by_episode(episode_ids, args.val_fraction, args.seed)
    if not np.any(train_mask):
        raise RuntimeError("No training samples after episode split.")
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
        feature_dim=features.shape[1],
        act_dim=actions.shape[1],
        hidden_dim=args.hidden_dim,
        depth=args.depth,
    ).to(device)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = nn.MSELoss()
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(x_train, y_train),
        batch_size=args.batch_size,
        shuffle=True,
    )
    obs_aug_dim = int(feature_config["base_obs_dim"]) if feature_config.get("use_observation", True) else 0

    history = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        total = 0.0
        count = 0
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            if obs_aug_dim > 0 and (args.normalized_obs_noise_std > 0.0 or args.obs_dropout_prob > 0.0):
                batch_x = batch_x.clone()
                obs_view = batch_x[:, :obs_aug_dim]
                if args.normalized_obs_noise_std > 0.0:
                    obs_view.add_(torch.randn_like(obs_view) * float(args.normalized_obs_noise_std))
                if args.obs_dropout_prob > 0.0:
                    keep = torch.rand_like(obs_view) >= float(np.clip(args.obs_dropout_prob, 0.0, 1.0))
                    obs_view.mul_(keep)
            optimizer.zero_grad()
            pred = model(batch_x)
            loss = loss_fn(pred, batch_y)
            loss.backward()
            optimizer.step()
            total += float(loss.item()) * batch_x.shape[0]
            count += int(batch_x.shape[0])
        train_loss = total / max(1, count)
        model.eval()
        with torch.no_grad():
            val_loss = float(loss_fn(model(x_val.to(device)), y_val.to(device)).item())
        history.append({"epoch": int(epoch), "train_loss": float(train_loss), "val_loss": float(val_loss)})
        if epoch == 1 or epoch == args.epochs or epoch % 10 == 0:
            print(f"epoch {epoch:03d}/{args.epochs} train={train_loss:.8f} val={val_loss:.8f}")

    model.eval()
    with torch.no_grad():
        pred_norm_all = model(torch.from_numpy(feature_norm).to(device)).cpu().numpy()
    pred_actions = pred_norm_all * action_std + action_mean
    train_rmse_raw = rmse(pred_actions[train_mask], actions[train_mask])
    val_rmse_raw = rmse(pred_actions[val_mask], actions[val_mask])
    val_rmse_by_dim = np.sqrt(np.mean((pred_actions[val_mask] - actions[val_mask]) ** 2, axis=0)).astype(np.float64)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "status": STATUS_EXPERIMENTAL,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(args.data.resolve()),
        "action_field": str(args.action_field),
        "contract_version": str(data["contract_version"][0]),
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
        "train_action_rmse_raw": float(train_rmse_raw),
        "val_action_rmse_raw": float(val_rmse_raw),
        "seed": int(args.seed),
        "normalized_obs_noise_std": float(args.normalized_obs_noise_std),
        "obs_dropout_prob": float(args.obs_dropout_prob),
    }
    torch.save(checkpoint, args.output)

    report = {
        **{key: value for key, value in checkpoint.items() if key != "model_state_dict"},
        "checkpoint": str(args.output.resolve()),
        "report": str(args.report.resolve()),
        "metadata": str(args.metadata.resolve()),
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "lr": float(args.lr),
        "device": str(device),
        "normalized_obs_noise_std": float(args.normalized_obs_noise_std),
        "obs_dropout_prob": float(args.obs_dropout_prob),
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
