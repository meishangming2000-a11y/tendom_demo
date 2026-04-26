#!/usr/bin/env python3
"""
Collect expert trajectories for behavior cloning.

Canonical example:
    python scripts/collect_expert_data.py --task pre_grasp --output data/expert_pre_grasp_mixed_v2.npz --report reports/expert_pre_grasp_mixed_v2.json
"""

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.controllers import create_controller
from src.environments.shadow_grasp_env import ShadowGraspEnv
from scripts.common.grasp_workflow import (
    compute_pre_grasp_expert_action,
    configure_controller,
    get_success_rule,
    get_task_name,
    place_object,
)


def resolve_structured_task_name(task_name_arg="", structured_task_name=None):
    """Prefer --task while keeping --structured-task backward compatible."""
    return (task_name_arg or structured_task_name or "").strip() or None


def default_dataset_path_for_task(structured_task_name):
    """Return a task-specific dataset path without changing legacy defaults."""
    if structured_task_name:
        return f"data/expert_{structured_task_name}.npz"
    return "data/expert_data.npz"


def parse_float_list(raw_value):
    """Parse a comma-separated list of floats."""
    if raw_value is None:
        return []

    values = []
    for item in str(raw_value).split(","):
        item = item.strip()
        if not item:
            continue
        values.append(float(item))
    return values


def parse_vec3(raw_value, default_value):
    """Parse a comma-separated xyz tuple while preserving a default."""
    if raw_value is None or str(raw_value).strip() == "":
        return tuple(float(v) for v in default_value)

    values = parse_float_list(raw_value)
    if len(values) != 3:
        raise ValueError(f"Expected 3 comma-separated values, got: {raw_value}")
    return tuple(float(v) for v in values)


def build_pre_grasp_task_kwargs(structured_task_name, args):
    """Return task kwargs for pre_grasp without affecting other tasks."""
    if structured_task_name != "pre_grasp":
        return {}

    return {
        "target_offset": parse_vec3(
            getattr(args, "pre_grasp_target_offset", ""),
            default_value=(0.008, 0.0165, 0.0),
        ),
    }


def build_pre_grasp_policy_config(structured_task_name, args):
    """Return the expert policy config used for pre_grasp collection."""
    if structured_task_name != "pre_grasp":
        return {}

    return {
        "gain_scale": float(args.pre_grasp_gain_scale),
        "clip_scale": float(args.pre_grasp_clip_scale),
        "start_bias": parse_vec3(
            getattr(args, "pre_grasp_start_bias", ""),
            default_value=(0.01, 0.0, -0.005),
        ),
    }


