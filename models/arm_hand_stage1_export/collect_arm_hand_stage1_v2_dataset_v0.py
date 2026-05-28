#!/usr/bin/env python3
"""Collect Stage2 lift-ball dataset v0 against the frozen task contract.

This is a tiny scripted rollout dataset for contract/replay QA. It is not a
training run and should not be treated as a promoted BC/RL dataset.
"""

from __future__ import annotations

import argparse
import json
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
from run_arm_hand_stage1_v2_ball_pose_sweep import (
    DEFAULT_X_OFFSETS,
    DEFAULT_Y_OFFSETS,
    DEFAULT_Z_OFFSETS,
    blend_targets,
    build_phases,
    grid_offsets,
)


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DEFAULT_DATASET = DATA / "arm_hand_stage1_v2_lift_ball_dataset_v0.npz"
DEFAULT_REPORT = DOCS / "arm_hand_stage1_v2_dataset_v0_report.md"
DEFAULT_META = META / "arm_hand_stage1_v2_dataset_v0.json"
CONTRACT_META = META / "arm_hand_stage1_v2_task_contract.json"


def phase_id_table(phases: list[tuple[str, dict[str, float], dict[str, float], int]]) -> list[str]:
    return [name for name, _, _, _ in phases]


def terminal_reason_table() -> list[str]:
    return [
        "running",
        "success_lift_ball",
        "non_finite_state",
        "excessive_penetration",
        "ball_dropped",
        "floor_contact_after_lift",
        "timeout",
    ]


def reason_code(reason: str, table: list[str]) -> int:
    if reason not in table:
        return 0
    return table.index(reason)


