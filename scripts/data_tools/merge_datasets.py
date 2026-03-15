#!/usr/bin/env python3
"""Merge multiple expert NPZ datasets into a single dataset."""

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def load_dataset(path_str):
    """Load one expert dataset and return episodes plus metadata."""
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    payload = np.load(path, allow_pickle=True)
    if "episodes" not in payload or "metadata" not in payload:
        raise ValueError(f"Dataset missing required fields: {path}")

    episodes = list(payload["episodes"])
    metadata = payload["metadata"].item() if hasattr(payload["metadata"], "item") else payload["metadata"]
    return episodes, metadata


def main():
    parser = argparse.ArgumentParser(description="Merge multiple expert NPZ datasets")
    parser.add_argument("--inputs", type=str, nargs="+", required=True, help="Input dataset paths")
    parser.add_argument("--output", type=str, required=True, help="Merged output NPZ path")
    args = parser.parse_args()

    merged_episodes = []
    source_metadata = []
    obs_dim = None
    act_dim = None

    print("=" * 60)
    print("Merge Expert Datasets")
    print("=" * 60)

    for input_path in args.inputs:
        episodes, metadata = load_dataset(input_path)
        dataset_obs_dim = int(metadata.get("obs_dim", 0))
        dataset_act_dim = int(metadata.get("act_dim", 0))

        if obs_dim is None:
            obs_dim = dataset_obs_dim
            act_dim = dataset_act_dim
        elif obs_dim != dataset_obs_dim or act_dim != dataset_act_dim:
            raise ValueError(
                f"Dimension mismatch for {input_path}: "
                f"expected obs_dim={obs_dim}, act_dim={act_dim}, "
                f"got obs_dim={dataset_obs_dim}, act_dim={dataset_act_dim}"
            )

        merged_episodes.extend(episodes)
        source_metadata.append(
            {
                "path": input_path,
                "num_episodes": len(episodes),
                "placement_mode": metadata.get("placement_mode"),
                "max_steps": metadata.get("max_steps"),
            }
        )
        print(
            f"Loaded {input_path}: episodes={len(episodes)}, "
            f"placement_mode={metadata.get('placement_mode')}, max_steps={metadata.get('max_steps')}"
        )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    merged_metadata = {
        "num_episodes": len(merged_episodes),
        "obs_dim": int(obs_dim or 0),
        "act_dim": int(act_dim or 0),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "merged_v1",
        "sources": source_metadata,
    }

    np.savez_compressed(
        output_path,
        episodes=np.array(merged_episodes, dtype=object),
        metadata=merged_metadata,
    )

    print(f"Saved merged dataset to: {output_path}")
    print(f"  Episodes: {len(merged_episodes)}")
    print(f"  Obs dim: {merged_metadata['obs_dim']}")
    print(f"  Act dim: {merged_metadata['act_dim']}")


if __name__ == "__main__":
    main()
