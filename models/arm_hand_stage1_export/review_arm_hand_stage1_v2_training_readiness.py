#!/usr/bin/env python3
"""Training-readiness review for the Stage2 arm-hand v2 dataset-v0 smoke path."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_v2_bc_common import (
    DEFAULT_DATASET,
    DEFAULT_READINESS_META,
    DEFAULT_READINESS_REPORT,
    META,
    dataset_phase_lengths,
    episode_lengths,
    feature_config_from_dataset,
    json_ready,
    load_dataset,
    require_fields,
    split_by_episode,
    string_list,
)


REQUIRED_FIELDS = [
    "obs",
    "actions",
    "next_obs",
    "rewards",
    "dones",
    "successes",
    "episode_ids",
    "step_ids",
    "phase_ids",
    "phase_step_ids",
    "initial_ball_positions",
    "ball_offsets",
    "phase_name_table",
    "terminal_reason_table",
    "contract_version",
]


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload(args) -> dict[str, Any]:
    data = load_dataset(args.dataset)
    require_fields(data, REQUIRED_FIELDS)
    require_fields(data, [args.action_field])

    obs = data["obs"]
    actions = data[args.action_field]
    next_obs = data["next_obs"]
    episode_ids = data["episode_ids"].astype(np.int32)
    phase_ids = data["phase_ids"].astype(np.int32)
    phase_names = string_list(data["phase_name_table"])
    terminal_reasons = string_list(data["terminal_reason_table"])
    phase_lengths = dataset_phase_lengths(data)
    lengths_by_episode = episode_lengths(data)
    feature_config = feature_config_from_dataset(
        data,
        include_phase_features=not args.no_phase_features,
        feature_mode=args.feature_mode,
    )
    train_mask, val_mask, train_episodes, val_episodes = split_by_episode(episode_ids, args.val_fraction, args.seed)

    row_count = int(obs.shape[0])
    terminal_success_only = bool(np.all(data["successes"][data["dones"].astype(bool)]))
    hard_checks = {
        "required_fields_present": True,
        "obs_is_2d": obs.ndim == 2,
        "actions_is_2d": actions.ndim == 2,
        "next_obs_shape_matches": next_obs.shape == obs.shape,
        "row_counts_match": row_count
        == len(actions)
        == len(next_obs)
        == len(data["rewards"])
        == len(data["dones"])
        == len(data["successes"])
        == len(episode_ids),
        "obs_finite": bool(np.isfinite(obs).all()),
        "actions_finite": bool(np.isfinite(actions).all()),
        "next_obs_finite": bool(np.isfinite(next_obs).all()),
        "contract_version_matches": str(data["contract_version"][0]) == args.contract_version,
        "all_episodes_terminal_success": terminal_success_only or bool(args.allow_terminal_failures),
        "episode_split_has_train": bool(np.any(train_mask)),
        "episode_split_has_val": bool(np.any(val_mask)),
    }

    replay_meta = load_optional_json(META / "arm_hand_stage1_v2_dataset_v0_replay.json")
    replay_status = replay_meta.get("status") if replay_meta else "missing"
    hard_checks["replay_qa_pass"] = replay_status == "PASS"

    action_std = actions.astype(np.float64).std(axis=0)
    obs_std = obs.astype(np.float64).std(axis=0)
    low_variance_actions = [int(i) for i, value in enumerate(action_std) if float(value) < args.low_variance_warn]
    low_variance_obs = [int(i) for i, value in enumerate(obs_std) if float(value) < args.low_variance_warn]
    phase_counts = {
        phase_names[int(phase_id)]: int(np.sum(phase_ids == phase_id)) for phase_id in sorted(int(v) for v in np.unique(phase_ids))
    }
    terminal_reason_ids = data["terminal_reason_ids"].astype(np.int32) if "terminal_reason_ids" in data.files else np.zeros(row_count, dtype=np.int32)
    terminal_reason_counts: dict[str, int] = {}
    done_idxs = np.where(data["dones"].astype(bool))[0]
    for idx in done_idxs:
        reason_id = int(terminal_reason_ids[idx])
        reason = terminal_reasons[reason_id] if 0 <= reason_id < len(terminal_reasons) else f"unknown_{reason_id}"
        terminal_reason_counts[reason] = terminal_reason_counts.get(reason, 0) + 1

    bc_smoke_ready = bool(all(hard_checks.values()))
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(Path(args.dataset).resolve()),
        "contract_version": str(data["contract_version"][0]),
        "task_name": str(data["task_name"][0]) if "task_name" in data.files else "unknown",
        "action_field": str(args.action_field),
        "status": "PASS" if bc_smoke_ready else "BLOCKED",
        "bc_smoke_ready": bc_smoke_ready,
        "training_ready": False,
        "training_scope": "BC smoke only; not a promoted baseline; RL remains blocked.",
        "hard_checks": hard_checks,
        "replay_status": replay_status,
        "row_count": row_count,
        "obs_shape": list(obs.shape),
        "actions_shape": list(actions.shape),
        "next_obs_shape": list(next_obs.shape),
        "episode_count": int(len(lengths_by_episode)),
        "episode_lengths": lengths_by_episode,
        "success_count": int(np.sum(data["dones"].astype(bool) & data["successes"].astype(bool))),
        "terminal_reason_counts": terminal_reason_counts,
        "phase_names": phase_names,
        "phase_lengths_observed": phase_lengths,
        "phase_counts": phase_counts,
        "feature_config": feature_config,
        "train_episodes": train_episodes,
        "val_episodes": val_episodes,
        "train_samples": int(train_mask.sum()),
        "val_samples": int(val_mask.sum()),
        "obs_range": [float(np.min(obs)), float(np.max(obs))],
        "action_range": [float(np.min(actions)), float(np.max(actions))],
        "reward_range": [float(np.min(data["rewards"])), float(np.max(data["rewards"]))],
        "low_variance_action_dims": low_variance_actions,
        "low_variance_obs_dims": low_variance_obs,
        "warnings": [
            "Dataset v0 has only 9 scripted episodes and should be used only for first BC smoke training.",
            "Phase features are enabled by default because this dataset is a scripted multi-stage controller.",
            "Online rollout success is not guaranteed by low offline validation loss.",
        ]
        + (
            ["Terminal failures are present and allowed for this review because this dataset is intended to include boundary states."]
            if args.allow_terminal_failures and not terminal_success_only
            else []
        ),
        "next_step": "Run train_arm_hand_stage1_v2_bc_smoke.py only if status is PASS.",
    }
    return payload


def write_report(payload: dict[str, Any], report_path: Path, meta_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm-Hand Stage1 V2 Training Readiness Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Contract: `{payload['contract_version']}`\n",
        f"- Status: **{payload['status']}**\n",
        f"- BC smoke ready: `{payload['bc_smoke_ready']}`\n",
        f"- Training ready: **No, experimental BC smoke only**\n",
        f"- Rows: `{payload['row_count']}`\n",
        f"- Action field: `{payload['action_field']}`\n",
        f"- Episodes: `{payload['episode_count']}`\n",
        f"- Success terminals: `{payload['success_count']} / {payload['episode_count']}`\n",
        f"- Replay QA: `{payload['replay_status']}`\n",
        f"- Recommended feature mode: `{payload['feature_config']['feature_mode']}`\n",
        f"- Train episodes: `{payload['train_episodes']}`\n",
        f"- Val episodes: `{payload['val_episodes']}`\n",
        f"- Train samples: `{payload['train_samples']}`\n",
        f"- Val samples: `{payload['val_samples']}`\n\n",
        "## Hard Checks\n\n",
        "| check | pass |\n",
        "|---|---:|\n",
    ]
    for key, value in payload["hard_checks"].items():
        lines.append(f"| {key} | {value} |\n")
    lines.extend(
        [
            "\n## Phase Coverage\n\n",
            "| phase | observed length | rows |\n",
            "|---|---:|---:|\n",
        ]
    )
    for idx, name in enumerate(payload["phase_names"]):
        lines.append(
            f"| {name} | {payload['phase_lengths_observed'][idx]} | {payload['phase_counts'].get(name, 0)} |\n"
        )
    lines.extend(
        [
            "\n## Ranges\n\n",
            f"- Observation range: `{payload['obs_range']}`\n",
            f"- Action range: `{payload['action_range']}`\n",
            f"- Reward range: `{payload['reward_range']}`\n",
            f"- Low-variance action dims: `{payload['low_variance_action_dims']}`\n",
            f"- Low-variance obs dims count: `{len(payload['low_variance_obs_dims'])}`\n\n",
            "## Interpretation\n\n",
            "- PASS means the dataset is acceptable for one experimental offline BC smoke run.\n",
            "- This does not promote the dataset to a maintained training baseline.\n",
            "- If terminal failures were allowed, they are treated as boundary-state coverage, not task success evidence.\n",
            "- RL remains blocked until the reset distribution, reward design, and broader data quality are accepted.\n\n",
            "## Next Step\n\n",
            f"{payload['next_step']}\n",
        ]
    )
    report_path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Review dataset-v0 readiness for experimental BC smoke training.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--report", type=Path, default=DEFAULT_READINESS_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_READINESS_META)
    parser.add_argument("--contract-version", default="stage2_lift_ball_v0_1")
    parser.add_argument("--action-field", default="actions", help="Dataset action field to review for BC targets.")
    parser.add_argument("--allow-terminal-failures", action="store_true")
    parser.add_argument("--val-fraction", type=float, default=0.22)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--low-variance-warn", type=float, default=1e-8)
    parser.add_argument(
        "--feature-mode",
        choices=["obs_phase", "obs_only", "phase_only", "obs_phase_offset", "obs_only_offset", "phase_offset"],
        default="phase_only",
        help="Recommended mode for the current smoke path after the first online repair.",
    )
    parser.add_argument("--no-phase-features", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_report(payload, args.report, args.metadata)
    print(f"Readiness status: {payload['status']}")
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0 if payload["bc_smoke_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
