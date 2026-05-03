#!/usr/bin/env python3
"""Attach a visual palm trace to an existing expert dataset."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_npz_payload(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    return np.load(path, allow_pickle=True)


def _metadata_dict(payload) -> dict:
    raw = payload["metadata"]
    return dict(raw.item() if hasattr(raw, "item") else raw)


def _resample_features(features: np.ndarray, total_steps: int) -> np.ndarray:
    if total_steps <= 0:
        return np.zeros((0, features.shape[1]), dtype=np.float32)
    if features.shape[0] == total_steps:
        return features.astype(np.float32)
    if features.shape[0] == 0:
        raise ValueError("Palm trace has zero frames")

    src_x = np.linspace(0.0, 1.0, num=features.shape[0], dtype=np.float32)
    dst_x = np.linspace(0.0, 1.0, num=total_steps, dtype=np.float32)
    out = np.zeros((total_steps, features.shape[1]), dtype=np.float32)
    for col in range(features.shape[1]):
        out[:, col] = np.interp(dst_x, src_x, features[:, col]).astype(np.float32)
    return out


def _slice_sequential(features: np.ndarray, total_steps: int, allow_repeat_last: bool) -> np.ndarray:
    if features.shape[0] >= total_steps:
        return features[:total_steps].astype(np.float32)
    if not allow_repeat_last:
        raise ValueError(
            f"Palm trace has {features.shape[0]} frames but dataset needs {total_steps} steps. "
            "Use --mode stretch or --allow-repeat-last."
        )
    if features.shape[0] == 0:
        raise ValueError("Palm trace has zero frames")
    pad = np.repeat(features[-1:, :], total_steps - features.shape[0], axis=0)
    return np.concatenate([features, pad], axis=0).astype(np.float32)


def attach_features(args: argparse.Namespace) -> None:
    dataset_path = Path(args.dataset)
    palm_path = Path(args.palm_trace)
    output_path = Path(args.output)

    dataset_payload = _load_npz_payload(dataset_path)
    palm_payload = _load_npz_payload(palm_path)

    episodes = [dict(item) for item in dataset_payload["episodes"]]
    metadata = _metadata_dict(dataset_payload)
    palm_metadata = _metadata_dict(palm_payload)
    features = np.asarray(palm_payload["features"], dtype=np.float32)

    lengths = [int(np.asarray(ep[args.base_observation_field]).shape[0]) for ep in episodes]
    total_steps = int(sum(lengths))
    if args.mode == "stretch":
        aligned = _resample_features(features, total_steps)
    else:
        aligned = _slice_sequential(features, total_steps, args.allow_repeat_last)

    cursor = 0
    for episode, length in zip(episodes, lengths):
        visual_obs = aligned[cursor: cursor + length]
        cursor += length
        episode[args.field] = visual_obs.astype(np.float32)
        if args.fused_field:
            base_obs = np.asarray(episode[args.base_observation_field], dtype=np.float32)
            episode[args.fused_field] = np.concatenate([base_obs, visual_obs], axis=1).astype(np.float32)

    metadata["vision_palm_trace"] = {
        "source_dataset": str(palm_path),
        "source_metadata": palm_metadata,
        "alignment_mode": args.mode,
        "field": args.field,
        "fused_field": args.fused_field,
        "feature_dim": int(features.shape[1]),
        "total_aligned_steps": total_steps,
    }
    if args.fused_field:
        metadata[f"{args.fused_field}_dim"] = int(episodes[0][args.fused_field].shape[1]) if episodes else 0
    metadata[f"{args.field}_dim"] = int(features.shape[1])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        episodes=np.asarray(episodes, dtype=object),
        metadata=metadata,
    )
    print(f"Saved dataset with palm trace: {output_path}")
    print(f"  episodes: {len(episodes)}")
    print(f"  aligned steps: {total_steps}")
    print(f"  visual field: {args.field} ({features.shape[1]} dims)")
    if args.fused_field:
        print(f"  fused field: {args.fused_field} ({metadata[f'{args.fused_field}_dim']} dims)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Attach a palm trace to an expert dataset")
    parser.add_argument("--dataset", required=True, help="Existing expert dataset NPZ")
    parser.add_argument("--palm-trace", required=True, help="Palm trace NPZ from collect_palm_trace.py")
    parser.add_argument("--output", required=True, help="Output dataset NPZ")
    parser.add_argument("--field", default="vision_palm_observations", help="Episode field for visual features")
    parser.add_argument("--fused-field", default="fused_observations", help="Optional fused observation field; empty disables")
    parser.add_argument("--base-observation-field", default="observations", help="Base episode observation field")
    parser.add_argument("--mode", choices=["sequential", "stretch"], default="stretch", help="Alignment mode")
    parser.add_argument("--allow-repeat-last", action="store_true", help="Pad short sequential traces with the last frame")
    args = parser.parse_args()
    attach_features(args)


if __name__ == "__main__":
    main()
