#!/usr/bin/env python3
"""
Grasp demo and batch evaluation entrypoint.

Single episode:
    python scripts/demo_grasp.py --steps 1000

Batch evaluation:
    python scripts/demo_grasp.py --no-viewer --episodes 20 --report reports/demo_eval.json
"""

import json
import os
import sys
import time
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.common.grasp_workflow import (
    compute_pre_grasp_expert_action,
    configure_controller,
    get_success_rule,
    get_task_name,
    place_object,
)
from src.controllers import create_controller
from src.environments.shadow_grasp_env import ShadowGraspEnv


def _configure_controller(controller, enable_catch_task, profile="default", max_steps=None):
    """Apply demo timings to the controller."""
    if enable_catch_task:
        print("  Catch task timing enabled")
    else:
        print(f"  Demo timing enabled (profile: {profile})")
    configure_controller(
        controller,
        enable_catch_task,
        profile=profile,
        max_steps=max_steps,
    )


def _create_env_and_controller(
    max_steps,
    enable_catch_task,
    object_fall_speed,
    controller_name,
    controller_profile="default",
    observation_mode="oracle",
    structured_task_name=None,
):
    """Create a fresh environment/controller pair."""
    print("Creating environment...")
    env = ShadowGraspEnv(
        max_steps=max_steps,
        enable_catch_task=enable_catch_task,
        object_fall_speed=object_fall_speed,
        task_name=structured_task_name,
        observation_mode=observation_mode,
    )

    print(f"Creating controller '{controller_name}'...")
    controller = create_controller(controller_name, env.model, env.data)
    _configure_controller(
        controller,
        enable_catch_task,
        profile=controller_profile,
        max_steps=max_steps,
    )
    return env, controller


def _resolve_structured_task_name(task_name_arg="", structured_task_name=None):
    """Prefer the new --task alias while preserving the legacy --structured-task flag."""
    return (task_name_arg or structured_task_name or "").strip() or None


def _print_pre_grasp_pose_debug(step_count, info, action=None):
    """Emit task-space pose debug for pre-grasp episodes."""
    palm_pos = np.asarray(info.get("current_palm_position", []), dtype=np.float32)
    target_pos = np.asarray(info.get("target_palm_position", []), dtype=np.float32)
    object_pos = np.asarray(info.get("object_position", []), dtype=np.float32)
    if palm_pos.size != 3 or target_pos.size != 3 or object_pos.size != 3:
        return

    print(
        f"Step {step_count:3d}: success = task.check_success(...) -> {bool(info.get('success', False))} | "
        f"hold={int(info.get('pre_grasp_hold_steps', 0))}/{int(info.get('pre_grasp_required_hold_steps', 0))} | "
        f"distance={float(info.get('position_error', 0.0)):.4f} | "
        f"ori_err={float(info.get('orientation_error_rad', 0.0)):.4f}"
    )
    print(f"  palm_pose(position):   {np.array2string(palm_pos, precision=4)}")
    print(f"  target_pose(position): {np.array2string(target_pos, precision=4)}")
    print(f"  object_pose(position): {np.array2string(object_pos, precision=4)}")
    if action is not None:
        print(
            f"  action stats: min={float(np.min(action)):.3f}, "
            f"max={float(np.max(action)):.3f}, std={float(np.std(action)):.3f}"
        )


