#!/usr/bin/env python3
"""Validate Stage3.4 MuJoCo tactile/slip sensor on scripted grasp phases."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE, Stage3Thresholds


ROOT = Path(__file__).resolve().parent
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import run_stage3_visual_guided_grasp_sweep as sweep
from mujoco_tactile_slip_sensor import MujocoTactileSlipSensor


DEFAULT_REPORT = ROOT / "docs" / "stage3_tactile_slip_sensor_v0_report.md"
DEFAULT_METADATA = ROOT / "metadata" / "stage3_tactile_slip_sensor_v0.json"


def run_phase_with_sensor(model, data, mujoco, actuator_names: list[str], sensor: MujocoTactileSlipSensor, start: dict[str, float], end: dict[str, float], steps: int) -> list[dict[str, Any]]:
    rows = []
    for idx in range(max(1, int(steps))):
        alpha = idx / max(1, int(steps) - 1)
        targets = sweep.blend_targets(start, end, alpha)
        data.ctrl[:] = sweep.actuator_targets(model, mujoco, actuator_names, targets)
        mujoco.mj_step(model, data)
        tactile = sensor.sample(data)
        if idx == 0 or idx == int(steps) - 1 or tactile["contact_present"]:
            rows.append(
                {
                    "step_in_phase": int(idx),
                    "contact_present": bool(tactile["contact_present"]),
                    "contact_regions": list(tactile["contact_regions"]),
                    "contact_persistence": int(tactile["contact_persistence"]),
                    "slip_score": float(tactile["slip_score"]),
                    "crush_risk": float(tactile["crush_risk"]),
                    "grip_stable": bool(tactile["grip_stable"]),
                    "normal_contact_proxy": float(tactile["normal_contact_proxy"]),
                    "egg_hand_contact_count": int(tactile["egg_hand_contact_count"]),
                    "egg_floor_contact_count": int(tactile["egg_floor_contact_count"]),
                }
            )
    return rows


def run_trial(model, mujoco, *, trial: sweep.TrialConfig, egg_position: np.ndarray, args: argparse.Namespace) -> dict[str, Any]:
    data = mujoco.MjData(model)
    sweep.reset_episode(model, data, mujoco, egg_position)
    actuator_names = sweep.base.actuator_names(model, mujoco)
    thresholds = Stage3Thresholds()
    sensor = MujocoTactileSlipSensor(model, mujoco, thresholds=thresholds)
    sensor.reset(data)
    initial_tactile = sensor.sample(data)
    grasp_local = sweep.DEFAULT_GRASP_LOCAL.copy()
    solver = sweep.ArmProxyIkSolver(model, mujoco, grasp_local)

    approach_target = np.asarray(egg_position, dtype=np.float64).copy()
    approach_target[2] += float(trial.grasp_z_bias_m)
    lift_target = approach_target.copy()
    lift_target[2] += float(trial.lift_delta_m)
    approach_solution = solver.solve(approach_target, z_weight=10.0)
    lift_solution = solver.solve(lift_target, z_weight=6.0)
    approach_arm = sweep.arm_dict(approach_solution)
    lift_arm = sweep.arm_dict(lift_solution)
    pre_arm = dict(approach_arm)
    pre_arm["j2"] = float(np.clip(pre_arm["j2"] + float(trial.pre_j2_delta), -1.5708, 1.5708))

    sweep.reset_episode(model, data, mujoco, egg_position)
    for joint, value in pre_arm.items():
        data.qpos[sweep.base.joint_qadr(model, mujoco, joint)] = float(value)
    data.ctrl[:] = sweep.actuator_targets(model, mujoco, actuator_names, pre_arm)
    mujoco.mj_forward(model, data)
    sensor.reset(data)
    initial_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()

    hand_targets = {
        "preshape": {**approach_arm, **sweep.base.PRESHAPE_TARGETS},
        "close_fingers": {**approach_arm, **sweep.base.LONG_FINGER_TARGETS},
        "close_thumb": {**approach_arm, **sweep.base.LONG_FINGER_TARGETS, **sweep.base.THUMB_SMOKE_TARGETS},
        "lift": {**lift_arm, **sweep.base.LONG_FINGER_TARGETS, **sweep.base.THUMB_SMOKE_TARGETS},
    }
    phases = [
        ("approach", pre_arm, approach_arm, int(args.approach_steps)),
        ("preshape", approach_arm, hand_targets["preshape"], int(args.hand_steps)),
        ("close_fingers", hand_targets["preshape"], hand_targets["close_fingers"], int(args.close_fingers_steps)),
        ("close_thumb", hand_targets["close_fingers"], hand_targets["close_thumb"], int(args.close_thumb_steps)),
        ("close_hold", hand_targets["close_thumb"], hand_targets["close_thumb"], int(trial.close_hold_steps)),
        ("lift", hand_targets["close_thumb"], hand_targets["lift"], int(args.lift_steps)),
        ("hold_lift", hand_targets["lift"], hand_targets["lift"], int(args.hold_steps)),
    ]
    phase_rows = []
    max_slip = 0.0
    max_crush = 0.0
    max_persistence = 0
    contact_ever = False
    stable_ever = False
    first_contact_phase = None
    for phase_name, start, end, steps in phases:
        tactile_rows = run_phase_with_sensor(model, data, mujoco, actuator_names, sensor, start, end, steps)
        last = tactile_rows[-1] if tactile_rows else sensor.sample(data)
        for row in tactile_rows:
            max_slip = max(max_slip, float(row["slip_score"]))
            max_crush = max(max_crush, float(row["crush_risk"]))
            max_persistence = max(max_persistence, int(row["contact_persistence"]))
            contact_ever = contact_ever or bool(row["contact_present"])
            stable_ever = stable_ever or bool(row["grip_stable"])
            if first_contact_phase is None and row["contact_present"]:
                first_contact_phase = phase_name
        phase_rows.append(
            {
                "phase": phase_name,
                "final_tactile": last,
                "samples_logged": len(tactile_rows),
                "egg_position": data.xpos[sweep.egg_body_id(model, mujoco)].copy(),
            }
        )
    final_tactile = sensor.sample(data)
    final_egg = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    final_lift = float(final_egg[2] - initial_egg[2])
    checks = {
        "initial_no_contact": not bool(initial_tactile["contact_present"]),
        "contact_acquired": bool(contact_ever),
        "grip_stable_seen": bool(stable_ever),
        "final_contact_present": bool(final_tactile["contact_present"]),
        "final_grip_stable": bool(final_tactile["grip_stable"]),
        "max_crush_below_gate": float(max_crush) <= float(thresholds.success_max_crush_risk),
        "final_lift_height_pass": final_lift >= float(thresholds.success_lift_height_m),
    }
    risk_flags = []
    if first_contact_phase == "approach":
        risk_flags.append("early_contact_in_approach")
    if float(max_slip) > float(thresholds.success_max_slip_score):
        risk_flags.append("transient_slip_above_hold_gate")
    return {
        "trial": trial.name,
        "trial_config": asdict(trial),
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "risk_flags": risk_flags,
        "initial_tactile": initial_tactile,
        "final_tactile": final_tactile,
        "first_contact_phase": first_contact_phase,
        "max_slip_score": float(max_slip),
        "max_crush_risk": float(max_crush),
        "max_contact_persistence": int(max_persistence),
        "final_lift_height_m": final_lift,
        "phase_rows": phase_rows,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Stage3.4 Tactile/Slip Sensor V0\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Status: `{payload['status']}`\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Trials: `{len(payload['results'])}`\n\n",
        "## Trial Summary\n\n",
        "| trial | status | first contact | max slip | max crush | max persistence | final lift m | final grip stable | risk flags |\n",
        "|---|---|---|---:|---:|---:|---:|---:|---|\n",
    ]
    for row in payload["results"]:
        lines.append(
            f"| {row['trial']} | {row['status']} | `{row['first_contact_phase']}` | "
            f"{row['max_slip_score']:.3f} | {row['max_crush_risk']:.3f} | "
            f"{row['max_contact_persistence']} | {row['final_lift_height_m']:.5f} | "
            f"{int(row['final_tactile']['grip_stable'])} | `{row['risk_flags']}` |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- The tactile/slip sensor is MuJoCo contact-derived and policy-visible; it does not use real tactile hardware.\n",
            "- It separates pre-contact vision guidance from post-contact stability checks: contact acquisition, persistence, slip score, and crush risk.\n",
            "- Risk flags are controller/expert tuning signals, not sensor schema failures.\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Stage3.4 tactile/slip sensor.")
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--approach-steps", type=int, default=200)
    parser.add_argument("--hand-steps", type=int, default=120)
    parser.add_argument("--close-fingers-steps", type=int, default=160)
    parser.add_argument("--close-thumb-steps", type=int, default=160)
    parser.add_argument("--lift-steps", type=int, default=300)
    parser.add_argument("--hold-steps", type=int, default=180)
    args = parser.parse_args()

    import mujoco

    scene = args.scene.resolve()
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    base_egg_position = data.xpos[sweep.egg_body_id(model, mujoco)].copy()
    results = []
    for trial in sweep.trial_configs()[: max(1, int(args.trials))]:
        egg_position = base_egg_position + np.asarray(trial.offset_xyz, dtype=np.float64)
        row = run_trial(model, mujoco, trial=trial, egg_position=egg_position, args=args)
        results.append(row)
        print(f"{trial.name}: {row['status']} first_contact={row['first_contact_phase']} final_lift={row['final_lift_height_m']:.4f}")
    status = "PASS" if all(row["status"] == "PASS" for row in results) else "FAIL"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "scene": str(scene),
        "results": results,
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(args.report, payload)
    print(f"Status: {status}")
    print(f"Report: {args.report}")
    print(f"Metadata: {args.metadata}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
