#!/usr/bin/env python3
"""Collect expert trajectories for behavior cloning."""

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.controllers import create_controller
from src.environments.shadow_grasp_env import ShadowGraspEnv
from scripts.common.grasp_workflow import configure_controller, get_success_rule, get_task_name, place_object


def collect_episode(
    env,
    controller,
    controller_name,
    max_steps=200,
    grasp_strength=0.7,
    placement_mode="demo",
    placement_jitter=0.0,
    early_stop_on_stable_grasp=False,
    stable_grasp_target_steps=None,
    post_success_padding=0,
    verbose=True,
):
    """Collect one expert rollout."""
    if hasattr(controller, "reset"):
        controller.reset()

    obs = env.reset()
    placement_info = place_object(
        env,
        placement_mode=placement_mode,
        placement_jitter=placement_jitter,
        verbose=verbose,
    )
    obs = env.get_obs()

    if hasattr(controller, "start_grasp_sequence"):
        controller.start_grasp_sequence()
    elif hasattr(controller, "set_grasping"):
        controller.set_grasping(True, strength=grasp_strength)
    elif hasattr(controller, "grasp_strength"):
        controller.grasp_strength = grasp_strength

    observations = []
    actions = []
    rewards = []
    dones = []
    infos = []

    done = False
    step_count = 0
    hold_mode_enabled = False
    max_contact_duration = 0
    grasp_contact_steps = 0
    max_grasp_contact_duration = 0
    stable_grasp_target_steps = int(
        stable_grasp_target_steps
        if stable_grasp_target_steps is not None
        else getattr(env, "success_contact_duration", 50)
    )
    stable_grasp_achieved = False
    first_success_step = None
    stop_after_step = None

    while not done and step_count < max_steps:
        observations.append(obs.copy())

        if hasattr(controller, "compute_control"):
            control_values = controller.compute_control(
                t=step_count * env.control_timestep,
                grasp_strength=grasp_strength,
                control_mode="position",
            )
            action = env._denormalize_action(control_values)
        else:
            action = np.random.uniform(-1.0, 1.0, env.nu)

        obs, reward, done, info = env.step(action)
        actions.append(action.copy())
        rewards.append(float(reward))
        dones.append(bool(done))
        infos.append(info.copy())

        step_count += 1
        max_contact_duration = max(max_contact_duration, int(info.get("contact_duration", 0)))
        if info.get("grasp_contact"):
            grasp_contact_steps += 1
        max_grasp_contact_duration = max(
            max_grasp_contact_duration,
            int(info.get("grasp_contact_duration", 0)),
        )
        if info.get("grasp_contact_duration", 0) >= getattr(env, "success_contact_duration", 50):
            stable_grasp_achieved = True
            if first_success_step is None:
                first_success_step = step_count
        if early_stop_on_stable_grasp and info.get("grasp_contact_duration", 0) >= stable_grasp_target_steps:
            if stop_after_step is None:
                stop_after_step = step_count + int(max(0, post_success_padding))
            if step_count >= stop_after_step:
                done = True

        if verbose and step_count % 50 == 0:
            print(
                f"  Step {step_count}: reward={reward:.3f}, distance={info['distance']:.3f}, "
                f"contact={'yes' if info['contact'] else 'no'}, "
                f"grasp={'yes' if info.get('grasp_contact') else 'no'}"
            )

        if (
            controller_name == "enhanced"
            and hasattr(controller, "set_grasping")
            and not getattr(controller, "is_grasping", True)
            and not hold_mode_enabled
        ):
            controller.set_grasping(False, strength=1.0)
            hold_mode_enabled = True

    episode_data = {
        "observations": np.array(observations, dtype=np.float32),
        "actions": np.array(actions, dtype=np.float32),
        "rewards": np.array(rewards, dtype=np.float32),
        "dones": np.array(dones, dtype=bool),
        "infos": infos,
        "steps": step_count,
        "success": bool(stable_grasp_achieved),
        "terminal_success": bool(env.is_success()) if hasattr(env, "is_success") else False,
        "placement_info": placement_info,
        "metrics": {
            "contact_steps": int(sum(1 for item in infos if item.get("contact"))),
            "max_contact_duration": int(max_contact_duration),
            "grasp_contact_steps": int(grasp_contact_steps),
            "max_grasp_contact_duration": int(max_grasp_contact_duration),
            "first_success_step": int(first_success_step) if first_success_step is not None else -1,
            "stable_grasp_target_steps": int(stable_grasp_target_steps),
            "early_stop_on_stable_grasp": bool(early_stop_on_stable_grasp),
            "final_distance": float(infos[-1]["distance"]) if infos else float(env._get_distance()),
            "object_height": float(infos[-1].get("object_height", env._get_object_height())) if infos else float(env._get_object_height()),
        },
    }
    return episode_data