def _run_grasp_episode(env, controller, max_steps, with_viewer=False, verbose=True,
                       placement_mode="demo", placement_jitter=0.0, structured_task_name=None):
    """Run one grasp episode and return metrics."""
    if hasattr(controller, "reset"):
        controller.reset()

    if verbose:
        print("\nResetting environment...")
    env.reset()

    placement_info = place_object(
        env,
        placement_mode=placement_mode,
        placement_jitter=placement_jitter,
        verbose=verbose,
    )

    if verbose:
        print(f"\nObject position: {env._get_object_position()}")
        print(f"Hand position: {env._get_hand_position()}")
        print(f"Initial distance: {env._get_distance():.3f}")

    viewer = None
    if with_viewer:
        try:
            import mujoco.viewer

            viewer = mujoco.viewer.launch_passive(env.model, env.data)
            print("Viewer started. Press space if the viewer is paused.")
            time.sleep(0.5)
        except Exception as exc:
            print(f"Viewer failed to start: {exc}")
            viewer = None

    if verbose:
        print("\nStarting grasp demo...")
        if structured_task_name == "pre_grasp":
            print("Task-only rollout: hold current hand pose and evaluate pre_grasp success.")
        else:
            print("Stages: approach -> close_fingers -> lift")

    if structured_task_name != "pre_grasp" and hasattr(controller, "start_grasp_sequence"):
        controller.start_grasp_sequence()

    done = False
    step_count = 0
    contact_history = []
    grasp_contact_history = []
    phase_history = []
    reward_history = []
    max_contact_duration = 0
    max_grasp_contact_duration = 0
    hold_mode_enabled = False
    first_success_step = None
    last_info = {
        "distance": env._get_distance(),
        "contact": False,
        "contact_duration": 0,
        "grasp_contact": False,
        "grasp_contact_duration": 0,
        "object_height": env._get_object_height(),
        "object_on_floor": False,
        "success": False,
    }

    while not done and step_count < max_steps:
        step_count += 1
        if structured_task_name == "pre_grasp":
            action, _pose_debug = compute_pre_grasp_expert_action(env)
        else:
            control_values = controller.compute_control(
                t=step_count * env.control_timestep,
                control_mode="position",
            )
            action = env._denormalize_action(control_values)
        _, reward, done, info = env.step(action)

        last_info = info
        phase_history.append(controller.grasp_phase)
        contact_history.append(info["contact"])
        grasp_contact_history.append(bool(info.get("grasp_contact")))
        reward_history.append(float(reward))
        max_contact_duration = max(max_contact_duration, int(info.get("contact_duration", 0)))
        max_grasp_contact_duration = max(
            max_grasp_contact_duration,
            int(info.get("grasp_contact_duration", 0)),
        )
        if info.get("success") and first_success_step is None:
            first_success_step = step_count

        if verbose and structured_task_name == "pre_grasp" and (
            step_count <= 5 or step_count % 10 == 0 or info.get("success")
        ):
            _print_pre_grasp_pose_debug(step_count, info, action=action)
        elif verbose and step_count % 20 == 0:
            phase = controller.grasp_phase
            phase_timer = controller.grasp_phase_timer
            phase_duration = controller.phase_durations.get(phase, 100)
            progress = min(1.0, phase_timer / max(1, phase_duration))
            print(
                f"Step {step_count:3d}: phase={phase:15s} progress={progress:.1%}, "
                f"distance={info['distance']:.3f}, contact={'yes' if info['contact'] else 'no'}, "
                f"grasp={'yes' if info.get('grasp_contact') else 'no'}, "
                f"reward={reward:.3f}"
            )

        if viewer is not None:
            viewer.sync()
            time.sleep(0.01)

        if (
            structured_task_name != "pre_grasp"
            and not controller.is_grasping
            and not hold_mode_enabled
        ):
            if verbose:
                print(f"\nSequence finished. Switching to hold mode until step limit {max_steps}.")
            controller.set_grasping(False, strength=1.0)
            hold_mode_enabled = True

    if viewer is not None:
        viewer.close()

    phase_counts = {}
    for phase in phase_history:
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

    total_steps = step_count
    contact_steps = sum(contact_history)
    contact_rate = contact_steps / total_steps if total_steps else 0.0
    grasp_contact_steps = sum(grasp_contact_history)
    grasp_contact_rate = grasp_contact_steps / total_steps if total_steps else 0.0

    return {
        "success": bool(last_info.get("success", env.is_success())),
        "steps": int(total_steps),
        "task_name": env.get_task_name(),
        "first_success_step": int(first_success_step) if first_success_step is not None else -1,
        "contact_steps": int(contact_steps),
        "contact_rate": float(contact_rate),
        "max_contact_duration": int(max_contact_duration),
        "grasp_contact_steps": int(grasp_contact_steps),
        "grasp_contact_rate": float(grasp_contact_rate),
        "max_grasp_contact_duration": int(max_grasp_contact_duration),
        "final_distance": float(env._get_distance()),
        "final_legacy_distance": float(env._get_distance()),
        "final_phase": controller.grasp_phase,
        "phase_counts": phase_counts,
        "total_reward": float(sum(reward_history)),
        "object_height": float(last_info.get("object_height", env._get_object_height())),
        "object_on_floor": bool(last_info.get("object_on_floor", False)),
        "finger_contact_count": int(last_info.get("finger_contact_count", 0)),
        "finger_contact_groups": list(last_info.get("finger_contact_groups", [])),
        "palm_only_contact": bool(last_info.get("palm_only_contact", False)),
        "final_task_distance": float(last_info.get("position_error", 0.0)),
        "position_error": float(last_info.get("position_error", 0.0)),
        "orientation_error_rad": float(last_info.get("orientation_error_rad", 0.0)),
        "target_palm_position": list(last_info.get("target_palm_position", [])),
        "current_palm_position": list(last_info.get("current_palm_position", [])),
        "placement_info": placement_info,
        "repositioned_object": bool(placement_info.get("repositioned", False)),
    }


