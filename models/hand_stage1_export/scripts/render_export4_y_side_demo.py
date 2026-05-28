#!/usr/bin/env python3
"""Render +Y versus -Y ball-side demos for visual confirmation."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from export4_task_api import load_model
from export4_wrist2_common import (
    DOCS_DIR,
    LONG_FINGER_TARGETS,
    PRESHAPE_TARGETS,
    THUMB_SMOKE_TARGETS,
    json_ready,
    render_free_camera,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENE = ROOT / "mjcf" / "scene_ball_export4_palmar_ypos_collision_candidate.xml"
OUT_DIR = DOCS_DIR / "visual_checks_export4_y_side_demo"
REPORT = DOCS_DIR / "export4_y_side_visual_demo_report.md"
META = ROOT / "metadata" / "export4_y_side_visual_demo.json"

STAGE_TARGETS = {
    "open": {},
    "preshape": PRESHAPE_TARGETS,
    "close_four_fingers": LONG_FINGER_TARGETS,
    "close_thumb": {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS},
    "hold": {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS},
}

VIEWS = {
    "front": {"lookat": (0.0, 0.045, 0.20), "distance": 0.34, "azimuth": 145, "elevation": -25},
    "top": {"lookat": (0.0, 0.045, 0.20), "distance": 0.30, "azimuth": 180, "elevation": -78},
    "thumb": {"lookat": (-0.015, 0.035, 0.19), "distance": 0.26, "azimuth": 75, "elevation": -18},
}


def action_from_targets(api, targets: Dict[str, float]) -> np.ndarray:
    action = np.zeros(api.get_action_dim(), dtype=np.float64)
    for idx, actuator_name in enumerate(api.get_actuator_names()):
        joint_name = actuator_name[:-4] if actuator_name.endswith("_pos") else actuator_name
        value = float(targets.get(joint_name, 0.0))
        low, high = api.model.actuator_ctrlrange[idx]
        action[idx] = np.clip(value, low, high)
    return action


def step_to(api, target: np.ndarray, steps: int) -> None:
    start = api.data.ctrl.copy()
    for idx in range(max(1, steps)):
        alpha = idx / max(1, steps - 1)
        api.apply_action((1.0 - alpha) * start + alpha * target)
        api.step(1, pin_ball=True)


def metrics(api) -> Dict[str, Any]:
    obs = api.get_observation()
    d = obs["fingertip_ball_distances"]
    return {
        "contact_count": int(obs["contact_summary"]["contact_count"]),
        "ball_hand_contact_count": int(obs["contact_summary"]["ball_hand_contact_count"]),
        "max_penetration": float(obs["contact_summary"]["max_penetration"]),
        "four_finger_avg_tip_ball_distance": float(np.mean([d[name] for name in ("index", "middle", "ring", "little")])),
        "thumb_ball_distance": float(d["thumb"]),
    }


def render_side(scene: Path, label: str, ball_y: float, ball_z: float, steps: int) -> Dict[str, Any]:
    api = load_model(scene)
    api.reset_hand_open()
    api.set_ball_pose(0.0, ball_y, ball_z)
    side_dir = OUT_DIR / label
    side_dir.mkdir(parents=True, exist_ok=True)
    rows = {}
    images = {}
    for stage_name, targets in STAGE_TARGETS.items():
        step_to(api, action_from_targets(api, targets), steps if stage_name != "open" else 1)
        rows[stage_name] = metrics(api)
        images[stage_name] = {}
        for view_name, camera in VIEWS.items():
            output = side_dir / f"{label}_{stage_name}_{view_name}.png"
            images[stage_name][view_name] = render_free_camera(api.model, api.data, api.mujoco, output, **camera)
    return {
        "label": label,
        "ball_position": [0.0, ball_y, ball_z],
        "metrics": rows,
        "images": images,
    }


def make_sheet(left_path: Path, right_path: Path, output: Path, left_label: str, right_label: str) -> str:
    left = Image.open(left_path).convert("RGB")
    right = Image.open(right_path).convert("RGB")
    width = left.width + right.width
    title_h = 54
    height = max(left.height, right.height) + title_h
    sheet = Image.new("RGB", (width, height), (20, 22, 24))
    sheet.paste(left, (0, title_h))
    sheet.paste(right, (left.width, title_h))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        font = ImageFont.load_default()
    draw.text((20, 14), left_label, fill=(255, 255, 255), font=font)
    draw.text((left.width + 20, 14), right_label, fill=(255, 255, 255), font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return str(output)


def write_report(payload: Dict[str, Any]) -> None:
    plus = payload["plus_y"]
    minus = payload["minus_y"]
    plus_hold_contact = plus["metrics"]["hold"]["ball_hand_contact_count"]
    plus_contact_text = (
        "generates ball-hand contact in hold"
        if plus_hold_contact > 0
        else "is visually close in hold but does not generate contact in this render-only run"
    )
    lines = [
        "# Export4 +Y / -Y Visual Demo\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "Same export4 candidate scene, same scripted close target, only the ball Y side changes. "
        "This is for visual confirmation of palm/grasp side; no CAD/STL/joint names/current-baseline files were changed.\n\n",
        "## Files To Open First\n\n",
        f"- Front hold comparison: `{payload['comparison_sheets']['hold_front']}`\n",
        f"- Top hold comparison: `{payload['comparison_sheets']['hold_top']}`\n",
        f"- +Y hold front: `{plus['images']['hold']['front']['file']}`\n",
        f"- -Y hold front: `{minus['images']['hold']['front']['file']}`\n\n",
        "## Metrics\n\n",
        "| side | stage | contacts | ball-hand contacts | max penetration | four-tip avg | thumb-ball |\n",
        "|---|---|---:|---:|---:|---:|---:|\n",
    ]
    for side in (plus, minus):
        for stage_name, row in side["metrics"].items():
            lines.append(
                f"| {side['label']} | {stage_name} | {row['contact_count']} | {row['ball_hand_contact_count']} | "
                f"{row['max_penetration']:.6f} | {row['four_finger_avg_tip_ball_distance']:.6f} | "
                f"{row['thumb_ball_distance']:.6f} |\n"
            )
    lines.extend(
        [
            "\n## Visual Interpretation\n\n",
            f"- `+Y` places the ball near the closing fingertips in the current candidate scene and {plus_contact_text}.\n",
            "- `-Y` places the ball on the far/opposite side for this same scripted close and remains visually far from the fingertips.\n",
            "- Please use these images to confirm whether `+Y` is the intended palm/grasp side for export4 task scenes.\n",
        ]
    )
    write_text(REPORT, "".join(lines), "before_y_side_demo_report")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render +Y/-Y export4 visual demo.")
    parser.add_argument("--scene", default=str(DEFAULT_SCENE))
    parser.add_argument("--plus-y", type=float, default=0.08)
    parser.add_argument("--minus-y", type=float, default=-0.08)
    parser.add_argument("--ball-z", type=float, default=0.21)
    parser.add_argument("--steps", type=int, default=120)
    args = parser.parse_args()

    scene = Path(args.scene).resolve()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plus = render_side(scene, "plus_y", args.plus_y, args.ball_z, args.steps)
    minus = render_side(scene, "minus_y", args.minus_y, args.ball_z, args.steps)
    sheets = {
        "hold_front": make_sheet(
            Path(plus["images"]["hold"]["front"]["file"]),
            Path(minus["images"]["hold"]["front"]["file"]),
            OUT_DIR / "comparison_hold_front_plus_y_vs_minus_y.png",
            "+Y hold",
            "-Y hold",
        ),
        "hold_top": make_sheet(
            Path(plus["images"]["hold"]["top"]["file"]),
            Path(minus["images"]["hold"]["top"]["file"]),
            OUT_DIR / "comparison_hold_top_plus_y_vs_minus_y.png",
            "+Y hold",
            "-Y hold",
        ),
        "open_front": make_sheet(
            Path(plus["images"]["open"]["front"]["file"]),
            Path(minus["images"]["open"]["front"]["file"]),
            OUT_DIR / "comparison_open_front_plus_y_vs_minus_y.png",
            "+Y open",
            "-Y open",
        ),
    }
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(scene),
        "plus_y": plus,
        "minus_y": minus,
        "comparison_sheets": sheets,
        "notes": [
            "Same model and scripted targets; only ball Y side differs.",
            "This demo is for visual side confirmation, not training.",
        ],
    }
    write_json(META, payload, "before_y_side_demo_metadata")
    write_report(json_ready(payload))
    print(f"Saved +Y/-Y demo report: {REPORT}")
    print(f"Saved metadata: {META}")
    print(f"Open comparison: {sheets['hold_front']}")


if __name__ == "__main__":
    main()
