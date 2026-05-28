#!/usr/bin/env python3
"""Run a small scripted arm-hand stage1 task on the physics-v0 scene."""

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
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DATA = ROOT / "data"
VIS = DOCS / "visual_checks_arm_hand_stage1_scripted_task"
REPORT = DOCS / "arm_hand_stage1_scripted_task_report.md"
META_OUT = META / "arm_hand_stage1_scripted_task.json"

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


def scalar_metrics(obs: dict[str, Any]) -> dict[str, Any]:
    distances = obs["fingertip_ball_distances"]
    four = [distances[name] for name in ["index", "middle", "ring", "little"]]
    contact = obs["contact_summary"]
    ball_vel = float(np.linalg.norm(obs["ball_velocity"]))
    return {
        "contact_count": int(contact["contact_count"]),
        "ball_hand_contact_count": int(contact["ball_hand_contact_count"]),
        "ball_arm_contact_count": int(contact["ball_arm_contact_count"]),
        "max_penetration": float(contact["max_penetration"]),
        "four_finger_avg_tip_ball_distance": float(np.mean(four)),
        "thumb_ball_distance": float(distances["thumb"]),
        "thumb_index_distance": float(np.linalg.norm(obs["fingertip_positions"]["thumb"] - obs["fingertip_positions"]["index"])),
        "ball_velocity_norm": ball_vel,
    }


def success(open_metrics: dict[str, Any], hold_metrics: dict[str, Any]) -> tuple[bool, list[str]]:
    failures = []
    if open_metrics["max_penetration"] > 0.005:
        failures.append("open penetration > 5mm")
    if hold_metrics["ball_hand_contact_count"] < 1:
        failures.append("no ball-hand contact at hold")
    if hold_metrics["max_penetration"] > 0.01:
        failures.append("hold penetration > 10mm")
    if hold_metrics["four_finger_avg_tip_ball_distance"] > 0.075:
        failures.append("four-finger avg tip-ball distance > 75mm")
    return (not failures), failures


