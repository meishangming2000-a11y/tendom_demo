#!/usr/bin/env python3
"""Initialize a standardized arm-hand Stage1 training/evaluation run folder."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from arm_hand_stage1_run_artifacts import ROOT, initialize_run, write_manifest


DEFAULT_CONFIG = ROOT / "configs" / "stage2_pick_place_v0_5.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a standardized arm-hand Stage1 run folder.")
    parser.add_argument("--task", default="stage2_pick_place_v0_5")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-id", default=None, help="Optional explicit run id. Defaults to timestamp_seedNNN.")
    parser.add_argument("--notes", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = args.config.resolve() if args.config else None
    if config and not config.exists():
        raise FileNotFoundError(f"Config file does not exist: {config}")

    command_line = subprocess.list2cmdline(["python", *sys.argv])
    if args.dry_run:
        print("Would initialize run:")
        print(f"  task: {args.task}")
        print(f"  seed: {args.seed}")
        print(f"  config: {config}")
        print(f"  run_id: {args.run_id or '<timestamp_seed>'}")
        return 0

    run_dir = initialize_run(
        task=args.task,
        seed=args.seed,
        config_source=config,
        command_line=command_line,
        notes=args.notes,
        run_id=args.run_id,
    )
    write_manifest(run_dir)
    print(f"Run initialized: {run_dir}")
    print(f"Report: {run_dir / 'report.md'}")
    print(f"Config lock: {run_dir / 'config.lock.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
