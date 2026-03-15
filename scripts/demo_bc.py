#!/usr/bin/env python3
"""One-command showcase demo for the current BC grasping model."""

import argparse
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts import eval_bc
from scripts.common.grasp_workflow import get_success_rule, get_task_name
from src.environments.shadow_grasp_env import ShadowGraspEnv


def _get_task_defaults(enable_catch_task):
    """Return task-specific defaults for the BC demo."""
    if enable_catch_task:
        return {
            "model": "models/bc_catch_v2_j002_f030_40ep_h128.pth",
            "max_steps": 300,
            "placement_mode": "scene",
            "placement_jitter": 0.002,
            "viewer_step_sleep": 0.04,
            "viewer_hold_secs": 4.0,
            "object_fall_speed": -0.3,
            "finger_ramp_steps": 0,
            "finger_ramp_start_scale": 1.0,
        }

    return {
        "model": "models/bc_showcase_v5_success400_phase_h128_80ep.pth",
        "max_steps": 400,
        "placement_mode": "demo",
        "placement_jitter": 0.01,
        "viewer_step_sleep": 0.04,
        "viewer_hold_secs": 4.0,
        "object_fall_speed": -0.3,
        "finger_ramp_steps": 160,
        "finger_ramp_start_scale": 0.25,
    }


def _resolve_demo_args(args):
    """Fill unset CLI options from the current task defaults."""
    defaults = _get_task_defaults(args.enable_catch_task)
    if not args.model:
        args.model = defaults["model"]
    if args.max_steps is None:
        args.max_steps = defaults["max_steps"]
    if not args.placement_mode:
        args.placement_mode = defaults["placement_mode"]
    if args.placement_jitter is None:
        args.placement_jitter = defaults["placement_jitter"]
    if args.viewer_step_sleep is None:
        args.viewer_step_sleep = defaults["viewer_step_sleep"]
    if args.viewer_hold_secs is None:
        args.viewer_hold_secs = defaults["viewer_hold_secs"]
    if args.object_fall_speed is None:
        args.object_fall_speed = defaults["object_fall_speed"]
    if args.finger_ramp_steps is None:
        args.finger_ramp_steps = defaults["finger_ramp_steps"]
    if args.finger_ramp_start_scale is None:
        args.finger_ramp_start_scale = defaults["finger_ramp_start_scale"]
    return args


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the current showcase BC demo")
    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="Path to the BC checkpoint",
    )
    parser.add_argument("--max-steps", type=int, default=None, help="Maximum steps for the demo episode")
    parser.add_argument(
        "--placement-mode",
        type=str,
        default="",
        choices=["demo", "scene"],
        help="Object placement mode",
    )
    parser.add_argument(
        "--placement-jitter",
        type=float,
        default=None,
        help="Random object-position jitter in meters",
    )
    parser.add_argument(
        "--viewer-step-sleep",
        type=float,
        default=None,
        help="Seconds to sleep after each viewer frame",
    )
    parser.add_argument(
        "--viewer-hold-secs",
        type=float,
        default=None,
        help="Seconds to hold the final frame before closing the viewer",
    )
    parser.add_argument("--device", type=str, default="cpu", help="cpu or cuda")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed")
    parser.add_argument("--report", type=str, default="", help="Optional JSON report path")
    parser.add_argument("--enable-catch-task", action="store_true", help="Run the falling-object catch task")
    parser.add_argument("--object-fall-speed", type=float, default=None, help="Catch-task fall speed in m/s")
    parser.add_argument("--finger-ramp-steps", type=int, default=None, help="Optional finger action ramp length")
    parser.add_argument(
        "--finger-ramp-start-scale",
        type=float,
        default=None,
        help="Optional starting scale for the finger action ramp",
    )
    parser.add_argument("--no-viewer", action="store_true", help="Run the demo headlessly")

    args = parser.parse_args(argv)
    args = _resolve_demo_args(args)

    if args.seed is not None:
        np.random.seed(args.seed)

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA is not available, falling back to CPU.")
        args.device = "cpu"

    device = torch.device(args.device)
    model, metadata = eval_bc.load_bc_model(args.model, device)

    print("=" * 60)
    print("BC Showcase Demo")
    print("=" * 60)
    print(f"Task: {get_task_name(args.enable_catch_task)}")
    print(f"Model: {args.model}")
    print(f"Placement mode: {args.placement_mode}")
    print(f"Placement jitter: {args.placement_jitter:.4f} m")
    print(f"Max steps: {args.max_steps}")
    print(f"Viewer: {'disabled' if args.no_viewer else 'enabled'}")
    print(f"Viewer step sleep: {args.viewer_step_sleep:.3f}s")
    print(f"Viewer hold: {args.viewer_hold_secs:.1f}s")
    if args.finger_ramp_steps > 0:
        print(f"Finger ramp: {args.finger_ramp_start_scale:.2f} -> 1.00 over {args.finger_ramp_steps} steps")
    if args.enable_catch_task:
        print(f"Object fall speed: {args.object_fall_speed:.3f} m/s")

    env = ShadowGraspEnv(
        max_steps=args.max_steps,
        enable_catch_task=args.enable_catch_task,
        object_fall_speed=args.object_fall_speed,
    )
    result = eval_bc.run_policy_episode(
        model=model,
        env=env,
        device=device,
        metadata=metadata,
        max_steps=args.max_steps,
        with_viewer=not args.no_viewer,
        placement_mode=args.placement_mode,
        placement_jitter=args.placement_jitter,
        viewer_step_sleep=args.viewer_step_sleep,
        viewer_hold_seconds=args.viewer_hold_secs,
        finger_ramp_steps=args.finger_ramp_steps,
        finger_ramp_start_scale=args.finger_ramp_start_scale,
        verbose=True,
    )
    result["episode_idx"] = 0

    print(
        f"Result: {'success' if result['success'] else 'failure'} | "
        f"reward={result['total_reward']:.3f} | "
        f"max_grasp={result['max_grasp_contact_duration']} | "
        f"final_distance={result['final_distance']:.3f}"
    )

    summary = eval_bc.summarize_results([result])
    eval_bc.print_summary(summary)

    if args.report:
        config = {
            "model": args.model,
            "episodes": 1,
            "max_steps": args.max_steps,
            "placement_mode": args.placement_mode,
            "placement_jitter": args.placement_jitter,
            "enable_catch_task": args.enable_catch_task,
            "object_fall_speed": args.object_fall_speed,
            "device": args.device,
            "seed": args.seed,
            "viewer_step_sleep": args.viewer_step_sleep,
            "viewer_hold_secs": args.viewer_hold_secs,
            "finger_ramp_steps": args.finger_ramp_steps,
            "finger_ramp_start_scale": args.finger_ramp_start_scale,
            "task_name": get_task_name(args.enable_catch_task),
            "success_rule": get_success_rule(args.enable_catch_task),
            "training_metadata": metadata,
        }
        eval_bc.save_report(args.report, config, summary, [result])

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
