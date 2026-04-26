#!/usr/bin/env python3
"""
Evaluate a behavior-cloning policy in the grasp environment.

Canonical example:
    python scripts/eval_bc.py --model models/bc_pre_grasp_v2.pth --episodes 20 --no-viewer --placement-mode demo --placement-jitter 0.02 --report reports/bc_pre_grasp_v2_eval_j002.json
"""

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import torch
    import torch.nn as nn
except ImportError:
    print("PyTorch is required. Install it with: pip install torch")
    sys.exit(1)

from scripts.common.grasp_workflow import get_success_rule, get_task_name, place_object
from src.environments.shadow_grasp_env import ShadowGraspEnv


class SimpleBCModel(nn.Module):
    """Simple MLP policy matching the training script."""

    def __init__(self, obs_dim=70, act_dim=24, hidden_dim=64):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, act_dim),
            nn.Tanh(),
        )

    def forward(self, x):
        return self.network(x)


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


def resolve_structured_task_name(cli_value, metadata):
    """Prefer CLI override, then fall back to training metadata."""
    cli_value = str(cli_value or "").strip()
    if cli_value:
        return cli_value
    return metadata.get("structured_task_name") or None


def resolve_task_kwargs(structured_task_name, metadata):
    """Restore task kwargs from training metadata when available."""
    task_kwargs = dict(metadata.get("task_kwargs", {}) or {})
    if structured_task_name == "pre_grasp" and "target_offset" not in task_kwargs:
        task_kwargs["target_offset"] = (0.008, 0.0165, 0.0)
    return task_kwargs


def resolve_pre_grasp_start_bias(raw_cli_value, metadata):
    """Restore the demo-placement start bias for pre_grasp."""
    cli_values = parse_float_list(raw_cli_value)
    if cli_values:
        if len(cli_values) != 3:
            raise ValueError(f"Expected 3 comma-separated values, got: {raw_cli_value}")
        return tuple(float(v) for v in cli_values)

    policy_config = dict(metadata.get("pre_grasp_policy_config", {}) or {})
    start_bias = policy_config.get("start_bias", (0.01, 0.0, -0.005))
    return tuple(float(v) for v in start_bias)


