#!/usr/bin/env python3
"""Generate a compact markdown inventory for datasets in the project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _load_metadata(dataset_path):
    payload = np.load(dataset_path, allow_pickle=True)
    episodes = list(payload["episodes"])
    metadata = payload["metadata"]
    metadata = metadata.item() if hasattr(metadata, "item") else metadata
    success_count = sum(1 for episode in episodes if bool(episode.get("success", False)))
    avg_steps = float(np.mean([len(episode["actions"]) for episode in episodes])) if episodes else 0.0
    return episodes, metadata, success_count, avg_steps


def build_inventory(data_dir):
    """Collect summary rows for every dataset under the given directory."""
    rows = []
    for dataset_path in sorted(Path(data_dir).glob("*.npz")):
        try:
            episodes, metadata, success_count, avg_steps = _load_metadata(dataset_path)
        except Exception as exc:
            rows.append(
                {
                    "name": dataset_path.name,
                    "task": "load_failed",
                    "episodes": "-",
                    "success_rate": "-",
                    "avg_steps": "-",
                    "notes": str(exc),
                }
            )
            continue

        episode_count = len(episodes)
        success_rate = (success_count / episode_count) if episode_count else 0.0
        rows.append(
            {
                "name": dataset_path.name,
                "task": metadata.get("task_name", "unknown"),
                "episodes": str(episode_count),
                "success_rate": f"{success_rate:.1%}",
                "avg_steps": f"{avg_steps:.1f}",
                "notes": json.dumps(
                    {
                        "placement_mode": metadata.get("placement_mode"),
                        "success_rule": metadata.get("success_rule"),
                    },
                    ensure_ascii=True,
                ),
            }
        )
    return rows


def write_report(output_path, rows):
    """Write the inventory as a markdown table."""
    lines = [
        "# Dataset Inventory",
        "",
        "| Dataset | Task | Episodes | Success Rate | Avg Steps | Notes |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['task']} | {row['episodes']} | "
            f"{row['success_rate']} | {row['avg_steps']} | {row['notes']} |"
        )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote dataset inventory to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate a markdown inventory of local datasets")
    parser.add_argument("--data-dir", type=str, default="data", help="Directory containing .npz datasets")
    parser.add_argument("--output", type=str, default="reports/dataset_inventory.md", help="Markdown report path")
    args = parser.parse_args()

    rows = build_inventory(args.data_dir)
    write_report(args.output, rows)


if __name__ == "__main__":
    main()