def _print_episode_summary(result, header="Demo Summary"):
    """Print a human-readable episode summary."""
    print("\n" + "=" * 60)
    print(header)
    print("=" * 60)
    print(f"Steps: {result['steps']}")
    print(f"Any-contact steps: {result['contact_steps']} ({result['contact_rate']:.1%})")
    print(f"Stable-grasp steps: {result['grasp_contact_steps']} ({result['grasp_contact_rate']:.1%})")
    print(f"Max any-contact duration: {result['max_contact_duration']} steps")
    print(f"Max stable-grasp duration: {result['max_grasp_contact_duration']} steps")
    if result.get("task_name") == "pre_grasp":
        print(f"Final task-space distance: {result.get('final_task_distance', 0.0):.4f}")
        print(f"Final legacy hand-body distance: {result.get('final_legacy_distance', result['final_distance']):.3f}")
    else:
        print(f"Final distance: {result['final_distance']:.3f}")
    print(f"Object height: {result['object_height']:.3f}")
    print(f"Success: {result['success']}")
    if result.get("first_success_step", -1) >= 0:
        print(f"First success step: {result['first_success_step']}")
    print(f"Final phase: {result['final_phase']}")
    print(f"Final finger groups: {result['finger_contact_groups']}")
    print(f"Total reward: {result['total_reward']:.3f}")
    if result.get("task_name") == "pre_grasp":
        print(f"Final position error: {result.get('position_error', 0.0):.4f}")
        print(f"Final orientation error: {result.get('orientation_error_rad', 0.0):.4f}")

    print("\nPhase distribution:")
    total_steps = max(1, result["steps"])
    for phase, count in sorted(result["phase_counts"].items()):
        print(f"  {phase}: {count} steps ({count / total_steps:.1%})")

    if result["success"]:
        if result["object_on_floor"]:
            print("\n[Success] Valid contact criterion was satisfied, but the object ended on the floor.")
        else:
            print("\n[Success] The active task success criterion was satisfied.")
    else:
        print("\n[Warning] The active task success criterion was not satisfied.")
        if result.get("task_name") == "pre_grasp":
            print("  Reason: the palm pose never stayed within the target tolerance for enough steps.")
        elif result["contact_steps"] == 0:
            print("  Reason: no valid palm/finger contact was detected.")
        elif result["max_grasp_contact_duration"] < 50:
            print("  Reason: palm contact plus thumb and at least three finger groups did not last for 50 steps.")
        elif result["object_on_floor"]:
            print("  Reason: the object touched the floor before the hold criterion was satisfied.")
        else:
            print("  Reason: other grasp condition failed.")


def _summarize_batch_results(episode_results):
    """Aggregate per-episode metrics."""
    total_episodes = len(episode_results)
    success_count = sum(1 for item in episode_results if item["success"])
    return {
        "episodes": total_episodes,
        "success_count": success_count,
        "success_rate": success_count / total_episodes if total_episodes else 0.0,
        "avg_steps": float(np.mean([item["steps"] for item in episode_results])) if episode_results else 0.0,
        "avg_contact_rate": float(np.mean([item["contact_rate"] for item in episode_results])) if episode_results else 0.0,
        "avg_max_contact_duration": float(np.mean([item["max_contact_duration"] for item in episode_results])) if episode_results else 0.0,
        "avg_grasp_contact_rate": float(np.mean([item["grasp_contact_rate"] for item in episode_results])) if episode_results else 0.0,
        "avg_max_grasp_contact_duration": float(np.mean([item["max_grasp_contact_duration"] for item in episode_results])) if episode_results else 0.0,
        "avg_final_distance": float(np.mean([item["final_distance"] for item in episode_results])) if episode_results else 0.0,
        "avg_final_task_distance": float(np.mean([item.get("final_task_distance", 0.0) for item in episode_results])) if episode_results else 0.0,
        "avg_total_reward": float(np.mean([item["total_reward"] for item in episode_results])) if episode_results else 0.0,
    }


