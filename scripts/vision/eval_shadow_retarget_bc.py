#!/usr/bin/env python3
"""Evaluate a trained visual-to-Shadow BC model on a retarget trace."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import torch
    import torch.nn as nn
except ImportError:
    print("PyTorch is required. Install it with: pip install torch")
    sys.exit(1)

from scripts.vision.retarget_palm_trace_to_shadow import rollout_actions, save_rollout_dataset
from vision.hand_open_close import open_close_features_from_landmarks
from vision.palm_landmarks import build_palm_feature


class SimpleBCModel(nn.Module):
    """Simple MLP policy matching scripts/train_bc.py."""

    def __init__(self, obs_dim: int, act_dim: int, hidden_dim: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, act_dim),
            nn.Tanh(),
        )

    def forward(self, x):
        return self.network(x)


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


def _features_from_landmarks(landmarks: np.ndarray, observation_schema: str) -> np.ndarray:
    if observation_schema == "hand_open_close_feature_v1":
        return open_close_features_from_landmarks(landmarks)
    return np.asarray([build_palm_feature(frame)[0] for frame in landmarks], dtype=np.float32)


def _append_phase_feature(observations: np.ndarray, horizon: int) -> np.ndarray:
    phase = np.arange(observations.shape[0], dtype=np.float32) / max(1, int(horizon) - 1)
    phase = np.clip(phase, 0.0, 1.0)
    return np.concatenate([observations.astype(np.float32), phase[:, None]], axis=1)


def load_model(model_path: Path, device: torch.device):
    checkpoint = torch.load(model_path, map_location=device)
    obs_dim = int(checkpoint.get("obs_dim", 76))
    act_dim = int(checkpoint.get("act_dim", 24))
    hidden_dim = int(checkpoint.get("hidden_dim", 64))
    model = SimpleBCModel(obs_dim=obs_dim, act_dim=act_dim, hidden_dim=hidden_dim)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model, checkpoint


def predict_actions(model, observations: np.ndarray, device: torch.device, batch_size: int) -> np.ndarray:
    predictions: List[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, observations.shape[0], batch_size):
            batch = torch.from_numpy(observations[start : start + batch_size]).float().to(device)
            predictions.append(model(batch).cpu().numpy())
    return np.concatenate(predictions, axis=0).astype(np.float32)


def save_predicted_retarget(
    path: Path,
    source_payload: np.lib.npyio.NpzFile,
    predicted_actions: np.ndarray,
    metadata: Dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamps": np.asarray(source_payload["timestamps"], dtype=np.float32),
        "landmarks": np.asarray(source_payload["landmarks"], dtype=np.float32),
        "actions": predicted_actions.astype(np.float32),
        "metadata": metadata,
    }
    if "actuator_names" in source_payload:
        payload["actuator_names"] = source_payload["actuator_names"]
    if "source_frame_indices" in source_payload:
        payload["source_frame_indices"] = np.asarray(source_payload["source_frame_indices"], dtype=np.float32)
    np.savez_compressed(path, **payload)


def save_report(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate a visual-to-Shadow BC model on a retarget trace")
    parser.add_argument("--model", required=True, help="Checkpoint from scripts/train_bc.py")
    parser.add_argument("--retarget", required=True, help="Reference retarget NPZ containing landmarks and target actions")
    parser.add_argument("--output", required=True, help="Predicted retarget NPZ output")
    parser.add_argument("--rollout-output", default="", help="Optional MuJoCo rollout dataset for predicted actions")
    parser.add_argument("--report", default="", help="Optional JSON report path")
    parser.add_argument("--visualization-dir", default="", help="Optional visualization output directory")
    parser.add_argument("--render-mujoco", action="store_true", help="Render MuJoCo keyframes in visualization")
    parser.add_argument("--batch-size", type=int, default=512, help="Prediction batch size")
    parser.add_argument("--max-steps", type=int, default=0, help="Evaluate only the first N steps; 0 uses all")
    parser.add_argument("--no-cuda", action="store_true", help="Disable CUDA")
    parser.add_argument("--observation-mode", default="oracle", choices=["oracle", "deployable"])
    parser.add_argument("--placement-mode", default="demo", choices=["scene", "demo"])
    parser.add_argument("--placement-jitter", type=float, default=0.0)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    model_path = Path(args.model)
    retarget_path = Path(args.retarget)
    if not model_path.exists():
        raise FileNotFoundError(model_path)
    if not retarget_path.exists():
        raise FileNotFoundError(retarget_path)

    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    model, checkpoint = load_model(model_path, device)
    model_metadata = dict(checkpoint.get("metadata", {}) or {})

    source_payload = np.load(retarget_path, allow_pickle=True)
    landmarks = np.asarray(source_payload["landmarks"], dtype=np.float32)
    target_actions = np.asarray(source_payload["actions"], dtype=np.float32)
    if args.max_steps and args.max_steps > 0:
        limit = min(int(args.max_steps), landmarks.shape[0])
        landmarks = landmarks[:limit]
        target_actions = target_actions[:limit]

    observation_schema = str(model_metadata.get("observation_schema", "normalized_21_landmarks_plus_palm_frame_v1"))
    observations = _features_from_landmarks(landmarks, observation_schema=observation_schema)
    if model_metadata.get("phase_feature"):
        horizon = int(model_metadata.get("phase_feature_horizon") or observations.shape[0])
        observations = _append_phase_feature(observations, horizon)

    expected_obs_dim = int(checkpoint.get("obs_dim", observations.shape[1]))
    if observations.shape[1] != expected_obs_dim:
        raise ValueError(f"Observation dim mismatch: model expects {expected_obs_dim}, got {observations.shape[1]}")

    predicted_actions = predict_actions(model, observations, device=device, batch_size=int(args.batch_size))
    target_actions = target_actions[: predicted_actions.shape[0]]
    action_error = predicted_actions - target_actions
    metrics = {
        "steps": int(predicted_actions.shape[0]),
        "target_action_mse": float(np.mean(np.square(action_error))),
        "target_action_mae": float(np.mean(np.abs(action_error))),
        "target_action_max_abs_error": float(np.max(np.abs(action_error))),
        "predicted_action_min": float(np.min(predicted_actions)),
        "predicted_action_max": float(np.max(predicted_actions)),
        "predicted_action_mean_abs": float(np.mean(np.abs(predicted_actions))),
    }

    source_metadata = _metadata_dict(source_payload)
    predicted_metadata = {
        "dataset_type": "vision_shadow_retarget_model_prediction",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_retarget": str(retarget_path),
        "source_retarget_metadata": source_metadata,
        "model": str(model_path),
        "model_metadata": model_metadata,
        "observation_schema": observation_schema,
        "action_schema": "shadow_hand_normalized_action_v1",
        "summary": metrics,
        "boundary": "Diagnostic learned imitation of the heuristic visual-to-Shadow retarget output.",
    }

    output_path = Path(args.output)
    if args.max_steps and args.max_steps > 0:
        temp_payload = {
            "timestamps": np.asarray(source_payload["timestamps"], dtype=np.float32)[: predicted_actions.shape[0]],
            "landmarks": landmarks,
            "actions": target_actions,
            "metadata": source_payload["metadata"] if "metadata" in source_payload else {},
        }
        if "actuator_names" in source_payload:
            temp_payload["actuator_names"] = source_payload["actuator_names"]
        if "source_frame_indices" in source_payload:
            temp_payload["source_frame_indices"] = np.asarray(source_payload["source_frame_indices"], dtype=np.float32)[
                : predicted_actions.shape[0]
            ]
        temp_path = output_path.with_name(output_path.stem + "_source_slice_tmp.npz")
        np.savez_compressed(temp_path, **temp_payload)
        source_payload = np.load(temp_path, allow_pickle=True)

    save_predicted_retarget(output_path, source_payload, predicted_actions, predicted_metadata)

    rollout_summary = None
    if args.rollout_output:
        rollout_args = argparse.Namespace(
            rollout_steps=0,
            observation_mode=args.observation_mode,
            placement_mode=args.placement_mode,
            placement_jitter=float(args.placement_jitter),
        )
        rollout_dataset, rollout_summary = rollout_actions(rollout_args, predicted_actions, predicted_metadata)
        save_rollout_dataset(Path(args.rollout_output), rollout_dataset)

    visual_summary = None
    if args.visualization_dir:
        cmd = [
            sys.executable,
            "scripts/vision/visualize_shadow_retarget.py",
            "--retarget",
            str(output_path.resolve()),
            "--output-dir",
            str(Path(args.visualization_dir).resolve()),
        ]
        if args.rollout_output:
            cmd.extend(["--rollout", str(Path(args.rollout_output).resolve())])
        if args.render_mujoco:
            cmd.append("--render-mujoco")
        subprocess.run(cmd, cwd=str(Path(__file__).resolve().parents[2]), check=True)
        visual_summary = str(Path(args.visualization_dir).resolve() / "visual_summary.json")

    report_payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": str(model_path),
        "retarget": str(retarget_path),
        "output": str(output_path),
        "rollout_output": args.rollout_output,
        "visual_summary": visual_summary,
        "metrics": metrics,
        "rollout_summary": rollout_summary,
    }
    if args.report:
        save_report(Path(args.report), report_payload)

    print(f"Saved predicted retarget: {output_path}")
    print(json.dumps(_json_ready({"metrics": metrics, "rollout_summary": rollout_summary}), indent=2))
    if args.rollout_output:
        print(f"Saved rollout: {args.rollout_output}")
    if args.report:
        print(f"Saved report: {args.report}")


if __name__ == "__main__":
    main()
