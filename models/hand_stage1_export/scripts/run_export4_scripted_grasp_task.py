#!/usr/bin/env python3
"""Run a small scripted grasp task using the export4 task API scaffold."""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from export4_task_api import load_model
from export4_wrist2_common import (
    DEFAULT_BALL_POSITION,
    DOCS_DIR,
    LONG_FINGER_TARGETS,
    METADATA_DIR,
    PRESHAPE_TARGETS,
    SCENE_TUNED,
    THUMB_SMOKE_TARGETS,
    json_ready,
    write_json,
    write_text,
)


DEFAULT_REPORT = DOCS_DIR / "export4_scripted_grasp_task_report.md"
DEFAULT_METADATA = METADATA_DIR / "export4_scripted_grasp_task_results.json"
DEFAULT_ROLLOUT = METADATA_DIR / "export4_scripted_grasp_task_rollout.npz"

STAGES = [
    ("open_hand", {}),
    ("preshape", PRESHAPE_TARGETS),
    ("close_four_fingers", LONG_FINGER_TARGETS),
    ("close_thumb", {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}),
    ("hold", {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}),
]


def action_from_targets(api, targets: Dict[str, float]) -> np.ndarray:
    action = np.zeros(api.get_action_dim(), dtype=np.float64)
    for idx, actuator_name in enumerate(api.get_actuator_names()):
        joint_name = actuator_name[:-4] if actuator_name.endswith("_pos") else actuator_name
        value = float(targets.get(joint_name, 0.0))
        low, high = api.model.actuator_ctrlrange[idx]
        action[idx] = np.clip(value, low, high)
    return action


def scalar_metrics(obs: Dict[str, Any]) -> Dict[str, Any]:
    distances = obs["fingertip_ball_distances"]
    four_avg = float(np.mean([distances[name] for name in ("index", "middle", "ring", "little")]))
    return {
        "contact_count": int(obs["contact_summary"]["contact_count"]),
        "ball_hand_contact_count": int(obs["contact_summary"]["ball_hand_contact_count"]),
        "max_penetration": float(obs["contact_summary"]["max_penetration"]),
        "ball_hand_max_penetration": float(obs["contact_summary"]["ball_hand_max_penetration"]),
        "four_finger_avg_tip_ball_distance": four_avg,
        "thumb_ball_distance": float(distances["thumb"]),
        "thumb_index_distance": float(np.linalg.norm(obs["fingertip_positions"]["thumb"] - obs["fingertip_positions"]["index"])),
        "ball_position": obs["ball_position"].copy(),
        "ball_velocity_norm": float(np.linalg.norm(obs["ball_velocity"])),
    }


def run_episode(api, episode_id: int, ball_position: List[float], args, viewer=None) -> Dict[str, Any]:
    api.reset_hand_open()
    api.set_ball_pose(*ball_position)
    open_obs = api.get_observation()
    initial_ball = open_obs["ball_position"].copy()
    stages = []
    rollout_rows = {"qpos": [], "qvel": [], "ctrl": [], "obs": [], "stage_id": [], "episode_id": []}

    for stage_id, (stage_name, targets) in enumerate(STAGES):
        target_action = action_from_targets(api, targets)
        start_action = api.data.ctrl.copy()
        steps = args.hold_steps if stage_name == "hold" else args.phase_steps
        for step_idx in range(max(1, steps)):
            alpha = step_idx / max(1, steps - 1)
            action = (1.0 - alpha) * start_action + alpha * target_action
            api.apply_action(action)
            api.step(1, pin_ball=not args.free_ball)
            obs = api.get_observation()
            rollout_rows["qpos"].append(api.data.qpos.copy())
            rollout_rows["qvel"].append(api.data.qvel.copy())
            rollout_rows["ctrl"].append(api.data.ctrl.copy())
            rollout_rows["obs"].append(obs["vector"].copy())
            rollout_rows["stage_id"].append(stage_id)
            rollout_rows["episode_id"].append(episode_id)
            if viewer is not None:
                viewer.sync()
                time.sleep(0.004)
        obs = api.get_observation()
        stages.append({"name": stage_name, "target": dict(targets), "metrics": scalar_metrics(obs)})

    hold = stages[-1]["metrics"]
    open_metrics = stages[0]["metrics"]
    ball_displacement = float(np.linalg.norm(hold["ball_position"] - initial_ball))
    success = (
        open_metrics["max_penetration"] < 0.005
        and hold["ball_hand_contact_count"] >= 1
        and ball_displacement < 0.05
        and hold["four_finger_avg_tip_ball_distance"] < args.four_tip_threshold
    )
    if success:
        label = "success_smoke"
    elif hold["four_finger_avg_tip_ball_distance"] < args.four_tip_threshold:
        label = "near_no_contact"
    else:
        label = "fail_far_or_wrong_side"
    return {
        "episode": episode_id,
        "ball_position": ball_position,
        "pin_ball": not args.free_ball,
        "stages": stages,
        "success": bool(success),
        "label": label,
        "ball_displacement": ball_displacement,
        "rollout": rollout_rows,
    }


