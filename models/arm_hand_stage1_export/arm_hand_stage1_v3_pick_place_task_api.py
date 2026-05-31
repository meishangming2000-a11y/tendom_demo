#!/usr/bin/env python3
"""Task contract helpers for the experimental arm-hand pick-place extension."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from arm_hand_stage1_task_api import (
    CURRENT_BASELINE_VERSION,
    DEFAULT_TASK_THRESHOLDS,
    ArmHandStage1TaskAPI,
    json_ready,
)


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
CURRENT_PICK_PLACE_SCENE = ROOT / "mjcf" / "scene_arm_hand_export4_pick_place_demo.xml"
DEFAULT_REPORT = DOCS / "arm_hand_stage1_v3_pick_place_task_contract.md"
DEFAULT_META = META / "arm_hand_stage1_v3_pick_place_task_contract.json"

TASK_NAME = "arm_hand_stage1_pick_place_ball"
TASK_CONTRACT_VERSION = "stage2_pick_place_v0_1"
DEFAULT_MAX_EPISODE_STEPS = 4200
DEFAULT_TARGET_CENTER = np.array([0.165, 0.230, -0.06538044], dtype=np.float64)
DEFAULT_TARGET_RADIUS_M = 0.035
DEFAULT_REQUIRED_STABLE_STEPS = 240
DEFAULT_RELEASE_MAX_HAND_CONTACTS = 0
DEFAULT_TARGET_VELOCITY_NORM_MAX = 0.05


def target_array(value: Iterable[float] | None = None) -> np.ndarray:
    if value is None:
        return DEFAULT_TARGET_CENTER.copy()
    out = np.asarray(list(value), dtype=np.float64)
    if out.shape != (3,):
        raise ValueError(f"Expected target center shape {(3,)}, got {out.shape}")
    return out


def ball_velocity_norm(api: ArmHandStage1TaskAPI) -> float:
    pose = api.get_ball_pose()
    return float(np.linalg.norm(pose["velocity"]))


def compute_pick_place_metrics(
    api: ArmHandStage1TaskAPI,
    initial_ball_position: Iterable[float],
    target_center: Iterable[float] | None = None,
) -> dict[str, Any]:
    target = target_array(target_center)
    base_metrics = api.compute_task_metrics(initial_ball_position)
    ball = np.asarray(base_metrics["ball_position"], dtype=np.float64)
    target_delta = ball - target
    out = {
        **base_metrics,
        "target_center": target,
        "target_delta_xyz": target_delta,
        "target_distance_xy": float(np.linalg.norm(target_delta[:2])),
        "target_distance_xyz": float(np.linalg.norm(target_delta)),
        "target_height_error": float(target_delta[2]),
        "ball_velocity_norm": ball_velocity_norm(api),
    }
    return out


def evaluate_pick_place_state(
    api: ArmHandStage1TaskAPI,
    initial_ball_position: Iterable[float],
    *,
    target_center: Iterable[float] | None = None,
    step_count: int = 0,
    max_episode_steps: int = DEFAULT_MAX_EPISODE_STEPS,
    lifted_once: bool = False,
    release_started: bool = False,
    stable_target_steps: int = 0,
    transport_floor_contacts: int = 0,
    target_radius_m: float = DEFAULT_TARGET_RADIUS_M,
    required_stable_steps: int = DEFAULT_REQUIRED_STABLE_STEPS,
) -> dict[str, Any]:
    metrics = compute_pick_place_metrics(api, initial_ball_position, target_center)
    contact = metrics["contact"]
    failure_reasons: list[str] = []
    success_reasons: list[str] = []
    placed_on_target = (
        metrics["finite_state"]
        and lifted_once
        and release_started
        and int(stable_target_steps) >= int(required_stable_steps)
        and metrics["target_distance_xy"] <= float(target_radius_m)
        and contact.get("ball_floor_contact_count", 0) >= 1
        and contact["ball_hand_contact_count"] <= DEFAULT_RELEASE_MAX_HAND_CONTACTS
        and contact["max_penetration"] <= DEFAULT_TASK_THRESHOLDS["success_max_penetration_m"]
    )
    if placed_on_target:
        success_reasons.append("success_pick_place_ball")
    if not metrics["finite_state"]:
        failure_reasons.append("non_finite_state")
    if contact["max_penetration"] > DEFAULT_TASK_THRESHOLDS["failure_max_penetration_m"]:
        failure_reasons.append("excessive_penetration")
    if lifted_once and not release_started and int(transport_floor_contacts) > 0:
        failure_reasons.append("transport_drop_before_release")
    if step_count >= max_episode_steps and not placed_on_target:
        failure_reasons.append("timeout")
    failure = bool(failure_reasons and not placed_on_target)
    if placed_on_target:
        status = "success"
        reason = "success_pick_place_ball"
    elif failure:
        status = "failure"
        reason = failure_reasons[0]
    else:
        status = "running"
        reason = "running"
    return {
        "task_name": TASK_NAME,
        "contract_version": TASK_CONTRACT_VERSION,
        "episode_status": status,
        "terminal_reason": reason,
        "success": bool(placed_on_target),
        "failure": bool(failure),
        "done": bool(placed_on_target or failure),
        "step_count": int(step_count),
        "success_reasons": success_reasons,
        "failure_reasons": failure_reasons,
        "stable_target_steps": int(stable_target_steps),
        "transport_floor_contacts": int(transport_floor_contacts),
        "official_metrics": metrics,
    }


def build_contract(scene: Path = CURRENT_PICK_PLACE_SCENE) -> dict[str, Any]:
    api = ArmHandStage1TaskAPI(scene)
    base_schema = api.get_observation_schema()
    return {
        "task_name": TASK_NAME,
        "contract_version": TASK_CONTRACT_VERSION,
        "stage": "stage2_pick_place_task_system_v0",
        "baseline_version": CURRENT_BASELINE_VERSION,
        "training_ready": False,
        "scene": scene.resolve(),
        "base_action": api.get_action_schema(),
        "base_observation": base_schema,
        "recommended_feature_extension": {
            "target_center_xyz": 3,
            "ball_to_target_xyz": 3,
            "phase_one_hot": [
                "default_hold",
                "move_to_pre_approach",
                "approach_ball",
                "preshape",
                "close_four_fingers",
                "close_thumb",
                "lift",
                "transport",
                "descend_to_target",
                "release",
                "retreat",
                "settle_on_target",
            ],
        },
        "target": {
            "default_center": DEFAULT_TARGET_CENTER,
            "success_radius_m": DEFAULT_TARGET_RADIUS_M,
            "required_stable_steps": DEFAULT_REQUIRED_STABLE_STEPS,
            "velocity_norm_max": DEFAULT_TARGET_VELOCITY_NORM_MAX,
            "velocity_note": "Velocity is diagnostic for v0.1; stable placement is gated by consecutive target occupancy because free-joint velocity can include residual ball spin.",
        },
        "official_metrics": [
            "ball_lift_height",
            "ball_displacement",
            "ball_velocity_norm",
            "ball_hand_contact_count",
            "ball_floor_contact_count",
            "ball_arm_contact_count",
            "max_penetration",
            "target_distance_xy",
            "target_distance_xyz",
            "target_height_error",
            "stable_target_steps",
            "transport_floor_contacts",
            "finite_state",
        ],
        "termination": {
            "max_episode_steps": DEFAULT_MAX_EPISODE_STEPS,
            "success_when_all_true": [
                "ball was lifted at least once",
                "release phase has started",
                "ball center XY is within target radius",
                "ball-floor contact is present after release",
                "ball-hand contact count is zero after release",
                "target stability count reaches required stable steps",
                "max penetration is within lift-task success threshold",
                "finite_state is true",
            ],
            "failure_when_any_true": [
                "finite_state is false",
                "max penetration exceeds lift-task failure threshold",
                "ball touches floor during transport before release",
                "timeout before stable target placement",
            ],
        },
        "current_limits": [
            "Same-platform target pad only; not yet a two-platform task.",
            "Scripted expert is pure-physics but tuned for a small target displacement.",
            "No dataset v0.5 or trained policy is promoted yet.",
            "Collision proxy v2 remains smoke geometry.",
        ],
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    target = payload["target"]
    lines = [
        "# Arm-Hand Stage1 V3 Pick-Place Task Contract\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Task name: `{payload['task_name']}`\n",
        f"- Contract version: `{payload['contract_version']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Training ready: **{payload['training_ready']}**\n",
        f"- Default target center: `{json_ready(target['default_center'])}`\n",
        f"- Target radius: `{target['success_radius_m']:.3f} m`\n",
        f"- Required stable steps: `{target['required_stable_steps']}`\n\n",
        "## Feature Extension\n\n",
        "- Add `target_center_xyz` and `ball_to_target_xyz` to the current v2 observation vector.\n",
        "- Keep phase-conditioning explicit; pick-place needs transport, release, retreat, and settle phases.\n\n",
        "## Success Contract\n\n",
    ]
    for item in payload["termination"]["success_when_all_true"]:
        lines.append(f"- {item}\n")
    lines.extend(["\n## Failure Contract\n\n"])
    for item in payload["termination"]["failure_when_any_true"]:
        lines.append(f"- {item}\n")
    lines.extend(["\n## Current Limits\n\n"])
    for item in payload["current_limits"]:
        lines.append(f"- {item}\n")
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the experimental Stage1 v3 pick-place task contract.")
    parser.add_argument("--scene", type=Path, default=CURRENT_PICK_PLACE_SCENE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_META)
    args = parser.parse_args()
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        **build_contract(args.scene),
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, payload)
    print(f"Report: {args.report}")
    print(f"Metadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
