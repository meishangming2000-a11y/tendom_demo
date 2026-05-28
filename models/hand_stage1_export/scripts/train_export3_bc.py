from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from export3_common import DOCS_DIR, METADATA_DIR, ROOT


DATA_DIR = ROOT / "data"
CHECKPOINT_DIR = ROOT / "checkpoints"
DEFAULT_DATASET = DATA_DIR / "export3_scripted_pinned_wrap_v0.npz"
DEFAULT_OUTPUT = CHECKPOINT_DIR / "bc_hand_stage1_export3_pinned_wrap_v0.pth"
DEFAULT_REPORT = DOCS_DIR / "export3_bc_pinned_wrap_v0_report.md"
DEFAULT_METADATA = METADATA_DIR / "export3_bc_pinned_wrap_v0.json"


class BCPolicy(nn.Module):
    def __init__(self, obs_dim: int, act_dim: int, hidden_dim: int, depth: int):
        super().__init__()
        layers: list[nn.Module] = []
        current = obs_dim
        for _ in range(depth):
            layers.append(nn.Linear(current, hidden_dim))
            layers.append(nn.ReLU())
            current = hidden_dim
        layers.append(nn.Linear(current, act_dim))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


def parse_class_filter(raw: str | None) -> list[str]:
    return [item.strip() for item in str(raw or "").split(",") if item.strip()]


def load_npz_dataset(path: Path, class_filter: str | None) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    data = np.load(path, allow_pickle=True)
    obs = data["observations"].astype(np.float32)
    actions = data["actions"].astype(np.float32)
    episode_id = data["episode_id"].astype(np.int32)
    metadata = {
        "feature_names": [str(x) for x in data["feature_names"].tolist()],
        "action_names": [str(x) for x in data["action_names"].tolist()],
        "class_names": [str(x) for x in data["class_names"].tolist()],
        "stage_names": [str(x) for x in data["stage_names"].tolist()],
    }
    filters = parse_class_filter(class_filter)
    if filters:
        missing = [name for name in filters if name not in metadata["class_names"]]
        if missing:
            raise ValueError(f"class_filter entries {missing!r} not in dataset class_names={metadata['class_names']}")
        class_ids = {metadata["class_names"].index(name) for name in filters}
        sample_class = data["sample_class"].astype(np.int16)
        mask = np.array([int(value) in class_ids for value in sample_class], dtype=bool)
        obs = obs[mask]
        actions = actions[mask]
        episode_id = episode_id[mask]
    return obs, actions, episode_id, metadata


