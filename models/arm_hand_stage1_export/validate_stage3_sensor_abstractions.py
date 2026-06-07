#!/usr/bin/env python3
"""Validate Stage3 replay-safe sensor abstractions."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
from stage3_sensor_aware_gentle_grasp_hold_task_api import (
    CURRENT_STAGE3_SCENE,
    TASK_CONTRACT_VERSION,
    TASK_NAME,
    Stage3GentleGraspTaskAPI,
)


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DEFAULT_REPORT = DOCS / "stage3_sensor_abstraction_v0_report.md"
DEFAULT_META = META / "stage3_sensor_abstraction_v0.json"


def compare_array(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        return float("inf")
    return float(np.max(np.abs(a - b))) if a.size else 0.0


def compare_sensor_obs(a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    return {
        "vector": compare_array(a["vector"], b["vector"]),
        "vision_pose": compare_array(a["vision"]["object_pose_xyz_est"], b["vision"]["object_pose_xyz_est"]),
        "vision_axis": compare_array(a["vision"]["object_axis_est"], b["vision"]["object_axis_est"]),
        "vision_shape": compare_array(a["vision"]["object_shape_params_est"], b["vision"]["object_shape_params_est"]),
        "vision_goal": compare_array(a["vision"]["goal_pose_xyz_est"], b["vision"]["goal_pose_xyz_est"]),
        "vision_object_to_goal": compare_array(a["vision"]["object_to_goal_est"], b["vision"]["object_to_goal_est"]),
        "tactile_scalars": compare_array(
            np.asarray(
                [
                    a["tactile"]["normal_contact_proxy"],
                    a["tactile"]["contact_persistence"],
                    a["tactile"]["relative_tangential_motion"],
                    a["tactile"]["slip_score"],
                    a["tactile"]["crush_risk"],
                ],
                dtype=np.float64,
            ),
            np.asarray(
                [
                    b["tactile"]["normal_contact_proxy"],
                    b["tactile"]["contact_persistence"],
                    b["tactile"]["relative_tangential_motion"],
                    b["tactile"]["slip_score"],
                    b["tactile"]["crush_risk"],
                ],
                dtype=np.float64,
            ),
        ),
    }


def build_payload(scene: Path, seed: int, max_reconstruction_error: float) -> dict[str, Any]:
    api_a = Stage3GentleGraspTaskAPI(scene, rng_seed=seed)
    api_b = Stage3GentleGraspTaskAPI(scene, rng_seed=seed)
    same_a = api_a.get_observation(phase="vision_acquire", episode_id=3, step_index=11, deterministic_vision=False)
    same_b = api_b.get_observation(phase="vision_acquire", episode_id=3, step_index=11, deterministic_vision=False)
    repeated_after_other_key = api_a.get_observation(phase="vision_acquire", episode_id=9, step_index=41, deterministic_vision=False)
    same_a_reconstructed = api_a.get_observation(phase="vision_acquire", episode_id=3, step_index=11, deterministic_vision=False)
    next_step = api_b.get_observation(phase="vision_acquire", episode_id=3, step_index=12, deterministic_vision=False)
    other_episode = api_b.get_observation(phase="vision_acquire", episode_id=4, step_index=11, deterministic_vision=False)

    same_api_error = compare_sensor_obs(same_a, same_b)
    order_independence_error = compare_sensor_obs(same_a, same_a_reconstructed)
    next_step_delta = compare_sensor_obs(same_a, next_step)
    other_episode_delta = compare_sensor_obs(same_a, other_episode)
    validation_rows = [
        {"label": "same_key_api_a", "validation": same_a["sensor_validation"]},
        {"label": "same_key_api_b", "validation": same_b["sensor_validation"]},
        {"label": "other_key_throwaway", "validation": repeated_after_other_key["sensor_validation"]},
        {"label": "next_step", "validation": next_step["sensor_validation"]},
        {"label": "other_episode", "validation": other_episode["sensor_validation"]},
    ]
    all_validation_pass = all(row["validation"]["status"] == "PASS" for row in validation_rows)
    max_same_api_error = max(same_api_error.values())
    max_order_error = max(order_independence_error.values())
    checks = {
        "scene_exists": scene.exists(),
        "same_key_reconstructs_across_api_instances": max_same_api_error <= max_reconstruction_error,
        "same_key_reconstructs_after_other_keys": max_order_error <= max_reconstruction_error,
        "different_step_changes_vision_pose": next_step_delta["vision_pose"] > 0.0,
        "different_episode_changes_vision_pose": other_episode_delta["vision_pose"] > 0.0,
        "sensor_field_ranges_pass": all_validation_pass,
        "policy_vector_excludes_gt": "gt" not in same_a and api_a.get_observation_schema()["ground_truth_policy_input"] is False,
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task_name": TASK_NAME,
        "contract_version": TASK_CONTRACT_VERSION,
        "scene": scene,
        "status": status,
        "seed": int(seed),
        "max_reconstruction_error_threshold": float(max_reconstruction_error),
        "checks": checks,
        "same_key_error": same_api_error,
        "order_independence_error": order_independence_error,
        "next_step_delta": next_step_delta,
        "other_episode_delta": other_episode_delta,
        "sensor_config": api_a.sensor_config.as_metadata(),
        "sample_replay_key": same_a["sensor_replay_key"],
        "validation_rows": validation_rows,
        "sample_observation_summary": {
            "vision": same_a["vision"],
            "tactile": same_a["tactile"],
            "observation_dim": int(len(same_a["vector"])),
        },
    }


def write_outputs(payload: dict[str, Any], report: Path, metadata: Path) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Stage3 Sensor Abstraction V0 Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: **{payload['status']}**\n",
        f"- Task: `{payload['task_name']}`\n",
        f"- Contract: `{payload['contract_version']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Seed: `{payload['seed']}`\n",
        f"- Observation dim: `{payload['sample_observation_summary']['observation_dim']}`\n\n",
        "## Checks\n\n",
    ]
    for key, value in payload["checks"].items():
        lines.append(f"- {key}: `{value}`\n")
    lines.extend(
        [
            "\n## Replay Errors\n\n",
            f"- Same key across API instances max error: `{max(payload['same_key_error'].values()):.3e}`\n",
            f"- Same key after other keys max error: `{max(payload['order_independence_error'].values()):.3e}`\n",
            f"- Next-step vision pose delta: `{payload['next_step_delta']['vision_pose']:.3e}`\n",
            f"- Other-episode vision pose delta: `{payload['other_episode_delta']['vision_pose']:.3e}`\n\n",
            "## Sensor Config\n\n",
            f"- Base seed: `{payload['sensor_config']['base_seed']}`\n",
            f"- Replay key: `{payload['sensor_config']['replay_key']}`\n",
            f"- Vision config: `{json.dumps(payload['sensor_config']['vision'], ensure_ascii=False)}`\n",
            f"- Tactile config: `{json.dumps(payload['sensor_config']['tactile'], ensure_ascii=False)}`\n\n",
            "## Boundary\n\n",
            "This validates replay-safe simulated sensor abstractions only. It does not validate a scripted expert, dataset collection, real camera, real tactile sensor, ultrasound hardware, or real-hand integration.\n",
        ]
    )
    report.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Stage3 sensor abstraction replay safety.")
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--seed", type=int, default=80)
    parser.add_argument("--max-reconstruction-error", type=float, default=0.0)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_META)
    args = parser.parse_args()
    payload = build_payload(args.scene.resolve(), args.seed, args.max_reconstruction_error)
    write_outputs(payload, args.report, args.metadata)
    print(f"Status: {payload['status']}")
    print(f"Report: {args.report}")
    print(f"Metadata: {args.metadata}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