def _save_batch_report(report_path, config, summary, episode_results):
    """Save evaluation metrics to JSON."""
    report_file = Path(report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": config,
        "summary": summary,
        "episodes": episode_results,
    }
    report_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nSaved batch report to: {report_file}")


def run_batch_evaluation(
    num_episodes=10,
    max_steps=300,
    enable_catch_task=False,
    object_fall_speed=-0.3,
    controller_name="enhanced",
    controller_profile="default",
    placement_mode=None,
    placement_jitter=0.0,
    report_path=None,
    observation_mode="oracle",
    structured_task_name=None,
):
    """Run the demo repeatedly and report success metrics."""
    print("=" * 60)
    print("Batch Demo Evaluation")
    print("=" * 60)
    print(f"Task: {get_task_name(enable_catch_task, structured_task_name=structured_task_name)}")
    print(f"Episodes: {num_episodes}")
    print(f"Step limit: {max_steps}")
    print(f"Controller: {controller_name}")
    if not enable_catch_task:
        print(f"Controller profile: {controller_profile}")
    print(f"Catch task: {'enabled' if enable_catch_task else 'disabled'}")
    effective_placement_mode = placement_mode or ("scene" if enable_catch_task else "demo")
    print(f"Placement mode: {effective_placement_mode}")
    print(f"Placement jitter: {placement_jitter:.4f} m")
    print(f"Observation mode: {observation_mode}")
    if structured_task_name:
        print(f"Structured task: {structured_task_name}")
    if enable_catch_task:
        print(f"Object fall speed: {object_fall_speed:.3f} m/s")

    episode_results = []

    for episode_idx in range(num_episodes):
        print(f"\nEpisode {episode_idx + 1}/{num_episodes}")
        env, controller = _create_env_and_controller(
            max_steps=max_steps,
            enable_catch_task=enable_catch_task,
            object_fall_speed=object_fall_speed,
            controller_name=controller_name,
            controller_profile=controller_profile,
            observation_mode=observation_mode,
            structured_task_name=structured_task_name,
        )
        result = _run_grasp_episode(
            env,
            controller,
            max_steps=max_steps,
            with_viewer=False,
            verbose=False,
            placement_mode=effective_placement_mode,
            placement_jitter=placement_jitter,
            structured_task_name=structured_task_name,
        )
        result["episode_idx"] = episode_idx
        episode_results.append(result)
        print(
            f"  Result: {'success' if result['success'] else 'failure'} | "
            f"grasp_steps={result['grasp_contact_steps']} | "
            f"max_grasp={result['max_grasp_contact_duration']} | "
            f"final_distance={result['final_distance']:.3f}"
        )

    summary = _summarize_batch_results(episode_results)

    print("\n" + "=" * 60)
    print("Batch Summary")
    print("=" * 60)
    print(f"Success rate: {summary['success_rate']:.1%} ({summary['success_count']}/{summary['episodes']})")
    print(f"Average steps: {summary['avg_steps']:.1f}")
    print(f"Average any-contact ratio: {summary['avg_contact_rate']:.1%}")
    print(f"Average max any-contact: {summary['avg_max_contact_duration']:.1f} steps")
    print(f"Average stable-grasp ratio: {summary['avg_grasp_contact_rate']:.1%}")
    print(f"Average max stable-grasp: {summary['avg_max_grasp_contact_duration']:.1f} steps")
    if structured_task_name == "pre_grasp":
        print(f"Average final task-space distance: {summary['avg_final_task_distance']:.4f}")
        print(f"Average final legacy distance: {summary['avg_final_distance']:.3f}")
    else:
        print(f"Average final distance: {summary['avg_final_distance']:.3f}")
    print(f"Average total reward: {summary['avg_total_reward']:.3f}")

    if report_path:
        config = {
            "episodes": num_episodes,
            "max_steps": max_steps,
            "controller": controller_name,
            "controller_profile": controller_profile,
            "enable_catch_task": enable_catch_task,
            "object_fall_speed": object_fall_speed,
            "placement_mode": effective_placement_mode,
            "placement_jitter": placement_jitter,
            "observation_mode": observation_mode,
            "structured_task_name": structured_task_name,
            "task_name": get_task_name(enable_catch_task, structured_task_name=structured_task_name),
            "success_rule": get_success_rule(enable_catch_task, structured_task_name=structured_task_name),
        }
        _save_batch_report(report_path, config, summary, episode_results)

    return summary, episode_results