def collect_multiple_episodes(
    env,
    controller,
    controller_name,
    num_episodes=10,
    max_steps=200,
    grasp_strength=0.7,
    placement_mode="demo",
    placement_jitter=0.0,
    early_stop_on_stable_grasp=False,
    stable_grasp_target_steps=None,
    post_success_padding=0,
):
    """Collect multiple expert episodes."""
    all_episodes = []

    for episode_idx in range(num_episodes):
        print(f"\nCollecting episode {episode_idx + 1}/{num_episodes}...")
        episode_data = collect_episode(
            env=env,
            controller=controller,
            controller_name=controller_name,
            max_steps=max_steps,
            grasp_strength=grasp_strength,
            placement_mode=placement_mode,
            placement_jitter=placement_jitter,
            early_stop_on_stable_grasp=early_stop_on_stable_grasp,
            stable_grasp_target_steps=stable_grasp_target_steps,
            post_success_padding=post_success_padding,
            verbose=True,
        )
        all_episodes.append(episode_data)

        metrics = episode_data["metrics"]
        print("  Episode summary:")
        print(f"    steps: {episode_data['steps']}")
        print(f"    success: {episode_data['success']}")
        print(f"    terminal_success: {episode_data.get('terminal_success', False)}")
        print(f"    total reward: {episode_data['rewards'].sum():.3f}")
        print(f"    final distance: {metrics['final_distance']:.3f}")
        print(f"    max any-contact duration: {metrics['max_contact_duration']}")
        print(f"    max stable-grasp duration: {metrics['max_grasp_contact_duration']}")

        time.sleep(0.05)

    return all_episodes


def summarize_episodes(all_episodes):
    """Build an aggregate summary over collected episodes."""
    total_episodes = len(all_episodes)
    success_count = sum(1 for episode in all_episodes if episode["success"])
    terminal_success_count = sum(1 for episode in all_episodes if episode.get("terminal_success", False))
    return {
        "episodes": total_episodes,
        "success_count": success_count,
        "success_rate": success_count / total_episodes if total_episodes else 0.0,
        "terminal_success_count": terminal_success_count,
        "terminal_success_rate": terminal_success_count / total_episodes if total_episodes else 0.0,
        "avg_steps": float(np.mean([episode["steps"] for episode in all_episodes])) if all_episodes else 0.0,
        "avg_reward": float(np.mean([episode["rewards"].sum() for episode in all_episodes])) if all_episodes else 0.0,
        "avg_final_distance": float(np.mean([episode["metrics"]["final_distance"] for episode in all_episodes])) if all_episodes else 0.0,
        "avg_max_contact_duration": float(np.mean([episode["metrics"]["max_contact_duration"] for episode in all_episodes])) if all_episodes else 0.0,
        "avg_max_grasp_contact_duration": float(np.mean([episode["metrics"]["max_grasp_contact_duration"] for episode in all_episodes])) if all_episodes else 0.0,
        "avg_first_success_step": float(
            np.mean(
                [
                    episode["metrics"]["first_success_step"]
                    for episode in all_episodes
                    if episode["metrics"]["first_success_step"] >= 0
                ]
            )
        ) if any(episode["metrics"]["first_success_step"] >= 0 for episode in all_episodes) else -1.0,
    }