def load_bc_model(model_path, device):
    """Load a trained BC checkpoint."""
    model_file = Path(model_path)
    print(f"Loading model: {model_file}")
    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found: {model_file}")

    checkpoint = torch.load(model_file, map_location=device)
    model = SimpleBCModel(
        obs_dim=checkpoint.get("obs_dim", 70),
        act_dim=checkpoint.get("act_dim", 24),
        hidden_dim=checkpoint.get("hidden_dim", 64),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    metadata = checkpoint.get("metadata", {}) or {}
    print("Model parameters:")
    print(f"  obs_dim: {checkpoint.get('obs_dim', 70)}")
    print(f"  act_dim: {checkpoint.get('act_dim', 24)}")
    print(f"  hidden_dim: {checkpoint.get('hidden_dim', 64)}")
    if metadata.get("phase_feature"):
        print(f"  phase_feature: enabled (horizon={metadata.get('phase_feature_horizon', 'unknown')})")
    return model, metadata


def build_policy_observation(obs, policy_step, metadata, max_steps):
    """Append optional derived features expected by the checkpoint."""
    policy_obs = np.asarray(obs, dtype=np.float32)
    if not metadata.get("phase_feature"):
        return policy_obs

    horizon = int(metadata.get("phase_feature_horizon") or max_steps)
    normalized_phase = min(max(policy_step, 0) / max(1, horizon - 1), 1.0)
    return np.concatenate([policy_obs, np.array([normalized_phase], dtype=np.float32)])


def run_policy_episode(
    model,
    env,
    device,
    metadata,
    max_steps,
    with_viewer=False,
    placement_mode="scene",
    placement_jitter=0.0,
    pre_grasp_start_bias=None,
    viewer_step_sleep=0.02,
    viewer_hold_seconds=2.0,
    finger_ramp_steps=0,
    finger_ramp_start_scale=1.0,
    verbose=True,
):
    """Run one policy episode and collect metrics."""
    obs = env.reset()
    placement_info = place_object(
        env,
        placement_mode=placement_mode,
        placement_jitter=placement_jitter,
        verbose=verbose,
        pre_grasp_start_bias=pre_grasp_start_bias,
    )
    obs = env.get_obs()

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

    done = False
    step_count = 0
    total_reward = 0.0
    contact_steps = 0
    max_contact_duration = 0
    grasp_contact_steps = 0
    max_grasp_contact_duration = 0
    action_l1_sum = 0.0
    finger_action_l1_sum = 0.0
    zero_like_action_steps = 0
    aligned_steps = 0
    initial_position_error = None
    min_position_error = None
    last_info = {
        "distance": env._get_distance(),
        "contact_duration": 0,
        "grasp_contact_duration": 0,
        "object_height": env._get_object_height(),
        "object_on_floor": False,
        "success": False,
    }

    while not done and step_count < max_steps:
        policy_obs = build_policy_observation(obs, step_count, metadata, max_steps)
        next_step = step_count + 1
        with torch.no_grad():
            obs_tensor = torch.from_numpy(policy_obs).float().to(device)
            action = model(obs_tensor).cpu().numpy()

        if finger_ramp_steps > 0 and next_step <= finger_ramp_steps:
            ramp_progress = (next_step - 1) / max(1, finger_ramp_steps - 1)
            finger_scale = finger_ramp_start_scale + (1.0 - finger_ramp_start_scale) * ramp_progress
            action = action.copy()
            action[2:] *= finger_scale

        action_abs = np.abs(action)
        action_l1_sum += float(np.mean(action_abs))
        finger_action_l1_sum += float(np.mean(action_abs[2:])) if action_abs.shape[0] > 2 else 0.0
        if float(np.mean(action_abs)) < 0.05:
            zero_like_action_steps += 1

        obs, reward, done, info = env.step(action)
        step_count = next_step
        last_info = info
        total_reward += float(reward)

        if info["contact"]:
            contact_steps += 1
        if info.get("grasp_contact"):
            grasp_contact_steps += 1
        max_contact_duration = max(max_contact_duration, int(info.get("contact_duration", 0)))
        max_grasp_contact_duration = max(
            max_grasp_contact_duration,
            int(info.get("grasp_contact_duration", 0)),
        )
        if info.get("pre_grasp_is_aligned"):
            aligned_steps += 1
        if "position_error" in info:
            position_error = float(info["position_error"])
            if initial_position_error is None:
                initial_position_error = position_error
            min_position_error = (
                position_error
                if min_position_error is None
                else min(min_position_error, position_error)
            )

        if verbose and step_count % 50 == 0:
            distance_label = (
                f"position_error={float(info.get('position_error', 0.0)):.4f}"
                if "position_error" in info
                else f"distance={info['distance']:.3f}"
            )
            print(
                f"  Step {step_count}: reward={reward:.3f}, {distance_label}, "
                f"contact={'yes' if info['contact'] else 'no'}, "
                f"grasp={'yes' if info.get('grasp_contact') else 'no'}"
            )

        if viewer is not None:
            viewer.sync()
            time.sleep(max(0.0, viewer_step_sleep))

    if viewer is not None and viewer_hold_seconds > 0:
        if verbose:
            print(f"Holding final frame for {viewer_hold_seconds:.1f}s.")
        hold_until = time.time() + viewer_hold_seconds
        while time.time() < hold_until:
            viewer.sync()
            time.sleep(0.02)

    if viewer is not None:
        viewer.close()

    return {
        "success": bool(env.is_success()),
        "task_name": env.get_task_name(),
        "steps": int(step_count),
        "contact_steps": int(contact_steps),
        "contact_rate": float(contact_steps / step_count) if step_count else 0.0,
        "max_contact_duration": int(max_contact_duration),
        "grasp_contact_steps": int(grasp_contact_steps),
        "grasp_contact_rate": float(grasp_contact_steps / step_count) if step_count else 0.0,
        "max_grasp_contact_duration": int(max_grasp_contact_duration),
        "final_distance": float(last_info["distance"]),
        "mean_abs_action": float(action_l1_sum / step_count) if step_count else 0.0,
        "mean_abs_finger_action": float(finger_action_l1_sum / step_count) if step_count else 0.0,
        "zero_like_action_ratio": float(zero_like_action_steps / step_count) if step_count else 0.0,
        "initial_position_error": float(initial_position_error) if initial_position_error is not None else -1.0,
        "min_position_error": float(min_position_error) if min_position_error is not None else -1.0,
        "final_position_error": float(last_info.get("position_error", -1.0)),
        "position_error_improvement": (
            float(initial_position_error - last_info.get("position_error", initial_position_error))
            if initial_position_error is not None and "position_error" in last_info
            else 0.0
        ),
        "aligned_rate": float(aligned_steps / step_count) if step_count else 0.0,
        "object_height": float(last_info.get("object_height", env._get_object_height())),
        "object_on_floor": bool(last_info.get("object_on_floor", False)),
        "finger_contact_count": int(last_info.get("finger_contact_count", 0)),
        "finger_contact_groups": list(last_info.get("finger_contact_groups", [])),
        "palm_only_contact": bool(last_info.get("palm_only_contact", False)),
        "total_reward": float(total_reward),
        "placement_info": placement_info,
    }


def summarize_results(episode_results):
    """Aggregate per-episode evaluation metrics."""
    total_episodes = len(episode_results)
    success_count = sum(1 for result in episode_results if result["success"])
    summary = {
        "episodes": total_episodes,
        "success_count": success_count,
        "success_rate": success_count / total_episodes if total_episodes else 0.0,
        "avg_steps": float(np.mean([result["steps"] for result in episode_results])) if episode_results else 0.0,
        "avg_total_reward": float(np.mean([result["total_reward"] for result in episode_results])) if episode_results else 0.0,
        "avg_contact_rate": float(np.mean([result["contact_rate"] for result in episode_results])) if episode_results else 0.0,
        "avg_max_contact_duration": float(np.mean([result["max_contact_duration"] for result in episode_results])) if episode_results else 0.0,
        "avg_grasp_contact_rate": float(np.mean([result["grasp_contact_rate"] for result in episode_results])) if episode_results else 0.0,
        "avg_max_grasp_contact_duration": float(np.mean([result["max_grasp_contact_duration"] for result in episode_results])) if episode_results else 0.0,
        "avg_final_distance": float(np.mean([result["final_distance"] for result in episode_results])) if episode_results else 0.0,
        "avg_mean_abs_action": float(np.mean([result["mean_abs_action"] for result in episode_results])) if episode_results else 0.0,
        "avg_mean_abs_finger_action": float(np.mean([result["mean_abs_finger_action"] for result in episode_results])) if episode_results else 0.0,
        "avg_zero_like_action_ratio": float(np.mean([result["zero_like_action_ratio"] for result in episode_results])) if episode_results else 0.0,
    }
    if any(result.get("final_position_error", -1.0) >= 0 for result in episode_results):
        summary["avg_initial_position_error"] = float(
            np.mean([result["initial_position_error"] for result in episode_results if result["initial_position_error"] >= 0])
        )
        summary["avg_min_position_error"] = float(
            np.mean([result["min_position_error"] for result in episode_results if result["min_position_error"] >= 0])
        )
        summary["avg_final_position_error"] = float(
            np.mean([result["final_position_error"] for result in episode_results if result["final_position_error"] >= 0])
        )
        summary["avg_position_error_improvement"] = float(
            np.mean([result.get("position_error_improvement", 0.0) for result in episode_results])
        )
        summary["avg_aligned_rate"] = float(
            np.mean([result.get("aligned_rate", 0.0) for result in episode_results])
        )
    return summary


def save_report(report_path, config, summary, episode_results):
    """Write evaluation results to JSON."""
    report_file = Path(report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": config,
        "summary": summary,
        "episodes": episode_results,
    }
    report_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved evaluation report to: {report_file}")


def print_summary(summary):
    """Print a readable summary."""
    print("\n" + "=" * 60)
    print("BC Evaluation Summary")
    print("=" * 60)
    print(f"Success rate: {summary['success_rate']:.1%} ({summary['success_count']}/{summary['episodes']})")
    print(f"Average steps: {summary['avg_steps']:.1f}")
    print(f"Average reward: {summary['avg_total_reward']:.3f}")
    print(f"Average any-contact ratio: {summary['avg_contact_rate']:.1%}")
    print(f"Average max any-contact duration: {summary['avg_max_contact_duration']:.1f}")
    print(f"Average stable-grasp ratio: {summary['avg_grasp_contact_rate']:.1%}")
    print(f"Average max stable-grasp duration: {summary['avg_max_grasp_contact_duration']:.1f}")
    print(f"Average final distance: {summary['avg_final_distance']:.3f}")
    print(f"Average mean |action|: {summary['avg_mean_abs_action']:.4f}")
    print(f"Average mean |finger action|: {summary['avg_mean_abs_finger_action']:.4f}")
    print(f"Average near-zero action ratio: {summary['avg_zero_like_action_ratio']:.1%}")
    if "avg_final_position_error" in summary:
        print(f"Average initial position error: {summary['avg_initial_position_error']:.4f}")
        print(f"Average min position error: {summary['avg_min_position_error']:.4f}")
        print(f"Average final position error: {summary['avg_final_position_error']:.4f}")
        print(f"Average position error improvement: {summary['avg_position_error_improvement']:.4f}")
        print(f"Average aligned ratio: {summary['avg_aligned_rate']:.1%}")
        if summary["avg_position_error_improvement"] <= 0.002:
            print("Warning: success may still be tolerance-driven; position error is barely improving.")


def main():
    """CLI entrypoint."""
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate a BC model in the grasp environment")
    parser.add_argument("--model", type=str, default="models/test_bc.pth", help="Path to the BC checkpoint")
    parser.add_argument("--episodes", type=int, default=10, help="Number of evaluation episodes")
    parser.add_argument("--no-viewer", action="store_true", help="Disable MuJoCo viewer")
    parser.add_argument("--max-steps", type=int, default=200, help="Maximum steps per episode")
    parser.add_argument("--device", type=str, default="cpu", help="Evaluation device: cpu or cuda")
    parser.add_argument(
        "--placement-mode",
        type=str,
        default="scene",
        choices=["scene", "demo"],
        help="Object placement mode for evaluation",
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
        "--structured-task",
        type=str,
        default="",
        choices=["", "pre_grasp", "stable_grasp", "lift_and_hold"],
        help="Optional task-driven interface override",
    )
    parser.add_argument("--report", type=str, default="", help="Optional JSON report path")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed")
    parser.add_argument(
        "--viewer-step-sleep",
        type=float,
        default=0.02,
        help="Seconds to sleep after each viewer frame in single-episode mode",
    )
    parser.add_argument(
        "--viewer-hold-secs",
        type=float,
        default=2.0,
        help="Seconds to keep the final frame visible before closing the viewer",
    )
    parser.add_argument(
        "--finger-ramp-steps",
        type=int,
        default=0,
        help="If > 0, gradually scale finger actions from the start scale to 1.0 over this many steps",
    )
    parser.add_argument(
        "--finger-ramp-start-scale",
        type=float,
        default=1.0,
        help="Starting scale for finger actions during the optional ramp",
    )
    parser.add_argument(
        "--pre-grasp-start-bias",
        type=str,
        default="",
        help="Optional comma-separated xyz bias for pre_grasp demo placement",
    )

    args = parser.parse_args()

    if args.seed is not None:
        np.random.seed(args.seed)

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA is not available, falling back to CPU.")
        args.device = "cpu"

    device = torch.device(args.device)
    model, metadata = load_bc_model(args.model, device)
    structured_task_name = resolve_structured_task_name(args.structured_task, metadata)
    task_kwargs = resolve_task_kwargs(structured_task_name, metadata)
    placement_jitters = parse_float_list(args.placement_jitters) or [float(args.placement_jitter)]
    pre_grasp_start_bias = resolve_pre_grasp_start_bias(args.pre_grasp_start_bias, metadata)

    print("=" * 60)
    print("BC Policy Evaluation")
    print("=" * 60)
    print(f"Task: {get_task_name(args.enable_catch_task, structured_task_name=structured_task_name)}")
    print(f"Device: {device}")
    print(f"Episodes: {args.episodes}")
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
        print(f"Pre-grasp start bias: {pre_grasp_start_bias}")
        print(f"Pre-grasp target offset: {task_kwargs.get('target_offset')}")
    if (not args.no_viewer) and args.episodes == 1:
        print(f"Viewer step sleep: {args.viewer_step_sleep:.3f}s")
        print(f"Viewer hold: {args.viewer_hold_secs:.1f}s")
    if args.finger_ramp_steps > 0:
        print(f"Finger ramp: {args.finger_ramp_start_scale:.2f} -> 1.00 over {args.finger_ramp_steps} steps")

    env = ShadowGraspEnv(
        max_steps=args.max_steps,
        enable_catch_task=args.enable_catch_task,
        object_fall_speed=args.object_fall_speed,
        task_name=structured_task_name,
        observation_mode=args.observation_mode,
        task_kwargs=task_kwargs,
    )
    resolved_task_spec = (
        env.task.get_task_spec()
        if env.task is not None and hasattr(env.task, "get_task_spec")
        else {}
    )

    episode_results = []
    show_viewer = (not args.no_viewer) and args.episodes == 1
    if (not args.no_viewer) and args.episodes > 1:
        print("Batch evaluation uses headless mode to avoid blocking the run.")

    for episode_idx in range(args.episodes):
        episode_jitter = float(placement_jitters[episode_idx % len(placement_jitters)])
        print(f"\nEpisode {episode_idx + 1}/{args.episodes}")
        print(f"  Placement jitter for this episode: {episode_jitter:.4f} m")
        result = run_policy_episode(
            model=model,
            env=env,
            device=device,
            metadata=metadata,
            max_steps=args.max_steps,
            with_viewer=show_viewer,
            placement_mode=args.placement_mode,
            placement_jitter=episode_jitter,
            pre_grasp_start_bias=pre_grasp_start_bias,
            viewer_step_sleep=args.viewer_step_sleep,
            viewer_hold_seconds=args.viewer_hold_secs,
            finger_ramp_steps=args.finger_ramp_steps,
            finger_ramp_start_scale=args.finger_ramp_start_scale,
            verbose=True,
        )
        result["episode_idx"] = episode_idx
        episode_results.append(result)
        print(
            f"  Result: {'success' if result['success'] else 'failure'} | "
            f"reward={result['total_reward']:.3f} | "
            f"max_grasp={result['max_grasp_contact_duration']} | "
            f"final_distance={result['final_distance']:.3f}"
        )
        if result.get("final_position_error", -1.0) >= 0:
            print(
                f"  Reach check: initial={result['initial_position_error']:.4f} | "
                f"min={result['min_position_error']:.4f} | "
                f"final={result['final_position_error']:.4f} | "
                f"improve={result['position_error_improvement']:.4f} | "
                f"mean|a|={result['mean_abs_action']:.4f} | "
                f"near_zero={result['zero_like_action_ratio']:.1%}"
            )

    summary = summarize_results(episode_results)
    print_summary(summary)

    if args.report:
        config = {
            "model": args.model,
            "episodes": args.episodes,
            "max_steps": args.max_steps,
            "placement_mode": args.placement_mode,
            "placement_jitter": placement_jitters[0] if len(placement_jitters) == 1 else "mixed",
            "placement_jitters": placement_jitters,
            "enable_catch_task": args.enable_catch_task,
            "object_fall_speed": args.object_fall_speed,
            "observation_mode": args.observation_mode,
            "structured_task_name": structured_task_name,
            "task_kwargs": task_kwargs,
            "pre_grasp_start_bias": pre_grasp_start_bias,
            "device": args.device,
            "seed": args.seed,
            "viewer_step_sleep": args.viewer_step_sleep,
            "viewer_hold_secs": args.viewer_hold_secs,
            "finger_ramp_steps": args.finger_ramp_steps,
            "finger_ramp_start_scale": args.finger_ramp_start_scale,
            "task_name": get_task_name(args.enable_catch_task, structured_task_name=structured_task_name),
            "success_rule": get_success_rule(args.enable_catch_task, structured_task_name=structured_task_name),
            "training_metadata": metadata,
            "task_spec": resolved_task_spec,
        }
        save_report(args.report, config, summary, episode_results)

    return 0 if summary["success_rate"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
