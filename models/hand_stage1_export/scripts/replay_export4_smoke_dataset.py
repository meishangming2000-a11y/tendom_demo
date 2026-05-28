#!/usr/bin/env python3
"""Replay the tiny export4 scripted smoke dataset."""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from export4_task_api import load_model
from export4_wrist2_common import DATA_DIR, DOCS_DIR, SCENE_TUNED, json_ready, render_standard_views, write_text


DEFAULT_DATASET = DATA_DIR / "export4_scripted_smoke_dataset.npz"
DEFAULT_REPORT = DOCS_DIR / "export4_replay_report.md"
DEFAULT_VISUAL_DIR = DOCS_DIR / "visual_checks_export4_replay"


def replay_dataset(args) -> Dict[str, Any]:
    dataset = Path(args.dataset).resolve()
    if not dataset.exists():
        raise FileNotFoundError(dataset)
    api = load_model(args.scene)
    data = np.load(dataset, allow_pickle=True)
    obs = data["obs"]
    actions = data["actions"] if "actions" in data.files else data["ctrl"]
    episode_ids = data["episode_ids"] if "episode_ids" in data.files else np.zeros(len(obs), dtype=np.int32)
    available_episodes = sorted(int(v) for v in np.unique(episode_ids))
    selected = args.episode_id if args.episode_id is not None else available_episodes[0]
    if selected not in available_episodes:
        raise ValueError(f"Episode {selected} not in dataset. Available: {available_episodes}")
    idxs = np.where(episode_ids == selected)[0]
    if args.max_frames:
        idxs = idxs[: args.max_frames]

    action_dim_matches = actions.shape[1] == api.get_action_dim()
    task_api_obs_dim = len(api.get_observation()["vector"])
    obs_dim_matches_task_api = obs.shape[1] == task_api_obs_dim
    qpos_prefix_available = obs.shape[1] >= api.model.nq
    qvel_prefix_available = obs.shape[1] >= api.model.nq + api.model.nv

    viewer = None
    if args.viewer:
        import mujoco.viewer

        viewer = mujoco.viewer.launch_passive(api.model, api.data)

    screenshots = {}
    keyframe_positions = {0, max(0, len(idxs) // 2), max(0, len(idxs) - 1)}
    try:
        for local_i, idx in enumerate(idxs):
            if qpos_prefix_available:
                api.data.qpos[:] = obs[idx, : api.model.nq]
            if qvel_prefix_available:
                api.data.qvel[:] = obs[idx, api.model.nq : api.model.nq + api.model.nv]
            if action_dim_matches:
                api.data.ctrl[:] = actions[idx]
            api.mujoco.mj_forward(api.model, api.data)
            if args.save_keyframes and local_i in keyframe_positions:
                screenshots[f"frame_{local_i}"] = render_standard_views(
                    api.model,
                    api.data,
                    api.mujoco,
                    Path(args.visual_dir).resolve(),
                    f"episode_{selected}_frame_{local_i:04d}",
                )
            if viewer is not None:
                viewer.sync()
                time.sleep(0.01)
    finally:
        if viewer is not None:
            viewer.close()

    final_obs = api.get_observation()
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(Path(args.scene).resolve()),
        "dataset": str(dataset),
        "dataset_files": list(data.files),
        "selected_episode": int(selected),
        "available_episodes": available_episodes,
        "frames_replayed": int(len(idxs)),
        "dataset_obs_shape": list(obs.shape),
        "dataset_action_shape": list(actions.shape),
        "task_api_obs_dim": int(task_api_obs_dim),
        "task_api_action_dim": int(api.get_action_dim()),
        "action_dim_matches": bool(action_dim_matches),
        "obs_dim_matches_task_api": bool(obs_dim_matches_task_api),
        "qpos_prefix_available": bool(qpos_prefix_available),
        "qvel_prefix_available": bool(qvel_prefix_available),
        "final_contact_count": int(final_obs["contact_count"]),
        "final_max_penetration": float(final_obs["max_penetration"]),
        "screenshots": screenshots,
        "status": "PASS" if action_dim_matches and qpos_prefix_available else "FAIL",
        "notes": [
            "The legacy smoke dataset obs dim may differ from the newer task API obs dim because task API adds ctrl, ball velocity, and distance fields.",
            "Replay uses the qpos/qvel prefix from obs plus action/ctrl arrays.",
        ],
    }
    return payload


def write_report(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Export4 Replay Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Selected episode: `{payload['selected_episode']}`\n",
        f"- Frames replayed: `{payload['frames_replayed']}`\n",
        f"- Status: **{payload['status']}**\n\n",
        "## Dimension Check\n\n",
        f"- Dataset obs shape: `{payload['dataset_obs_shape']}`\n",
        f"- Dataset action shape: `{payload['dataset_action_shape']}`\n",
        f"- Task API obs dim: `{payload['task_api_obs_dim']}`\n",
        f"- Task API action dim: `{payload['task_api_action_dim']}`\n",
        f"- Action dim matches: `{payload['action_dim_matches']}`\n",
        f"- Obs dim matches task API: `{payload['obs_dim_matches_task_api']}`\n",
        f"- qpos prefix available: `{payload['qpos_prefix_available']}`\n",
        f"- qvel prefix available: `{payload['qvel_prefix_available']}`\n\n",
        "## Replay Metrics\n\n",
        f"- Final contact count: `{payload['final_contact_count']}`\n",
        f"- Final max penetration: `{payload['final_max_penetration']:.6f}`\n\n",
        "## Screenshots\n\n",
    ]
    if payload["screenshots"]:
        for key, value in payload["screenshots"].items():
            lines.append(f"- `{key}`: `{value}`\n")
    else:
        lines.append("- No keyframe screenshots requested.\n")
    lines.extend(
        [
            "\n## Notes\n\n",
            "- Replay passing means dataset shape and qpos/action replay are usable; it does not mean the grasp task succeeds.\n",
            "- Dataset collection v0 should wait until canonical ball side and contact proxy are fixed.\n",
        ]
    )
    write_text(path, "".join(lines), "before_export4_replay_report")


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay export4 scripted smoke dataset.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--scene", default=str(SCENE_TUNED))
    parser.add_argument("--episode-id", type=int)
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--save-keyframes", action="store_true")
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()
    payload = replay_dataset(args)
    write_report(Path(args.report).resolve(), json_ready(payload))
    print(f"Replay status: {payload['status']}")
    print(f"Action dim matches: {payload['action_dim_matches']}")
    print(f"Obs dim matches task API: {payload['obs_dim_matches_task_api']}")
    print(f"Saved report: {Path(args.report).resolve()}")


if __name__ == "__main__":
    main()
