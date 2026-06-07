#!/usr/bin/env python3
"""Train the first experimental BC policy for Stage2 pick-place v0.5."""

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

from arm_hand_stage1_v2_bc_common import (
    BCPolicy,
    STATUS_EXPERIMENTAL,
    build_feature_matrix,
    dataset_phase_lengths,
    episode_lengths,
    json_ready,
    load_dataset,
    require_fields,
    rmse,
    split_by_episode,
    standardize,
    string_list,
)


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CHECKPOINTS = ROOT / "checkpoints"

DEFAULT_DATASET = DATA / "arm_hand_stage1_v3_pick_place_dataset_v0_5.npz"
DEFAULT_CHECKPOINT = CHECKPOINTS / "bc_arm_hand_stage1_v3_pick_place_dataset_v0_5_obs_phase_target.pth"
DEFAULT_REPORT = DOCS / "arm_hand_stage1_v3_pick_place_bc_v0_5_train_report.md"
DEFAULT_META = META / "arm_hand_stage1_v3_pick_place_bc_v0_5_train.json"

REQUIRED_FIELDS = [
    "obs",
    "expert_actions",
    "episode_ids",
    "step_ids",
    "phase_ids",
    "phase_step_ids",
    "phase_name_table",
    "actuator_names",
    "contract_version",
]


def feature_config_from_pick_place_dataset(data, *, feature_mode: str) -> dict[str, Any]:
    if feature_mode not in {"obs_phase_target", "phase_only", "phase_target_static"}:
        raise ValueError("The pick-place trainer supports obs_phase_target, phase_only, and phase_target_static.")
    if feature_mode == "phase_target_static" and "target_centers" not in data.files:
        raise KeyError("phase_target_static requires dataset field `target_centers`.")
    phase_names = string_list(data["phase_name_table"])
    phase_lengths = dataset_phase_lengths(data)
    max_episode_steps = max(episode_lengths(data).values())
    base_obs_dim = int(data["obs"].shape[1])
    phase_dim = len(phase_names) + 2
    use_obs = feature_mode == "obs_phase_target"
    use_target_center = feature_mode == "phase_target_static"
    return {
        "base_obs_dim": base_obs_dim,
        "feature_dim": int((base_obs_dim if use_obs else 0) + phase_dim + (3 if use_target_center else 0)),
        "feature_mode": feature_mode,
        "use_observation": bool(use_obs),
        "include_phase_features": True,
        "include_offset_features": False,
        "include_target_center_features": bool(use_target_center),
        "target_features_in_observation": bool(use_obs),
        "target_feature_note": (
            "obs already contains target_center_xyz and ball_to_target_xyz"
            if use_obs
            else "static target_center_xyz appended without live ball observation"
        ),
        "phase_names": phase_names,
        "phase_lengths": phase_lengths,
        "max_episode_steps": int(max_episode_steps),
        "extra_features": ["phase_one_hot", "phase_progress", "episode_progress"]
        + (["target_center_xyz"] if use_target_center else []),
    }