def collect_episode(
    env,
    controller,
    controller_name,
    max_steps=200,
    grasp_strength=0.7,
    placement_mode="demo",
    placement_jitter=0.0,
    pre_grasp_policy_config=None,
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
        pre_grasp_start_bias=(pre_grasp_policy_config or {}).get("start_bias"),
    )
    obs = env.get_obs()

    if env.get_task_name() == "pre_grasp":
        pass
    elif hasattr(controller, "start_grasp_sequence"):
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
    task_success_steps = 0
    stable_grasp_target_steps = int(
        stable_grasp_target_steps
        if stable_grasp_target_steps is not None
        else getattr(env, "success_contact_duration", 50)
    )
    episode_success = False
    first_success_step = None
    stop_after_step = None
    initial_position_error = None
    min_position_error = None

    while not done and step_count < max_steps:
        observations.append(obs.copy())

        if env.get_task_name() == "pre_grasp":
            action, _ = compute_pre_grasp_expert_action(
                env,
                gain_scale=(pre_grasp_policy_config or {}).get("gain_scale", 1.0),
                clip_scale=(pre_grasp_policy_config or {}).get("clip_scale", 1.0),
            )
        elif hasattr(controller, "compute_control"):
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
        if info.get("success", False):
            episode_success = True
            task_success_steps += 1
            if first_success_step is None:
                first_success_step = step_count
        if "position_error" in info:
            position_error = float(info["position_error"])
            if initial_position_error is None:
                initial_position_error = position_error
            min_position_error = (
                position_error
                if min_position_error is None
                else min(min_position_error, position_error)
            )
        if (
            early_stop_on_stable_grasp
            and env.task is None
            and info.get("grasp_contact_duration", 0) >= stable_grasp_target_steps
        ):
            if stop_after_step is None:
                stop_after_step = step_count + int(max(0, post_success_padding))
            if step_count >= stop_after_step:
                done = True
        elif (
            env.task is not None
            and info.get("success", False)
            and stop_after_step is None
            and post_success_padding > 0
        ):
            stop_after_step = step_count + int(max(0, post_success_padding))
        elif stop_after_step is not None and step_count >= stop_after_step:
            done = True

        if verbose and step_count % 50 == 0:
            distance_label = (
                f"position_error={float(info.get('position_error', 0.0)):.4f}"
                if env.get_task_name() == "pre_grasp"
                else f"distance={info['distance']:.3f}"
            )
            print(
                f"  Step {step_count}: reward={reward:.3f}, {distance_label}, "
                f"contact={'yes' if info['contact'] else 'no'}, "
                f"grasp={'yes' if info.get('grasp_contact') else 'no'}, "
                f"success={bool(info.get('success', False))}"
            )
        if verbose and info.get("success", False) and first_success_step == step_count:
            print(f"  success = task.check_success(...) -> True at step {step_count}")

        if (
            controller_name == "enhanced"
            and env.get_task_name() != "pre_grasp"
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
        "success": bool(episode_success),
        "terminal_success": bool(env.is_success()) if hasattr(env, "is_success") else False,
        "placement_info": placement_info,
        "metrics": {
            "contact_steps": int(sum(1 for item in infos if item.get("contact"))),
            "max_contact_duration": int(max_contact_duration),
            "grasp_contact_steps": int(grasp_contact_steps),
            "max_grasp_contact_duration": int(max_grasp_contact_duration),
            "task_success_steps": int(task_success_steps),
            "first_success_step": int(first_success_step) if first_success_step is not None else -1,
            "stable_grasp_target_steps": int(stable_grasp_target_steps),
            "early_stop_on_stable_grasp": bool(early_stop_on_stable_grasp),
            "final_distance": float(infos[-1]["distance"]) if infos else float(env._get_distance()),
            "initial_position_error": float(initial_position_error) if initial_position_error is not None else -1.0,
            "min_position_error": float(min_position_error) if min_position_error is not None else -1.0,
            "final_position_error": float(infos[-1].get("position_error", -1.0)) if infos else -1.0,
            "position_error_improvement": (
                float(initial_position_error - infos[-1].get("position_error", initial_position_error))
                if infos and initial_position_error is not None and "position_error" in infos[-1]
                else 0.0
            ),
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
    placement_jitters=None,
    pre_grasp_policy_config=None,
    early_stop_on_stable_grasp=False,
    stable_grasp_target_steps=None,
    post_success_padding=0,
):
    """Collect multiple expert episodes."""
    all_episodes = []
    jitter_schedule = list(placement_jitters or [placement_jitter])

    for episode_idx in range(num_episodes):
        episode_jitter = float(jitter_schedule[episode_idx % len(jitter_schedule)])
        print(f"\nCollecting episode {episode_idx + 1}/{num_episodes}...")
        print(f"  Placement jitter for this episode: {episode_jitter:.4f} m")
        episode_data = collect_episode(
            env=env,
            controller=controller,
            controller_name=controller_name,
            max_steps=max_steps,
            grasp_strength=grasp_strength,
            placement_mode=placement_mode,
            placement_jitter=episode_jitter,
            pre_grasp_policy_config=pre_grasp_policy_config,
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
        if metrics.get("final_position_error", -1.0) >= 0:
            print(f"    final position error: {metrics['final_position_error']:.4f}")
            print(f"    min position error: {metrics['min_position_error']:.4f}")
        print(f"    max any-contact duration: {metrics['max_contact_duration']}")
        print(f"    max stable-grasp duration: {metrics['max_grasp_contact_duration']}")

        time.sleep(0.05)

    return all_episodes


def summarize_episodes(all_episodes):
    """Build an aggregate summary over collected episodes."""
    total_episodes = len(all_episodes)
    success_count = sum(1 for episode in all_episodes if episode["success"])
    terminal_success_count = sum(1 for episode in all_episodes if episode.get("terminal_success", False))
    jitter_breakdown = {}
    for episode in all_episodes:
        jitter = float(episode.get("placement_info", {}).get("placement_jitter", 0.0))
        bucket = jitter_breakdown.setdefault(
            jitter,
            {"episodes": 0, "success_count": 0, "terminal_success_count": 0, "final_position_errors": []},
        )
        bucket["episodes"] += 1
        bucket["success_count"] += int(bool(episode.get("success", False)))
        bucket["terminal_success_count"] += int(bool(episode.get("terminal_success", False)))
        final_position_error = float(episode.get("metrics", {}).get("final_position_error", -1.0))
        if final_position_error >= 0:
            bucket["final_position_errors"].append(final_position_error)

    summary = {
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
        "avg_initial_position_error": float(
            np.mean(
                [
                    episode["metrics"]["initial_position_error"]
                    for episode in all_episodes
                    if episode["metrics"].get("initial_position_error", -1.0) >= 0
                ]
            )
        ) if any(episode["metrics"].get("initial_position_error", -1.0) >= 0 for episode in all_episodes) else -1.0,
        "avg_min_position_error": float(
            np.mean(
                [
                    episode["metrics"]["min_position_error"]
                    for episode in all_episodes
                    if episode["metrics"].get("min_position_error", -1.0) >= 0
                ]
            )
        ) if any(episode["metrics"].get("min_position_error", -1.0) >= 0 for episode in all_episodes) else -1.0,
        "avg_final_position_error": float(
            np.mean(
                [
                    episode["metrics"]["final_position_error"]
                    for episode in all_episodes
                    if episode["metrics"].get("final_position_error", -1.0) >= 0
                ]
            )
        ) if any(episode["metrics"].get("final_position_error", -1.0) >= 0 for episode in all_episodes) else -1.0,
        "avg_position_error_improvement": float(
            np.mean([episode["metrics"].get("position_error_improvement", 0.0) for episode in all_episodes])
        ) if all_episodes else 0.0,
    }

    summary["jitter_breakdown"] = [
        {
            "placement_jitter": jitter,
            "episodes": bucket["episodes"],
            "success_count": bucket["success_count"],
            "success_rate": bucket["success_count"] / bucket["episodes"] if bucket["episodes"] else 0.0,
            "terminal_success_count": bucket["terminal_success_count"],
            "terminal_success_rate": bucket["terminal_success_count"] / bucket["episodes"] if bucket["episodes"] else 0.0,
            "avg_final_position_error": (
                float(np.mean(bucket["final_position_errors"]))
                if bucket["final_position_errors"]
                else -1.0
            ),
        }
        for jitter, bucket in sorted(jitter_breakdown.items())
    ]
    return summary


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
    parser.add_argument("--output", type=str, default="", help="Output NPZ path")
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
    parser.add_argument(
        "--placement-jitters",
        type=str,
        default="",
        help="Optional comma-separated jitter schedule, e.g. 0.02,0.04",
    )
    parser.add_argument("--enable-catch-task", action="store_true", help="Enable the catch-task variant")
    parser.add_argument("--object-fall-speed", type=float, default=-0.3, help="Catch-task fall speed in m/s")
    parser.add_argument(
        "--observation-mode",
        type=str,
        default="oracle",
        choices=["oracle", "deployable"],
        help="Observation layer to expose through env.get_obs()",
    )
    parser.add_argument(
        "--task",
        type=str,
        default="",
        choices=["", "pre_grasp", "stable_grasp", "lift_and_hold"],
        help="Preferred alias for --structured-task",
    )
    parser.add_argument(
        "--structured-task",
        type=str,
        default="",
        choices=["", "pre_grasp", "stable_grasp", "lift_and_hold"],
        help="Optional task-driven interface override",
    )
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
    parser.add_argument(
        "--pre-grasp-gain-scale",
        type=float,
        default=1.0,
        help="Global gain scale for the minimal pre_grasp reach controller",
    )
    parser.add_argument(
        "--pre-grasp-clip-scale",
        type=float,
        default=1.0,
        help="Global clip scale for the minimal pre_grasp reach controller",
    )
    parser.add_argument(
        "--pre-grasp-start-bias",
        type=str,
        default="0.01,0.0,-0.005",
        help="Comma-separated xyz bias used by pre_grasp demo placement",
    )
    parser.add_argument(
        "--pre-grasp-target-offset",
        type=str,
        default="0.008,0.0165,0.0",
        help="Comma-separated xyz target offset for the pre_grasp task",
    )

    args = parser.parse_args()
    structured_task_name = resolve_structured_task_name(
        task_name_arg=args.task,
        structured_task_name=args.structured_task,
    )
    output_path = args.output or default_dataset_path_for_task(structured_task_name)
    placement_jitters = parse_float_list(args.placement_jitters) or [float(args.placement_jitter)]
    pre_grasp_task_kwargs = build_pre_grasp_task_kwargs(structured_task_name, args)
    pre_grasp_policy_config = build_pre_grasp_policy_config(structured_task_name, args)

    if args.seed is not None:
        np.random.seed(args.seed)

    print("=" * 60)
    print("Expert Data Collection")
    print("=" * 60)
    print(f"Task: {get_task_name(args.enable_catch_task, structured_task_name=structured_task_name)}")
    print(f"Controller: {args.controller}")
    print(f"Episodes: {args.episodes}")
    print(f"Output: {output_path}")
    print(f"Max steps: {args.max_steps}")
    print(f"Placement mode: {args.placement_mode}")
    if len(placement_jitters) == 1:
        print(f"Placement jitter: {placement_jitters[0]:.4f} m")
    else:
        print(f"Placement jitters: {', '.join(f'{item:.4f}' for item in placement_jitters)} m")
    print(f"Catch task: {'enabled' if args.enable_catch_task else 'disabled'}")
    print(f"Observation mode: {args.observation_mode}")
    if structured_task_name:
        print(f"Structured task: {structured_task_name}")
    if structured_task_name == "pre_grasp":
        print(
            "Pre-grasp expert config: "
            f"gain_scale={pre_grasp_policy_config['gain_scale']:.3f}, "
            f"clip_scale={pre_grasp_policy_config['clip_scale']:.3f}, "
            f"start_bias={pre_grasp_policy_config['start_bias']}, "
            f"target_offset={pre_grasp_task_kwargs['target_offset']}"
        )
    if args.early_stop_on_stable_grasp:
        print(
            "Early stop on stable grasp: "
            f"target={args.stable_grasp_target_steps or 50}, padding={args.post_success_padding}"
        )

    env = ShadowGraspEnv(
        max_steps=args.max_steps,
        enable_catch_task=args.enable_catch_task,
        object_fall_speed=args.object_fall_speed,
        task_name=structured_task_name,
        observation_mode=args.observation_mode,
        task_kwargs=pre_grasp_task_kwargs,
    )
    resolved_task_kwargs = (
        env.task.get_task_config()
        if env.task is not None and hasattr(env.task, "get_task_config")
        else pre_grasp_task_kwargs
    )
    resolved_task_spec = (
        env.task.get_task_spec()
        if env.task is not None and hasattr(env.task, "get_task_spec")
        else {}
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
        placement_jitter=placement_jitters[0],
        placement_jitters=placement_jitters,
        pre_grasp_policy_config=pre_grasp_policy_config,
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
        "placement_jitter": placement_jitters[0] if len(placement_jitters) == 1 else "mixed",
        "placement_jitters": placement_jitters,
        "enable_catch_task": args.enable_catch_task,
        "object_fall_speed": args.object_fall_speed,
        "observation_mode": args.observation_mode,
        "structured_task_name": structured_task_name,
        "task_name": get_task_name(args.enable_catch_task, structured_task_name=structured_task_name),
        "success_rule": get_success_rule(args.enable_catch_task, structured_task_name=structured_task_name),
        "controller_profile": controller_profile,
        "seed": args.seed,
        "early_stop_on_stable_grasp": args.early_stop_on_stable_grasp,
        "stable_grasp_target_steps": args.stable_grasp_target_steps,
        "post_success_padding": args.post_success_padding,
        "task_kwargs": resolved_task_kwargs,
        "task_spec": resolved_task_spec,
        "pre_grasp_policy_config": pre_grasp_policy_config,
    }

    save_data(all_episodes, output_path, metadata)
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
    if summary["avg_final_position_error"] >= 0:
        print(f"Average initial position error: {summary['avg_initial_position_error']:.4f}")
        print(f"Average min position error: {summary['avg_min_position_error']:.4f}")
        print(f"Average final position error: {summary['avg_final_position_error']:.4f}")
        print(f"Average position error improvement: {summary['avg_position_error_improvement']:.4f}")
    if summary.get("jitter_breakdown"):
        print("Per-jitter summary:")
        for item in summary["jitter_breakdown"]:
            jitter_line = (
                f"  jitter={item['placement_jitter']:.4f} | "
                f"success={item['success_rate']:.1%} ({item['success_count']}/{item['episodes']})"
            )
            if item["avg_final_position_error"] >= 0:
                jitter_line += f" | avg_final_position_error={item['avg_final_position_error']:.4f}"
            print(jitter_line)

    if args.report:
        config = {
            "controller": args.controller,
            "episodes": args.episodes,
            "max_steps": args.max_steps,
            "placement_mode": args.placement_mode,
            "placement_jitter": placement_jitters[0] if len(placement_jitters) == 1 else "mixed",
            "placement_jitters": placement_jitters,
            "enable_catch_task": args.enable_catch_task,
            "object_fall_speed": args.object_fall_speed,
            "task_name": get_task_name(args.enable_catch_task, structured_task_name=structured_task_name),
            "success_rule": get_success_rule(args.enable_catch_task, structured_task_name=structured_task_name),
            "controller_profile": controller_profile,
            "seed": args.seed,
            "task_kwargs": resolved_task_kwargs,
            "task_spec": resolved_task_spec,
            "pre_grasp_policy_config": pre_grasp_policy_config,
        }
        save_report(args.report, config, summary)


if __name__ == "__main__":
    main()
