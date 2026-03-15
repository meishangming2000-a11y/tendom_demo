#!/usr/bin/env python3
"""Validate the current catch-task setup without patching the environment."""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from scripts.common.grasp_workflow import configure_controller, place_object
from src.controllers import create_controller
from src.environments.shadow_grasp_env import ShadowGraspEnv


def _get_object_vertical_velocity(env):
    joint_dof_adr = env.model.jnt_dofadr[env.object_joint_id]
    return float(env.data.qvel[joint_dof_adr + 2])


def run_episode(env, controller, placement_jitter):
    """Run one expert catch episode and inspect fall-speed preservation."""
    if hasattr(controller, "reset"):
        controller.reset()

    env.reset()
    velocity_after_reset = _get_object_vertical_velocity(env)
    place_object(env, placement_mode="scene", placement_jitter=placement_jitter, verbose=False)
    velocity_after_placement = _get_object_vertical_velocity(env)

    if hasattr(controller, "start_grasp_sequence"):
        controller.start_grasp_sequence()

    done = False
    step_idx = 0
    info = {
        "object_on_floor": False,
        "grasp_contact_duration": 0,
    }
    max_grasp_duration = 0

    while not done and step_idx < env.max_steps:
        control_values = controller.compute_control(
            t=step_idx * env.control_timestep,
            grasp_strength=0.7,
            control_mode="position",
        )
        action = env._denormalize_action(control_values)
        _, _, done, info = env.step(action)
        step_idx += 1
        max_grasp_duration = max(max_grasp_duration, int(info.get("grasp_contact_duration", 0)))

    return {
        "success": bool(env.is_success()),
        "object_on_floor": bool(info.get("object_on_floor", False)),
        "max_grasp_duration": max_grasp_duration,
        "velocity_after_reset": velocity_after_reset,
        "velocity_after_placement": velocity_after_placement,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate catch-task physics and expert behavior")
    parser.add_argument("--episodes", type=int, default=5, help="Number of expert episodes to run")
    parser.add_argument("--max-steps", type=int, default=300, help="Maximum steps per episode")
    parser.add_argument("--fall-speed", type=float, default=-0.3, help="Initial object fall speed in m/s")
    parser.add_argument("--placement-jitter", type=float, default=0.002, help="Scene jitter in meters")
    parser.add_argument("--controller", type=str, default="enhanced", help="Expert controller name")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed")
    args = parser.parse_args()

    if args.seed is not None:
        np.random.seed(args.seed)

    env = ShadowGraspEnv(
        max_steps=args.max_steps,
        enable_catch_task=True,
        object_fall_speed=args.fall_speed,
    )
    controller = create_controller(args.controller, env.model, env.data)
    configure_controller(controller, enable_catch_task=True)

    results = []
    for episode_idx in range(args.episodes):
        result = run_episode(env, controller, args.placement_jitter)
        results.append(result)
        print(
            f"Episode {episode_idx + 1}: success={result['success']} "
            f"floor={result['object_on_floor']} "
            f"max_grasp={result['max_grasp_duration']} "
            f"vz_reset={result['velocity_after_reset']:.4f} "
            f"vz_place={result['velocity_after_placement']:.4f}"
        )

    success_rate = sum(1 for result in results if result["success"]) / len(results)
    print("\nSummary:")
    print(f"  Success rate: {success_rate:.1%}")
    print(f"  Avg vz after reset: {np.mean([result['velocity_after_reset'] for result in results]):.4f}")
    print(f"  Avg vz after placement: {np.mean([result['velocity_after_placement'] for result in results]):.4f}")


if __name__ == "__main__":
    main()