def save_data(all_episodes, output_path, metadata):
    """Save collected trajectories to a compressed NPZ file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    save_dict = {
        "episodes": all_episodes,
        "metadata": metadata,
    }
    np.savez_compressed(output_file, **save_dict)
    print(f"\nSaved dataset to: {output_file}")
    print(f"  Episodes: {len(all_episodes)}")
    print(f"  Observation dim: {metadata.get('obs_dim', 0)}")
    print(f"  Action dim: {metadata.get('act_dim', 0)}")


def save_report(report_path, config, summary):
    """Save a JSON summary report next to the dataset if requested."""
    report_file = Path(report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": config,
        "summary": summary,
    }
    report_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved collection report to: {report_file}")


def main():
    """CLI entrypoint."""
    import argparse

    parser = argparse.ArgumentParser(description="Collect expert grasp demonstrations")
    parser.add_argument("--controller", type=str, default="enhanced", help="Controller type")
    parser.add_argument("--episodes", type=int, default=10, help="Number of episodes to collect")
    parser.add_argument("--output", type=str, default="data/expert_data.npz", help="Output NPZ path")
    parser.add_argument("--report", type=str, default="", help="Optional JSON summary path")
    parser.add_argument("--max-steps", type=int, default=200, help="Maximum steps per episode")
    parser.add_argument("--grasp-strength", type=float, default=0.7, help="Nominal grasp strength")
    parser.add_argument(
        "--placement-mode",
        type=str,
        default="demo",
        choices=["scene", "demo"],
        help="Object placement mode for collection",
    )
    parser.add_argument(
        "--placement-jitter",
        type=float,
        default=0.0,
        help="Random object-position jitter in meters",
    )
    parser.add_argument("--enable-catch-task", action="store_true", help="Enable the catch-task variant")
    parser.add_argument("--object-fall-speed", type=float, default=-0.3, help="Catch-task fall speed in m/s")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed")
    parser.add_argument(
        "--early-stop-on-stable-grasp",
        action="store_true",
        help="Stop static-grasp episodes shortly after reaching a stable grasp target",
    )
    parser.add_argument(
        "--stable-grasp-target-steps",
        type=int,
        default=None,
        help="Consecutive stable-grasp steps to target before early stopping",
    )
    parser.add_argument(
        "--post-success-padding",
        type=int,
        default=0,
        help="Additional steps to record after the stable-grasp target is reached",
    )

    args = parser.parse_args()

    if args.seed is not None:
        np.random.seed(args.seed)

    print("=" * 60)
    print("Expert Data Collection")
    print("=" * 60)
    print(f"Task: {get_task_name(args.enable_catch_task)}")
    print(f"Controller: {args.controller}")
    print(f"Episodes: {args.episodes}")
    print(f"Output: {args.output}")
    print(f"Max steps: {args.max_steps}")
    print(f"Placement mode: {args.placement_mode}")
    print(f"Placement jitter: {args.placement_jitter:.4f} m")
    print(f"Catch task: {'enabled' if args.enable_catch_task else 'disabled'}")
    if args.early_stop_on_stable_grasp:
        print(
            "Early stop on stable grasp: "
            f"target={args.stable_grasp_target_steps or 50}, padding={args.post_success_padding}"
        )

    env = ShadowGraspEnv(
        max_steps=args.max_steps,
        enable_catch_task=args.enable_catch_task,
        object_fall_speed=args.object_fall_speed,
    )

    controller = create_controller(args.controller, env.model, env.data)
    controller_profile = "default" if args.enable_catch_task else "expert_collection"
    configure_controller(
        controller,
        args.enable_catch_task,
        profile=controller_profile,
        max_steps=args.max_steps,
    )

    all_episodes = collect_multiple_episodes(
        env=env,
        controller=controller,
        controller_name=args.controller,
        num_episodes=args.episodes,
        max_steps=args.max_steps,
        grasp_strength=args.grasp_strength,
        placement_mode=args.placement_mode,
        placement_jitter=args.placement_jitter,
        early_stop_on_stable_grasp=args.early_stop_on_stable_grasp,
        stable_grasp_target_steps=args.stable_grasp_target_steps,
        post_success_padding=args.post_success_padding,
    )

    metadata = {
        "num_episodes": len(all_episodes),
        "obs_dim": int(all_episodes[0]["observations"].shape[1]) if all_episodes else 0,
        "act_dim": int(all_episodes[0]["actions"].shape[1]) if all_episodes else 0,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "env": "ShadowGraspEnv",
        "version": "2.0",
        "controller": args.controller,
        "max_steps": args.max_steps,
        "grasp_strength": args.grasp_strength,
        "placement_mode": args.placement_mode,
        "placement_jitter": args.placement_jitter,
        "enable_catch_task": args.enable_catch_task,
        "object_fall_speed": args.object_fall_speed,
        "task_name": get_task_name(args.enable_catch_task),
        "success_rule": get_success_rule(args.enable_catch_task),
        "controller_profile": controller_profile,
        "seed": args.seed,
        "early_stop_on_stable_grasp": args.early_stop_on_stable_grasp,
        "stable_grasp_target_steps": args.stable_grasp_target_steps,
        "post_success_padding": args.post_success_padding,
    }

    save_data(all_episodes, args.output, metadata)
    summary = summarize_episodes(all_episodes)

    print("\n" + "=" * 60)
    print("Collection Summary")
    print("=" * 60)
    print(f"Success rate: {summary['success_rate']:.1%} ({summary['success_count']}/{summary['episodes']})")
    print(
        "Terminal success rate: "
        f"{summary['terminal_success_rate']:.1%} "
        f"({summary['terminal_success_count']}/{summary['episodes']})"
    )
    print(f"Average steps: {summary['avg_steps']:.1f}")
    print(f"Average reward: {summary['avg_reward']:.3f}")
    print(f"Average final distance: {summary['avg_final_distance']:.3f}")
    print(f"Average max any-contact duration: {summary['avg_max_contact_duration']:.1f}")
    print(f"Average max stable-grasp duration: {summary['avg_max_grasp_contact_duration']:.1f}")
    if summary["avg_first_success_step"] >= 0:
        print(f"Average first success step: {summary['avg_first_success_step']:.1f}")

    if args.report:
        config = {
            "controller": args.controller,
            "episodes": args.episodes,
            "max_steps": args.max_steps,
            "placement_mode": args.placement_mode,
            "placement_jitter": args.placement_jitter,
            "enable_catch_task": args.enable_catch_task,
            "object_fall_speed": args.object_fall_speed,
            "task_name": get_task_name(args.enable_catch_task),
            "success_rule": get_success_rule(args.enable_catch_task),
            "controller_profile": controller_profile,
            "seed": args.seed,
        }
        save_report(args.report, config, summary)


if __name__ == "__main__":
    main()
