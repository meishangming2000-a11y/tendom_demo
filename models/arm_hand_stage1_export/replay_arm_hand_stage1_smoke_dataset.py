#!/usr/bin/env python3
"""Replay and validate the arm-hand stage1 tiny smoke dataset."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np

from arm_hand_stage1_task_api import DEFAULT_SCENE, load_model, json_ready


ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "data" / "arm_hand_stage1_scripted_smoke_dataset_v0.npz"
DOCS = ROOT / "docs"
META = ROOT / "metadata"
REPORT = DOCS / "arm_hand_stage1_replay_report.md"
META_OUT = META / "arm_hand_stage1_replay.json"
VIS = DOCS / "visual_checks_arm_hand_stage1_replay"


def render(api, path: Path) -> str:
    palm_id = api.mujoco.mj_name2id(api.model, api.mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    lookat = api.data.xpos[palm_id].copy() if palm_id >= 0 else np.array([0.0, 0.0, 0.4])
    renderer = api.mujoco.Renderer(api.model, width=1280, height=900)
    try:
        cam = api.mujoco.MjvCamera()
        cam.type = api.mujoco.mjtCamera.mjCAMERA_FREE
        cam.lookat[:] = lookat
        cam.distance = 0.86
        cam.azimuth = 205
        cam.elevation = -22
        renderer.update_scene(api.data, camera=cam)
        img = renderer.render()
    finally:
        renderer.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, img)
    return str(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(DATASET))
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--episode-id", type=int, default=0)
    parser.add_argument("--save-keyframes", action="store_true")
    args = parser.parse_args()

    dataset_path = Path(args.dataset).resolve()
    if not dataset_path.exists():
        raise FileNotFoundError(dataset_path)
    data = np.load(dataset_path, allow_pickle=True)
    qpos = data["qpos"]
    qvel = data["qvel"]
    ctrl = data["ctrl"]
    obs = data["obs"]
    episode_ids = data["episode_ids"]
    phase_ids = data["phase_ids"]
    phase_names = [str(v) for v in data["phase_name_table"]]

    api = load_model(args.scene)
    available = sorted(int(v) for v in np.unique(episode_ids))
    if args.episode_id not in available:
        raise ValueError(f"Episode {args.episode_id} unavailable; available={available}")
    idxs = np.where(episode_ids == args.episode_id)[0]

    action_dim_matches = ctrl.shape[1] == api.get_action_dim()
    qpos_matches = qpos.shape[1] == api.model.nq
    qvel_matches = qvel.shape[1] == api.model.nv
    obs_dim = len(api.get_observation()["vector"])
    obs_dim_matches = obs.shape[1] == obs_dim

    screenshots = {}
    key_idxs = {int(idxs[0]), int(idxs[len(idxs) // 2]), int(idxs[-1])}
    for idx in idxs:
        api.data.qpos[:] = qpos[idx]
        api.data.qvel[:] = qvel[idx]
        api.data.ctrl[:] = ctrl[idx]
        api.mujoco.mj_forward(api.model, api.data)
        if args.save_keyframes and int(idx) in key_idxs:
            phase_name = phase_names[int(phase_ids[idx])]
            screenshots[f"frame_{int(idx)}_{phase_name}"] = render(api, VIS / f"episode_{args.episode_id}_frame_{int(idx):04d}_{phase_name}.png")

    final_obs = api.get_observation()
    payload: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(dataset_path),
        "scene": str(Path(args.scene).resolve()),
        "episode_id": int(args.episode_id),
        "frames_replayed": int(len(idxs)),
        "available_episodes": available,
        "dataset_files": list(data.files),
        "qpos_shape": list(qpos.shape),
        "qvel_shape": list(qvel.shape),
        "ctrl_shape": list(ctrl.shape),
        "obs_shape": list(obs.shape),
        "task_action_dim": api.get_action_dim(),
        "task_obs_dim": obs_dim,
        "action_dim_matches": bool(action_dim_matches),
        "qpos_matches": bool(qpos_matches),
        "qvel_matches": bool(qvel_matches),
        "obs_dim_matches": bool(obs_dim_matches),
        "final_contact": final_obs["contact_summary"],
        "final_distances": final_obs["fingertip_ball_distances"],
        "screenshots": screenshots,
        "status": "PASS" if all([action_dim_matches, qpos_matches, qvel_matches, obs_dim_matches]) else "FAIL",
    }
    META_OUT.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm-Hand Stage1 Replay Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Dataset: `{payload['dataset']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Episode: `{payload['episode_id']}`\n",
        f"- Frames replayed: `{payload['frames_replayed']}`\n",
        f"- Status: **{payload['status']}**\n\n",
        "## Shape Check\n\n",
        f"- qpos shape: `{payload['qpos_shape']}`; matches model: `{payload['qpos_matches']}`\n",
        f"- qvel shape: `{payload['qvel_shape']}`; matches model: `{payload['qvel_matches']}`\n",
        f"- ctrl shape: `{payload['ctrl_shape']}`; action dim matches: `{payload['action_dim_matches']}`\n",
        f"- obs shape: `{payload['obs_shape']}`; task obs dim: `{payload['task_obs_dim']}`; matches: `{payload['obs_dim_matches']}`\n\n",
        "## Final Frame Metrics\n\n",
        f"- Contact count: `{payload['final_contact']['contact_count']}`\n",
        f"- Max penetration: `{payload['final_contact']['max_penetration']:.6f} m`\n",
        f"- Fingertip-ball distances: `{json.dumps(json_ready(payload['final_distances']), ensure_ascii=False)}`\n\n",
        "## Screenshots\n\n",
    ]
    if screenshots:
        for key, path in screenshots.items():
            lines.append(f"- `{key}`: `{path}`\n")
    else:
        lines.append("- Keyframes were not requested.\n")
    lines.extend(
        [
            "\n## Notes\n\n",
            "- Replay PASS means the smoke dataset is structurally consistent with the current task API.\n",
            "- It does not imply training readiness.\n",
        ]
    )
    REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"Replay status: {payload['status']}")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META_OUT}")


if __name__ == "__main__":
    main()
