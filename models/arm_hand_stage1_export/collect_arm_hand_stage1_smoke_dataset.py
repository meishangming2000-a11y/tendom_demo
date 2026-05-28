#!/usr/bin/env python3
"""Collect a tiny scripted smoke dataset for the arm + export4 hand.

This is a five-episode adapter/replay artifact, not training data.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import DEFAULT_SCENE, load_model, json_ready


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DEFAULT_DATASET = DATA / "arm_hand_stage1_scripted_smoke_dataset_v0.npz"
DEFAULT_REPORT = DOCS / "arm_hand_stage1_scripted_smoke_dataset_report.md"
DEFAULT_META = META / "arm_hand_stage1_scripted_smoke_dataset.json"

PRESHAPE_TARGETS = {
    "index_mcp_flex_joint": -0.035,
    "middle_mcp_flex_joint": -0.035,
    "ring_mcp_flex_joint": -0.020,
    "little_mcp_flex_joint": -0.015,
    "index_mcp_abd_joint": -0.34,
    "middle_mcp_abd_joint": -0.38,
    "ring_mcp_abd_joint": -0.20,
    "little_mcp_abd_joint": -0.15,
    "index_pip_joint": -0.48,
    "middle_pip_joint": -0.52,
    "ring_pip_joint": -0.20,
    "little_pip_joint": -0.16,
    "index_dip_joint": -0.22,
    "middle_dip_joint": -0.24,
    "ring_dip_joint": -0.10,
    "little_dip_joint": -0.08,
}

LONG_FINGER_TARGETS = {
    "index_mcp_flex_joint": -0.06,
    "middle_mcp_flex_joint": -0.06,
    "ring_mcp_flex_joint": -0.05,
    "little_mcp_flex_joint": -0.04,
    "index_mcp_abd_joint": -0.58,
    "middle_mcp_abd_joint": -0.64,
    "ring_mcp_abd_joint": -0.62,
    "little_mcp_abd_joint": -0.54,
    "index_pip_joint": -0.82,
    "middle_pip_joint": -0.88,
    "ring_pip_joint": -0.84,
    "little_pip_joint": -0.76,
    "index_dip_joint": -0.42,
    "middle_dip_joint": -0.46,
    "ring_dip_joint": -0.44,
    "little_dip_joint": -0.40,
}

THUMB_SMOKE_TARGETS = {
    "thumb_cmc_abd_joint": -0.30,
    "thumb_cmc_joint": 0.0,
    "thumb_mcp_joint": 0.25,
    "thumb_ip_joint": -0.25,
}

PHASES = [
    ("open_hand", {}),
    ("preshape", PRESHAPE_TARGETS),
    ("close_four_fingers", LONG_FINGER_TARGETS),
    ("close_thumb_smoke", {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}),
    ("hold", {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}),
]

# Small offsets around the validated default ball pose. These are smoke
# variations only; the ball is pinned during rollout collection.
BALL_OFFSETS = [
    [0.0, 0.0, 0.0],
    [0.006, 0.0, 0.0],
    [-0.006, 0.0, 0.0],
    [0.0, 0.006, 0.0],
    [0.0, -0.006, 0.0],
]


def classify(final_obs: dict[str, Any]) -> str:
    contact = final_obs["contact_summary"]
    distances = final_obs["fingertip_ball_distances"]
    four = np.mean([distances[name] for name in ["index", "middle", "ring", "little"]])
    if contact["max_penetration"] > 0.01:
        return "too_much_penetration"
    if contact["ball_hand_contact_count"] >= 1 and four < 0.07:
        return "contact_smoke_pass"
    if four < 0.08:
        return "visual_close_no_contact"
    return "far_from_ball"


def scalar_metrics(obs: dict[str, Any]) -> dict[str, Any]:
    distances = obs["fingertip_ball_distances"]
    four = [distances[name] for name in ["index", "middle", "ring", "little"]]
    contact = obs["contact_summary"]
    return {
        "contact_count": int(contact["contact_count"]),
        "ball_hand_contact_count": int(contact["ball_hand_contact_count"]),
        "ball_arm_contact_count": int(contact["ball_arm_contact_count"]),
        "max_penetration": float(contact["max_penetration"]),
        "four_finger_avg_tip_ball_distance": float(np.mean(four)),
        "thumb_ball_distance": float(distances["thumb"]),
        "thumb_index_distance": float(np.linalg.norm(obs["fingertip_positions"]["thumb"] - obs["fingertip_positions"]["index"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--steps-per-phase", type=int, default=48)
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    args = parser.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)

    api = load_model(args.scene)
    default_ball = api.get_ball_pose()["position"].copy()

    qpos_rows = []
    qvel_rows = []
    ctrl_rows = []
    obs_rows = []
    episode_ids = []
    step_ids = []
    phase_ids = []
    ball_rows = []
    episode_summaries = []

    for ep in range(args.episodes):
        offset = np.asarray(BALL_OFFSETS[ep % len(BALL_OFFSETS)], dtype=np.float64)
        ball = default_ball + offset
        api.reset_hand_open()
        api.set_ball_pose(*ball)
        global_step = 0
        phase_summaries = []
        for phase_idx, (phase_name, targets) in enumerate(PHASES):
            target_action = api.action_from_targets(targets)
            start_action = api.data.ctrl.copy()
            for local_step in range(max(1, args.steps_per_phase)):
                alpha = local_step / max(1, args.steps_per_phase - 1)
                action = (1.0 - alpha) * start_action + alpha * target_action
                api.apply_action(action)
                obs = api.step(1, pin_ball=True)
                qpos_rows.append(obs["qpos"])
                qvel_rows.append(obs["qvel"])
                ctrl_rows.append(obs["ctrl"])
                obs_rows.append(obs["vector"])
                episode_ids.append(ep)
                step_ids.append(global_step)
                phase_ids.append(phase_idx)
                ball_rows.append(ball.copy())
                global_step += 1
            phase_summaries.append({"phase": phase_name, "metrics": scalar_metrics(api.get_observation())})
        final_obs = api.get_observation()
        episode_summaries.append(
            {
                "episode": ep,
                "ball_position": ball,
                "offset": offset,
                "steps": global_step,
                "label": classify(final_obs),
                "final_metrics": scalar_metrics(final_obs),
                "phase_summaries": phase_summaries,
            }
        )

    dataset_path = Path(args.dataset).resolve()
    if dataset_path.exists():
        archive = ROOT / "archive"
        archive.mkdir(parents=True, exist_ok=True)
        dataset_path.replace(archive / f"{dataset_path.stem}.before_overwrite.{datetime.now().strftime('%Y%m%d_%H%M%S')}{dataset_path.suffix}")

    np.savez_compressed(
        dataset_path,
        qpos=np.asarray(qpos_rows, dtype=np.float64),
        qvel=np.asarray(qvel_rows, dtype=np.float64),
        ctrl=np.asarray(ctrl_rows, dtype=np.float64),
        obs=np.asarray(obs_rows, dtype=np.float64),
        episode_ids=np.asarray(episode_ids, dtype=np.int32),
        step_ids=np.asarray(step_ids, dtype=np.int32),
        phase_ids=np.asarray(phase_ids, dtype=np.int32),
        ball_positions=np.asarray(ball_rows, dtype=np.float64),
        joint_names=np.asarray(api.get_joint_names(), dtype=object),
        actuator_names=np.asarray(api.get_actuator_names(), dtype=object),
        phase_name_table=np.asarray([name for name, _ in PHASES], dtype=object),
        scene=str(api.scene_path),
    )

    labels = {}
    for item in episode_summaries:
        labels[item["label"]] = labels.get(item["label"], 0) + 1
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(api.scene_path),
        "dataset": str(dataset_path),
        "episodes": int(args.episodes),
        "steps_per_phase": int(args.steps_per_phase),
        "total_steps": len(obs_rows),
        "qpos_shape": list(np.asarray(qpos_rows).shape),
        "qvel_shape": list(np.asarray(qvel_rows).shape),
        "ctrl_shape": list(np.asarray(ctrl_rows).shape),
        "obs_shape": list(np.asarray(obs_rows).shape),
        "action_dim": api.get_action_dim(),
        "joint_names": api.get_joint_names(),
        "actuator_names": api.get_actuator_names(),
        "labels": labels,
        "episode_summaries": episode_summaries,
        "training_ready": False,
        "notes": [
            "Ball is pinned during each rollout.",
            "Dataset is for replay/adapter smoke only, not policy training.",
        ],
    }
    DEFAULT_META.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm-Hand Stage1 Scripted Smoke Dataset Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Episodes: `{payload['episodes']}`\n",
        f"- Total steps: `{payload['total_steps']}`\n",
        f"- qpos shape: `{payload['qpos_shape']}`\n",
        f"- qvel shape: `{payload['qvel_shape']}`\n",
        f"- ctrl/action shape: `{payload['ctrl_shape']}`\n",
        f"- obs shape: `{payload['obs_shape']}`\n",
        f"- Labels: `{payload['labels']}`\n",
        f"- Training ready: **No**\n\n",
        "## Episodes\n\n",
        "| ep | label | ball | contacts | max pen | four avg | thumb-ball | thumb-index |\n",
        "|---:|---|---|---:|---:|---:|---:|---:|\n",
    ]
    for item in episode_summaries:
        m = item["final_metrics"]
        lines.append(
            f"| {item['episode']} | {item['label']} | `{np.round(item['ball_position'], 5).tolist()}` | "
            f"{m['ball_hand_contact_count']} | {m['max_penetration']:.6f} | "
            f"{m['four_finger_avg_tip_ball_distance']:.6f} | {m['thumb_ball_distance']:.6f} | {m['thumb_index_distance']:.6f} |\n"
        )
    lines.extend(
        [
            "\n## Notes\n\n",
            "- This is intentionally small and pinned-ball. It verifies data shapes, staged control, contacts, and replayability.\n",
            "- It should not be used for RL/BC training yet.\n",
        ]
    )
    DEFAULT_REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"Saved dataset: {dataset_path}")
    print(f"Saved report: {DEFAULT_REPORT}")
    print(f"Saved metadata: {DEFAULT_META}")


if __name__ == "__main__":
    main()
