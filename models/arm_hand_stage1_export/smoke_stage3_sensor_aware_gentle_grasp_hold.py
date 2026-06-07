#!/usr/bin/env python3
"""Smoke-check the Stage3 sensor-aware gentle grasp/hold contract."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from arm_hand_stage1_task_api import json_ready
from stage3_sensor_aware_gentle_grasp_hold_task_api import (
    CURRENT_STAGE3_SCENE,
    DEFAULT_OBJECT_POSITION,
    TASK_CONTRACT_VERSION,
    TASK_NAME,
    TACTILE_FIELD_NAMES,
    VISION_FIELD_NAMES,
    Stage3GentleGraspTaskAPI,
)


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
DEFAULT_REPORT = DOCS / "stage3_sensor_aware_gentle_grasp_hold_v0_smoke_report.md"
DEFAULT_META = META / "stage3_sensor_aware_gentle_grasp_hold_v0_smoke.json"


def build_smoke_payload(scene: Path, seed: int) -> dict[str, Any]:
    api = Stage3GentleGraspTaskAPI(scene, rng_seed=seed)
    obs = api.get_observation(phase="vision_acquire", deterministic_vision=True)
    contract = api.get_task_contract()
    evaluation = api.evaluate_state(
        DEFAULT_OBJECT_POSITION,
        phase="vision_acquire",
        step_count=0,
        hold_steps=0,
        contact_persistence_steps=0,
        lifted_once=False,
    )
    required_vision = set(VISION_FIELD_NAMES)
    required_tactile = set(TACTILE_FIELD_NAMES)
    vision_ok = required_vision.issubset(obs["vision"].keys())
    tactile_ok = required_tactile.issubset(obs["tactile"].keys())
    checks = {
        "scene_exists": scene.exists(),
        "scene_loads": True,
        "action_dim_positive": api.get_action_dim() > 0,
        "observation_dim_positive": len(obs["vector"]) > 0,
        "vision_fields_present": vision_ok,
        "tactile_fields_present": tactile_ok,
        "sensor_validation_pass": obs["sensor_validation"]["status"] == "PASS",
        "contract_mujoco_only": bool(contract["mujoco_only"]),
        "hardware_integration_false": not bool(contract["hardware_integration"]),
        "initial_eval_running": evaluation["terminal_reason"] == "running",
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task_name": TASK_NAME,
        "contract_version": TASK_CONTRACT_VERSION,
        "scene": scene,
        "status": status,
        "checks": checks,
        "action_dim": api.get_action_dim(),
        "observation_dim": len(obs["vector"]),
        "contract_summary": {
            "training_ready": contract["training_ready"],
            "mujoco_only": contract["mujoco_only"],
            "hardware_integration": contract["hardware_integration"],
            "required_hold_steps": contract["required_hold_steps"],
        },
        "sample_sensor_observation": {
            "phase": obs["phase"],
            "vision": obs["vision"],
            "tactile": obs["tactile"],
            "sensor_validation": obs["sensor_validation"],
            "sensor_replay_key": obs["sensor_replay_key"],
        },
        "initial_evaluation": evaluation,
    }


def write_outputs(payload: dict[str, Any], report: Path, metadata: Path) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Stage3 Sensor-Aware Gentle Grasp/Hold Smoke Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: **{payload['status']}**\n",
        f"- Task: `{payload['task_name']}`\n",
        f"- Contract: `{payload['contract_version']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Action dim: `{payload['action_dim']}`\n",
        f"- Observation dim: `{payload['observation_dim']}`\n\n",
        "## Checks\n\n",
    ]
    for key, value in payload["checks"].items():
        lines.append(f"- {key}: `{value}`\n")
    lines.extend(
        [
            "\n## Initial Evaluation\n\n",
            f"- Terminal reason: `{payload['initial_evaluation']['terminal_reason']}`\n",
            f"- Episode status: `{payload['initial_evaluation']['episode_status']}`\n",
            f"- Vision confidence: `{payload['initial_evaluation']['official_metrics']['vision_confidence']:.3f}`\n",
            f"- Slip score: `{payload['initial_evaluation']['official_metrics']['slip_score']:.3f}`\n",
            f"- Crush risk: `{payload['initial_evaluation']['official_metrics']['crush_risk']:.3f}`\n\n",
            "## Boundary\n\n",
            "This smoke check validates the Stage3 contract, scene load, and sensor abstraction schema only. Scripted expert, dataset collection, replay QA, and visual QA remain pending.\n",
        ]
    )
    report.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Stage3 sensor-aware gentle grasp/hold contract smoke check.")
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--seed", type=int, default=80)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_META)
    args = parser.parse_args()
    payload = build_smoke_payload(args.scene.resolve(), args.seed)
    write_outputs(payload, args.report, args.metadata)
    print(f"Status: {payload['status']}")
    print(f"Report: {args.report}")
    print(f"Metadata: {args.metadata}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
