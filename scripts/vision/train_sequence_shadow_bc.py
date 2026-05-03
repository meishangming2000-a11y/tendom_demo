#!/usr/bin/env python3
"""Train a sequence visual-to-Shadow action-chunk BC model."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
except ImportError:
    print("PyTorch is required. Install it with: pip install torch")
    sys.exit(1)

from scripts.vision.retarget_palm_trace_to_shadow import rollout_actions, save_rollout_dataset
from vision.palm_landmarks import build_palm_feature


def _metadata_dict(payload: np.lib.npyio.NpzFile) -> Dict[str, Any]:
    if "metadata" not in payload:
        return {}
    raw = payload["metadata"]
    return dict(raw.item() if hasattr(raw, "item") else raw)


def _json_ready(value):
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def _features_from_landmarks(landmarks: np.ndarray) -> np.ndarray:
    return np.asarray([build_palm_feature(frame)[0] for frame in landmarks], dtype=np.float32)


def _augment_sequence(
    observations: np.ndarray,
    add_velocity: bool,
    add_phase: bool,
    phase_start: int = 0,
    phase_horizon: int | None = None,
) -> np.ndarray:
    observations = np.asarray(observations, dtype=np.float32)
    features = [observations]
    if add_velocity:
        velocity = np.zeros_like(observations, dtype=np.float32)
        if observations.shape[0] > 1:
            velocity[1:] = observations[1:] - observations[:-1]
        features.append(velocity)
    if add_phase:
        horizon = max(1, int(phase_horizon or observations.shape[0]))
        phase = (np.arange(observations.shape[0], dtype=np.float32) + int(phase_start)) / max(1, horizon - 1)
        features.append(np.clip(phase, 0.0, 1.0)[:, None])
    return np.concatenate(features, axis=1).astype(np.float32)


def _window_episode(
    observations: np.ndarray,
    actions: np.ndarray,
    history: int,
    chunk: int,
    sample_stride: int,
    add_velocity: bool,
    add_phase: bool,
) -> Tuple[np.ndarray, np.ndarray]:
    observations = np.asarray(observations, dtype=np.float32)
    actions = np.asarray(actions, dtype=np.float32)
    length = min(observations.shape[0], actions.shape[0])
    observations = observations[:length]
    actions = actions[:length]
    if length < max(2, chunk):
        return np.zeros((0, history, observations.shape[1]), dtype=np.float32), np.zeros(
            (0, chunk, actions.shape[1]), dtype=np.float32
        )

    augmented = _augment_sequence(
        observations,
        add_velocity=add_velocity,
        add_phase=add_phase,
        phase_horizon=length,
    )
    padded = np.concatenate(
        [np.repeat(augmented[:1], max(0, history - 1), axis=0), augmented],
        axis=0,
    )
    xs = []
    ys = []
    last_start = max(0, length - chunk)
    for start in range(0, last_start + 1, max(1, sample_stride)):
        padded_start = start
        xs.append(padded[padded_start : padded_start + history])
        ys.append(actions[start : start + chunk])
    if not xs:
        return np.zeros((0, history, augmented.shape[1]), dtype=np.float32), np.zeros(
            (0, chunk, actions.shape[1]), dtype=np.float32
        )
    return np.asarray(xs, dtype=np.float32), np.asarray(ys, dtype=np.float32)


def load_episode_dataset(
    dataset_path: Path,
    observation_field: str,
    history: int,
    chunk: int,
    sample_stride: int,
    add_velocity: bool,
    add_phase: bool,
    val_fraction: float,
    seed: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any], Dict[str, Any]]:
    payload = np.load(dataset_path, allow_pickle=True)
    if "episodes" not in payload:
        raise ValueError(f"Dataset missing episodes: {dataset_path}")
    metadata = _metadata_dict(payload)
    episodes = [dict(item) for item in payload["episodes"]]
    if not episodes:
        raise ValueError(f"Dataset has no episodes: {dataset_path}")

    rng = np.random.default_rng(int(seed))
    episode_indices = np.arange(len(episodes))
    rng.shuffle(episode_indices)
    val_count = max(1, int(round(len(episodes) * float(val_fraction)))) if len(episodes) > 1 else 0
    val_indices = set(int(item) for item in episode_indices[:val_count])

    train_xs: List[np.ndarray] = []
    train_ys: List[np.ndarray] = []
    val_xs: List[np.ndarray] = []
    val_ys: List[np.ndarray] = []
    episode_summaries = []

    for idx, episode in enumerate(episodes):
        if observation_field not in episode:
            raise ValueError(f"Episode {idx} missing observation field: {observation_field}")
        observations = np.asarray(episode[observation_field], dtype=np.float32)
        actions = np.asarray(episode["actions"], dtype=np.float32)
        x, y = _window_episode(
            observations=observations,
            actions=actions,
            history=history,
            chunk=chunk,
            sample_stride=sample_stride,
            add_velocity=add_velocity,
            add_phase=add_phase,
        )
        target_xs, target_ys = (val_xs, val_ys) if idx in val_indices else (train_xs, train_ys)
        if x.shape[0]:
            target_xs.append(x)
            target_ys.append(y)
        episode_summaries.append(
            {
                "episode": int(idx),
                "steps": int(min(observations.shape[0], actions.shape[0])),
                "windows": int(x.shape[0]),
                "split": "val" if idx in val_indices else "train",
            }
        )

    if not train_xs:
        raise ValueError("No training windows were generated")
    train_x = np.concatenate(train_xs, axis=0)
    train_y = np.concatenate(train_ys, axis=0)
    if val_xs:
        val_x = np.concatenate(val_xs, axis=0)
        val_y = np.concatenate(val_ys, axis=0)
    else:
        val_x = train_x[:0].copy()
        val_y = train_y[:0].copy()

    split_summary = {
        "episodes": episode_summaries,
        "train_windows": int(train_x.shape[0]),
        "val_windows": int(val_x.shape[0]),
        "input_dim": int(train_x.shape[2]),
        "act_dim": int(train_y.shape[2]),
    }
    return train_x, train_y, val_x, val_y, metadata, split_summary


class SequenceActionChunkModel(nn.Module):
    """Small TCN + GRU encoder with an action-chunk head."""

    def __init__(self, input_dim: int, act_dim: int, history: int, chunk: int, hidden_dim: int):
        super().__init__()
        self.input_dim = int(input_dim)
        self.act_dim = int(act_dim)
        self.history = int(history)
        self.chunk = int(chunk)
        self.hidden_dim = int(hidden_dim)
        self.tcn = nn.Sequential(
            nn.Conv1d(input_dim, hidden_dim, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.Conv1d(hidden_dim, hidden_dim, kernel_size=5, padding=2),
            nn.ReLU(),
        )
        self.gru = nn.GRU(hidden_dim, hidden_dim, batch_first=True)
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, chunk * act_dim),
            nn.Tanh(),
        )

    def forward(self, x):
        # x: [batch, history, input_dim]
        z = self.tcn(x.transpose(1, 2)).transpose(1, 2)
        _seq, hidden = self.gru(z)
        out = self.head(hidden[-1])
        return out.view(x.shape[0], self.chunk, self.act_dim)


def _loss_fn(prediction, target, smoothness_weight: float):
    mse = nn.functional.mse_loss(prediction, target)
    if prediction.shape[1] <= 1 or smoothness_weight <= 0:
        return mse, mse.detach(), torch.tensor(0.0, device=prediction.device)
    pred_delta = prediction[:, 1:] - prediction[:, :-1]
    target_delta = target[:, 1:] - target[:, :-1]
    smooth = nn.functional.mse_loss(pred_delta, target_delta)
    return mse + float(smoothness_weight) * smooth, mse.detach(), smooth.detach()


def train_model(
    train_x: np.ndarray,
    train_y: np.ndarray,
    val_x: np.ndarray,
    val_y: np.ndarray,
    args: argparse.Namespace,
    device: torch.device,
) -> Tuple[SequenceActionChunkModel, Dict[str, Any]]:
    model = SequenceActionChunkModel(
        input_dim=train_x.shape[2],
        act_dim=train_y.shape[2],
        history=int(args.history),
        chunk=int(args.chunk),
        hidden_dim=int(args.hidden_dim),
    ).to(device)
    optimizer = optim.AdamW(model.parameters(), lr=float(args.lr), weight_decay=float(args.weight_decay))
    train_dataset = torch.utils.data.TensorDataset(torch.from_numpy(train_x), torch.from_numpy(train_y))
    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=int(args.batch_size),
        shuffle=True,
        drop_last=False,
    )

    history = []
    best_state = None
    best_val = float("inf")
    for epoch in range(int(args.epochs)):
        model.train()
        train_loss_sum = 0.0
        train_mse_sum = 0.0
        batches = 0
        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            prediction = model(batch_x)
            loss, mse, _smooth = _loss_fn(prediction, batch_y, float(args.smoothness_weight))
            loss.backward()
            if float(args.grad_clip) > 0:
                nn.utils.clip_grad_norm_(model.parameters(), float(args.grad_clip))
            optimizer.step()
            train_loss_sum += float(loss.item())
            train_mse_sum += float(mse.item())
            batches += 1

        train_loss = train_loss_sum / max(1, batches)
        train_mse = train_mse_sum / max(1, batches)
        val_mse = evaluate_mse(model, val_x, val_y, device=device, batch_size=int(args.batch_size)) if val_x.size else train_mse
        history.append({"epoch": epoch + 1, "train_loss": train_loss, "train_mse": train_mse, "val_mse": val_mse})
        if val_mse < best_val:
            best_val = float(val_mse)
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        if (epoch + 1) % int(args.log_interval) == 0 or epoch == 0 or epoch == int(args.epochs) - 1:
            print(
                f"Epoch [{epoch + 1:3d}/{args.epochs}] "
                f"train_loss={train_loss:.6f} train_mse={train_mse:.6f} val_mse={val_mse:.6f}"
            )

    if best_state is not None:
        model.load_state_dict(best_state)
    return model, {"best_val_mse": best_val, "history": history}


def evaluate_mse(
    model: SequenceActionChunkModel,
    x: np.ndarray,
    y: np.ndarray,
    device: torch.device,
    batch_size: int,
) -> float:
    if not x.size:
        return 0.0
    model.eval()
    losses = []
    with torch.no_grad():
        for start in range(0, x.shape[0], batch_size):
            batch_x = torch.from_numpy(x[start : start + batch_size]).to(device)
            batch_y = torch.from_numpy(y[start : start + batch_size]).to(device)
            prediction = model(batch_x)
            losses.append(float(nn.functional.mse_loss(prediction, batch_y).item()))
    return float(np.mean(losses)) if losses else 0.0


def save_checkpoint(
    path: Path,
    model: SequenceActionChunkModel,
    source_metadata: Dict[str, Any],
    split_summary: Dict[str, Any],
    train_summary: Dict[str, Any],
    args: argparse.Namespace,
) -> None:
    metadata = {
        "model_type": "sequence_tcn_gru_action_chunk_bc",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_dataset_metadata": source_metadata,
        "split_summary": split_summary,
        "train_summary": train_summary,
        "history": int(args.history),
        "chunk": int(args.chunk),
        "input_dim": int(model.input_dim),
        "obs_dim": int(model.input_dim),
        "act_dim": int(model.act_dim),
        "hidden_dim": int(model.hidden_dim),
        "add_velocity": bool(args.add_velocity),
        "add_phase_feature": bool(args.add_phase_feature),
        "observation_field": args.observation_field,
        "boundary": "Diagnostic sequence imitation of heuristic visual-to-Shadow retarget actions.",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "model_type": "sequence_tcn_gru_action_chunk_bc",
            "input_dim": int(model.input_dim),
            "act_dim": int(model.act_dim),
            "hidden_dim": int(model.hidden_dim),
            "history": int(model.history),
            "chunk": int(model.chunk),
            "metadata": metadata,
            "args": vars(args),
        },
        path,
    )


def _load_sequence_checkpoint(path: Path, device: torch.device):
    checkpoint = torch.load(path, map_location=device)
    if checkpoint.get("model_type") != "sequence_tcn_gru_action_chunk_bc":
        raise ValueError(f"Not a sequence checkpoint: {path}")
    model = SequenceActionChunkModel(
        input_dim=int(checkpoint["input_dim"]),
        act_dim=int(checkpoint["act_dim"]),
        history=int(checkpoint["history"]),
        chunk=int(checkpoint["chunk"]),
        hidden_dim=int(checkpoint["hidden_dim"]),
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, checkpoint


def predict_trace_actions(
    model: SequenceActionChunkModel,
    observations: np.ndarray,
    add_velocity: bool,
    add_phase: bool,
    device: torch.device,
    batch_size: int,
) -> np.ndarray:
    augmented = _augment_sequence(
        observations,
        add_velocity=add_velocity,
        add_phase=add_phase,
        phase_horizon=observations.shape[0],
    )
    padded = np.concatenate([np.repeat(augmented[:1], model.history - 1, axis=0), augmented], axis=0)
    windows = np.asarray([padded[idx : idx + model.history] for idx in range(observations.shape[0])], dtype=np.float32)
    chunk_sum = np.zeros((observations.shape[0], model.act_dim), dtype=np.float32)
    chunk_count = np.zeros((observations.shape[0], 1), dtype=np.float32)
    model.eval()
    with torch.no_grad():
        for start in range(0, windows.shape[0], batch_size):
            batch = torch.from_numpy(windows[start : start + batch_size]).to(device)
            chunks = model(batch).cpu().numpy().astype(np.float32)
            for batch_idx, chunk in enumerate(chunks):
                trace_start = start + batch_idx
                trace_end = min(observations.shape[0], trace_start + model.chunk)
                take = trace_end - trace_start
                if take <= 0:
                    continue
                chunk_sum[trace_start:trace_end] += chunk[:take]
                chunk_count[trace_start:trace_end] += 1.0
    return chunk_sum / np.maximum(chunk_count, 1.0)


def save_predicted_retarget(
    path: Path,
    source_payload: np.lib.npyio.NpzFile,
    predicted_actions: np.ndarray,
    metadata: Dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamps": np.asarray(source_payload["timestamps"], dtype=np.float32)[: predicted_actions.shape[0]],
        "landmarks": np.asarray(source_payload["landmarks"], dtype=np.float32)[: predicted_actions.shape[0]],
        "actions": predicted_actions.astype(np.float32),
        "metadata": metadata,
    }
    if "actuator_names" in source_payload:
        payload["actuator_names"] = source_payload["actuator_names"]
    if "source_frame_indices" in source_payload:
        payload["source_frame_indices"] = np.asarray(source_payload["source_frame_indices"], dtype=np.float32)[
            : predicted_actions.shape[0]
        ]
    np.savez_compressed(path, **payload)


def evaluate_on_retarget(
    model: SequenceActionChunkModel,
    checkpoint_metadata: Dict[str, Any],
    retarget_path: Path,
    output_path: Path,
    rollout_output: Path | None,
    visualization_dir: Path | None,
    render_mujoco: bool,
    device: torch.device,
    args: argparse.Namespace,
) -> Dict[str, Any]:
    payload = np.load(retarget_path, allow_pickle=True)
    landmarks = np.asarray(payload["landmarks"], dtype=np.float32)
    target_actions = np.asarray(payload["actions"], dtype=np.float32)
    if int(args.max_eval_steps) > 0:
        limit = min(int(args.max_eval_steps), landmarks.shape[0])
        landmarks = landmarks[:limit]
        target_actions = target_actions[:limit]
    observations = _features_from_landmarks(landmarks)
    predicted = predict_trace_actions(
        model=model,
        observations=observations,
        add_velocity=bool(args.add_velocity),
        add_phase=bool(args.add_phase_feature),
        device=device,
        batch_size=int(args.batch_size),
    )
    target_actions = target_actions[: predicted.shape[0]]
    error = predicted - target_actions
    metrics = {
        "steps": int(predicted.shape[0]),
        "target_action_mse": float(np.mean(np.square(error))),
        "target_action_mae": float(np.mean(np.abs(error))),
        "target_action_max_abs_error": float(np.max(np.abs(error))),
        "predicted_action_min": float(np.min(predicted)),
        "predicted_action_max": float(np.max(predicted)),
        "predicted_action_mean_abs": float(np.mean(np.abs(predicted))),
    }
    prediction_metadata = {
        "dataset_type": "vision_shadow_retarget_sequence_prediction",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_retarget": str(retarget_path),
        "source_retarget_metadata": _metadata_dict(payload),
        "model_metadata": checkpoint_metadata,
        "summary": metrics,
        "boundary": "Diagnostic sequence model prediction on visual-to-Shadow retarget data.",
    }
    save_predicted_retarget(output_path, payload, predicted, prediction_metadata)

    rollout_summary = None
    if rollout_output:
        rollout_args = argparse.Namespace(
            rollout_steps=0,
            observation_mode=args.observation_mode,
            placement_mode=args.placement_mode,
            placement_jitter=float(args.placement_jitter),
        )
        rollout_dataset, rollout_summary = rollout_actions(rollout_args, predicted, prediction_metadata)
        save_rollout_dataset(rollout_output, rollout_dataset)

    visual_summary = None
    if visualization_dir:
        cmd = [
            sys.executable,
            "scripts/vision/visualize_shadow_retarget.py",
            "--retarget",
            str(output_path.resolve()),
            "--output-dir",
            str(visualization_dir.resolve()),
        ]
        if rollout_output:
            cmd.extend(["--rollout", str(rollout_output.resolve())])
        if render_mujoco:
            cmd.append("--render-mujoco")
        subprocess.run(cmd, cwd=str(Path(__file__).resolve().parents[2]), check=True)
        visual_summary = str(visualization_dir / "visual_summary.json")

    return {
        "retarget": str(retarget_path),
        "prediction": str(output_path),
        "rollout": str(rollout_output) if rollout_output else "",
        "visual_summary": visual_summary,
        "metrics": metrics,
        "rollout_summary": rollout_summary,
    }


def save_report(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train sequence visual-to-Shadow action chunk BC")
    parser.add_argument("--data", required=True, help="BC dataset from build_shadow_retarget_bc_dataset.py")
    parser.add_argument("--output", required=True, help="Output checkpoint path")
    parser.add_argument("--report", default="", help="Optional JSON report path")
    parser.add_argument("--observation-field", default="observations")
    parser.add_argument("--history", type=int, default=32, help="Number of past frames per training sample")
    parser.add_argument("--chunk", type=int, default=8, help="Number of future actions predicted per sample")
    parser.add_argument("--sample-stride", type=int, default=2, help="Window stride within each episode")
    parser.add_argument("--add-velocity", action="store_true", help="Append per-frame palm-feature deltas")
    parser.add_argument("--add-phase-feature", action="store_true", help="Append normalized episode phase per frame")
    parser.add_argument("--val-fraction", type=float, default=0.2, help="Episode-level validation fraction")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--smoothness-weight", type=float, default=0.1)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--log-interval", type=int, default=25)
    parser.add_argument("--no-cuda", action="store_true")
    parser.add_argument("--eval-retarget", default="", help="Optional retarget NPZ for model prediction evaluation")
    parser.add_argument("--prediction-output", default="", help="Predicted retarget NPZ for --eval-retarget")
    parser.add_argument("--rollout-output", default="", help="Optional MuJoCo rollout output for predicted actions")
    parser.add_argument("--visualization-dir", default="", help="Optional visualization dir for predicted retarget")
    parser.add_argument("--render-mujoco", action="store_true")
    parser.add_argument("--max-eval-steps", type=int, default=0)
    parser.add_argument("--observation-mode", default="oracle", choices=["oracle", "deployable"])
    parser.add_argument("--placement-mode", default="demo", choices=["scene", "demo"])
    parser.add_argument("--placement-jitter", type=float, default=0.0)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    print("=" * 72)
    print("Sequence Visual-to-Shadow Action-Chunk BC")
    print("=" * 72)
    print(f"Dataset: {args.data}")
    print(f"Output: {args.output}")
    print(f"Device: {device}")

    train_x, train_y, val_x, val_y, source_metadata, split_summary = load_episode_dataset(
        dataset_path=Path(args.data),
        observation_field=args.observation_field,
        history=int(args.history),
        chunk=int(args.chunk),
        sample_stride=int(args.sample_stride),
        add_velocity=bool(args.add_velocity),
        add_phase=bool(args.add_phase_feature),
        val_fraction=float(args.val_fraction),
        seed=int(args.seed),
    )
    print("Dataset windows:")
    print(json.dumps(_json_ready(split_summary), indent=2, ensure_ascii=False))

    model, train_summary = train_model(train_x, train_y, val_x, val_y, args=args, device=device)
    checkpoint_path = Path(args.output)
    save_checkpoint(
        checkpoint_path,
        model=model,
        source_metadata=source_metadata,
        split_summary=split_summary,
        train_summary=train_summary,
        args=args,
    )
    print(f"Saved checkpoint: {checkpoint_path}")

    checkpoint_model, checkpoint = _load_sequence_checkpoint(checkpoint_path, device)
    eval_summary = None
    if args.eval_retarget:
        prediction_output = Path(args.prediction_output) if args.prediction_output else checkpoint_path.with_suffix(".prediction.npz")
        rollout_output = Path(args.rollout_output) if args.rollout_output else None
        visualization_dir = Path(args.visualization_dir) if args.visualization_dir else None
        eval_summary = evaluate_on_retarget(
            model=checkpoint_model,
            checkpoint_metadata=dict(checkpoint.get("metadata", {}) or {}),
            retarget_path=Path(args.eval_retarget),
            output_path=prediction_output,
            rollout_output=rollout_output,
            visualization_dir=visualization_dir,
            render_mujoco=bool(args.render_mujoco),
            device=device,
            args=args,
        )
        print("Evaluation on retarget:")
        print(json.dumps(_json_ready(eval_summary), indent=2, ensure_ascii=False))

    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "checkpoint": str(checkpoint_path),
        "data": args.data,
        "split_summary": split_summary,
        "train_summary": train_summary,
        "eval_summary": eval_summary,
        "config": vars(args),
    }
    if args.report:
        save_report(Path(args.report), report)
        print(f"Saved report: {args.report}")


if __name__ == "__main__":
    main()