def write_report(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Export4 Scripted Grasp Task Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "Uses `export4_task_api.py` to run a small scripted grasp scaffold. "
        "No RL/BC/training, CAD edit, STL edit, joint-tree edit, joint rename, or tendon routing is performed.\n\n",
        "## Setup\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Episodes: `{payload['episodes']}`\n",
        f"- Ball position: `{payload['ball_position']}`\n",
        f"- Ball pinned: `{payload['pin_ball']}`\n",
        f"- Four-tip threshold: `{payload['four_tip_threshold']}`\n",
        f"- Success count: `{payload['success_count']}`\n",
        f"- Status: **{payload['status']}**\n\n",
        "## Episode Results\n\n",
        "| ep | label | success | contacts | ball-hand | max pen | ball disp | four-tip avg | thumb-ball |\n",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for ep in payload["episode_results"]:
        hold = ep["stages"][-1]["metrics"]
        lines.append(
            f"| {ep['episode']} | {ep['label']} | {ep['success']} | {hold['contact_count']} | "
            f"{hold['ball_hand_contact_count']} | {hold['max_penetration']:.6f} | "
            f"{ep['ball_displacement']:.6f} | {hold['four_finger_avg_tip_ball_distance']:.6f} | "
            f"{hold['thumb_ball_distance']:.6f} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- Failure here is expected while the canonical palm/ball side remains unresolved.\n",
            "- The scaffold is still useful because it exercises reset, action application, staged control, observation, contact metrics, and rollout saving.\n",
            "- `thumb_ball_distance` is recorded but not required for success yet.\n",
        ]
    )
    write_text(path, "".join(lines), "before_export4_scripted_task_report")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run export4 scripted grasp task scaffold.")
    parser.add_argument("--scene", default=str(SCENE_TUNED))
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--ball-x", type=float, default=DEFAULT_BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=DEFAULT_BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=DEFAULT_BALL_POSITION[2])
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--phase-steps", type=int, default=80)
    parser.add_argument("--hold-steps", type=int, default=100)
    parser.add_argument("--four-tip-threshold", type=float, default=0.08)
    parser.add_argument("--free-ball", action="store_true")
    parser.add_argument("--save-rollout", action="store_true")
    parser.add_argument("--rollout", default=str(DEFAULT_ROLLOUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    args = parser.parse_args()

    np.random.seed(args.seed)
    api = load_model(args.scene)
    viewer = None
    if args.viewer:
        import mujoco.viewer

        viewer = mujoco.viewer.launch_passive(api.model, api.data)
    ball = [args.ball_x, args.ball_y, args.ball_z]
    episodes = []
    try:
        for ep in range(args.episodes):
            result = run_episode(api, ep, ball, args, viewer)
            episodes.append(result)
            hold = result["stages"][-1]["metrics"]
            print(
                f"episode {ep}: {result['label']} contacts={hold['contact_count']} "
                f"ballhand={hold['ball_hand_contact_count']} four_tip={hold['four_finger_avg_tip_ball_distance']:.4f}"
            )
    finally:
        if viewer is not None:
            viewer.close()

    rollout_path = None
    if args.save_rollout:
        rollout_path = Path(args.rollout).resolve()
        rollout_path.parent.mkdir(parents=True, exist_ok=True)
        qpos = np.concatenate([np.asarray(ep["rollout"]["qpos"]) for ep in episodes], axis=0)
        qvel = np.concatenate([np.asarray(ep["rollout"]["qvel"]) for ep in episodes], axis=0)
        ctrl = np.concatenate([np.asarray(ep["rollout"]["ctrl"]) for ep in episodes], axis=0)
        obs = np.concatenate([np.asarray(ep["rollout"]["obs"]) for ep in episodes], axis=0)
        stage_ids = np.concatenate([np.asarray(ep["rollout"]["stage_id"], dtype=np.int32) for ep in episodes], axis=0)
        episode_ids = np.concatenate([np.asarray(ep["rollout"]["episode_id"], dtype=np.int32) for ep in episodes], axis=0)
        np.savez_compressed(rollout_path, qpos=qpos, qvel=qvel, ctrl=ctrl, obs=obs, stage_ids=stage_ids, episode_ids=episode_ids)

    public_episodes = []
    for ep in episodes:
        ep = dict(ep)
        ep.pop("rollout", None)
        public_episodes.append(ep)
    success_count = sum(1 for ep in public_episodes if ep["success"])
    status = "PASS" if success_count == args.episodes else ("PARTIAL" if success_count else "FAIL_EXPECTED_UNTIL_GRASP_SIDE_FIXED")
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(Path(args.scene).resolve()),
        "episodes": int(args.episodes),
        "ball_position": ball,
        "pin_ball": not args.free_ball,
        "seed": int(args.seed),
        "four_tip_threshold": float(args.four_tip_threshold),
        "success_count": int(success_count),
        "status": status,
        "rollout_path": str(rollout_path) if rollout_path else None,
        "episode_results": public_episodes,
        "notes": [
            "Default -Y ball side is expected to fail based on prior palm-side diagnostics.",
            "This scaffold verifies control/data plumbing, not training readiness.",
        ],
    }
    write_json(Path(args.metadata).resolve(), payload, "before_export4_scripted_task_results")
    write_report(Path(args.report).resolve(), json_ready(payload))
    print(f"Scripted task status: {status}")
    print(f"Saved report: {Path(args.report).resolve()}")
    print(f"Saved metadata: {Path(args.metadata).resolve()}")
    if rollout_path:
        print(f"Saved rollout: {rollout_path}")


if __name__ == "__main__":
    main()
