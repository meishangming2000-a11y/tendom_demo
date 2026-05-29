#!/usr/bin/env python3
"""Collect Stage2 lift-ball dataset v0.1 for closed-loop BC smoke training.

Compared with dataset v0, this version broadens the reset distribution and adds
low-amplitude behavior perturbations. Rows keep `actions` as the applied
behavior action for deterministic replay, while `expert_actions` is the BC
target for the scripted recovery action at that same phase step.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import (
    CURRENT_LIFT_SCENE,
    DEFAULT_TASK_THRESHOLDS,
    TASK_CONTRACT_VERSION,
    TASK_NAME,
    ArmHandStage1TaskAPI,
    json_ready,
)
from collect_arm_hand_stage1_v2_dataset_v0 import (
    concatenate_rows,
    phase_id_table,
    reason_code,
    terminal_reason_table,
)
from run_arm_hand_stage1_v2_ball_pose_sweep import blend_targets, build_phases, grid_offsets


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DEFAULT_DATASET = DATA / "arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz"
DEFAULT_REPORT = DOCS / "arm_hand_stage1_v2_dataset_v0_1_report.md"
DEFAULT_META = META / "arm_hand_stage1_v2_dataset_v0_1.json"

DEFAULT_X_OFFSETS = [-0.02, -0.01, 0.0, 0.01, 0.02]
DEFAULT_Y_OFFSETS = [-0.02, -0.01, 0.0, 0.01, 0.02]
DEFAULT_Z_OFFSETS = [0.0]


@dataclass(frozen=True)
class BehaviorProfile:
    name: str
    timing_scale: float
    action_noise_abs: float
    action_lag: float
    seed_offset: int


PROFILES = [
    BehaviorProfile("clean_nominal", 1.0, 0.0, 0.0, 0),
    BehaviorProfile("mild_fast_jitter", 0.96, 0.006, 0.10, 1000),
    BehaviorProfile("mild_slow_jitter", 1.04, 0.010, 0.16, 2000),
]


def clip_action(api: ArmHandStage1TaskAPI, action: np.ndarray) -> np.ndarray:
    clipped = np.asarray(action, dtype=np.float64).copy()
    for aid in range(api.model.nu):
        if bool(api.model.actuator_ctrllimited[aid]):
            low, high = api.model.actuator_ctrlrange[aid]
            clipped[aid] = np.clip(clipped[aid], low, high)
    return clipped


def scaled_phase_args(args, profile: BehaviorProfile):
    class PhaseArgs:
        pass

    out = PhaseArgs()
    for name in ["default_hold_steps", "move_steps", "approach_steps", "hand_steps", "lift_steps", "hold_steps"]:
        value = int(round(getattr(args, name) * profile.timing_scale))
        setattr(out, name, max(1, value))
    return out


def make_behavior_action(
    api: ArmHandStage1TaskAPI,
    expert_action: np.ndarray,
    previous_behavior_action: np.ndarray | None,
    rng: np.random.Generator,
    profile: BehaviorProfile,
) -> np.ndarray:
    behavior = np.asarray(expert_action, dtype=np.float64).copy()
    if previous_behavior_action is not None and profile.action_lag > 0.0:
        lag = float(np.clip(profile.action_lag, 0.0, 0.95))
        behavior = (1.0 - lag) * behavior + lag * previous_behavior_action
    if profile.action_noise_abs > 0.0:
        behavior = behavior + rng.normal(0.0, profile.action_noise_abs, size=behavior.shape)
    return clip_action(api, behavior)


def collect_episode(
    api: ArmHandStage1TaskAPI,
    episode_id: int,
    base_ball: np.ndarray,
    offset: np.ndarray,
    profile: BehaviorProfile,
    args,
) -> dict[str, Any]:
    rng = np.random.default_rng(args.seed + profile.seed_offset + episode_id)
    ball = base_ball + offset
    api.reset_hand_open(ball_position=ball)
    initial_ball = api.get_ball_pose()["position"].copy()
    default_targets = api.targets_from_current_qpos()
    phase_args = scaled_phase_args(args, profile)
    phases = build_phases(default_targets, phase_args)
    phase_names = phase_id_table(phases)
    terminal_reasons = terminal_reason_table()
    threshold_for_lifted_once = DEFAULT_TASK_THRESHOLDS["dropped_after_lift_height_m"]

    rows = {
        "obs": [],
        "actions": [],
        "expert_actions": [],
        "next_obs": [],
        "rewards": [],
        "dones": [],
        "successes": [],
        "failures": [],
        "terminal_reason_ids": [],
        "episode_ids": [],
        "step_ids": [],
        "phase_ids": [],
        "phase_step_ids": [],
        "initial_ball_positions": [],
        "ball_offsets": [],
        "behavior_profile_ids": [],
        "timing_scales": [],
        "action_noise_abs": [],
        "action_lag": [],
    }
    phase_summaries = []
    lifted_once = False
    step_count = 0
    final_eval: dict[str, Any] | None = None
    terminal_phase = "none"
    previous_behavior_action: np.ndarray | None = None
    max_episode_steps = sum(p[3] for p in phases)

    for phase_id, (phase_name, start_targets, end_targets, steps) in enumerate(phases):
        phase_start_step = step_count
        for local_step in range(max(1, int(steps))):
            obs = api.get_observation()
            alpha = local_step / max(1, int(steps) - 1)
            expert_action = api.action_from_targets(blend_targets(start_targets, end_targets, alpha))
            behavior_action = make_behavior_action(api, expert_action, previous_behavior_action, rng, profile)
            previous_behavior_action = behavior_action.copy()
            api.step_action(behavior_action, n=1, pin_ball=False)
            step_count += 1
            metrics = api.compute_task_metrics(initial_ball)
            lifted_once = lifted_once or metrics["ball_lift_height"] >= threshold_for_lifted_once
            evaluation = api.evaluate_lift_task_state(
                initial_ball,
                step_count=step_count,
                max_episode_steps=max_episode_steps,
                lifted_once=lifted_once,
            )
            next_obs = api.get_observation()
            rows["obs"].append(obs["vector"])
            rows["actions"].append(behavior_action)
            rows["expert_actions"].append(expert_action)
            rows["next_obs"].append(next_obs["vector"])
            rows["rewards"].append(evaluation["reward"]["total"])
            rows["dones"].append(evaluation["done"])
            rows["successes"].append(evaluation["success"])
            rows["failures"].append(evaluation["failure"])
            rows["terminal_reason_ids"].append(reason_code(evaluation["terminal_reason"], terminal_reasons))
            rows["episode_ids"].append(episode_id)
            rows["step_ids"].append(step_count - 1)
            rows["phase_ids"].append(phase_id)
            rows["phase_step_ids"].append(local_step)
            rows["initial_ball_positions"].append(initial_ball.copy())
            rows["ball_offsets"].append(offset.copy())
            rows["behavior_profile_ids"].append(args.profile_names.index(profile.name))
            rows["timing_scales"].append(profile.timing_scale)
            rows["action_noise_abs"].append(profile.action_noise_abs)
            rows["action_lag"].append(profile.action_lag)
            final_eval = evaluation
            if evaluation["done"]:
                terminal_phase = phase_name
                break
        phase_eval = api.evaluate_lift_task_state(
            initial_ball,
            step_count=step_count,
            max_episode_steps=max_episode_steps,
            lifted_once=lifted_once,
        )
        phase_summaries.append(
            {
                "phase": phase_name,
                "start_step": int(phase_start_step),
                "end_step": int(step_count),
                "status": phase_eval["episode_status"],
                "terminal_reason": phase_eval["terminal_reason"],
                "metrics": phase_eval["official_metrics"],
            }
        )
        if final_eval is not None and final_eval["done"]:
            break

    if final_eval is None:
        final_eval = api.evaluate_lift_task_state(
            initial_ball,
            step_count=step_count,
            max_episode_steps=max_episode_steps,
            lifted_once=lifted_once,
        )
    return {
        "episode_id": int(episode_id),
        "initial_ball": initial_ball,
        "offset": offset,
        "profile": profile,
        "step_count": int(step_count),
        "terminal_phase": terminal_phase,
        "terminal_eval": final_eval,
        "phase_summaries": phase_summaries,
        "rows": rows,
        "phase_name_table": phase_names,
        "terminal_reason_table": terminal_reasons,
    }


def write_dataset(dataset_path: Path, episodes: list[dict[str, Any]], api: ArmHandStage1TaskAPI, contract: dict[str, Any], args) -> None:
    phase_names = episodes[0]["phase_name_table"]
    terminal_reasons = episodes[0]["terminal_reason_table"]
    np.savez_compressed(
        dataset_path,
        obs=concatenate_rows(episodes, "obs", np.float64),
        actions=concatenate_rows(episodes, "actions", np.float64),
        expert_actions=concatenate_rows(episodes, "expert_actions", np.float64),
        next_obs=concatenate_rows(episodes, "next_obs", np.float64),
        rewards=concatenate_rows(episodes, "rewards", np.float64),
        dones=concatenate_rows(episodes, "dones", np.bool_),
        successes=concatenate_rows(episodes, "successes", np.bool_),
        failures=concatenate_rows(episodes, "failures", np.bool_),
        terminal_reason_ids=concatenate_rows(episodes, "terminal_reason_ids", np.int32),
        episode_ids=concatenate_rows(episodes, "episode_ids", np.int32),
        step_ids=concatenate_rows(episodes, "step_ids", np.int32),
        phase_ids=concatenate_rows(episodes, "phase_ids", np.int32),
        phase_step_ids=concatenate_rows(episodes, "phase_step_ids", np.int32),
        initial_ball_positions=concatenate_rows(episodes, "initial_ball_positions", np.float64),
        ball_offsets=concatenate_rows(episodes, "ball_offsets", np.float64),
        behavior_profile_ids=concatenate_rows(episodes, "behavior_profile_ids", np.int32),
        timing_scales=concatenate_rows(episodes, "timing_scales", np.float64),
        action_noise_abs=concatenate_rows(episodes, "action_noise_abs", np.float64),
        action_lag=concatenate_rows(episodes, "action_lag", np.float64),
        joint_names=np.asarray(api.get_joint_names(), dtype=str),
        actuator_names=np.asarray(api.get_actuator_names(), dtype=str),
        phase_name_table=np.asarray(phase_names, dtype=str),
        terminal_reason_table=np.asarray(terminal_reasons, dtype=str),
        behavior_profile_table=np.asarray(args.profile_names, dtype=str),
        task_name=np.asarray([TASK_NAME], dtype=str),
        contract_version=np.asarray([TASK_CONTRACT_VERSION], dtype=str),
        dataset_version=np.asarray(["v0.1"], dtype=str),
        scene=np.asarray([str(api.scene_path)], dtype=str),
        contract_json=np.asarray([json.dumps(json_ready(contract), ensure_ascii=False)], dtype=str),
    )


def summarize_payload(dataset_path: Path, episodes: list[dict[str, Any]], api: ArmHandStage1TaskAPI, args) -> dict[str, Any]:
    obs = concatenate_rows(episodes, "obs", np.float64)
    actions = concatenate_rows(episodes, "actions", np.float64)
    expert_actions = concatenate_rows(episodes, "expert_actions", np.float64)
    next_obs = concatenate_rows(episodes, "next_obs", np.float64)
    success_count = sum(1 for ep in episodes if ep["terminal_eval"]["success"])
    terminal_counts: dict[str, int] = {}
    profile_counts: dict[str, int] = {}
    for ep in episodes:
        reason = ep["terminal_eval"]["terminal_reason"]
        terminal_counts[reason] = terminal_counts.get(reason, 0) + 1
        name = ep["profile"].name
        profile_counts[name] = profile_counts.get(name, 0) + 1
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task_name": TASK_NAME,
        "contract_version": TASK_CONTRACT_VERSION,
        "dataset_version": "v0.1",
        "scene": str(api.scene_path),
        "dataset": str(dataset_path),
        "episodes": len(episodes),
        "total_rows": int(obs.shape[0]),
        "obs_shape": list(obs.shape),
        "actions_shape": list(actions.shape),
        "expert_actions_shape": list(expert_actions.shape),
        "next_obs_shape": list(next_obs.shape),
        "behavior_action_range": [float(np.min(actions)), float(np.max(actions))],
        "expert_action_range": [float(np.min(expert_actions)), float(np.max(expert_actions))],
        "success_count": int(success_count),
        "terminal_reason_counts": terminal_counts,
        "profile_counts": profile_counts,
        "grid": {
            "x_offsets": args.x_offsets,
            "y_offsets": args.y_offsets,
            "z_offsets": args.z_offsets,
        },
        "profiles": [profile.__dict__ for profile in PROFILES if profile.name in args.profile_names],
        "episode_summaries": [
            {
                "episode_id": ep["episode_id"],
                "profile": ep["profile"].name,
                "initial_ball": ep["initial_ball"],
                "offset": ep["offset"],
                "step_count": ep["step_count"],
                "terminal_phase": ep["terminal_phase"],
                "terminal_eval": ep["terminal_eval"],
                "phase_summaries": ep["phase_summaries"],
            }
            for ep in episodes
        ],
        "training_ready": False,
        "bc_target_field": "expert_actions",
        "notes": [
            "Dataset v0.1 broadens ball offsets and scripted behavior perturbations.",
            "`actions` are applied behavior actions for deterministic replay.",
            "`expert_actions` are the BC targets for obs+phase closed-loop smoke training.",
            "This remains an experimental BC smoke dataset, not a promoted baseline.",
        ],
    }


def write_report(payload: dict[str, Any], report_path: Path, meta_path: Path) -> None:
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Arm-Hand Stage1 V2 Dataset V0.1 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Task: `{payload['task_name']}`\n",
        f"- Contract: `{payload['contract_version']}`\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Episodes: `{payload['episodes']}`\n",
        f"- Total rows: `{payload['total_rows']}`\n",
        f"- obs shape: `{payload['obs_shape']}`\n",
        f"- behavior actions shape: `{payload['actions_shape']}`\n",
        f"- expert actions shape: `{payload['expert_actions_shape']}`\n",
        f"- Success count: `{payload['success_count']} / {payload['episodes']}`\n",
        f"- Terminal reasons: `{payload['terminal_reason_counts']}`\n",
        f"- Profile counts: `{payload['profile_counts']}`\n",
        f"- BC target field: `{payload['bc_target_field']}`\n",
        f"- Training ready: **No, experimental BC smoke only**\n\n",
        "## Episode Summary\n\n",
        "| ep | profile | offset xyz | rows | terminal phase | status | reason | lift m | hand contacts | max pen m |\n",
        "|---:|---|---|---:|---|---|---|---:|---:|---:|\n",
    ]
    for ep in payload["episode_summaries"]:
        final = ep["terminal_eval"]
        metrics = final["official_metrics"]
        contact = metrics["contact"]
        lines.append(
            f"| {ep['episode_id']} | {ep['profile']} | `{np.round(ep['offset'], 5).tolist()}` | {ep['step_count']} | "
            f"{ep['terminal_phase']} | {final['episode_status']} | {final['terminal_reason']} | "
            f"{metrics['ball_lift_height']:.4f} | {contact['ball_hand_contact_count']} | {contact['max_penetration']:.6f} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- Replay should validate against `actions`, because those were applied in MuJoCo.\n",
            "- BC should train against `expert_actions`, because those are the scripted recovery targets.\n",
            "- The perturbations are intentionally mild and are meant to reduce closed-loop covariate shift for obs+phase BC.\n",
        ]
    )
    report_path.write_text("".join(lines), encoding="utf-8")


def parse_profiles(raw: str) -> list[BehaviorProfile]:
    requested = [item.strip() for item in raw.split(",") if item.strip()]
    by_name = {profile.name: profile for profile in PROFILES}
    missing = [name for name in requested if name not in by_name]
    if missing:
        raise ValueError(f"Unknown profiles {missing}; available={sorted(by_name)}")
    return [by_name[name] for name in requested]


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Stage2 lift-ball dataset v0.1 for obs+phase BC smoke.")
    parser.add_argument("--scene", default=str(CURRENT_LIFT_SCENE))
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_META)
    parser.add_argument("--x-offsets", nargs="+", type=float, default=DEFAULT_X_OFFSETS)
    parser.add_argument("--y-offsets", nargs="+", type=float, default=DEFAULT_Y_OFFSETS)
    parser.add_argument("--z-offsets", nargs="+", type=float, default=DEFAULT_Z_OFFSETS)
    parser.add_argument("--profiles", default="clean_nominal,mild_fast_jitter,mild_slow_jitter")
    parser.add_argument("--seed", type=int, default=31)
    parser.add_argument("--default-hold-steps", type=int, default=90)
    parser.add_argument("--move-steps", type=int, default=260)
    parser.add_argument("--approach-steps", type=int, default=180)
    parser.add_argument("--hand-steps", type=int, default=120)
    parser.add_argument("--lift-steps", type=int, default=220)
    parser.add_argument("--hold-steps", type=int, default=120)
    args = parser.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    selected_profiles = parse_profiles(args.profiles)
    args.profile_names = [profile.name for profile in selected_profiles]

    api = ArmHandStage1TaskAPI(args.scene)
    contract = api.get_task_contract()
    base_ball = api.get_ball_pose()["position"].copy()
    offsets = grid_offsets(args.x_offsets, args.y_offsets, args.z_offsets)
    episodes: list[dict[str, Any]] = []
    episode_id = 0
    for profile in selected_profiles:
        for offset in offsets:
            episodes.append(collect_episode(api, episode_id, base_ball, offset, profile, args))
            episode_id += 1
    dataset_path = args.dataset.resolve()
    write_dataset(dataset_path, episodes, api, contract, args)
    payload = summarize_payload(dataset_path, episodes, api, args)
    write_report(payload, args.report, args.metadata)
    print(f"Dataset v0.1 status: {payload['success_count']}/{payload['episodes']} success")
    print(f"Saved dataset: {dataset_path}")
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")


if __name__ == "__main__":
    main()