def collect_episode(
    api: ArmHandStage1TaskAPI,
    episode_id: int,
    base_ball: np.ndarray,
    offset: np.ndarray,
    args,
) -> dict[str, Any]:
    ball = base_ball + offset
    api.reset_hand_open(ball_position=ball)
    initial_ball = api.get_ball_pose()["position"].copy()
    default_targets = api.targets_from_current_qpos()
    phases = build_phases(default_targets, args)
    phase_names = phase_id_table(phases)
    terminal_reasons = terminal_reason_table()
    threshold_for_lifted_once = DEFAULT_TASK_THRESHOLDS["dropped_after_lift_height_m"]

    rows = {
        "obs": [],
        "actions": [],
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
    }
    phase_summaries = []
    lifted_once = False
    step_count = 0
    final_eval: dict[str, Any] | None = None
    terminal_phase = "none"

    for phase_id, (phase_name, start_targets, end_targets, steps) in enumerate(phases):
        phase_start_step = step_count
        for local_step in range(max(1, int(steps))):
            obs = api.get_observation()
            alpha = local_step / max(1, int(steps) - 1)
            action = api.action_from_targets(blend_targets(start_targets, end_targets, alpha))
            api.step_action(action, n=1, pin_ball=False)
            step_count += 1
            metrics = api.compute_task_metrics(initial_ball)
            lifted_once = lifted_once or metrics["ball_lift_height"] >= threshold_for_lifted_once
            evaluation = api.evaluate_lift_task_state(
                initial_ball,
                step_count=step_count,
                max_episode_steps=sum(p[3] for p in phases),
                lifted_once=lifted_once,
            )
            next_obs = api.get_observation()
            rows["obs"].append(obs["vector"])
            rows["actions"].append(action)
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
            final_eval = evaluation
            if evaluation["done"]:
                terminal_phase = phase_name
                break
        phase_eval = api.evaluate_lift_task_state(
            initial_ball,
            step_count=step_count,
            max_episode_steps=sum(p[3] for p in phases),
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
        final_eval = api.evaluate_lift_task_state(initial_ball, step_count=step_count, lifted_once=lifted_once)
    return {
        "episode_id": int(episode_id),
        "initial_ball": initial_ball,
        "offset": offset,
        "step_count": int(step_count),
        "terminal_phase": terminal_phase,
        "terminal_eval": final_eval,
        "phase_summaries": phase_summaries,
        "rows": rows,
        "phase_name_table": phase_names,
        "terminal_reason_table": terminal_reasons,
    }


def concatenate_rows(episodes: list[dict[str, Any]], key: str, dtype) -> np.ndarray:
    return np.concatenate([np.asarray(ep["rows"][key], dtype=dtype) for ep in episodes], axis=0)


def write_dataset(dataset_path: Path, episodes: list[dict[str, Any]], api: ArmHandStage1TaskAPI, contract: dict[str, Any]) -> None:
    phase_names = episodes[0]["phase_name_table"]
    terminal_reasons = episodes[0]["terminal_reason_table"]
    np.savez_compressed(
        dataset_path,
        obs=concatenate_rows(episodes, "obs", np.float64),
        actions=concatenate_rows(episodes, "actions", np.float64),
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
        joint_names=np.asarray(api.get_joint_names(), dtype=str),
        actuator_names=np.asarray(api.get_actuator_names(), dtype=str),
        phase_name_table=np.asarray(phase_names, dtype=str),
        terminal_reason_table=np.asarray(terminal_reasons, dtype=str),
        task_name=np.asarray([TASK_NAME], dtype=str),
        contract_version=np.asarray([TASK_CONTRACT_VERSION], dtype=str),
        scene=np.asarray([str(api.scene_path)], dtype=str),
        contract_json=np.asarray([json.dumps(json_ready(contract), ensure_ascii=False)], dtype=str),
    )


def summarize_payload(dataset_path: Path, episodes: list[dict[str, Any]], api: ArmHandStage1TaskAPI, args) -> dict[str, Any]:
    obs_shape = list(concatenate_rows(episodes, "obs", np.float64).shape)
    actions_shape = list(concatenate_rows(episodes, "actions", np.float64).shape)
    next_obs_shape = list(concatenate_rows(episodes, "next_obs", np.float64).shape)
    success_count = sum(1 for ep in episodes if ep["terminal_eval"]["success"])
    terminal_counts: dict[str, int] = {}
    for ep in episodes:
        reason = ep["terminal_eval"]["terminal_reason"]
        terminal_counts[reason] = terminal_counts.get(reason, 0) + 1
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task_name": TASK_NAME,
        "contract_version": TASK_CONTRACT_VERSION,
        "scene": str(api.scene_path),
        "dataset": str(dataset_path),
        "episodes": len(episodes),
        "total_rows": obs_shape[0],
        "obs_shape": obs_shape,
        "actions_shape": actions_shape,
        "next_obs_shape": next_obs_shape,
        "reward_shape": list(concatenate_rows(episodes, "rewards", np.float64).shape),
        "success_count": int(success_count),
        "terminal_reason_counts": terminal_counts,
        "grid": {
            "x_offsets": args.x_offsets,
            "y_offsets": args.y_offsets,
            "z_offsets": args.z_offsets,
        },
        "episode_summaries": [
            {
                "episode_id": ep["episode_id"],
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
        "notes": [
            "Dataset v0 is tiny and scripted.",
            "Rows follow obs_t, action_t, reward_t, done_t, next_obs_t.",
            "Reward/done/success labels are computed by the frozen task contract.",
            "This is not a BC/RL training run.",
        ],
    }


def write_report(payload: dict[str, Any]) -> None:
    DEFAULT_META.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Arm-Hand Stage1 V2 Dataset V0 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Task: `{payload['task_name']}`\n",
        f"- Contract: `{payload['contract_version']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Episodes: `{payload['episodes']}`\n",
        f"- Total rows: `{payload['total_rows']}`\n",
        f"- obs shape: `{payload['obs_shape']}`\n",
        f"- actions shape: `{payload['actions_shape']}`\n",
        f"- next_obs shape: `{payload['next_obs_shape']}`\n",
        f"- Success count: `{payload['success_count']} / {payload['episodes']}`\n",
        f"- Terminal reasons: `{payload['terminal_reason_counts']}`\n",
        f"- Training ready: **No**\n\n",
        "## Episode Summary\n\n",
        "| ep | offset xyz | rows | terminal phase | status | reason | lift m | reward | hand contacts | max pen m |\n",
        "|---:|---|---:|---|---|---|---:|---:|---:|---:|\n",
    ]
    for ep in payload["episode_summaries"]:
        final = ep["terminal_eval"]
        metrics = final["official_metrics"]
        contact = metrics["contact"]
        lines.append(
            f"| {ep['episode_id']} | `{np.round(ep['offset'], 5).tolist()}` | {ep['step_count']} | {ep['terminal_phase']} | "
            f"{final['episode_status']} | {final['terminal_reason']} | {metrics['ball_lift_height']:.4f} | "
            f"{final['reward']['total']:.4f} | {contact['ball_hand_contact_count']} | {contact['max_penetration']:.6f} |\n"
        )
    lines.extend(
        [
            "\n## Dataset Fields\n\n",
            "- `obs`: observation before action.\n",
            "- `actions`: position-target action applied at that step.\n",
            "- `next_obs`: observation after one MuJoCo step.\n",
            "- `rewards`, `dones`, `successes`, `failures`, `terminal_reason_ids`: labels from the frozen task contract.\n",
            "- `episode_ids`, `step_ids`, `phase_ids`, `phase_step_ids`: rollout indexing.\n",
            "- `initial_ball_positions`, `ball_offsets`: reset context for replay.\n\n",
            "## Next Step\n\n",
            "Run `replay_arm_hand_stage1_v2_dataset_v0.py` and use the replay report as the dataset QA gate before any BC/RL discussion.\n",
        ]
    )
    DEFAULT_REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Stage2 lift-ball dataset v0 from scripted rollouts.")
    parser.add_argument("--scene", default=str(CURRENT_LIFT_SCENE))
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--x-offsets", nargs="+", type=float, default=DEFAULT_X_OFFSETS)
    parser.add_argument("--y-offsets", nargs="+", type=float, default=DEFAULT_Y_OFFSETS)
    parser.add_argument("--z-offsets", nargs="+", type=float, default=DEFAULT_Z_OFFSETS)
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

    api = ArmHandStage1TaskAPI(args.scene)
    contract = api.get_task_contract()
    base_ball = api.get_ball_pose()["position"].copy()
    offsets = grid_offsets(args.x_offsets, args.y_offsets, args.z_offsets)
    episodes = [collect_episode(api, idx, base_ball, offset, args) for idx, offset in enumerate(offsets)]
    dataset_path = Path(args.dataset).resolve()
    write_dataset(dataset_path, episodes, api, contract)
    payload = summarize_payload(dataset_path, episodes, api, args)
    write_report(payload)
    print(f"Dataset status: {payload['success_count']}/{payload['episodes']} success")
    print(f"Saved dataset: {dataset_path}")
    print(f"Saved report: {DEFAULT_REPORT}")
    print(f"Saved metadata: {DEFAULT_META}")


if __name__ == "__main__":
    main()
