#!/usr/bin/env python3
"""Build a BC dataset that uses open/close semantic observations."""

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

from vision.hand_open_close import (
    OPEN_CLOSE_FEATURE_DIM,
    OPEN_CLOSE_FEATURE_NAMES,
    json_ready,
    open_close_features_from_landmarks,
    summarize_open_close_features,
)
from vision.palm_landmarks import build_palm_feature, summarize_palm_trace


def _load_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _features_from_landmarks(landmarks: np.ndarray) -> np.ndarray:
    return np.asarray([build_palm_feature(frame)[0] for frame in landmarks], dtype=np.float32)


def _mask_from_segment(payload: np.lib.npyio.NpzFile, segment: Dict[str, Any]) -> np.ndarray:
    landmarks = np.asarray(payload["landmarks"], dtype=np.float32)
    if not segment:
        return np.ones((landmarks.shape[0],), dtype=bool)
    start = int(segment.get("start_frame", 0))
    end = int(segment.get("end_frame_exclusive", landmarks.shape[0]))
    if "source_frame_indices" in payload:
        source_indices = np.asarray(payload["source_frame_indices"], dtype=np.float32)
        return (source_indices >= float(start)) & (source_indices < float(end))
    start = max(0, min(start, landmarks.shape[0]))
    end = max(start, min(end, landmarks.shape[0]))
    mask = np.zeros((landmarks.shape[0],), dtype=bool)
    mask[start:end] = True
    return mask


def build_episode(item: Dict[str, Any], episode_idx: int, full_episode: bool) -> Dict[str, Any]:
    retarget_path = Path(item["retarget"])
    payload = np.load(retarget_path, allow_pickle=True)
    landmarks = np.asarray(payload["landmarks"], dtype=np.float32)
    actions = np.asarray(payload["actions"], dtype=np.float32)
    timestamps = (
        np.asarray(payload["timestamps"], dtype=np.float32)
        if "timestamps" in payload
        else np.arange(actions.shape[0], dtype=np.float32)
    )
    if landmarks.shape[0] != actions.shape[0]:
        raise ValueError(f"Landmark/action mismatch in {retarget_path}")
    mask = np.ones((landmarks.shape[0],), dtype=bool)
    if not full_episode:
        mask = _mask_from_segment(payload, item.get("suggested_segment", {}))
    if not np.any(mask):
        raise ValueError(f"Empty selected segment for {retarget_path}")
    selected_landmarks = landmarks[mask]
    selected_actions = actions[mask]
    selected_timestamps = timestamps[mask]
    if selected_timestamps.size:
        selected_timestamps = selected_timestamps - selected_timestamps[0]

    open_close = open_close_features_from_landmarks(selected_landmarks)
    palm = _features_from_landmarks(selected_landmarks)
    episode = {
        "observations": open_close.astype(np.float32),
        "open_close_observations": open_close.astype(np.float32),
        "palm_observations": palm.astype(np.float32),
        "actions": selected_actions.astype(np.float32),
        "timestamps": selected_timestamps.astype(np.float32),
        "landmarks": selected_landmarks.astype(np.float32),
        "success": bool((item.get("rollout_summary") or {}).get("success", False)),
        "terminal_success": bool((item.get("rollout_summary") or {}).get("terminal_success", False)),
        "metrics": (item.get("rollout_summary") or {}).get("metrics", {}),
        "source_retarget": str(retarget_path),
        "source_video": item.get("video", ""),
        "episode_index": int(episode_idx),
        "manifest_status": item.get("status", ""),
        "review_reasons": item.get("review_reasons", []),
        "selected_segment": item.get("suggested_segment", {}),
    }
    if "source_frame_indices" in payload:
        episode["source_frame_indices"] = np.asarray(payload["source_frame_indices"], dtype=np.float32)[mask]
    return episode


def save_report(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build open/close semantic BC dataset")
    parser.add_argument("--manifest", required=True, help="Manifest from build_open_close_manifest.py")
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", default="")
    parser.add_argument("--tag", default="open_close_v1_shadow_retarget")
    parser.add_argument("--include-review", action="store_true", help="Include review-flagged videos")
    parser.add_argument("--full-episodes", action="store_true", help="Ignore suggested segment windows")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    manifest = _load_manifest(Path(args.manifest))
    items = []
    for item in manifest.get("items", []):
        if item.get("status") == "usable" or args.include_review:
            if item.get("retarget") and Path(item["retarget"]).exists():
                items.append(item)
    if not items:
        raise RuntimeError("No manifest entries selected for dataset")

    episodes = [build_episode(item, idx, full_episode=bool(args.full_episodes)) for idx, item in enumerate(items)]
    total_steps = int(sum(episode["actions"].shape[0] for episode in episodes))
    all_open_close = np.concatenate([episode["open_close_observations"] for episode in episodes], axis=0)
    all_palm = np.concatenate([episode["palm_observations"] for episode in episodes], axis=0)
    all_timestamps = np.concatenate([episode["timestamps"] for episode in episodes], axis=0)
    metadata = {
        "dataset_type": "open_close_shadow_retarget_bc_dataset",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tag": args.tag,
        "num_episodes": int(len(episodes)),
        "obs_dim": OPEN_CLOSE_FEATURE_DIM,
        "open_close_obs_dim": OPEN_CLOSE_FEATURE_DIM,
        "palm_obs_dim": int(all_palm.shape[1]) if all_palm.size else 0,
        "act_dim": int(episodes[0]["actions"].shape[1]) if episodes else 0,
        "max_steps": int(max(episode["actions"].shape[0] for episode in episodes)),
        "total_steps": total_steps,
        "observation_schema": "hand_open_close_feature_v1",
        "open_close_feature_names": list(OPEN_CLOSE_FEATURE_NAMES),
        "action_schema": "shadow_hand_normalized_action_v1",
        "task_name": "open_close_shadow_retarget_bc",
        "success_rule": "supervised imitation of diagnostic heuristic Shadow retarget actions",
        "training_boundary": (
            "Intermediate open/close visual features to Shadow diagnostic actions. "
            "This is not a calibrated custom tendon-hand controller."
        ),
        "source_manifest": str(Path(args.manifest)),
        "selected_videos": [item.get("video_name", Path(item.get("video", "")).name) for item in items],
        "open_close_summary": summarize_open_close_features(all_open_close, all_timestamps),
        "palm_feature_summary": summarize_palm_trace(all_palm, all_timestamps),
        "full_episodes": bool(args.full_episodes),
        "include_review": bool(args.include_review),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, episodes=np.asarray(episodes, dtype=object), metadata=metadata)
    report = {
        "output": str(output),
        "metadata": metadata,
        "episode_steps": [int(episode["actions"].shape[0]) for episode in episodes],
    }
    if args.report:
        save_report(Path(args.report), report)
    print(f"Saved open/close BC dataset: {output}")
    print(json.dumps(json_ready({"episodes": len(episodes), "total_steps": total_steps, "obs_dim": OPEN_CLOSE_FEATURE_DIM}), indent=2))
    if args.report:
        print(f"Saved report: {args.report}")


if __name__ == "__main__":
    main()