def run_grasp_demo(
    with_viewer=True,
    max_steps=300,
    enable_catch_task=False,
    object_fall_speed=-0.3,
    controller_name="enhanced",
    controller_profile="default",
    placement_mode=None,
    placement_jitter=0.0,
    observation_mode="oracle",
    structured_task_name=None,
):
    """Run a single interactive demo episode."""
    print("=" * 60)
    if enable_catch_task:
        print(
            f"Grasp Demo - "
            f"{get_task_name(enable_catch_task, structured_task_name=structured_task_name)} "
            f"(fall speed: {object_fall_speed:.3f} m/s)"
        )
    else:
        print(f"Grasp Demo - {get_task_name(enable_catch_task, structured_task_name=structured_task_name)}")
    print("=" * 60)
    print(f"Observation mode: {observation_mode}")
    if structured_task_name:
        print(f"Structured task: {structured_task_name}")

    env, controller = _create_env_and_controller(
        max_steps=max_steps,
        enable_catch_task=enable_catch_task,
        object_fall_speed=object_fall_speed,
        controller_name=controller_name,
        controller_profile=controller_profile,
        observation_mode=observation_mode,
        structured_task_name=structured_task_name,
    )

    print("\nController info:")
    controller.print_info()

    result = _run_grasp_episode(
        env,
        controller,
        max_steps=max_steps,
        with_viewer=with_viewer,
        verbose=True,
        placement_mode=placement_mode or ("scene" if enable_catch_task else "demo"),
        placement_jitter=placement_jitter,
        structured_task_name=structured_task_name,
    )
    _print_episode_summary(result)
    print("\nDemo finished.")
    return env, controller, result


def main():
    """CLI entrypoint."""
    import argparse

    parser = argparse.ArgumentParser(description="Grasp demo script")
    parser.add_argument("--no-viewer", action="store_true", help="Disable visualization")
    parser.add_argument("--steps", type=int, default=1000, help="Maximum steps per episode")
    parser.add_argument("--episodes", type=int, default=1, help="Number of episodes for batch evaluation")
    parser.add_argument(
        "--report",
        type=str,
        default="",
        help="Optional JSON report path for batch evaluation",
    )
    parser.add_argument(
        "--controller",
        type=str,
        default="enhanced",
        help="Controller type (linear, bio, enhanced)",
    )
    parser.add_argument(
        "--controller-profile",
        type=str,
        default="default",
        choices=["default", "expert_collection"],
        help="Stage-timing profile for the enhanced static-grasp controller",
    )
    parser.add_argument(
        "--enable-catch-task",
        action="store_true",
        help="Enable the falling-object catch task",
    )
    parser.add_argument(
        "--placement-mode",
        type=str,
        default="",
        choices=["", "scene", "demo"],
        help="Optional object placement mode override",
    )
    parser.add_argument(
        "--placement-jitter",
        type=float,
        default=0.0,
        help="Optional random jitter for demo object placement in meters",
    )
    parser.add_argument(
        "--object-fall-speed",
        type=float,
        default=-0.3,
        help="Initial object fall speed in m/s",
    )
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

    args = parser.parse_args()
    structured_task_name = _resolve_structured_task_name(
        task_name_arg=args.task,
        structured_task_name=args.structured_task,
    )

    try:
        if args.episodes > 1:
            if not args.no_viewer:
                print("Batch evaluation runs without viewer to avoid blocking.")
            run_batch_evaluation(
                num_episodes=args.episodes,
                max_steps=args.steps,
                enable_catch_task=args.enable_catch_task,
                object_fall_speed=args.object_fall_speed,
                controller_name=args.controller,
                controller_profile=args.controller_profile,
                placement_mode=args.placement_mode or None,
                placement_jitter=args.placement_jitter,
                report_path=args.report or None,
                observation_mode=args.observation_mode,
                structured_task_name=structured_task_name,
            )
        else:
            run_grasp_demo(
                with_viewer=not args.no_viewer,
                max_steps=args.steps,
                enable_catch_task=args.enable_catch_task,
                object_fall_speed=args.object_fall_speed,
                controller_name=args.controller,
                controller_profile=args.controller_profile,
                placement_mode=args.placement_mode or None,
                placement_jitter=args.placement_jitter,
                observation_mode=args.observation_mode,
                structured_task_name=structured_task_name,
            )
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as exc:
        print(f"\nDemo failed: {exc}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
