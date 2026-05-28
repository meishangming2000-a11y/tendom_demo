#!/usr/bin/env python3
"""Stage2 smoke sweep for the current arm+hand v2 lift-ball baseline.

This is a small scripted pose-region check. It does not collect training data
and it does not promote the collision proxy to final contact geometry.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np

import demo_arm_hand_lift_ball_scripted as lift_targets
from arm_hand_stage1_task_api import CURRENT_LIFT_SCENE, ArmHandStage1TaskAPI, json_ready


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
REPORT = DOCS / "arm_hand_stage1_v2_ball_pose_sweep_report.md"
META_OUT = META / "arm_hand_stage1_v2_ball_pose_sweep.json"

DEFAULT_X_OFFSETS = [-0.015, 0.0, 0.015]
DEFAULT_Y_OFFSETS = [-0.015, 0.0, 0.015]
DEFAULT_Z_OFFSETS = [0.0]


def blend_targets(a: dict[str, float], b: dict[str, float], alpha: float) -> dict[str, float]:
    keys = set(a) | set(b)
    return {key: (1.0 - alpha) * float(a.get(key, 0.0)) + alpha * float(b.get(key, 0.0)) for key in keys}


def build_phases(default_targets: dict[str, float], args) -> list[tuple[str, dict[str, float], dict[str, float], int]]:
    pre_approach = {**default_targets, **lift_targets.ARM_PRE_APPROACH}
    approach = {**default_targets, **lift_targets.ARM_APPROACH}
    preshape = {**approach, **lift_targets.PRESHAPE_TARGETS}
    close_fingers = {**approach, **lift_targets.LONG_FINGER_TARGETS}
    close_thumb = {**close_fingers, **lift_targets.THUMB_SMOKE_TARGETS}
    lift = {**close_thumb, **lift_targets.ARM_LIFT}
    return [
        ("default_hold", default_targets, default_targets, args.default_hold_steps),
        ("move_to_pre_approach", default_targets, pre_approach, args.move_steps),
        ("approach_ball", pre_approach, approach, args.approach_steps),
        ("preshape", approach, preshape, args.hand_steps),
        ("close_four_fingers", preshape, close_fingers, args.hand_steps),
        ("close_thumb", close_fingers, close_thumb, args.hand_steps),
        ("lift", close_thumb, lift, args.lift_steps),
        ("hold_lift", lift, lift, args.hold_steps),
    ]


def scalar_metrics(api: ArmHandStage1TaskAPI, initial_ball: np.ndarray) -> dict[str, Any]:
    obs = api.get_observation()
    ball = obs["ball_position"].copy()
    distances = obs["fingertip_ball_distances"]
    four = [distances[name] for name in ["index", "middle", "ring", "little"]]
    contact = {key: value for key, value in obs["contact_summary"].items() if key != "top_contacts"}
    return {
        "ball_position": ball,
        "ball_lift_height": float(ball[2] - initial_ball[2]),
        "ball_displacement": float(np.linalg.norm(ball - initial_ball)),
        "contact": contact,
        "four_finger_avg_tip_ball_distance": float(np.mean(four)),
        "thumb_ball_distance": float(distances["thumb"]),
        "finite_state": bool(np.isfinite(api.data.qpos).all() and np.isfinite(api.data.qvel).all()),
    }


def run_phase(
    api: ArmHandStage1TaskAPI,
    phase_name: str,
    start_targets: dict[str, float],
    end_targets: dict[str, float],
    steps: int,
    initial_ball: np.ndarray,
) -> dict[str, Any]:
    finite = True
    for i in range(max(1, int(steps))):
        alpha = i / max(1, int(steps) - 1)
        action = api.action_from_targets(blend_targets(start_targets, end_targets, alpha))
        api.step_action(action, n=1, pin_ball=False)
        finite = finite and bool(np.isfinite(api.data.qpos).all() and np.isfinite(api.data.qvel).all())
    metrics = scalar_metrics(api, initial_ball)
    metrics["finite_state"] = bool(metrics["finite_state"] and finite)
    return {"phase": phase_name, "metrics": metrics}


def classify(final: dict[str, Any], args) -> tuple[bool, list[str], str]:
    failures = []
    contact = final["contact"]
    if not final["finite_state"]:
        failures.append("non-finite state")
    if final["ball_lift_height"] < args.success_lift_height:
        failures.append(f"lift < {args.success_lift_height:.3f} m")
    if contact["ball_hand_contact_count"] < args.min_ball_hand_contacts:
        failures.append(f"ball-hand contacts < {args.min_ball_hand_contacts}")
    if contact.get("ball_floor_contact_count", 0) > args.max_ball_floor_contacts:
        failures.append(f"ball-floor contacts > {args.max_ball_floor_contacts}")
    if contact["max_penetration"] > args.max_penetration:
        failures.append(f"max penetration > {args.max_penetration:.3f} m")
    if not failures:
        return True, [], "lift_success"
    if contact["ball_hand_contact_count"] >= 1:
        return False, failures, "contact_no_lift"
    return False, failures, "miss"


def grid_offsets(xs: Iterable[float], ys: Iterable[float], zs: Iterable[float]) -> list[np.ndarray]:
    return [np.asarray([x, y, z], dtype=np.float64) for z in zs for y in ys for x in xs]


def run_pose(api: ArmHandStage1TaskAPI, index: int, base_ball: np.ndarray, offset: np.ndarray, args) -> dict[str, Any]:
    ball = base_ball + offset
    api.reset_hand_open(ball_position=ball)
    initial_ball = api.get_ball_pose()["position"].copy()
    default_targets = api.targets_from_current_qpos()
    phase_rows = []
    for phase_name, start, end, steps in build_phases(default_targets, args):
        phase_rows.append(run_phase(api, phase_name, start, end, steps, initial_ball))
    lifted_once = any(row["metrics"]["ball_lift_height"] >= args.success_lift_height for row in phase_rows)
    thresholds = {
        "success_lift_height_m": args.success_lift_height,
        "success_min_ball_hand_contacts": args.min_ball_hand_contacts,
        "success_max_ball_floor_contacts": args.max_ball_floor_contacts,
        "success_max_penetration_m": args.max_penetration,
    }
    step_count = sum(steps for _, _, _, steps in build_phases(default_targets, args))
    evaluation = api.evaluate_lift_task_state(
        initial_ball,
        step_count=step_count,
        max_episode_steps=step_count,
        lifted_once=lifted_once,
        thresholds=thresholds,
    )
    final = evaluation["official_metrics"]
    ok = evaluation["success"]
    failure_reasons = evaluation["failure_reasons"]
    label = "lift_success" if ok else evaluation["terminal_reason"]
    return {
        "index": int(index),
        "offset": offset,
        "initial_ball": initial_ball,
        "success": bool(ok),
        "label": label,
        "failure_reasons": failure_reasons,
        "final_metrics": final,
        "contract_evaluation": evaluation,
        "phase_results": phase_rows,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    META_OUT.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Arm-Hand Stage1 V2 Ball-Pose Sweep Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Base ball: `{json.dumps(json_ready(payload['base_ball']), ensure_ascii=False)}`\n",
        f"- Grid: `{json.dumps(json_ready(payload['grid']), ensure_ascii=False)}`\n",
        f"- Episodes: `{payload['episode_count']}`\n",
        f"- Success count: `{payload['success_count']}`\n",
        f"- Status: **{payload['status']}**\n",
        f"- Training used: **No**\n\n",
        "## Success Criteria\n\n",
    ]
    for item in payload["success_criteria"]:
        lines.append(f"- {item}\n")
    lines.extend(
        [
            "\n## Results\n\n",
            "| idx | offset xyz | label | success | lift m | hand contacts | floor contacts | max pen m | four avg m | thumb m | failure reasons |\n",
            "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|\n",
        ]
    )
    for row in payload["results"]:
        final = row["final_metrics"]
        contact = final["contact"]
        lines.append(
            f"| {row['index']} | `{np.round(row['offset'], 5).tolist()}` | {row['label']} | {int(row['success'])} | "
            f"{final['ball_lift_height']:.4f} | {contact['ball_hand_contact_count']} | "
            f"{contact.get('ball_floor_contact_count', 0)} | {contact['max_penetration']:.6f} | "
            f"{final['four_finger_avg_tip_ball_distance']:.4f} | {final['thumb_ball_distance']:.4f} | "
            f"{'; '.join(row['failure_reasons']) or '-'} |\n"
        )
    lines.extend(
        [
            "\n## Interpretation\n\n",
            "- This sweep checks whether the scripted pure-physics lift has a local success region around the validated demo ball pose.\n",
            "- It is a Stage2 task/API smoke artifact, not a training dataset and not a final collision-geometry validation.\n",
            "- The next step is to collect dataset v0 against the frozen observation/action/reward/done contract.\n",
        ]
    )
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a small ball-pose sweep on the Stage1 arm-hand v2 lift baseline.")
    parser.add_argument("--scene", default=str(CURRENT_LIFT_SCENE))
    parser.add_argument("--base-ball", nargs=3, type=float, default=None)
    parser.add_argument("--x-offsets", nargs="+", type=float, default=DEFAULT_X_OFFSETS)
    parser.add_argument("--y-offsets", nargs="+", type=float, default=DEFAULT_Y_OFFSETS)
    parser.add_argument("--z-offsets", nargs="+", type=float, default=DEFAULT_Z_OFFSETS)
    parser.add_argument("--default-hold-steps", type=int, default=90)
    parser.add_argument("--move-steps", type=int, default=260)
    parser.add_argument("--approach-steps", type=int, default=180)
    parser.add_argument("--hand-steps", type=int, default=120)
    parser.add_argument("--lift-steps", type=int, default=220)
    parser.add_argument("--hold-steps", type=int, default=120)
    parser.add_argument("--success-lift-height", type=float, default=0.08)
    parser.add_argument("--min-ball-hand-contacts", type=int, default=1)
    parser.add_argument("--max-ball-floor-contacts", type=int, default=0)
    parser.add_argument("--max-penetration", type=float, default=0.015)
    args = parser.parse_args()

    api = ArmHandStage1TaskAPI(args.scene)
    base_ball = np.asarray(args.base_ball, dtype=np.float64) if args.base_ball is not None else api.get_ball_pose()["position"].copy()
    offsets = grid_offsets(args.x_offsets, args.y_offsets, args.z_offsets)
    results = [run_pose(api, idx, base_ball, offset, args) for idx, offset in enumerate(offsets)]
    success_count = sum(1 for row in results if row["success"])
    if success_count == len(results):
        status = "PASS"
    elif success_count > 0:
        status = "PARTIAL"
    else:
        status = "FAIL"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(Path(args.scene).resolve()),
        "scene_info": api.get_scene_info(),
        "base_ball": base_ball,
        "grid": {
            "x_offsets": args.x_offsets,
            "y_offsets": args.y_offsets,
            "z_offsets": args.z_offsets,
        },
        "episode_count": len(results),
        "success_count": int(success_count),
        "status": status,
        "success_criteria": [
            f"final lift height >= {args.success_lift_height:.3f} m",
            f"ball-hand contacts >= {args.min_ball_hand_contacts}",
            f"ball-floor contacts <= {args.max_ball_floor_contacts}",
            f"max penetration <= {args.max_penetration:.3f} m",
            "state remains finite",
        ],
        "results": results,
        "training_ready": False,
    }
    write_outputs(payload)
    print(f"Status: {status} ({success_count}/{len(results)})")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {META_OUT}")


if __name__ == "__main__":
    main()
