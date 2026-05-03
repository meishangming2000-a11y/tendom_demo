#!/usr/bin/env python3
"""Build a BC dataset from one or more visual-to-Shadow retarget traces."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from vision.palm_landmarks import PALM_FEATURE_DIM, build_palm_feature, summarize_palm_trace


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


def _load_rollout_episode(path: Path) -> Dict[str, Any]:
    if not path:
        return {}
    payload = np.load(path, allow_pickle=True)
    if "episodes" not in payload or len(payload["episodes"]) == 0:
        return {}
    return dict(payload["episodes"][0])


def _features_from_landmarks(landmarks: np.ndarray) -> np.ndarray:
    features = []
    for frame in np.asarray(landmarks, dtype=np.float32):
        feature, _metadata = build_palm_feature(frame)
        features.append(feature)
    if not features:
        return np.zeros((0, PALM_FEATURE_DIM), dtype=np.float32)
    return np.asarray(features, dtype=np.float32)


def build_episode(retarget_path: Path, rollout_path: Path | None, episode_idx: int) -> Dict[str, Any]:
    payload = np.load(retarget_path, allow_pickle=True)
    if "landmarks" not in payload or "actions" not in payload:
        raise ValueError(f"Retarget NPZ must contain landmarks and actions: {retarget_path}")

    landmarks = np.asarray(payload["landmarks"], dtype=np.float32)
    actions = np.asarray(payload["actions"], dtype=np.float32)
    timestamps = (
        np.asarray(payload["timestamps"], dtype=np.float32)
        if "timestamps" in payload
        else np.arange(actions.shape[0], dtype=np.float32)
    )
    if landmarks.shape[0] != actions.shape[0]:
        raise ValueError(
            f"Landmark/action length mismatch in {retarget_path}: {landmarks.shape[0]} != {actions.shape[0]}"
        )

    observations = _features_from_landmarks(landmarks)
    if observations.shape[0] != actions.shape[0]:
        raise RuntimeError(f"Feature/action length mismatch in {retarget_path}")

    rollout_episode = _load_rollout_episode(rollout_path) if rollout_path else {}
    metrics = dict(rollout_episode.get("metrics", {}) or {})
    episode = {
        "observations": observations.astype(np.float32),
        "actions": actions.astype(np.float32),
        "timestamps": timestamps.astype(np.float32),
        "landmarks": landmarks.astype(np.float32),
        "success": bool(rollout_episode.get("success", False)),
        "terminal_success": bool(rollout_episode.get("terminal_success", False)),
        "metrics": metrics,
        "source_retarget": str(retarget_path),
        "source_rollout": str(rollout_path) if rollout_path else "",
        "episode_index": int(episode_idx),
    }
    if "source_frame_indices" in payload:
        episode["source_frame_indices"] = np.asarray(payload["source_frame_indices"], dtype=np.float32)
    if rollout_episode:
        for key in ("rewards", "dones", "infos", "placement_info"):
            if key in rollout_episode:
                episode[key] = rollout_episode[key]
    return episode


def save_report(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_ready(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert Shadow retarget traces into train_bc episodes")
    parser.add_argument(
        "--retarget",
        action="append",
        required=True,
        help="Retarget NPZ from retarget_palm_trace_to_shadow.py. Repeat for multiple episodes.",
    )
    parser.add_argument(
        "--rollout",
        action="append",
        default=[],
        help="Optional rollout NPZ aligned with --retarget. Repeat in the same order.",
    )
    parser.add_argument("--output", required=True, help="Output BC dataset NPZ")
    parser.add_argument("--report", default="", help="Optional JSON report path")
    parser.add_argument("--tag", default="real_hand_shadow_retarget", help="Dataset tag")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    retarget_paths = [Path(item) for item in args.retarget]
    rollout_paths = [Path(item) for item in args.rollout]
    if rollout_paths and len(rollout_paths) != len(retarget_paths):
        raise ValueError("--rollout must be provided the same number of times as --retarget")
    while len(rollout_paths) < len(retarget_paths):
        rollout_paths.append(None)

    episodes: List[Dict[str, Any]] = []
    source_metadata = []
    for idx, (retarget_path, rollout_path) in enumerate(zip(retarget_paths, rollout_paths)):
        if not retarget_path.exists():
            raise FileNotFoundError(retarget_path)
        if rollout_path and not rollout_path.exists():
            raise FileNotFoundError(rollout_path)
        episodes.append(build_episode(retarget_path, rollout_path, idx))
        source_metadata.append(_metadata_dict(np.load(retarget_path, allow_pickle=True)))

    total_steps = int(sum(item["actions"].shape[0] for item in episodes))
    obs_dim = int(episodes[0]["observations"].shape[1]) if episodes else PALM_FEATURE_DIM
    act_dim = int(episodes[0]["actions"].shape[1]) if episodes else 0
    all_features = np.concatenate([item["observations"] for item in episodes], axis=0)
    all_timestamps = np.concatenate([item["timestamps"] for item in episodes], axis=0)
    metadata = {
        "dataset_type": "vision_shadow_retarget_bc_dataset",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tag": args.tag,
        "num_episodes": int(len(episodes)),
        "obs_dim": obs_dim,
        "act_dim": act_dim,
        "max_steps": int(max(item["actions"].shape[0] for item in episodes)) if episodes else 0,
        "total_steps": total_steps,
        "observation_schema": "normalized_21_landmarks_plus_palm_frame_v1",
        "action_schema": "shadow_hand_normalized_action_v1",
        "task_name": "vision_shadow_retarget_bc",
        "success_rule": "supervised imitation of diagnostic heuristic retarget actions",
        "training_boundary": (
            "Diagnostic vision-to-Shadow imitation data. This does not imply camera calibration, "
            "IK, custom tendon-hand control, or a maintained benchmark baseline."
        ),
        "source_retarget_files": [str(path) for path in retarget_paths],
        "source_rollout_files": [str(path) if path else "" for path in rollout_paths],
        "source_retarget_metadata": source_metadata,
        "palm_feature_summary": summarize_palm_trace(all_features, all_timestamps),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, episodes=np.asarray(episodes, dtype=object), metadata=metadata)

    report_payload = {
        "output": str(output_path),
        "metadata": metadata,
        "episode_steps": [int(item["actions"].shape[0]) for item in episodes],
    }
    if args.report:
        save_report(Path(args.report), report_payload)

    print(f"Saved BC dataset: {output_path}")
    print(json.dumps(_json_ready({"episodes": len(episodes), "total_steps": total_steps, "obs_dim": obs_dim, "act_dim": act_dim}), indent=2))
    if args.report:
        print(f"Saved report: {args.report}")


if __name__ == "__main__":
    main()