def resolve_outputs(args) -> tuple[Path, Path, Path, Path | None]:
    run_dir = Path(args.run_dir).resolve() if args.run_dir else None
    data_path = args.data
    output = args.output
    report = args.report
    metadata = args.metadata
    if run_dir:
        (run_dir / "checkpoints").mkdir(parents=True, exist_ok=True)
        (run_dir / "eval").mkdir(parents=True, exist_ok=True)
        (run_dir / "logs").mkdir(parents=True, exist_ok=True)
        data_path = data_path or (run_dir / "datasets" / "arm_hand_stage1_v3_pick_place_dataset_v0_5.npz")
        output = output or (run_dir / "checkpoints" / "bc_arm_hand_stage1_v3_pick_place_dataset_v0_5_obs_phase_target.pth")
        report = report or (run_dir / "eval" / "bc_train_report.md")
        metadata = metadata or (run_dir / "eval" / "bc_train_summary.json")
    else:
        data_path = data_path or DEFAULT_DATASET
        output = output or DEFAULT_CHECKPOINT
        report = report or DEFAULT_REPORT
        metadata = metadata or DEFAULT_META
    return Path(data_path), Path(output), Path(report), Path(metadata)


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Arm-Hand Stage1 V3 Pick-Place BC {report['dataset_version'].upper()} Train Report\n\n",
        f"Generated: {report['created_at']}\n\n",
        f"- Status: `{report['status']}`\n",
        f"- Dataset: `{report['dataset']}`\n",
        f"- Checkpoint: `{report['checkpoint']}`\n",
        f"- Metadata: `{report['metadata']}`\n",
        f"- Contract: `{report['contract_version']}`\n",
        f"- Dataset version: `{report['dataset_version']}`\n",
        f"- Feature mode: `{report['feature_config']['feature_mode']}`\n",
        f"- Feature dim: `{report['feature_dim']}`\n",
        f"- Base obs dim: `{report['base_obs_dim']}`\n",
        f"- Action field: `{report['action_field']}`\n",
        f"- Action dim: `{report['act_dim']}`\n",
        f"- Hidden dim: `{report['hidden_dim']}`\n",
        f"- Depth: `{report['depth']}`\n",
        f"- Epochs: `{report['epochs']}`\n",
        f"- Batch size: `{report['batch_size']}`\n",
        f"- Device: `{report['device']}`\n",
        f"- Train episodes: `{report['train_episodes']}`\n",
        f"- Val episodes: `{report['val_episodes']}`\n",
        f"- Train samples: `{report['train_samples']}`\n",
        f"- Val samples: `{report['val_samples']}`\n",
        f"- Final train MSE normalized: `{report['final_train_loss']:.8f}`\n",
        f"- Final val MSE normalized: `{report['final_val_loss']:.8f}`\n",
        f"- Train action RMSE raw units: `{report['train_action_rmse_raw']:.8f}`\n",
        f"- Val action RMSE raw units: `{report['val_action_rmse_raw']:.8f}`\n",
        f"- Training ready: **No, online eval still required**\n\n",
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
            "- This checkpoint is the first fixed-target pick-place BC smoke artifact.\n",
            "- Low offline loss is not success; fixed-target and narrow-sweep online eval are the next gates.\n",
            "- This checkpoint is experimental and not a maintained baseline.\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Train experimental pick-place BC policy on dataset v0.5.")
    parser.add_argument("--data", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--metadata", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--action-field", default="expert_actions")
    parser.add_argument("--feature-mode", choices=["obs_phase_target", "phase_only", "phase_target_static"], default="obs_phase_target")
    parser.add_argument("--epochs", type=int, default=220)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--val-fraction", type=float, default=0.34)
    parser.add_argument("--train-all", action="store_true")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--no-cuda", action="store_true")
    args = parser.parse_args()

    data_path, output_path, report_path, metadata_path = resolve_outputs(args)

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    data = load_dataset(data_path)
    require_fields(data, REQUIRED_FIELDS)
    require_fields(data, [args.action_field])
    feature_config = feature_config_from_pick_place_dataset(data, feature_mode=args.feature_mode)
    features = build_feature_matrix(data, feature_config)
    actions = data[args.action_field].astype(np.float32)
    episode_ids = data["episode_ids"].astype(np.int32)
    if args.train_all:
        train_mask = np.ones_like(episode_ids, dtype=bool)
        val_mask = train_mask.copy()
        train_episodes = sorted(int(v) for v in np.unique(episode_ids))
        val_episodes = train_episodes.copy()
    else:
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
    history = []
    for epoch in range(1, args.epochs + 1):
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
            total += float(loss.item()) * batch_x.shape[0]
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
        pred_norm_all = model(torch.from_numpy(feature_norm).to(device)).cpu().numpy()
    pred_actions = pred_norm_all * action_std + action_mean
    train_rmse_raw = rmse(pred_actions[train_mask], actions[train_mask])
    val_rmse_raw = rmse(pred_actions[val_mask], actions[val_mask])
    val_rmse_by_dim = np.sqrt(np.mean((pred_actions[val_mask] - actions[val_mask]) ** 2, axis=0)).astype(np.float64)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "status": STATUS_EXPERIMENTAL,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(data_path.resolve()),
        "dataset_version": str(data["dataset_version"][0]) if "dataset_version" in data.files else "unknown",
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
    }
    torch.save(checkpoint, output_path)

    report = {
        **{key: value for key, value in checkpoint.items() if key != "model_state_dict"},
        "checkpoint": str(output_path.resolve()),
        "report": str(report_path.resolve()),
        "metadata": str(metadata_path.resolve()),
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "lr": float(args.lr),
        "device": str(device),
        "train_samples": int(train_mask.sum()),
        "val_samples": int(val_mask.sum()),
        "val_action_rmse_by_dim": val_rmse_by_dim,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(json_ready(report), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(report_path, json_ready(report))
    print(
        json.dumps(
            {
                "checkpoint": str(output_path),
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
