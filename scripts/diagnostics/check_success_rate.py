#!/usr/bin/env python3
"""Inspect success-rate results from either NPZ datasets or JSON demo reports."""

import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _print_summary(source_label, total_episodes, success_count, avg_steps,
                   avg_contact_rate=None, avg_max_contact_duration=None,
                   avg_grasp_contact_rate=None, avg_max_grasp_contact_duration=None):
    """Print a compact success summary."""
    success_rate = (success_count / total_episodes * 100) if total_episodes else 0.0
    print(f"\nSummary for: {source_label}")
    print(f"  Episodes: {total_episodes}")
    print(f"  Successful episodes: {success_count}")
    print(f"  Success rate: {success_rate:.1f}%")
    print(f"  Average steps/episode: {avg_steps:.1f}")
    if avg_contact_rate is not None:
        print(f"  Average valid contact ratio: {avg_contact_rate:.1%}")
    if avg_max_contact_duration is not None:
        print(f"  Average max valid contact duration: {avg_max_contact_duration:.1f}")
    if avg_grasp_contact_rate is not None:
        print(f"  Average stable-grasp ratio: {avg_grasp_contact_rate:.1%}")
    if avg_max_grasp_contact_duration is not None:
        print(f"  Average max stable-grasp duration: {avg_max_grasp_contact_duration:.1f}")

    return success_rate


def _check_npz(dataset_path):
    """Inspect success rate stored in an NPZ dataset."""
    data = np.load(dataset_path, allow_pickle=True)
    episodes = data["episodes"]

    success_count = 0
    episode_lengths = []

    for idx, episode in enumerate(episodes):
        success = bool(episode["success"])
        steps = int(episode["steps"])
        episode_lengths.append(steps)
        if success:
            success_count += 1

        if idx < 3:
            print(f"  Episode {idx}: steps={steps}, success={success}")

    return _print_summary(
        source_label=str(dataset_path),
        total_episodes=len(episodes),
        success_count=success_count,
        avg_steps=float(np.mean(episode_lengths)) if episode_lengths else 0.0,
    )


def _check_json(report_path):
    """Inspect success rate stored in a JSON batch-evaluation report."""
    payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
    episodes = payload.get("episodes", [])
    summary = payload.get("summary", {})

    for episode in episodes[:3]:
        max_grasp_contact_duration = episode.get(
            "max_grasp_contact_duration",
            episode.get("max_contact_duration", 0),
        )
        print(
            "  Episode {episode_idx}: steps={steps}, success={success}, "
            "max_grasp={max_grasp_contact_duration}".format(
                episode_idx=episode.get("episode_idx", -1),
                steps=episode.get("steps", 0),
                success=episode.get("success", False),
                max_grasp_contact_duration=max_grasp_contact_duration,
            )
        )

    if summary:
        return _print_summary(
            source_label=str(report_path),
            total_episodes=int(summary.get("episodes", len(episodes))),
            success_count=int(summary.get("success_count", 0)),
            avg_steps=float(summary.get("avg_steps", 0.0)),
            avg_contact_rate=float(summary.get("avg_contact_rate", 0.0)),
            avg_max_contact_duration=float(summary.get("avg_max_contact_duration", 0.0)),
            avg_grasp_contact_rate=float(summary.get("avg_grasp_contact_rate", 0.0)),
            avg_max_grasp_contact_duration=float(summary.get("avg_max_grasp_contact_duration", 0.0)),
        )

    success_count = sum(1 for episode in episodes if episode.get("success"))
    avg_steps = float(np.mean([episode.get("steps", 0) for episode in episodes])) if episodes else 0.0
    avg_contact_rate = (
        float(np.mean([episode.get("contact_rate", 0.0) for episode in episodes]))
        if episodes else 0.0
    )
    avg_max_contact_duration = (
        float(np.mean([episode.get("max_contact_duration", 0.0) for episode in episodes]))
        if episodes else 0.0
    )
    avg_grasp_contact_rate = (
        float(np.mean([episode.get("grasp_contact_rate", 0.0) for episode in episodes]))
        if episodes else 0.0
    )
    avg_max_grasp_contact_duration = (
        float(np.mean([episode.get("max_grasp_contact_duration", episode.get("max_contact_duration", 0.0)) for episode in episodes]))
        if episodes else 0.0
    )
    return _print_summary(
        source_label=str(report_path),
        total_episodes=len(episodes),
        success_count=success_count,
        avg_steps=avg_steps,
        avg_contact_rate=avg_contact_rate,
        avg_max_contact_duration=avg_max_contact_duration,
        avg_grasp_contact_rate=avg_grasp_contact_rate,
        avg_max_grasp_contact_duration=avg_max_grasp_contact_duration,
    )


def check_success_rate(path_str):
    """Read either an NPZ dataset or a JSON evaluation report."""
    path = Path(path_str)
    print(f"Checking success rate from: {path}")

    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")

    if path.suffix.lower() == ".json":
        return _check_json(path)
    if path.suffix.lower() == ".npz":
        return _check_npz(path)

    raise ValueError(f"Unsupported file type: {path.suffix}. Use .npz or .json")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check success-rate statistics")
    parser.add_argument("--data", type=str, required=True, help="Path to an NPZ dataset or JSON report")
    args = parser.parse_args()

    check_success_rate(args.data)
