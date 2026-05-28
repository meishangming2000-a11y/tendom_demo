#!/usr/bin/env python3
"""Position-control grasp smoke test for export4 wrist2/collision-tuned branch."""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from export4_wrist2_common import (
    DEFAULT_BALL_POSITION,
    DOCS_DIR,
    LONG_FINGER_TARGETS,
    METADATA_DIR,
    PRESHAPE_TARGETS,
    SCENE_TUNED,
    THUMB_SMOKE_TARGETS,
    actuator_names,
    ctrl_from_targets,
    json_ready,
    load_model,
    phase_metrics,
    render_standard_views,
    set_ball_position,
    step_ctrl,
    write_json,
    write_text,
)


DEFAULT_REPORT = DOCS_DIR / "export4_wrist2_collision_tuned_grasp_report.md"
DEFAULT_METADATA = METADATA_DIR / "export4_wrist2_collision_tuned_grasp.json"
DEFAULT_VISUAL_DIR = DOCS_DIR / "visual_checks_export4_wrist2_collision_tuned_grasp"


def stage_targets() -> Dict[str, Dict[str, float]]:
    return {
        "open_hand": {},
        "preshape": dict(PRESHAPE_TARGETS),
        "close_four_fingers": dict(LONG_FINGER_TARGETS),
        "close_thumb": {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS},
        "hold": {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS},
    }


def reset(model, data, mujoco, ball_position: List[float]) -> None:
    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0
    set_ball_position(model, data, mujoco, ball_position)
    mujoco.mj_forward(model, data)


def run_demo(args) -> Dict[str, Any]:
    scene = Path(args.scene).resolve()
    visual_dir = Path(args.visual_dir).resolve()
    ball_position = [args.ball_x, args.ball_y, args.ball_z]
    mujoco, model, data = load_model(scene)
    reset(model, data, mujoco, ball_position)
    names = actuator_names(model)

    viewer = None
    if args.viewer:
        import mujoco.viewer

        viewer = mujoco.viewer.launch_passive(model, data)

    stages = []
    try:
        for stage_name, targets in stage_targets().items():
            steps = int(args.hold_steps if stage_name == "hold" else args.phase_steps)
            target_ctrl = ctrl_from_targets(model, targets)
            step_ctrl(
                model,
                data,
                mujoco,
                target_ctrl,
                max(1, int(steps / max(args.speed, 1e-6))),
                ball_position=ball_position,
                pin_ball=not args.free_ball,
                viewer=viewer,
            )
            if not args.free_ball:
                set_ball_position(model, data, mujoco, ball_position)
                mujoco.mj_forward(model, data)
            metrics = phase_metrics(model, data, mujoco, ball_position)
            images = render_standard_views(model, data, mujoco, visual_dir, stage_name)
            stage_payload = {
                "name": stage_name,
                "target_joint_angles": dict(targets),
                "target_ctrl": {names[idx]: float(target_ctrl[idx]) for idx in range(model.nu)},
                "metrics": metrics,
                "images": images,
            }
            stages.append(stage_payload)
            print(
                f"{stage_name}: contacts={metrics['contact_count']} "
                f"max_pen={metrics['max_penetration']:.6f} "
                f"four_tip={metrics['four_finger_avg_tip_ball_distance']:.4f} "
                f"thumb_ball={metrics['thumb_ball_distance']:.4f}"
            )
            if viewer is not None:
                time.sleep(0.25)
    finally:
        if viewer is not None:
            viewer.close()

    hold = stages[-1]["metrics"]
    if hold["ball_hand_contact_count"] > 0 and hold["max_penetration"] < 0.008:
        status = "PASS_FOR_SCRIPTED_SMOKE"
    elif hold["four_finger_avg_tip_ball_distance"] < 0.08:
        status = "PARTIAL_NO_CONTACT_BUT_VISUALLY_CLOSE"
    else:
        status = "FAIL_GRASP_SIDE_OR_TARGET_NEEDS_REVIEW"

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(scene),
        "ball_position": ball_position,
        "ball_pinned": not args.free_ball,
        "uses_position_actuators": True,
        "direct_hand_qpos_write": False,
        "model_summary": {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "nu": int(model.nu),
            "ngeom": int(model.ngeom),
            "nsite": int(model.nsite),
        },
        "actuator_names": names,
        "stages": stages,
        "status": status,
        "notes": [
            "Ball is pinned by default to isolate hand closure and collision-proxy geometry; use --free-ball for dynamic free-object smoke.",
            "If the default -Y ball side remains far from fingertips, use the collision diagnosis mirror-side results before changing scripted targets.",
        ],
    }