def episode_split(episode_id: np.ndarray, val_fraction: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    episodes = np.unique(episode_id)
    rng.shuffle(episodes)
    val_count = max(1, int(round(len(episodes) * val_fraction))) if len(episodes) > 1 else 0
    val_episodes = set(int(x) for x in episodes[:val_count])
    val_mask = np.array([int(eid) in val_episodes for eid in episode_id], dtype=bool)
    train_mask = ~val_mask
    return train_mask, val_mask


def standardize(train: np.ndarray, all_values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = train.mean(axis=0, keepdims=True).astype(np.float32)
    std = train.std(axis=0, keepdims=True).astype(np.float32)
    std = np.where(std < 1e-6, 1.0, std).astype(np.float32)
    return ((all_values - mean) / std).astype(np.float32), mean.squeeze(0), std.squeeze(0)


def rmse(pred: np.ndarray, target: np.ndarray) -> float:
    return float(np.sqrt(np.mean((pred - target) ** 2)))


def write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Export3 BC Pinned-Wrap v0 Report",
        "",
        "Status: diagnostic offline BC smoke test, not a promoted stable_grasp baseline.",
        "",
        f"- Dataset: `{report['dataset']}`",
        f"- Checkpoint: `{report['checkpoint']}`",
        f"- Metadata: `{report['metadata']}`",
        f"- Init checkpoint: `{report['init_checkpoint']}`",
        f"- Normalization source: `{report['normalization_source']}`",
        f"- Class filter: `{report['class_filter']}`",
        f"- Train samples: {report['train_samples']}",
        f"- Val samples: {report['val_samples']}",
        f"- Observation dim: {report['obs_dim']}",
        f"- Action dim: {report['act_dim']}",
        f"- Hidden dim: {report['hidden_dim']}",
        f"- Depth: {report['depth']}",
        f"- Epochs: {report['epochs']}",
        f"- Final train MSE normalized: {report['final_train_loss']:.8f}",
        f"- Final val MSE normalized: {report['final_val_loss']:.8f}",
        f"- Val action RMSE raw units: {report['val_action_rmse_raw']:.8f}",
        "",
        "## Interpretation",
        "",
        "- This only checks whether the scripted export3 pinned-wrap target mapping is learnable offline.",
        "- It does not prove rollout stability, free-object retention, gravity grasp, or sim-to-real readiness.",
        "- Next required step is online rollout evaluation against `scene_ball_export3.xml`.",
        "",
        "## Loss Curve",
        "",
        "| Epoch | Train MSE | Val MSE |",
        "|---:|---:|---:|",
    ]
    for row in report["loss_history"]:
        lines.append(f"| {row['epoch']} | {row['train_loss']:.8f} | {row['val_loss']:.8f} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Train first-pass state-based BC on export3 scripted dataset.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--class-filter", type=str, default="PINNED_WRAP_PASS")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--init-checkpoint", type=Path, default=None)
    parser.add_argument("--use-init-normalization", action="store_true")
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--no-cuda", action="store_true")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    obs, actions, episode_id, ds_meta = load_npz_dataset(args.data, args.class_filter)
    if obs.shape[0] == 0:
        raise RuntimeError("No samples remain after filtering.")
    train_mask, val_mask = episode_split(episode_id, args.val_fraction, args.seed)
    if not np.any(train_mask):
        raise RuntimeError("No training samples after episode split.")
    if not np.any(val_mask):
        val_mask = train_mask.copy()

    init_checkpoint = None
    if args.init_checkpoint is not None:
        init_checkpoint = torch.load(args.init_checkpoint, map_location="cpu", weights_only=False)

    if args.use_init_normalization and init_checkpoint is not None:
        obs_mean = np.asarray(init_checkpoint["obs_mean"], dtype=np.float32)
        obs_std = np.asarray(init_checkpoint["obs_std"], dtype=np.float32)
        act_mean = np.asarray(init_checkpoint["action_mean"], dtype=np.float32)
        act_std = np.asarray(init_checkpoint["action_std"], dtype=np.float32)
        obs_norm = ((obs - obs_mean) / obs_std).astype(np.float32)
        act_norm = ((actions - act_mean) / act_std).astype(np.float32)
        normalization_source = str(args.init_checkpoint)
    else:
        obs_norm, obs_mean, obs_std = standardize(obs[train_mask], obs)
        act_norm, act_mean, act_std = standardize(actions[train_mask], actions)
        normalization_source = "current_dataset_train_split"

    x_train = torch.from_numpy(obs_norm[train_mask])
    y_train = torch.from_numpy(act_norm[train_mask])
    x_val = torch.from_numpy(obs_norm[val_mask])
    y_val = torch.from_numpy(act_norm[val_mask])

    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    model = BCPolicy(obs_dim=obs.shape[1], act_dim=actions.shape[1], hidden_dim=args.hidden_dim, depth=args.depth).to(device)
    if init_checkpoint is not None:
        expected = {
            "obs_dim": int(obs.shape[1]),
            "act_dim": int(actions.shape[1]),
            "hidden_dim": int(args.hidden_dim),
            "depth": int(args.depth),
        }
        actual = {
            "obs_dim": int(init_checkpoint["obs_dim"]),
            "act_dim": int(init_checkpoint["act_dim"]),
            "hidden_dim": int(init_checkpoint["hidden_dim"]),
            "depth": int(init_checkpoint.get("depth", 3)),
        }
        if actual != expected:
            raise ValueError(f"init checkpoint shape/config mismatch: expected={expected} actual={actual}")
        model.load_state_dict(init_checkpoint["model_state_dict"])
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = nn.MSELoss()
    loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x_train, y_train), batch_size=args.batch_size, shuffle=True)

    history = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        total = 0.0
        count = 0
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            pred = model(batch_x)
            loss = loss_fn(pred, batch_y)
            loss.backward()
            optimizer.step()
            total += float(loss.item()) * batch_x.shape[0]
            count += batch_x.shape[0]
        train_loss = total / max(count, 1)
        model.eval()
        with torch.no_grad():
            val_pred = model(x_val.to(device))
            val_loss = float(loss_fn(val_pred, y_val.to(device)).item())
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
        if epoch == 1 or epoch == args.epochs or epoch % 10 == 0:
            print(f"epoch {epoch:03d}/{args.epochs} train={train_loss:.8f} val={val_loss:.8f}")

    model.eval()
    with torch.no_grad():
        val_pred_norm = model(x_val.to(device)).cpu().numpy()
    val_pred_raw = val_pred_norm * act_std + act_mean
    val_target_raw = actions[val_mask]
    val_rmse = rmse(val_pred_raw, val_target_raw)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "obs_dim": int(obs.shape[1]),
        "act_dim": int(actions.shape[1]),
        "hidden_dim": int(args.hidden_dim),
        "depth": int(args.depth),
        "obs_mean": obs_mean,
        "obs_std": obs_std,
        "action_mean": act_mean,
        "action_std": act_std,
        "action_min": actions[train_mask].min(axis=0).astype(np.float32),
        "action_max": actions[train_mask].max(axis=0).astype(np.float32),
        "feature_names": ds_meta["feature_names"],
        "action_names": ds_meta["action_names"],
        "class_filter": args.class_filter,
        "dataset": str(args.data),
        "init_checkpoint": str(args.init_checkpoint) if args.init_checkpoint is not None else "",
        "normalization_source": normalization_source,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "diagnostic_offline_bc_not_promoted_baseline",
    }
    torch.save(checkpoint, args.output)

    report = {
        "created_at": checkpoint["created_at"],
        "status": checkpoint["status"],
        "dataset": str(args.data),
        "checkpoint": str(args.output),
        "report": str(args.report),
        "metadata": str(args.metadata),
        "init_checkpoint": checkpoint["init_checkpoint"],
        "normalization_source": normalization_source,
        "class_filter": args.class_filter,
        "train_samples": int(train_mask.sum()),
        "val_samples": int(val_mask.sum()),
        "obs_dim": int(obs.shape[1]),
        "act_dim": int(actions.shape[1]),
        "hidden_dim": args.hidden_dim,
        "depth": args.depth,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "device": str(device),
        "final_train_loss": float(history[-1]["train_loss"]),
        "final_val_loss": float(history[-1]["val_loss"]),
        "val_action_rmse_raw": val_rmse,
        "loss_history": history,
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, report)
    print(json.dumps({"checkpoint": str(args.output), "report": str(args.report), "val_action_rmse_raw": val_rmse}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
