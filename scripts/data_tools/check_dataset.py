#!/usr/bin/env python3
"""Inspect one expert dataset and print compact quality statistics."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def _safe_metadata(payload):
    metadata = payload["metadata"]
    return metadata.item() if hasattr(metadata, "item") else metadata


def analyze_dataset(data_path):
    """Load and summarize one dataset."""
    dataset_path = Path(data_path)
    print("=" * 60)
    print("Dataset Inspection")
    print("=" * 60)
    print(f"Dataset: {dataset_path}")

    if not dataset_path.exists():
        print("Error: dataset file does not exist.")
        return False

    try:
        payload = np.load(dataset_path, allow_pickle=True)
    except Exception as exc:
        print(f"Error: failed to load dataset: {exc}")
        return False

    required_keys = {"episodes", "metadata"}
    missing_keys = required_keys.difference(payload.files)
    if missing_keys:
        print(f"Error: missing required keys: {sorted(missing_keys)}")
        return False

    episodes = list(payload["episodes"])
    metadata = _safe_metadata(payload)

    print("\nMetadata:")
    for key in sorted(metadata):
        print(f"  {key}: {metadata[key]}")

    if not episodes:
        print("\nNo episodes found.")
        return True

    episode_lengths = np.array([len(episode["actions"]) for episode in episodes], dtype=np.int32)
    success_flags = np.array([bool(episode.get("success", False)) for episode in episodes], dtype=np.bool_)
    all_observations = np.concatenate([episode["observations"] for episode in episodes], axis=0)
    all_actions = np.concatenate([episode["actions"] for episode in episodes], axis=0)

    print("\nEpisodes:")
    print(f"  Count: {len(episodes)}")
    print(f"  Success rate: {success_flags.mean():.1%} ({success_flags.sum()}/{len(success_flags)})")
    print(f"  Length min/mean/max: {episode_lengths.min()} / {episode_lengths.mean():.1f} / {episode_lengths.max()}")

    print("\nObservations:")
    print(f"  Shape: {all_observations.shape}")
    print(f"  Range: [{all_observations.min():.4f}, {all_observations.max():.4f}]")
    print(f"  NaN count: {int(np.isnan(all_observations).sum())}")
    print(f"  Inf count: {int(np.isinf(all_observations).sum())}")

    print("\nActions:")
    print(f"  Shape: {all_actions.shape}")
    print(f"  Range: [{all_actions.min():.4f}, {all_actions.max():.4f}]")
    print(f"  Mean/std: {all_actions.mean():.4f} / {all_actions.std():.4f}")
    action_violations = int(((all_actions < -1.0) | (all_actions > 1.0)).sum())
    print(f"  Out-of-range values: {action_violations}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Inspect one expert dataset")
    parser.add_argument("--data", type=str, required=True, help="Path to the dataset (.npz)")
    args = parser.parse_args()
    raise SystemExit(0 if analyze_dataset(args.data) else 1)


if __name__ == "__main__":
    main()
