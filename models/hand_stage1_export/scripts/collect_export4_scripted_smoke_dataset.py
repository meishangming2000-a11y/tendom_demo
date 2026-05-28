#!/usr/bin/env python3
"""Collect a tiny export4 scripted smoke dataset.

This is not training data for policy learning yet. It is a five-episode
adapter/data-shape smoke artifact for downstream pipeline development.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from export4_wrist2_common import (
    DATA_DIR,
    DOCS_DIR,
    LONG_FINGER_TARGETS,
    METADATA_DIR,
    PRESHAPE_TARGETS,
    SCENE_TUNED,
    THUMB_SMOKE_TARGETS,
    actuator_names,
    contact_summary,
    ctrl_from_targets,
    fingertip_metrics,
    load_model,
    phase_metrics,
    set_ball_position,
    step_ctrl,
    write_json,
    write_text,
)
from test_export4_adapter_mapping import build_obs


DEFAULT_DATASET = DATA_DIR / "export4_scripted_smoke_dataset.npz"
DEFAULT_REPORT = DOCS_DIR / "export4_scripted_smoke_dataset_report.md"
DEFAULT_METADATA = METADATA_DIR / "export4_scripted_smoke_dataset_summary.json"

PHASES = [
    ("open_hand", {}),
    ("preshape", PRESHAPE_TARGETS),
    ("close_four_fingers", LONG_FINGER_TARGETS),
    ("close_thumb", {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}),
    ("hold", {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}),
]

BALL_POSITIONS = [
    [0.0, -0.10, 0.21],
    [0.0, 0.10, 0.21],
    [0.0, 0.08, 0.21],
    [0.0, -0.08, 0.21],
    [0.015, 0.10, 0.21],
]


def classify_episode(final_metrics: Dict[str, Any]) -> str:
    if final_metrics["ball_hand_contact_count"] > 0 and final_metrics["max_penetration"] < 0.008:
        return "contact_smoke_pass"
    if final_metrics["four_finger_avg_tip_ball_distance"] < 0.08:
        return "visual_close_no_contact"
    return "fail_far_from_ball"


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect five export4 scripted smoke episodes.")
    parser.add_argument("--scene", default=str(SCENE_TUNED))
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--steps-per-phase", type=int, default=30)
    args = parser.parse_args()

    scene = Path(args.scene).resolve()
    mujoco, model, data = load_model(scene)
    act_names = actuator_names(model)

    obs_rows: List[np.ndarray] = []
    action_rows: List[np.ndarray] = []
    episode_ids: List[int] = []
    step_ids: List[int] = []
    phase_ids: List[int] = []
    phase_names: List[str] = []
    ball_rows: List[List[float]] = []
    episode_summaries: List[Dict[str, Any]] = []

    for episode in range(int(args.episodes)):
        ball_position = BALL_POSITIONS[episode % len(BALL_POSITIONS)]
        data.qpos[:] = model.qpos0
        data.qvel[:] = 0.0
        data.ctrl[:] = 0.0
        set_ball_position(model, data, mujoco, ball_position)
        mujoco.mj_forward(model, data)
        global_step = 0
        phase_metrics_rows = []

        for phase_idx, (phase_name, targets) in enumerate(PHASES):
            ctrl = ctrl_from_targets(model, dict(targets))
            steps = int(args.steps_per_phase)
            start = data.ctrl.copy()
            for local_step in range(steps):
                alpha = local_step / max(1, steps - 1)
                target_ctrl = (1.0 - alpha) * start + alpha * ctrl
                data.ctrl[:] = target_ctrl
                set_ball_position(model, data, mujoco, ball_position)
                mujoco.mj_step(model, data)
                set_ball_position(model, data, mujoco, ball_position)
                mujoco.mj_forward(model, data)
                obs = build_obs(model, data, mujoco, ball_position)["vector"]
                obs_rows.append(obs)
                action_rows.append(data.ctrl.copy())
                episode_ids.append(episode)
                step_ids.append(global_step)
                phase_ids.append(phase_idx)
                phase_names.append(phase_name)
                ball_rows.append(ball_position)
                global_step += 1
            phase_metrics_rows.append({"phase": phase_name, "metrics": phase_metrics(model, data, mujoco, ball_position)})

        final_metrics = phase_metrics_rows[-1]["metrics"]
        episode_summaries.append(
            {
                "episode": episode,
                "ball_position": ball_position,
                "steps": global_step,
                "label": classify_episode(final_metrics),
                "final_metrics": final_metrics,
                "phase_metrics": phase_metrics_rows,
            }
        )

    obs = np.asarray(obs_rows, dtype=np.float64)
    actions = np.asarray(action_rows, dtype=np.float64)
    episode_ids_np = np.asarray(episode_ids, dtype=np.int32)
    step_ids_np = np.asarray(step_ids, dtype=np.int32)
    phase_ids_np = np.asarray(phase_ids, dtype=np.int32)
    ball_np = np.asarray(ball_rows, dtype=np.float64)

    dataset = Path(args.dataset).resolve()
    dataset.parent.mkdir(parents=True, exist_ok=True)
    if dataset.exists():
        from export4_wrist2_common import backup_if_exists

        backup_if_exists(dataset, "before_scripted_smoke_dataset")
    np.savez_compressed(
        dataset,
        obs=obs,
        actions=actions,
        episode_ids=episode_ids_np,
        step_ids=step_ids_np,
        phase_ids=phase_ids_np,
        ball_positions=ball_np,
        joint_names=np.asarray([], dtype=object),
        actuator_names=np.asarray(act_names, dtype=object),
        phase_name_table=np.asarray([name for name, _ in PHASES], dtype=object),
    )

    labels = {summary["label"]: sum(1 for item in episode_summaries if item["label"] == summary["label"]) for summary in episode_summaries}
    report_payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(scene),
        "dataset": str(dataset),
        "episodes": int(args.episodes),
        "steps_per_phase": int(args.steps_per_phase),
        "obs_shape": list(obs.shape),
        "action_shape": list(actions.shape),
        "action_dim": int(model.nu),
        "actuator_names": act_names,
        "labels": labels,
        "episode_summaries": episode_summaries,
        "wrist_2_joint_in_action": "wrist_2_joint_pos" in act_names,
        "notes": [
            "Ball is pinned during collection. This dataset is for adapter/data-shape smoke only.",
            "No RL, BC, neural training, CAD edit, STL edit, or tendon routing was performed.",
        ],
    }
    write_json(Path(args.metadata).resolve(), report_payload, "before_scripted_smoke_dataset_summary")

    lines = [
        "# Export4 Scripted Smoke Dataset Report\n\n",
        f"Generated: {report_payload['generated_at']}\n\n",
        f"- Scene: `{report_payload['scene']}`\n",
        f"- Dataset: `{report_payload['dataset']}`\n",
        f"- Episodes: `{report_payload['episodes']}`\n",
        f"- Steps per phase: `{report_payload['steps_per_phase']}`\n",
        f"- Obs shape: `{report_payload['obs_shape']}`\n",
        f"- Action shape: `{report_payload['action_shape']}`\n",
        f"- Action dim: `{report_payload['action_dim']}`\n",
        f"- wrist_2 in action: `{report_payload['wrist_2_joint_in_action']}`\n",
        f"- Labels: `{report_payload['labels']}`\n\n",
        "## Episode Summary\n\n",
        "| episode | ball | label | contacts | max pen | four-tip avg | thumb-ball | thumb-index |\n",
        "|---:|---|---|---:|---:|---:|---:|---:|\n",
    ]
    for summary in episode_summaries:
        metrics = summary["final_metrics"]
        lines.append(
            f"| {summary['episode']} | `{summary['ball_position']}` | {summary['label']} | "
            f"{metrics['contact_count']} | {metrics['max_penetration']:.6f} | "
            f"{metrics['four_finger_avg_tip_ball_distance']:.6f} | {metrics['thumb_ball_distance']:.6f} | "
            f"{metrics['thumb_index_distance']:.6f} |\n"
        )
    lines.extend(
        [
            "\n## Notes\n\n",
            "- This is deliberately tiny: 5 scripted episodes only.\n",
            "- It is useful for adapter, logging, shape, and replay tests.\n",
            "- It is not yet suitable as training data because the default grasp side/contact behavior is still unresolved.\n",
        ]
    )
    write_text(Path(args.report).resolve(), "".join(lines), "before_scripted_smoke_dataset_report")
    print(f"Saved dataset: {dataset}")
    print(f"Saved report: {Path(args.report).resolve()}")
    print(f"Saved metadata: {Path(args.metadata).resolve()}")


if __name__ == "__main__":
    main()
