#!/usr/bin/env python3
"""Run a minimal task-level smoke path for pre_grasp -> stable_grasp contracts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.environments.shadow_grasp_env import ShadowGraspEnv
from tasks.transitions import TransitionEvaluationInput, evaluate_pre_grasp_to_stable_grasp


def _run_pre_grasp_transition_path(max_steps: int) -> dict:
    env = ShadowGraspEnv(max_steps=max_steps, task_name="pre_grasp")
    try:
        env.reset()
        zero_action = np.zeros(env.nu, dtype=np.float32)
        _, _, _, info = env.step(zero_action)

        transition_input = dict(info.get("pre_to_stable_transition_input", {}))
        transition_spec = dict(
            info.get("pre_grasp_task_spec", {}).get("transition_to_stable_grasp", {})
        )
        decision = evaluate_pre_grasp_to_stable_grasp(
            TransitionEvaluationInput(
                transition_name="pre_grasp_to_stable_grasp",
                source_task="pre_grasp",
                target_task="stable_grasp",
                source_info=transition_input,
                transition_spec=transition_spec,
                source_task_config=dict(info.get("pre_grasp_task_config", {})),
                current_step=int(info.get("step", 0)),
            )
        )
        return {
            "task_name": "pre_grasp",
            "transition_input_fields": sorted(transition_input.keys()),
            "transition_input": transition_input,
            "transition_contract": info.get("pre_grasp_task_spec", {}).get(
                "transition_to_stable_grasp_contract",
                {},
            ),
            "transition_decision": decision.to_payload(),
        }
    finally:
        env.close()


def _run_stable_grasp_evaluation_path(max_steps: int) -> dict:
    env = ShadowGraspEnv(max_steps=max_steps, task_name="stable_grasp")
    try:
        env.reset()
        zero_action = np.zeros(env.nu, dtype=np.float32)
        _, _, _, info = env.step(zero_action)

        return {
            "task_name": "stable_grasp",
            "evaluation_contract": info.get("stable_grasp_evaluation_contract", {}),
            "entry_snapshot_contract": info.get("stable_grasp_entry_snapshot_contract", {}),
            "entry_snapshot": info.get("stable_grasp_entry_snapshot", {}),
            "evaluation": info.get("stable_grasp_evaluation", {}),
            "official_metrics": info.get("stable_grasp_official_metrics", {}),
            "debug_metric_keys": sorted(
                list((info.get("stable_grasp_debug_metrics") or {}).keys())
            ),
        }
    finally:
        env.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Minimal smoke path for task-level transition and evaluation contracts"
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=2,
        help="Maximum episode steps for each environment instance",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional JSON output path",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indent level",
    )
    args = parser.parse_args()

    payload = {
        "smoke_path": "pre_grasp_info -> transition_evaluator -> stable_grasp_evaluate_state",
        "backend": "shadow_backend_temporary",
        "pre_grasp_transition_sample": _run_pre_grasp_transition_path(args.max_steps),
        "stable_grasp_evaluation_sample": _run_stable_grasp_evaluation_path(args.max_steps),
    }

    text = json.dumps(payload, indent=args.indent, ensure_ascii=False)
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
