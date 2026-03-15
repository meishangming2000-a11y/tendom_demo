#!/usr/bin/env python3
"""Run the canonical catch-and-hold baseline pipeline end to end."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_step(command):
    """Run one subprocess step and stop the pipeline if it fails."""
    print("\n" + "=" * 80)
    print("Running:")
    print(" ".join(command))
    print("=" * 80)
    subprocess.run(command, check=True)


def build_paths(tag, episodes, eval_episodes, max_steps, epochs, hidden_dim):
    """Build the standard output paths for a catch baseline run."""
    dataset_path = Path(f"data/expert_{tag}_{episodes}x{max_steps}.npz")
    dataset_report = Path(f"reports/expert_{tag}_{episodes}x{max_steps}.json")
    model_suffix = f"{epochs}ep_h{hidden_dim}"
    model_path = Path(f"models/bc_{tag}_{model_suffix}.pth")
    eval_report = Path(f"reports/bc_{tag}_{model_suffix}_eval_{eval_episodes}x{max_steps}.json")
    return dataset_path, dataset_report, model_path, eval_report


def main():
    parser = argparse.ArgumentParser(description="Run the canonical catch baseline pipeline")
    parser.add_argument("--tag", type=str, default="catch_v1_j002_f030", help="Tag used in output filenames")
    parser.add_argument("--episodes", type=int, default=20, help="Number of expert episodes to collect")
    parser.add_argument("--eval-episodes", type=int, default=10, help="Number of BC evaluation episodes")
    parser.add_argument("--max-steps", type=int, default=300, help="Maximum steps per episode")
    parser.add_argument("--placement-jitter", type=float, default=0.002, help="Scene spawn jitter in meters")
    parser.add_argument("--object-fall-speed", type=float, default=-0.3, help="Initial fall speed in m/s")
    parser.add_argument("--epochs", type=int, default=30, help="BC training epochs")
    parser.add_argument("--batch-size", type=int, default=128, help="BC batch size")
    parser.add_argument("--hidden-dim", type=int, default=128, help="BC hidden layer width")

    args = parser.parse_args()

    dataset_path, dataset_report, model_path, eval_report = build_paths(
        tag=args.tag,
        episodes=args.episodes,
        eval_episodes=args.eval_episodes,
        max_steps=args.max_steps,
        epochs=args.epochs,
        hidden_dim=args.hidden_dim,
    )

    python = sys.executable

    collect_cmd = [
        python,
        "scripts/collect_expert_data.py",
        "--enable-catch-task",
        "--episodes",
        str(args.episodes),
        "--max-steps",
        str(args.max_steps),
        "--placement-mode",
        "scene",
        "--placement-jitter",
        str(args.placement_jitter),
        "--object-fall-speed",
        str(args.object_fall_speed),
        "--output",
        str(dataset_path),
        "--report",
        str(dataset_report),
    ]
    train_cmd = [
        python,
        "scripts/train_bc.py",
        "--data",
        str(dataset_path),
        "--success-only",
        "--epochs",
        str(args.epochs),
        "--batch-size",
        str(args.batch_size),
        "--hidden-dim",
        str(args.hidden_dim),
        "--output",
        str(model_path),
    ]
    eval_cmd = [
        python,
        "scripts/eval_bc.py",
        "--model",
        str(model_path),
        "--enable-catch-task",
        "--episodes",
        str(args.eval_episodes),
        "--no-viewer",
        "--max-steps",
        str(args.max_steps),
        "--placement-mode",
        "scene",
        "--placement-jitter",
        str(args.placement_jitter),
        "--object-fall-speed",
        str(args.object_fall_speed),
        "--report",
        str(eval_report),
    ]

    print("Catch baseline configuration:")
    print(f"  tag: {args.tag}")
    print(f"  episodes: {args.episodes}")
    print(f"  eval_episodes: {args.eval_episodes}")
    print(f"  max_steps: {args.max_steps}")
    print(f"  placement_jitter: {args.placement_jitter:.4f} m")
    print(f"  object_fall_speed: {args.object_fall_speed:.3f} m/s")
    print(f"  epochs: {args.epochs}")
    print(f"  batch_size: {args.batch_size}")
    print(f"  hidden_dim: {args.hidden_dim}")

    run_step(collect_cmd)
    run_step(train_cmd)
    run_step(eval_cmd)

    print("\nArtifacts:")
    print(f"  dataset: {dataset_path}")
    print(f"  dataset_report: {dataset_report}")
    print(f"  model: {model_path}")
    print(f"  eval_report: {eval_report}")


if __name__ == "__main__":
    main()
