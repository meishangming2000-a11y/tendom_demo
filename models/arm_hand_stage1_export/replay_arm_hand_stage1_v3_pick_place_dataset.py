#!/usr/bin/env python3
"""Replay and QA Stage2 pick-place datasets."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import ArmHandStage1TaskAPI, json_ready
from arm_hand_stage1_v3_pick_place_task_api import (
    CURRENT_PICK_PLACE_SCENE,
    DEFAULT_REQUIRED_STABLE_STEPS,
    DEFAULT_TARGET_RADIUS_M,
    TASK_CONTRACT_VERSION,
    compute_pick_place_metrics,
    evaluate_pick_place_state,
)
from collect_arm_hand_stage1_v3_pick_place_dataset_v0_5 import extended_observation, pick_place_reward, update_counters


ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "data" / "arm_hand_stage1_v3_pick_place_dataset_v0_5.npz"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
REPORT = DOCS / "arm_hand_stage1_v3_pick_place_dataset_v0_5_replay_report.md"
META_OUT = META / "arm_hand_stage1_v3_pick_place_dataset_v0_5_replay.json"


def reason_table(data) -> list[str]:
    return [str(item) for item in data["terminal_reason_table"]]


def compare_vectors(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        return float("inf")
    return float(np.max(np.abs(a - b))) if a.size else 0.0


def final_reason_from_metrics(metrics: dict[str, Any], stable_steps: int, required_stable_steps: int, target_radius: float) -> str:
    contact = metrics["contact"]
    if metrics["target_distance_xy"] > target_radius:
        return "target_miss"
    if contact["ball_hand_contact_count"] > 0:
        return "release_contact_remaining"
    if stable_steps < required_stable_steps:
        return "placement_not_stable"
    return "success_pick_place_ball"


def replay_episode(
    api: ArmHandStage1TaskAPI,
    data,
    episode_id: int,
    *,
    max_error_warn: float,
) -> dict[str, Any]:
    episode_ids = data["episode_ids"].astype(np.int32)
    idxs = np.where(episode_ids == episode_id)[0]
    if len(idxs) == 0:
        raise ValueError(f"Episode {episode_id} not found")

    actions = data["actions"]
    obs = data["obs"]
    next_obs = data["next_obs"]
    rewards = data["rewards"]
    dones = data["dones"]
    phase_ids = data["phase_ids"].astype(np.int32)
    phase_names = [str(item) for item in data["phase_name_table"]]
    terminal_reason_ids = data["terminal_reason_ids"].astype(np.int32)
    terminal_reasons = reason_table(data)
    initial_ball = data["initial_ball_positions"][idxs[0]].astype(np.float64)
    target_center = data["target_centers"][idxs[0]].astype(np.float64)
    target_radius = float(data["target_radius"][0]) if "target_radius" in data else DEFAULT_TARGET_RADIUS_M
    required_stable_steps = int(data["required_stable_steps"][0]) if "required_stable_steps" in data else DEFAULT_REQUIRED_STABLE_STEPS

    api.reset_hand_open(ball_position=initial_ball)
    counters: dict[str, Any] = {
        "lifted_once": False,
        "release_started": False,
        "transport_floor_contacts": 0,
        "stable_target_steps": 0,
        "step_count": 0,
    }
    max_obs_error = 0.0
    max_next_obs_error = 0.0
    max_reward_error = 0.0
    final_eval = None
    terminal_idx = None
    failures = []

    for local_i, idx in enumerate(idxs):
        current_obs, _ = extended_observation(api, target_center)
        max_obs_error = max(max_obs_error, compare_vectors(current_obs, obs[idx]))
        phase_name = phase_names[int(phase_ids[idx])]
        api.step_action(actions[idx], n=1, pin_ball=False)
        metrics = update_counters(api, initial_ball, target_center, phase_name, counters, target_radius)
        evaluation = evaluate_pick_place_state(
            api,
            initial_ball,
            target_center=target_center,
            step_count=int(counters["step_count"]),
            max_episode_steps=len(idxs),
            lifted_once=bool(counters["lifted_once"]),
            release_started=bool(counters["release_started"]),
            stable_target_steps=int(counters["stable_target_steps"]),
            transport_floor_contacts=int(counters["transport_floor_contacts"]),
            target_radius_m=target_radius,
            required_stable_steps=required_stable_steps,
        )
        replay_next, _ = extended_observation(api, target_center)
        max_next_obs_error = max(max_next_obs_error, compare_vectors(replay_next, next_obs[idx]))
        replay_reward = pick_place_reward(metrics, counters, bool(evaluation["success"]), bool(evaluation["failure"]))
        max_reward_error = max(max_reward_error, abs(float(replay_reward) - float(rewards[idx])))
        final_eval = evaluation
        if bool(dones[idx]):
            terminal_idx = int(idx)
            break

    if final_eval is None:
        failures.append("no frames replayed")
    elif terminal_idx is None:
        failures.append("dataset episode has no terminal done row")
    else:
        expected_reason = terminal_reasons[int(terminal_reason_ids[terminal_idx])]
        if final_eval["terminal_reason"] != expected_reason:
            failures.append(f"terminal reason mismatch: replay={final_eval['terminal_reason']} dataset={expected_reason}")
        if max_obs_error > max_error_warn:
            failures.append(f"obs max error {max_obs_error:.3e} > {max_error_warn:.3e}")
        if max_next_obs_error > max_error_warn:
            failures.append(f"next_obs max error {max_next_obs_error:.3e} > {max_error_warn:.3e}")
        if max_reward_error > max_error_warn:
            failures.append(f"reward max error {max_reward_error:.3e} > {max_error_warn:.3e}")

    final_metrics = compute_pick_place_metrics(api, initial_ball, target_center)
    gate_reason = final_reason_from_metrics(
        final_metrics,
        int(counters["stable_target_steps"]),
        required_stable_steps,
        target_radius,
    )
    gate_pass = (
        gate_reason == "success_pick_place_ball"
        and int(counters["transport_floor_contacts"]) == 0
        and int(final_metrics["contact"]["ball_hand_contact_count"]) == 0
    )
    if not gate_pass:
        failures.append(f"dataset gate failed: {gate_reason}")

    status = "PASS" if not failures else "FAIL"
    expected_reason = (
        terminal_reasons[int(terminal_reason_ids[terminal_idx])]
        if terminal_idx is not None
        else "none"
    )
    return {
        "episode_id": int(episode_id),
        "frames": int(len(idxs)),
        "terminal_dataset_index": terminal_idx,
        "expected_terminal_reason": expected_reason,
        "replay_eval": final_eval,
        "gate_reason": gate_reason,
        "gate_pass": bool(gate_pass),
        "stable_target_steps": int(counters["stable_target_steps"]),
        "transport_floor_contacts": int(counters["transport_floor_contacts"]),
        "final_target_distance_xy": float(final_metrics["target_distance_xy"]),
        "final_hand_contacts": int(final_metrics["contact"]["ball_hand_contact_count"]),
        "final_floor_contacts": int(final_metrics["contact"]["ball_floor_contact_count"]),
        "max_obs_error": max_obs_error,
        "max_next_obs_error": max_next_obs_error,
        "max_reward_error": max_reward_error,
        "status": status,
        "failures": failures,
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(json_ready(row), ensure_ascii=False) + "\n")


def write_outputs(payload: dict[str, Any], report_path: Path, metadata_path: Path, episodes_jsonl: Path | None) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    if episodes_jsonl:
        write_jsonl(episodes_jsonl, payload["episode_results"])

    lines = [
        "# Arm-Hand Stage1 V3 Pick-Place Dataset Replay QA Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Contract: `{payload['contract_version']}`\n",
        f"- Episodes checked: `{payload['episodes_checked']}`\n",
        f"- Status: **{payload['status']}**\n",
        f"- Shape check: `{payload['shape_status']}`\n",
        f"- Replay status: `{payload['replay_status']}`\n",
        f"- Dataset gate status: `{payload['dataset_gate_status']}`\n",
        f"- Max obs error: `{payload['max_obs_error']:.3e}`\n",
        f"- Max next_obs error: `{payload['max_next_obs_error']:.3e}`\n",
        f"- Max reward error: `{payload['max_reward_error']:.3e}`\n",
        f"- Success count: `{payload['success_count']} / {payload['episodes_checked']}`\n",
        f"- V0.6 needed now: **{payload['v0_6_needed_now']}**\n\n",
        "## Shape Check\n\n",
    ]
    for key, value in payload["shape_check"].items():
        lines.append(f"- {key}: `{value}`\n")
    lines.extend(
        [
            "\n## Episode Replay\n\n",
            "| ep | status | reason | gate | frames | target xy m | stable steps | transport floor | final hand | obs err | next err | failures |\n",
            "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|\n",
        ]
    )
    for item in payload["episode_results"]:
        reason = item["replay_eval"]["terminal_reason"] if item["replay_eval"] else "none"
        lines.append(
            f"| {item['episode_id']} | {item['status']} | {reason} | {item['gate_reason']} | "
            f"{item['frames']} | {item['final_target_distance_xy']:.6f} | "
            f"{item['stable_target_steps']} | {item['transport_floor_contacts']} | "
            f"{item['final_hand_contacts']} | {item['max_obs_error']:.3e} | "
            f"{item['max_next_obs_error']:.3e} | {'; '.join(item['failures']) or '-'} |\n"
        )
    lines.extend(
        [
            "\n## Self-Check\n\n",
            f"- Decision: `{payload['self_check_decision']}`\n",
            f"- Reason: {payload['self_check_reason']}\n\n",
            "## Interpretation\n\n",
            "- PASS means deterministic replay reproduces the dataset rows and each episode satisfies the fixed-target pick-place dataset gate.\n",
            "- This is still pre-training QA. The next gate is BC training plus online eval.\n",
        ]
    )
    report_path.write_text("".join(lines), encoding="utf-8")


def resolve_outputs(args) -> tuple[Path, Path, Path, Path | None]:
    run_dir = Path(args.run_dir).resolve() if args.run_dir else None
    report = args.report
    metadata = args.metadata
    episodes_jsonl = args.episodes_jsonl
    if run_dir:
        (run_dir / "eval").mkdir(parents=True, exist_ok=True)
        report = report or (run_dir / "eval" / "replay_qa_report.md")
        metadata = metadata or (run_dir / "eval" / "summary.json")
        episodes_jsonl = episodes_jsonl or (run_dir / "eval" / "episodes.jsonl")
    else:
        report = report or REPORT
        metadata = metadata or META_OUT
    return Path(report), Path(metadata), Path(episodes_jsonl) if episodes_jsonl else None, run_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay and QA a Stage2 pick-place dataset.")
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--scene", type=Path, default=CURRENT_PICK_PLACE_SCENE)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--metadata", type=Path, default=None)
    parser.add_argument("--episodes-jsonl", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--all-episodes", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--episode-id", type=int, default=0)
    parser.add_argument("--max-error-warn", type=float, default=1e-9)
    args = parser.parse_args()

    dataset_path = Path(args.dataset).resolve()
    if not dataset_path.exists():
        raise FileNotFoundError(dataset_path)
    report_path, metadata_path, episodes_jsonl, _ = resolve_outputs(args)
    data = np.load(dataset_path, allow_pickle=False)
    api = ArmHandStage1TaskAPI(args.scene)
    base_obs_dim = api.get_task_contract()["observation"]["dim"]
    obs = data["obs"]
    base_obs = data["base_obs"]
    actions = data["actions"]
    next_obs = data["next_obs"]
    rewards = data["rewards"]
    dones = data["dones"]
    episode_ids = data["episode_ids"].astype(np.int32)
    available = sorted(int(v) for v in np.unique(episode_ids))
    selected = available if args.all_episodes else [args.episode_id]

    shape_check = {
        "base_obs_dim_matches": base_obs.ndim == 2 and base_obs.shape[1] == base_obs_dim,
        "obs_dim_matches": obs.ndim == 2 and obs.shape[1] == base_obs_dim + 6,
        "next_obs_dim_matches": next_obs.ndim == 2 and next_obs.shape[1] == base_obs_dim + 6,
        "action_dim_matches": actions.ndim == 2 and actions.shape[1] == api.get_action_dim(),
        "row_counts_match": len(obs) == len(actions) == len(next_obs) == len(rewards) == len(dones) == len(episode_ids),
        "contract_version_matches": str(data["contract_version"][0]) == TASK_CONTRACT_VERSION,
    }
    episode_results = [replay_episode(api, data, ep, max_error_warn=args.max_error_warn) for ep in selected]
    shape_status = "PASS" if all(shape_check.values()) else "FAIL"
    replay_status = "PASS" if all(item["status"] == "PASS" for item in episode_results) else "FAIL"
    dataset_gate_status = "PASS" if all(item["gate_pass"] for item in episode_results) else "FAIL"
    status = "PASS" if shape_status == "PASS" and replay_status == "PASS" and dataset_gate_status == "PASS" else "FAIL"
    success_count = sum(1 for item in episode_results if item["gate_pass"])
    v0_6_needed_now = status != "PASS"
    if v0_6_needed_now:
        decision = "collect_v0_6_now"
        reason = "v0.5 failed replay or dataset gate; collect a corrected v0.6 before training."
    else:
        decision = "do_not_collect_v0_6_yet"
        reason = "v0.5 is replay-clean for fixed-target pick-place; train/eval first, then decide v0.6 from online policy failures."

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(dataset_path),
        "scene": str(Path(args.scene).resolve()),
        "contract_version": TASK_CONTRACT_VERSION,
        "episodes_checked": len(episode_results),
        "available_episodes": available,
        "shape_check": shape_check,
        "shape_status": shape_status,
        "replay_status": replay_status,
        "dataset_gate_status": dataset_gate_status,
        "status": status,
        "success_count": int(success_count),
        "max_obs_error": max(item["max_obs_error"] for item in episode_results) if episode_results else float("nan"),
        "max_next_obs_error": max(item["max_next_obs_error"] for item in episode_results) if episode_results else float("nan"),
        "max_reward_error": max(item["max_reward_error"] for item in episode_results) if episode_results else float("nan"),
        "episode_results": episode_results,
        "training_ready": status == "PASS",
        "v0_6_needed_now": bool(v0_6_needed_now),
        "self_check_decision": decision,
        "self_check_reason": reason,
    }
    write_outputs(payload, report_path, metadata_path, episodes_jsonl)
    print(f"Replay QA status: {status}")
    print(f"Success count: {success_count}/{len(episode_results)}")
    print(f"V0.6 needed now: {v0_6_needed_now}")
    print(f"Saved report: {report_path}")
    print(f"Saved metadata: {metadata_path}")
    if episodes_jsonl:
        print(f"Saved episodes JSONL: {episodes_jsonl}")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
