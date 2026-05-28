#!/usr/bin/env python3
"""Verify wrist_2_joint in the export4 wrist2/collision-tuned experiment."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import numpy as np

from export4_wrist2_common import (
    DOCS_DIR,
    HAND_TUNED,
    SCENE_TUNED,
    body_pos,
    json_ready,
    load_model,
    phase_metrics,
    render_standard_views,
    set_qpos_targets,
    write_json,
    write_text,
)


DEFAULT_REPORT = DOCS_DIR / "export4_wrist2_joint_fix_report.md"
DEFAULT_METADATA = Path(__file__).resolve().parents[1] / "metadata" / "export4_wrist2_joint_fix.json"
DEFAULT_VISUAL_DIR = DOCS_DIR / "visual_checks_export4_wrist2"


def parse_wrist2_xml(hand_xml: Path) -> Dict[str, Any]:
    tree = ET.parse(hand_xml)
    root = tree.getroot()
    bodies: Dict[str, str] = {}
    joint_info: Dict[str, Any] = {}

    def visit(body: ET.Element, parent: str | None) -> None:
        body_name = body.attrib.get("name", "")
        if body_name:
            bodies[body_name] = parent or "world"
        for joint in body.findall("joint"):
            if joint.attrib.get("name") == "wrist_2_joint":
                joint_info.update(
                    {
                        "parent_body": parent or "world",
                        "child_body": body_name,
                        "type": joint.attrib.get("type", ""),
                        "axis": joint.attrib.get("axis", ""),
                        "range": joint.attrib.get("range", ""),
                        "limited": joint.attrib.get("limited", ""),
                    }
                )
        for child in body.findall("body"):
            visit(child, body_name)

    world = root.find("worldbody")
    if world is not None:
        for body in world.findall("body"):
            visit(body, None)
    return joint_info


def measure_pose(model, data, mujoco, angle: float, ball_position: list[float]) -> Dict[str, Any]:
    applied = set_qpos_targets(model, data, mujoco, {"wrist_2_joint": angle}, ball_position=ball_position)
    wrist_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "wrist_middle_link")
    palm_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
    wrist = body_pos(model, data, mujoco, "wrist_middle_link")
    palm = body_pos(model, data, mujoco, "palm_link")
    relative = palm - wrist
    wrist_rot = data.xmat[wrist_id].reshape(3, 3).copy() if wrist_id >= 0 else np.eye(3)
    palm_rot = data.xmat[palm_id].reshape(3, 3).copy() if palm_id >= 0 else np.eye(3)
    relative_rot = wrist_rot.T @ palm_rot
    return {
        "requested_angle": angle,
        "applied": applied,
        "wrist_middle_link_pos": wrist,
        "palm_link_pos": palm,
        "palm_minus_wrist_middle": relative,
        "wrist_middle_link_xmat": wrist_rot,
        "palm_link_xmat": palm_rot,
        "relative_rotation_matrix": relative_rot,
        "metrics": phase_metrics(model, data, mujoco, ball_position),
    }


def write_report(path: Path, payload: Dict[str, Any]) -> None:
    xml_info = payload["xml_joint_info"]
    rows = payload["poses"]
    neg = next(row for row in rows if row["requested_angle"] < 0)
    pos = next(row for row in rows if row["requested_angle"] > 0)
    zero = next(row for row in rows if row["requested_angle"] == 0)
    delta_neg = np.asarray(neg["palm_minus_wrist_middle"]) - np.asarray(zero["palm_minus_wrist_middle"])
    delta_pos = np.asarray(pos["palm_minus_wrist_middle"]) - np.asarray(zero["palm_minus_wrist_middle"])
    rel_zero = np.asarray(zero["relative_rotation_matrix"])
    rel_neg = np.asarray(neg["relative_rotation_matrix"])
    rel_pos = np.asarray(pos["relative_rotation_matrix"])
    rot_delta_neg = rel_zero.T @ rel_neg
    rot_delta_pos = rel_zero.T @ rel_pos
    angle_neg = float(np.arccos(np.clip((np.trace(rot_delta_neg) - 1.0) / 2.0, -1.0, 1.0)))
    angle_pos = float(np.arccos(np.clip((np.trace(rot_delta_pos) - 1.0) / 2.0, -1.0, 1.0)))
    lines = [
        "# Export4 Wrist 2 Joint Fix Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "This verifies the experimental export4 branch only. CAD, STL, joint names, and the frozen current baseline were not modified.\n\n",
        "## XML Joint Info\n\n",
        f"- Hand MJCF: `{payload['hand_xml']}`\n",
        f"- Scene MJCF: `{payload['scene_xml']}`\n",
        f"- Parent body: `{xml_info.get('parent_body')}`\n",
        f"- Child body: `{xml_info.get('child_body')}`\n",
        f"- Type: `{xml_info.get('type')}`\n",
        f"- Axis: `{xml_info.get('axis')}`\n",
        f"- Range: `{xml_info.get('range')}`\n",
        f"- Limited: `{xml_info.get('limited')}`\n\n",
        "## Motion Result\n\n",
        f"- Negative test delta of palm relative to wrist_middle: `{delta_neg.tolist()}` m\n",
        f"- Positive test delta of palm relative to wrist_middle: `{delta_pos.tolist()}` m\n",
        f"- Motion norm, -0.3 rad: `{float(np.linalg.norm(delta_neg)):.6f}` m\n",
        f"- Motion norm, +0.3 rad: `{float(np.linalg.norm(delta_pos)):.6f}` m\n",
        f"- Relative orientation change, -0.3 rad: `{angle_neg:.6f}` rad\n",
        f"- Relative orientation change, +0.3 rad: `{angle_pos:.6f}` rad\n",
        f"- Status: **{payload['status']}**\n\n",
        "## Pose Metrics\n\n",
        "| requested angle | contact count | max penetration | ball-hand contacts | palm-wrist relative | relative rotation trace |\n",
        "|---:|---:|---:|---:|---|---:|\n",
    ]
    for row in rows:
        metrics = row["metrics"]
        lines.append(
            f"| {row['requested_angle']:.3f} | {metrics['contact_count']} | "
            f"{metrics['max_penetration']:.6f} | {metrics['ball_hand_contact_count']} | "
            f"`{[round(float(v), 6) for v in row['palm_minus_wrist_middle']]}` | "
            f"{float(np.trace(np.asarray(row['relative_rotation_matrix']))):.6f} |\n"
        )
    lines.extend(
        [
            "\n## Screenshots\n\n",
            f"- Before / zero: `{payload['screenshots'].get('zero', {})}`\n",
            f"- Negative: `{payload['screenshots'].get('negative', {})}`\n",
            f"- Positive: `{payload['screenshots'].get('positive', {})}`\n\n",
            "## Notes\n\n",
            "- The frozen baseline is preserved. This branch is the place to keep the wrist_2 revolute behavior if downstream checks remain stable.\n",
            "- If the visual pose looks wrong later, inspect the wrist_2 axis/csys in SolidWorks before changing the joint tree.\n",
        ]
    )
    write_text(path, "".join(lines), "before_wrist2_report")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test wrist_2_joint in export4 tuned scene.")
    parser.add_argument("--scene", default=str(SCENE_TUNED))
    parser.add_argument("--hand", default=str(HAND_TUNED))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
    parser.add_argument("--ball-x", type=float, default=0.0)
    parser.add_argument("--ball-y", type=float, default=-0.1)
    parser.add_argument("--ball-z", type=float, default=0.21)
    args = parser.parse_args()

    scene = Path(args.scene).resolve()
    hand = Path(args.hand).resolve()
    visual_dir = Path(args.visual_dir).resolve()
    ball_position = [args.ball_x, args.ball_y, args.ball_z]
    mujoco, model, data = load_model(scene)

    poses = []
    screenshots = {}
    for label, angle in (("zero", 0.0), ("negative", -0.3), ("positive", 0.3)):
        row = measure_pose(model, data, mujoco, angle, ball_position)
        poses.append(row)
        screenshots[label] = render_standard_views(model, data, mujoco, visual_dir, f"wrist2_{label}")

    zero = poses[0]
    translation_motion_norms = [
        float(np.linalg.norm(np.asarray(row["palm_minus_wrist_middle"]) - np.asarray(zero["palm_minus_wrist_middle"])))
        for row in poses[1:]
    ]
    rel_zero = poses[0]["relative_rotation_matrix"]
    orientation_motion_norms = []
    for row in poses[1:]:
        rot_delta = rel_zero.T @ row["relative_rotation_matrix"]
        orientation_motion_norms.append(float(np.arccos(np.clip((np.trace(rot_delta) - 1.0) / 2.0, -1.0, 1.0))))
    max_pen = max(float(row["metrics"]["max_penetration"]) for row in poses)
    status = "PASS"
    if max(orientation_motion_norms) < 1e-4:
        status = "FAIL_NO_RELATIVE_MOTION"
    elif max_pen > 0.02:
        status = "PARTIAL_MOTION_WITH_LARGE_PENETRATION"

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene_xml": str(scene),
        "hand_xml": str(hand),
        "ball_position": ball_position,
        "model_summary": {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "nu": int(model.nu),
            "ngeom": int(model.ngeom),
            "nsite": int(model.nsite),
        },
        "xml_joint_info": parse_wrist2_xml(hand),
        "poses": poses,
        "translation_motion_norms": translation_motion_norms,
        "orientation_motion_norms": orientation_motion_norms,
        "screenshots": screenshots,
        "status": status,
    }
    write_json(Path(args.metadata).resolve(), payload, "before_wrist2_metadata")
    write_report(Path(args.report).resolve(), json_ready(payload))
    print(f"wrist_2_joint status: {status}")
    print(f"Saved report: {Path(args.report).resolve()}")
    print(f"Saved metadata: {Path(args.metadata).resolve()}")


if __name__ == "__main__":
    main()