def run_episode(api, episode: int, ball_position: np.ndarray, args) -> dict[str, Any]:
    api.reset_hand_open()
    api.set_ball_pose(*ball_position)
    rows = {"qpos": [], "qvel": [], "ctrl": [], "obs": [], "episode_ids": [], "phase_ids": []}
    phase_results = []
    screenshots = {}
    for phase_idx, (phase_name, targets) in enumerate(PHASES):
        target_action = api.action_from_targets(targets)
        start = api.data.ctrl.copy()
        steps = args.hold_steps if phase_name == "hold" else args.phase_steps
        for step in range(max(1, steps)):
            alpha = step / max(1, steps - 1)
            action = (1 - alpha) * start + alpha * target_action
            api.apply_action(action)
            obs = api.step(1, pin_ball=True)
            if args.save_rollout:
                rows["qpos"].append(obs["qpos"])
                rows["qvel"].append(obs["qvel"])
                rows["ctrl"].append(obs["ctrl"])
                rows["obs"].append(obs["vector"])
                rows["episode_ids"].append(episode)
                rows["phase_ids"].append(phase_idx)
        obs = api.get_observation()
        metrics = scalar_metrics(obs)
        phase_results.append({"phase": phase_name, "metrics": metrics})
        if args.save_screenshots:
            screenshots[phase_name] = render(api, VIS / f"episode_{episode}_{phase_idx:02d}_{phase_name}.png")
    ok, failure_reasons = success(phase_results[0]["metrics"], phase_results[-1]["metrics"])
    return {
        "episode": episode,
        "ball_position": ball_position,
        "success": bool(ok),
        "failure_reasons": failure_reasons,
        "phase_results": phase_results,
        "screenshots": screenshots,
        "rollout": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--phase-steps", type=int, default=70)
    parser.add_argument("--hold-steps", type=int, default=100)
    parser.add_argument("--save-rollout", action="store_true")
    parser.add_argument("--save-screenshots", action="store_true")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    DOCS.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    api = load_model(args.scene)
    base_ball = api.get_ball_pose()["position"].copy()

    episodes = []
    for ep in range(args.episodes):
        offset = rng.uniform([-0.006, -0.006, -0.003], [0.006, 0.006, 0.003])
        episodes.append(run_episode(api, ep, base_ball + offset, args))

    rollout_path = None
    if args.save_rollout:
        rollout_path = DATA / "arm_hand_stage1_scripted_task_rollout_v0.npz"
        qpos = np.concatenate([np.asarray(ep["rollout"]["qpos"], dtype=np.float64) for ep in episodes], axis=0)
        qvel = np.concatenate([np.asarray(ep["rollout"]["qvel"], dtype=np.float64) for ep in episodes], axis=0)
        ctrl = np.concatenate([np.asarray(ep["rollout"]["ctrl"], dtype=np.float64) for ep in episodes], axis=0)
        obs = np.concatenate([np.asarray(ep["rollout"]["obs"], dtype=np.float64) for ep in episodes], axis=0)
        episode_ids = np.concatenate([np.asarray(ep["rollout"]["episode_ids"], dtype=np.int32) for ep in episodes], axis=0)
        phase_ids = np.concatenate([np.asarray(ep["rollout"]["phase_ids"], dtype=np.int32) for ep in episodes], axis=0)
        np.savez_compressed(rollout_path, qpos=qpos, qvel=qvel, ctrl=ctrl, obs=obs, episode_ids=episode_ids, phase_ids=phase_ids)

    public_episodes = []
    for ep in episodes:
        public_episodes.append({k: v for k, v in ep.items() if k != "rollout"})
    pass_count = sum(1 for ep in public_episodes if ep["success"])
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(Path(args.scene).resolve()),
        "episodes": int(args.episodes),
        "success_count": int(pass_count),
        "status": "PASS" if pass_count == args.episodes else "PARTIAL",
        "rollout_path": str(rollout_path) if rollout_path else None,
        "task_success_criteria": [
            "open penetration <= 5mm",
            "hold ball-hand contacts >= 1",
            "hold penetration <= 10mm",
            "four-finger avg tip-ball distance <= 75mm",
            "thumb distance is recorded but not required",
        ],
        "episode_results": public_episodes,
        "training_ready": False,
    }
    META_OUT.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm-Hand Stage1 Scripted Task Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Episodes: `{payload['episodes']}`\n",
        f"- Success count: `{payload['success_count']}`\n",
        f"- Status: **{payload['status']}**\n",
        f"- Rollout path: `{payload['rollout_path']}`\n",
        f"- Training ready: **No**\n\n",
        "## Episode Results\n\n",
        "| ep | success | ball | hold contacts | hold pen | four avg | thumb-ball | failure reasons |\n",
        "|---:|---:|---|---:|---:|---:|---:|---|\n",
    ]
    for ep in public_episodes:
        hold = ep["phase_results"][-1]["metrics"]
        lines.append(
            f"| {ep['episode']} | {int(ep['success'])} | `{np.round(ep['ball_position'], 5).tolist()}` | "
            f"{hold['ball_hand_contact_count']} | {hold['max_penetration']:.6f} | "
            f"{hold['four_finger_avg_tip_ball_distance']:.6f} | {hold['thumb_ball_distance']:.6f} | "
            f"{'; '.join(ep['failure_reasons']) or '-'} |\n"
        )
    lines.extend(
        [
            "\n## Notes\n\n",
            "- This is a Shadow-style task scaffold shape, not a Shadow-equivalent dexterity claim.\n",
            "- The ball remains pinned for this smoke task.\n",
            "- No training was performed.\n",
        ]
    )
    REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"Status: {payload['status']} ({pass_count}/{args.episodes})")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META_OUT}")


if __name__ == "__main__":
    main()
