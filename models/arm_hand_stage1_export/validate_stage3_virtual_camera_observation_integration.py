#!/usr/bin/env python3
"""Validate Stage3.3 virtual-camera observation integration."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, Stage3GentleGraspTaskAPI


ROOT = Path(__file__).resolve().parent
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import run_stage3_visual_guided_grasp_sweep as sweep
from mujoco_egg_pose_sensor import EggPoseSensorConfig, MujocoEggPoseSensor
from run_stage3_noisy_virtual_camera_perception_test import NoiseScenario, estimate_noisy_pose, scenario_rng


DEFAULT_REPORT = ROOT / "docs" / "stage3_virtual_camera_observation_integration_v0.md"
DEFAULT_METADATA = ROOT / "metadata" / "stage3_virtual_camera_observation_integration_v0.json"


def build_payload(scene: Path, seed: int) -> dict[str, Any]:
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    base_egg_position = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    trial = sweep.trial_configs()[0]
    egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
    sweep.reset_episode(model, data, mujoco, egg_position)

    sensor = MujocoEggPoseSensor(model, mujoco, EggPoseSensorConfig(camera_name="stage3_egg_closeup"))
    clean_estimate = sensor.estimate(data, label="stage3_3_clean")
    clean_estimate["accepted_as_pose_update"] = True
    clean_estimate["tracking_confidence"] = float(clean_estimate["confidence"])
    clean_estimate["mask_retention_ratio"] = 1.0

    noisy_estimate = estimate_noisy_pose(
        model=model,
        data=data,
        mujoco=mujoco,
        config=EggPoseSensorConfig(camera_name="stage3_egg_closeup"),
        scenario=NoiseScenario("stage3_3_mask_dropout_55", mask_dropout=0.55),
        rng=scenario_rng(seed, trial.name, "stage3_3_mask_dropout_55"),
    )
    noisy_estimate["tracking_confidence"] = float(noisy_estimate.get("confidence", 0.0))
    noisy_estimate["accepted_as_pose_update"] = float(noisy_estimate.get("confidence", 0.0)) >= 0.55

    api = Stage3GentleGraspTaskAPI(scene)
    api.reset_open(egg_position)
    clean_obs = api.get_observation(phase="vision_acquire", vision_override=clean_estimate)
    noisy_obs = api.get_observation(phase="vision_acquire", vision_override=noisy_estimate)
    schema = api.get_observation_schema()

    checks = {
        "clean_sensor_validation_pass": clean_obs["sensor_validation"]["status"] == "PASS",
        "noisy_sensor_validation_pass": noisy_obs["sensor_validation"]["status"] == "PASS",
        "clean_vision_source_virtual_camera": clean_obs["vision"].get("vision_source") == "virtual_camera",
        "noisy_vision_source_virtual_camera": noisy_obs["vision"].get("vision_source") == "virtual_camera",
        "clean_vector_dim_matches_schema": len(clean_obs["vector"]) == int(schema["dim"]),
        "noisy_vector_dim_matches_schema": len(noisy_obs["vector"]) == int(schema["dim"]),
        "clean_pose_matches_sensor": bool(
            np.linalg.norm(clean_obs["vision"]["object_pose_xyz_est"] - np.asarray(clean_estimate["position_world_est"], dtype=np.float64)) < 1e-12
        ),
        "noisy_confidence_below_clean": float(noisy_obs["vision"]["confidence"]) < float(clean_obs["vision"]["confidence"]),
        "noisy_occlusion_positive": float(noisy_obs["vision"]["occlusion"]) > 0.0,
        "policy_boundary_not_hardware": bool(api.get_task_contract()["mujoco_only"]) and not bool(api.get_task_contract()["hardware_integration"]),
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "scene": str(scene),
        "checks": checks,
        "clean_estimate_summary": {
            "status": clean_estimate["status"],
            "confidence": float(clean_estimate["confidence"]),
            "mask_pixels": int(clean_estimate["mask_pixels"]),
            "position_world_est": clean_estimate["position_world_est"],
        },
        "noisy_estimate_summary": {
            "status": noisy_estimate["status"],
            "confidence": float(noisy_estimate.get("confidence", 0.0)),
            "mask_pixels": int(noisy_estimate.get("mask_pixels", 0)),
            "mask_retention_ratio": float(noisy_estimate.get("mask_retention_ratio", 0.0)),
            "accepted_as_pose_update": bool(noisy_estimate["accepted_as_pose_update"]),
        },
        "clean_observation_summary": {
            "vector_dim": len(clean_obs["vector"]),
            "vision_source": clean_obs["vision"].get("vision_source"),
            "confidence": float(clean_obs["vision"]["confidence"]),
            "occlusion": float(clean_obs["vision"]["occlusion"]),
            "sensor_validation": clean_obs["sensor_validation"],
        },
        "noisy_observation_summary": {
            "vector_dim": len(noisy_obs["vector"]),
            "vision_source": noisy_obs["vision"].get("vision_source"),
            "confidence": float(noisy_obs["vision"]["confidence"]),
            "occlusion": float(noisy_obs["vision"]["occlusion"]),
            "sensor_validation": noisy_obs["sensor_validation"],
        },
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Stage3.3 Virtual-Camera Observation Integration V0\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: `{payload['status']}`\n",
        f"- Scene: `{payload['scene']}`\n\n",
        "## Checks\n\n",
    ]
    for key, value in payload["checks"].items():
        lines.append(f"- {key}: `{value}`\n")
    lines.extend(
        [
            "\n## Clean Observation\n\n",
            f"- Source: `{payload['clean_observation_summary']['vision_source']}`\n",
            f"- Confidence: `{payload['clean_observation_summary']['confidence']:.3f}`\n",
            f"- Occlusion: `{payload['clean_observation_summary']['occlusion']:.3f}`\n",
            f"- Vector dim: `{payload['clean_observation_summary']['vector_dim']}`\n\n",
            "## Noisy Observation\n\n",
            f"- Source: `{payload['noisy_observation_summary']['vision_source']}`\n",
            f"- Confidence: `{payload['noisy_observation_summary']['confidence']:.3f}`\n",
            f"- Occlusion: `{payload['noisy_observation_summary']['occlusion']:.3f}`\n",
            f"- Accepted update: `{payload['noisy_estimate_summary']['accepted_as_pose_update']}`\n\n",
            "## Interpretation\n\n",
            "- The task API can now expose rendered virtual-camera perception as policy-visible vision fields.\n",
            "- Ground truth remains available only for evaluation/logging unless explicitly passed as the old replay-safe abstraction path.\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Stage3.3 virtual-camera observation integration.")
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--seed", type=int, default=330)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    args = parser.parse_args()
    payload = build_payload(args.scene.resolve(), args.seed)
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, payload)
    print(f"Status: {payload['status']}")
    print(f"Report: {args.report}")
    print(f"Metadata: {args.metadata}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
