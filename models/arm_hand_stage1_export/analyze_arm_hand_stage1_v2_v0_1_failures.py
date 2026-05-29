#!/usr/bin/env python3
"""Summarize the Stage2 dataset-v0.1 obs+phase timeout cases.

This is a diagnostic report generator only. It does not modify datasets,
checkpoints, or promoted baselines.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
from arm_hand_stage1_v2_bc_common import load_dataset
from eval_arm_hand_stage1_v2_bc_smoke import available_episode_ids, episode_offset


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DEFAULT_DATASET = ROOT / "data" / "arm_hand_stage1_v2_lift_ball_dataset_v0_1.npz"
DEFAULT_EVAL_META = META / "arm_hand_stage1_v2_bc_v0_1_obs_phase_strongreg_smooth_eval.json"
DEFAULT_REPORT = DOCS / "arm_hand_stage1_v2_v0_1_failure_analysis_report.md"
DEFAULT_META = META / "arm_hand_stage1_v2_v0_1_failure_analysis.json"


def first_row_index(data, episode_id: int) -> int:
    idxs = np.where(data["episode_ids"].astype(np.int32) == int(episode_id))[0]
    if len(idxs) == 0:
        raise KeyError(f"Episode {episode_id} not found in dataset")
    return int(idxs[0])


def profile_name_for_episode(data, episode_id: int) -> str:
    if "behavior_profile_ids" not in data or "behavior_profile_table" not in data:
        return "unknown"
    idx = first_row_index(data, episode_id)
    profile_id = int(data["behavior_profile_ids"][idx])
    table = [str(item) for item in data["behavior_profile_table"]]
    return table[profile_id] if 0 <= profile_id < len(table) else f"profile_{profile_id}"


def terminal_reason_for_dataset_episode(data, episode_id: int) -> str:
    idxs = np.where(data["episode_ids"].astype(np.int32) == int(episode_id))[0]
    if len(idxs) == 0:
        return "missing"
    done_idxs = [idx for idx in idxs if bool(data["dones"][idx])]
    idx = done_idxs[-1] if done_idxs else idxs[-1]
    table = [str(item) for item in data["terminal_reason_table"]]
    reason_id = int(data["terminal_reason_ids"][idx])
    return table[reason_id] if 0 <= reason_id < len(table) else f"reason_{reason_id}"


def offset_key(offset: np.ndarray) -> str:
    rounded = [round(float(v), 5) for v in offset.tolist()]
    return json.dumps(rounded, separators=(",", ":"))


def summarize_failures(data, eval_payload: dict[str, Any]) -> dict[str, Any]:
    results = list(eval_payload.get("results", []))
    failed = [row for row in results if not bool(row.get("success"))]
    by_reason = Counter(str(row.get("terminal_reason", "unknown")) for row in failed)
    by_offset: dict[str, dict[str, Any]] = {}
    by_profile = Counter()

    rows = []
    for row in failed:
        episode_id = int(row["episode_id"])
        offset = episode_offset(data, episode_id)
        profile = profile_name_for_episode(data, episode_id)
        by_profile[profile] += 1
        key = offset_key(offset)
        metrics = row.get("final_metrics", {})
        contact = metrics.get("contact", {})
        entry = {
            "episode_id": episode_id,
            "profile": profile,
            "offset": offset,
            "eval_terminal_reason": str(row.get("terminal_reason", "unknown")),
            "dataset_terminal_reason": terminal_reason_for_dataset_episode(data, episode_id),
            "steps": int(row.get("steps", 0)),
            "lift_height_m": float(metrics.get("ball_lift_height", float("nan"))),
            "ball_hand_contacts": int(contact.get("ball_hand_contact_count", 0)),
            "ball_floor_contacts": int(contact.get("ball_floor_contact_count", 0)),
            "max_penetration_m": float(contact.get("max_penetration", float("nan"))),
        }
        rows.append(entry)
        by_offset.setdefault(
            key,
            {
                "offset": offset,
                "count": 0,
                "profiles": [],
                "episode_ids": [],
                "terminal_reasons": Counter(),
            },
        )
        by_offset[key]["count"] += 1
        by_offset[key]["profiles"].append(profile)
        by_offset[key]["episode_ids"].append(episode_id)
        by_offset[key]["terminal_reasons"][entry["eval_terminal_reason"]] += 1

    offset_rows = []
    for item in by_offset.values():
        offset_rows.append(
            {
                "offset": item["offset"],
                "count": int(item["count"]),
                "profiles": sorted(set(item["profiles"])),
                "episode_ids": sorted(item["episode_ids"]),
                "terminal_reasons": dict(item["terminal_reasons"]),
            }
        )
    offset_rows.sort(key=lambda item: (-int(item["count"]), item["offset"].tolist()))

    dataset_reasons = Counter(
        terminal_reason_for_dataset_episode(data, episode_id) for episode_id in available_episode_ids(data)
    )
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(Path(str(eval_payload.get("dataset", DEFAULT_DATASET))).resolve()),
        "eval_metadata": str(DEFAULT_EVAL_META.resolve()),
        "eval_summary": eval_payload.get("summary", {}),
        "failed_episode_count": len(failed),
        "failed_terminal_reasons": dict(by_reason),
        "failed_profile_counts": dict(by_profile),
        "failed_offsets": offset_rows,
        "failed_episodes": rows,
        "dataset_terminal_reason_counts": dict(dataset_reasons),
        "diagnosis": (
            "The retained obs+phase v0.1 failures cluster on the right-edge ball offsets. "
            "Final states show near-zero lift and zero ball-hand contacts, so the main gap is "
            "approach/closure coverage at the right boundary rather than lift-after-contact stability."
        ),
        "recommended_recovery_offsets": [
            [0.02, -0.01, 0.0],
            [0.02, 0.02, 0.0],
            [0.02, -0.015, 0.0],
            [0.02, -0.005, 0.0],
            [0.02, 0.015, 0.0],
            [0.02, 0.025, 0.0],
        ],
        "training_ready": False,
    }


def write_report(payload: dict[str, Any], report_path: Path, meta_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm-Hand Stage1 V2 V0.1 Failure Analysis\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Eval metadata: `{payload['eval_metadata']}`\n",
        f"- Eval success count: `{payload['eval_summary'].get('success_count')} / {payload['eval_summary'].get('episodes')}`\n",
        f"- Failed episodes: `{payload['failed_episode_count']}`\n",
        f"- Failed reasons: `{payload['failed_terminal_reasons']}`\n",
        f"- Failed profile counts: `{payload['failed_profile_counts']}`\n",
        f"- Dataset terminal reason counts: `{payload['dataset_terminal_reason_counts']}`\n",
        "- Training ready: **No, diagnostic only**\n\n",
        "## Failed Offsets\n\n",
        "| offset xyz | count | profiles | episodes | reasons |\n",
        "|---|---:|---|---|---|\n",
    ]
    for row in payload["failed_offsets"]:
        lines.append(
            f"| `{np.round(row['offset'], 5).tolist()}` | {row['count']} | "
            f"{', '.join(row['profiles'])} | {row['episode_ids']} | {row['terminal_reasons']} |\n"
        )
    lines.extend(
        [
            "\n## Failed Episodes\n\n",
            "| ep | profile | offset xyz | eval reason | dataset reason | steps | lift m | hand contacts | floor contacts | max pen m |\n",
            "|---:|---|---|---|---|---:|---:|---:|---:|---:|\n",
        ]
    )
    for row in payload["failed_episodes"]:
        lines.append(
            f"| {row['episode_id']} | {row['profile']} | `{np.round(row['offset'], 5).tolist()}` | "
            f"{row['eval_terminal_reason']} | {row['dataset_terminal_reason']} | {row['steps']} | "
            f"{row['lift_height_m']:.6f} | {row['ball_hand_contacts']} | {row['ball_floor_contacts']} | "
            f"{row['max_penetration_m']:.6f} |\n"
        )
    lines.extend(
        [
            "\n## Diagnosis\n\n",
            f"{payload['diagnosis']}\n\n",
            "## Recommended V0.2 Recovery Offsets\n\n",
        ]
    )
    for item in payload["recommended_recovery_offsets"]:
        lines.append(f"- `{item}`\n")
    report_path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze Stage2 v0.1 obs+phase rollout failures.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--eval-metadata", type=Path, default=DEFAULT_EVAL_META)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_META)
    args = parser.parse_args()

    data = load_dataset(args.dataset)
    eval_payload = json.loads(args.eval_metadata.read_text(encoding="utf-8"))
    payload = summarize_failures(data, eval_payload)
    payload["dataset"] = str(args.dataset.resolve())
    payload["eval_metadata"] = str(args.eval_metadata.resolve())
    write_report(payload, args.report, args.metadata)
    print(f"Failures: {payload['failed_episode_count']}")
    print(f"Failed offsets: {len(payload['failed_offsets'])}")
    print(f"Saved report: {args.report}")
    print(f"Saved metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