def write_report(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Export4 Wrist2 Collision-Tuned Grasp Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "Scripted position-control smoke test for the experimental export4 wrist2/collision-tuned scene. "
        "The hand is controlled through MuJoCo position actuators; the script does not write hand qpos directly.\n\n",
        "## Setup\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Ball position: `{payload['ball_position']}`\n",
        f"- Ball pinned: `{payload['ball_pinned']}`\n",
        f"- Status: **{payload['status']}**\n",
        f"- Bodies/joints/actuators/geoms/sites: `{payload['model_summary']}`\n\n",
        "## Stage Metrics\n\n",
        "| stage | contacts | ball-hand contacts | max penetration | ball displacement | four-tip avg | thumb-ball | thumb-index |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for stage in payload["stages"]:
        m = stage["metrics"]
        lines.append(
            f"| {stage['name']} | {m['contact_count']} | {m['ball_hand_contact_count']} | "
            f"{m['max_penetration']:.6f} | {m['ball_displacement']:.6f} | "
            f"{m['four_finger_avg_tip_ball_distance']:.6f} | {m['thumb_ball_distance']:.6f} | "
            f"{m['thumb_index_distance']:.6f} |\n"
        )
    lines.extend(
        [
            "\n## Target Angles\n\n",
            "Only non-zero stage target angles are listed.\n\n",
        ]
    )
    for stage in payload["stages"]:
        nz = {k: v for k, v in stage["target_joint_angles"].items() if abs(v) > 1e-9}
        lines.append(f"### {stage['name']}\n\n")
        if not nz:
            lines.append("- all actuator targets zero\n\n")
            continue
        for joint, value in nz.items():
            lines.append(f"- `{joint}`: `{value:.4f}`\n")
        lines.append("\n")
    lines.extend(
        [
            "## Interpretation\n\n",
            "- `PASS_FOR_SCRIPTED_SMOKE` means the branch can be used for scripted inspection, not training.\n",
            "- `PARTIAL_NO_CONTACT_BUT_VISUALLY_CLOSE` means the closure shape is useful, but collision/ball placement still needs tuning.\n",
            "- The current `*_mcp_flex_joint` names are retained, but these joints are treated as lateral spread / abduction-adduction in the report.\n\n",
            "## Screenshots\n\n",
        ]
    )
    for stage in payload["stages"]:
        lines.append(f"- `{stage['name']}`: `{stage['images']}`\n")
    write_text(path, "".join(lines), "before_wrist2_grasp_report")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run export4 wrist2/collision-tuned position-control grasp smoke test.")
    parser.add_argument("--scene", default=str(SCENE_TUNED))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
    parser.add_argument("--ball-x", type=float, default=DEFAULT_BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=DEFAULT_BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=DEFAULT_BALL_POSITION[2])
    parser.add_argument("--phase-steps", type=int, default=160)
    parser.add_argument("--hold-steps", type=int, default=220)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--free-ball", action="store_true")
    parser.add_argument("--viewer", action="store_true")
    args = parser.parse_args()

    payload = run_demo(args)
    write_json(Path(args.metadata).resolve(), payload, "before_wrist2_grasp_metadata")
    write_report(Path(args.report).resolve(), json_ready(payload))
    print(f"Saved report: {Path(args.report).resolve()}")
    print(f"Saved metadata: {Path(args.metadata).resolve()}")


if __name__ == "__main__":
    main()
