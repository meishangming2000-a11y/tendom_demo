#!/usr/bin/env python3
"""Write the Stage2 lift-ball task contract.

This freezes the observation/action/reward/done contract used before dataset v0.
It is documentation plus machine-readable metadata, not a training run.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from arm_hand_stage1_task_api import CURRENT_LIFT_SCENE, ArmHandStage1TaskAPI, json_ready


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
REPORT = DOCS / "arm_hand_stage1_v2_task_contract.md"
META_OUT = META / "arm_hand_stage1_v2_task_contract.json"
SWEEP_META = META / "arm_hand_stage1_v2_ball_pose_sweep.json"


def load_sweep_summary() -> dict[str, Any] | None:
    if not SWEEP_META.exists():
        return None
    payload = json.loads(SWEEP_META.read_text(encoding="utf-8"))
    lifts = [float(row["final_metrics"]["ball_lift_height"]) for row in payload.get("results", [])]
    return {
        "metadata": str(SWEEP_META),
        "status": payload.get("status"),
        "episode_count": payload.get("episode_count"),
        "success_count": payload.get("success_count"),
        "lift_min": min(lifts) if lifts else None,
        "lift_max": max(lifts) if lifts else None,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    META_OUT.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    contract = payload["contract"]
    obs = contract["observation"]
    action = contract["action"]
    termination = contract["termination"]
    reward = contract["reward"]
    initial_eval = payload["initial_eval"]
    sweep = payload["sweep_summary"]

    lines = [
        "# Arm-Hand Stage1 V2 Task Contract\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Purpose\n\n",
        "This document freezes the first Stage2 contract for the current arm+hand v2 lift-ball task. "
        "It defines what a future dataset row means, how a step is scored, and when an episode ends. "
        "No training is performed here.\n\n",
        "## Contract Summary\n\n",
        f"- Task name: `{contract['task_name']}`\n",
        f"- Contract version: `{contract['contract_version']}`\n",
        f"- Baseline: `{contract['baseline_version']}`\n",
        f"- Recommended rollout scene: `{contract['scene_roles']['recommended_rollout_scene']}`\n",
        f"- Training ready: **No**\n\n",
        "## Observation\n\n",
        f"- Type: `{obs['type']}`\n",
        f"- Dimension: `{obs['dim']}`\n",
        f"- Slices: `{json.dumps(json_ready(obs['slices']), ensure_ascii=False)}`\n",
        f"- Finger order: `{json.dumps(json_ready(obs['finger_order']), ensure_ascii=False)}`\n",
        f"- Scalar names: `{json.dumps(json_ready(obs['scalar_names']), ensure_ascii=False)}`\n\n",
        "Plain meaning: each observation records the model state, current controls, fingertip positions, ball pose/velocity, contact counts, penetration, and fingertip-ball distances.\n\n",
        "## Action\n\n",
        f"- Type: `{action['type']}`\n",
        f"- Dimension: `{action['dim']}`\n",
        "- Meaning: one position target per actuator, clipped by each actuator's control range.\n\n",
        "## Reward\n\n",
        f"- Type: `{reward['type']}`\n",
        f"- Weights: `{json.dumps(json_ready(reward['weights']), ensure_ascii=False)}`\n",
        "- Positive terms: lift height, hand-ball contact, terminal success bonus.\n",
        "- Negative terms: floor contact after lift, excessive penetration, large fingertip-ball distances, terminal failure penalty.\n",
        f"- Note: {reward['note']}\n\n",
        "## Done / Terminal Rules\n\n",
        f"- Max episode steps: `{termination['max_episode_steps']}`\n",
        f"- Thresholds: `{json.dumps(json_ready(termination['thresholds']), ensure_ascii=False)}`\n",
        "- Success: ball is lifted high enough, still has hand contact, has no floor contact, has acceptable penetration, and the state is finite.\n",
        "- Failure: non-finite state, severe penetration, ball drop, floor contact after the ball has been lifted, or timeout.\n",
        f"- Note: {termination['note']}\n\n",
        "## Episode Result Schema\n\n",
        f"`{json.dumps(json_ready(contract['episode_result_schema']), ensure_ascii=False)}`\n\n",
        "## Validation\n\n",
        f"- Contract JSON: `{META_OUT}`\n",
        f"- API observation dim matches schema: `{payload['obs_dim_matches']}`\n",
        f"- API action dim matches schema: `{payload['action_dim_matches']}`\n",
        f"- Initial lift-scene state: `{initial_eval['episode_status']}` / `{initial_eval['terminal_reason']}`\n",
        f"- Initial reward total: `{initial_eval['reward']['total']:.6f}`\n",
    ]
    if sweep:
        lines.extend(
            [
                f"- Sweep metadata: `{sweep['metadata']}`\n",
                f"- Sweep status: `{sweep['status']}`\n",
                f"- Sweep success count: `{sweep['success_count']} / {sweep['episode_count']}`\n",
                f"- Sweep lift range: `{sweep['lift_min']:.6f} m` to `{sweep['lift_max']:.6f} m`\n",
            ]
        )
    else:
        lines.append("- Sweep metadata: not found.\n")
    lines.extend(
        [
            "\n## Next Step\n\n",
            "Use this contract to create dataset-v0 metadata and rollout rows. Keep BC/RL training blocked until dataset replay and QA pass against this contract.\n",
        ]
    )
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    api = ArmHandStage1TaskAPI(CURRENT_LIFT_SCENE)
    initial_ball = api.get_ball_pose()["position"].copy()
    obs = api.get_observation()
    contract = api.get_task_contract()
    initial_eval = api.evaluate_lift_task_state(initial_ball, step_count=0)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(api.scene_path),
        "contract": contract,
        "initial_eval": initial_eval,
        "obs_dim_matches": len(obs["vector"]) == contract["observation"]["dim"],
        "action_dim_matches": api.get_action_dim() == contract["action"]["dim"],
        "sweep_summary": load_sweep_summary(),
        "training_ready": False,
    }
    write_outputs(payload)
    status = "PASS" if payload["obs_dim_matches"] and payload["action_dim_matches"] else "FAIL"
    print(f"Contract status: {status}")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META_OUT}")


if __name__ == "__main__":
    main()
