#!/usr/bin/env python3
"""Inspect action, success, and distance distributions for pre_grasp datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def load_dataset(data_path):
    """Load the dataset payload."""
    dataset_path = Path(data_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    payload = np.load(dataset_path, allow_pickle=True)
    episodes = payload["episodes"]
    raw_metadata = payload["metadata"].item() if hasattr(payload["metadata"], "item") else payload["metadata"]
    return episodes, dict(raw_metadata)


def _safe_mean(values, default=-1.0):
    """Return the mean or a fallback for empty lists."""
    return float(np.mean(values)) if values else float(default)


def summarize_dataset(episodes, metadata):
    """Build a compact summary over action, success, and distance metrics."""
    action_blocks = []
    success_count = 0
    total_steps = 0
    initial_position_errors = []
    min_position_errors = []
    final_position_errors = []
    position_error_improvements = []
    per_jitter = {}

    for episode in episodes:
        actions = np.asarray(episode["actions"], dtype=np.float32)
        metrics = dict(episode.get("metrics", {}) or {})
        placement_info = dict(episode.get("placement_info", {}) or {})
        infos = list(episode.get("infos", []) or [])
        success = bool(episode.get("success", False))
        jitter = float(placement_info.get("placement_jitter", 0.0))

        action_blocks.append(actions)
        success_count += int(success)
        total_steps += int(actions.shape[0])

        initial_error = float(metrics.get("initial_position_error", -1.0))
        min_error = float(metrics.get("min_position_error", -1.0))
        final_error = float(metrics.get("final_position_error", -1.0))
        improvement = float(metrics.get("position_error_improvement", 0.0))
        if infos and initial_error < 0:
            step_errors = [float(item["position_error"]) for item in infos if "position_error" in item]
            if step_errors:
                initial_error = float(step_errors[0])
                min_error = float(min(step_errors))
                final_error = float(step_errors[-1])
                improvement = float(initial_error - final_error)
        if initial_error >= 0:
            initial_position_errors.append(initial_error)
        if min_error >= 0:
            min_position_errors.append(min_error)
        if final_error >= 0:
            final_position_errors.append(final_error)
        position_error_improvements.append(improvement)

        bucket = per_jitter.setdefault(
            jitter,
            {
                "episodes": 0,
                "success_count": 0,
                "final_position_errors": [],
                "position_error_improvements": [],
            },
        )
        bucket["episodes"] += 1
        bucket["success_count"] += int(success)
        if final_error >= 0:
            bucket["final_position_errors"].append(final_error)
        bucket["position_error_improvements"].append(improvement)

    all_actions = np.concatenate(action_blocks, axis=0) if action_blocks else np.zeros((0, 0), dtype=np.float32)
    per_actuator_mean_abs = (
        np.mean(np.abs(all_actions), axis=0).tolist()
        if all_actions.size
        else []
    )
    top_actuators = [
        {"actuator": int(idx), "mean_abs_action": float(per_actuator_mean_abs[idx])}
        for idx in np.argsort(np.asarray(per_actuator_mean_abs))[::-1][:8]
    ]

    summary = {
        "task_name": metadata.get("task_name"),
        "num_episodes": len(episodes),
        "total_steps": total_steps,
        "success_count": success_count,
        "success_rate": success_count / len(episodes) if len(episodes) > 0 else 0.0,
        "action": {
            "shape": list(all_actions.shape),
            "min": float(all_actions.min()) if all_actions.size else 0.0,
            "max": float(all_actions.max()) if all_actions.size else 0.0,
            "mean": float(all_actions.mean()) if all_actions.size else 0.0,
            "std": float(all_actions.std()) if all_actions.size else 0.0,
            "mean_abs": float(np.mean(np.abs(all_actions))) if all_actions.size else 0.0,
            "near_zero_ratio_abs_lt_0p05": float(np.mean(np.abs(all_actions) < 0.05)) if all_actions.size else 0.0,
            "top_mean_abs_actuators": top_actuators,
        },
        "distance": {
            "avg_initial_position_error": _safe_mean(initial_position_errors),
            "avg_min_position_error": _safe_mean(min_position_errors),
            "avg_final_position_error": _safe_mean(final_position_errors),
            "avg_position_error_improvement": _safe_mean(position_error_improvements, default=0.0),
        },
        "per_jitter": [
            {
                "placement_jitter": jitter,
                "episodes": bucket["episodes"],
                "success_count": bucket["success_count"],
                "success_rate": bucket["success_count"] / bucket["episodes"] if bucket["episodes"] else 0.0,
                "avg_final_position_error": _safe_mean(bucket["final_position_errors"]),
                "avg_position_error_improvement": _safe_mean(bucket["position_error_improvements"], default=0.0),
            }
            for jitter, bucket in sorted(per_jitter.items())
        ],
        "metadata": metadata,
    }
    return summary


def print_summary(summary):
    """Print a readable summary."""
    print("=" * 60)
    print("Pre-Grasp Dataset Analysis")
    print("=" * 60)
    print(f"Task: {summary.get('task_name')}")
    print(f"Episodes: {summary['num_episodes']}")
    print(f"Total steps: {summary['total_steps']}")
    print(f"Success rate: {summary['success_rate']:.1%} ({summary['success_count']}/{summary['num_episodes']})")

    action = summary["action"]
    print("\nAction distribution")
    print(f"  Shape: {tuple(action['shape'])}")
    print(f"  Range: [{action['min']:.4f}, {action['max']:.4f}]")
    print(f"  Mean +/- std: {action['mean']:.4f} +/- {action['std']:.4f}")
    print(f"  Mean |action|: {action['mean_abs']:.4f}")
    print(f"  Near-zero ratio (|a| < 0.05): {action['near_zero_ratio_abs_lt_0p05']:.1%}")
    print("  Most active actuators:")
    for item in action["top_mean_abs_actuators"]:
        print(f"    actuator {item['actuator']:2d}: mean|a|={item['mean_abs_action']:.4f}")

    distance = summary["distance"]
    print("\nDistance distribution")
    print(f"  Avg initial position error: {distance['avg_initial_position_error']:.4f}")
    print(f"  Avg min position error: {distance['avg_min_position_error']:.4f}")
    print(f"  Avg final position error: {distance['avg_final_position_error']:.4f}")
    print(f"  Avg position error improvement: {distance['avg_position_error_improvement']:.4f}")

    print("\nQuick read")
    if distance["avg_position_error_improvement"] <= 0.002:
        print("  Warning: average position-error improvement is very small; this dataset may still be close to a hold-biased regime.")
    if action["near_zero_ratio_abs_lt_0p05"] >= 0.5:
        print("  Warning: more than half of action entries are near zero; check for weak reach supervision.")
    if distance["avg_final_position_error"] >= 0 and distance["avg_initial_position_error"] >= 0:
        print(
            "  Delta initial->final: "
            f"{distance['avg_initial_position_error'] - distance['avg_final_position_error']:.4f}"
        )

    print("\nPer-jitter breakdown")
    for item in summary["per_jitter"]:
        print(
            f"  jitter={item['placement_jitter']:.4f} | "
            f"success={item['success_rate']:.1%} ({item['success_count']}/{item['episodes']}) | "
            f"avg_final_position_error={item['avg_final_position_error']:.4f} | "
            f"avg_improvement={item['avg_position_error_improvement']:.4f}"
        )


def main():
    parser = argparse.ArgumentParser(description="Analyze a pre_grasp expert dataset")
    parser.add_argument("--data", type=str, required=True, help="Path to the dataset (.npz)")
    parser.add_argument("--report", type=str, default="", help="Optional JSON report path")
    args = parser.parse_args()

    episodes, metadata = load_dataset(args.data)
    summary = summarize_dataset(episodes, metadata)
    print_summary(summary)

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\nSaved analysis report to: {report_path}")


if __name__ == "__main__":
    main()
