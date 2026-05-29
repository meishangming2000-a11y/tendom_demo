#!/usr/bin/env python3
"""Replay and QA the Stage2 lift-ball dataset v0."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import CURRENT_LIFT_SCENE, TASK_CONTRACT_VERSION, ArmHandStage1TaskAPI, json_ready


ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "data" / "arm_hand_stage1_v2_lift_ball_dataset_v0.npz"
DATASET_META = ROOT / "metadata" / "arm_hand_stage1_v2_dataset_v0.json"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
REPORT = DOCS / "arm_hand_stage1_v2_dataset_v0_replay_report.md"
META_OUT = META / "arm_hand_stage1_v2_dataset_v0_replay.json"


def reason_table(data) -> list[str]:
    return [str(item) for item in data["terminal_reason_table"]]


def compare_vectors(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        return float("inf")
    return float(np.max(np.abs(a - b))) if a.size else 0.0


def replay_episode(api: ArmHandStage1TaskAPI, data, episode_id: int, *, max_error_warn: float) -> dict[str, Any]:
    episode_ids = data["episode_ids"].astype(np.int32)
    idxs = np.where(episode_ids == episode_id)[0]
    if len(idxs) == 0:
        raise ValueError(f"Episode {episode_id} not found")

    obs = data["obs"]
    actions = data["actions"]
    next_obs = data["next_obs"]
    rewards = data["rewards"]
    dones = data["dones"]
    terminal_reason_ids = data["terminal_reason_ids"].astype(np.int32)
    terminal_reasons = reason_table(data)
    initial_ball = data["initial_ball_positions"][idxs[0]].astype(np.float64)

    api.reset_hand_open(ball_position=initial_ball)
    lifted_once = False
    max_obs_error = 0.0
    max_next_obs_error = 0.0
    max_reward_error = 0.0
    final_eval = None
    terminal_idx = None

    for local_i, idx in enumerate(idxs):
        current_obs = api.get_observation()["vector"]
        max_obs_error = max(max_obs_error, compare_vectors(current_obs, obs[idx]))
        api.step_action(actions[idx], n=1, pin_ball=False)
        metrics = api.compute_task_metrics(initial_ball)
        lifted_once = lifted_once or metrics["ball_lift_height"] >= api.get_task_contract()["termination"]["thresholds"]["dropped_after_lift_height_m"]
        evaluation = api.evaluate_lift_task_state(
            initial_ball,
            step_count=local_i + 1,
            max_episode_steps=len(idxs),
            lifted_once=lifted_once,
        )
        max_next_obs_error = max(max_next_obs_error, compare_vectors(api.get_observation()["vector"], next_obs[idx]))
        max_reward_error = max(max_reward_error, abs(float(evaluation["reward"]["total"]) - float(rewards[idx])))
        final_eval = evaluation
        if bool(dones[idx]):
            terminal_idx = int(idx)
            break

    expected_reason = terminal_reasons[int(terminal_reason_ids[terminal_idx])] if terminal_idx is not None else "none"
    status = "PASS"
    failures = []
    if final_eval is None:
        status = "FAIL"
        failures.append("no frames replayed")
    else:
        if final_eval["terminal_reason"] != expected_reason:
            failures.append(f"terminal reason mismatch: replay={final_eval['terminal_reason']} dataset={expected_reason}")
        if max_obs_error > max_error_warn:
            failures.append(f"obs max error {max_obs_error:.3e} > {max_error_warn:.3e}")
        if max_next_obs_error > max_error_warn:
            failures.append(f"next_obs max error {max_next_obs_error:.3e} > {max_error_warn:.3e}")
        if max_reward_error > max_error_warn:
            failures.append(f"reward max error {max_reward_error:.3e} > {max_error_warn:.3e}")
        if failures:
            status = "FAIL"
    return {
        "episode_id": int(episode_id),
        "frames": int(len(idxs)),
        "terminal_dataset_index": terminal_idx,
        "expected_terminal_reason": expected_reason,
        "replay_eval": final_eval,
        "max_obs_error": max_obs_error,
        "max_next_obs_error": max_next_obs_error,
        "max_reward_error": max_reward_error,
        "status": status,
        "failures": failures,
    }


def write_outputs(payload: dict[str, Any], report_path: Path = REPORT, metadata_path: Path = META_OUT) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm-Hand Stage1 V2 Dataset V0 Replay Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Contract: `{payload['contract_version']}`\n",
        f"- Episodes checked: `{payload['episodes_checked']}`\n",
        f"- Status: **{payload['status']}**\n",
        f"- Shape check: `{payload['shape_status']}`\n",
        f"- Max obs error: `{payload['max_obs_error']:.3e}`\n",
        f"- Max next_obs error: `{payload['max_next_obs_error']:.3e}`\n",
        f"- Max reward error: `{payload['max_reward_error']:.3e}`\n\n",
        "## Shape Check\n\n",
    ]
    for key, value in payload["shape_check"].items():
        lines.append(f"- {key}: `{value}`\n")
    lines.extend(
        [
            "\n## Episode Replay\n\n",
            "| ep | status | reason | frames | obs err | next obs err | reward err | failures |\n",
            "|---:|---|---|---:|---:|---:|---:|---|\n",
        ]
    )
    for item in payload["episode_results"]:
        reason = item["replay_eval"]["terminal_reason"] if item["replay_eval"] else "none"
        lines.append(
            f"| {item['episode_id']} | {item['status']} | {reason} | {item['frames']} | "
            f"{item['max_obs_error']:.3e} | {item['max_next_obs_error']:.3e} | {item['max_reward_error']:.3e} | "
            f"{'; '.join(item['failures']) or '-'} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- PASS means the dataset is structurally consistent with the frozen task contract and deterministic replay reproduces obs/reward labels within tolerance.\n",
            "- This is still dataset QA, not model training.\n",
        ]
    )
    report_path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay Stage2 lift-ball dataset v0 and validate labels.")
    parser.add_argument("--dataset", default=str(DATASET))
    parser.add_argument("--scene", default=str(CURRENT_LIFT_SCENE))
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--metadata", type=Path, default=META_OUT)
    parser.add_argument("--all-episodes", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--episode-id", type=int, default=0)
    parser.add_argument("--max-error-warn", type=float, default=1e-9)
    args = parser.parse_args()

    dataset_path = Path(args.dataset).resolve()
    if not dataset_path.exists():
        raise FileNotFoundError(dataset_path)
    data = np.load(dataset_path, allow_pickle=False)
    api = ArmHandStage1TaskAPI(args.scene)
    contract = api.get_task_contract()

    obs = data["obs"]
    actions = data["actions"]
    next_obs = data["next_obs"]
    rewards = data["rewards"]
    dones = data["dones"]
    episode_ids = data["episode_ids"].astype(np.int32)
    available = sorted(int(v) for v in np.unique(episode_ids))
    selected = available if args.all_episodes else [args.episode_id]

    shape_check = {
        "obs_dim_matches": obs.ndim == 2 and obs.shape[1] == contract["observation"]["dim"],
        "next_obs_dim_matches": next_obs.ndim == 2 and next_obs.shape[1] == contract["observation"]["dim"],
        "action_dim_matches": actions.ndim == 2 and actions.shape[1] == contract["action"]["dim"],
        "row_counts_match": len(obs) == len(actions) == len(next_obs) == len(rewards) == len(dones) == len(episode_ids),
        "contract_version_matches": str(data["contract_version"][0]) == TASK_CONTRACT_VERSION,
    }
    episode_results = [replay_episode(api, data, ep, max_error_warn=args.max_error_warn) for ep in selected]
    shape_status = "PASS" if all(shape_check.values()) else "FAIL"
    replay_status = "PASS" if all(item["status"] == "PASS" for item in episode_results) else "FAIL"
    status = "PASS" if shape_status == "PASS" and replay_status == "PASS" else "FAIL"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(dataset_path),
        "dataset_metadata": str(DATASET_META) if DATASET_META.exists() else None,
        "scene": str(Path(args.scene).resolve()),
        "contract_version": TASK_CONTRACT_VERSION,
        "episodes_checked": len(episode_results),
        "available_episodes": available,
        "shape_check": shape_check,
        "shape_status": shape_status,
        "replay_status": replay_status,
        "status": status,
        "max_obs_error": max(item["max_obs_error"] for item in episode_results) if episode_results else float("nan"),
        "max_next_obs_error": max(item["max_next_obs_error"] for item in episode_results) if episode_results else float("nan"),
        "max_reward_error": max(item["max_reward_error"] for item in episode_results) if episode_results else float("nan"),
        "episode_results": episode_results,
        "training_ready": False,
    }
    write_outputs(payload, args.report, args.metadata)
    print(f"Replay status: {status}")
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")


if __name__ == "__main__":
    main()
