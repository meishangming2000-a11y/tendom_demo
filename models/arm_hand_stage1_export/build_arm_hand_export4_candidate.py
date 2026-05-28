#!/usr/bin/env python3
"""Build an experimental arm_stage1 + export4 hand MuJoCo assembly.

This creates a new combined MJCF and does not modify the source arm or hand
models. The hand is attached as a real child body under arm `ee_tool_frame`
rather than rendered as a separate model at a coincident point.
"""

from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[3]
OUT_ROOT = Path(__file__).resolve().parent
ARCHIVE_DIR = OUT_ROOT / "archive"
DOCS_DIR = OUT_ROOT / "docs"
METADATA_DIR = OUT_ROOT / "metadata"
VISUAL_DIR = OUT_ROOT / "visual_checks"

ARM_XML = ROOT / "simulations" / "models" / "arm_stage1_export" / "robot.xml"
HAND_XML = ROOT / "simulations" / "models" / "hand_stage1_export" / "mjcf" / "hand_stage1_export4_palmar_ypos_collision_candidate.xml"
OUT_XML = OUT_ROOT / "arm_hand_export4_palmar_ypos_candidate.xml"
SCENE_XML = OUT_ROOT / "scene_arm_hand_export4_palmar_ypos_candidate.xml"
REPORT = DOCS_DIR / "arm_hand_export4_assembly_report.md"
META = METADATA_DIR / "arm_hand_export4_assembly.json"


def backup(path: Path, tag: str) -> str | None:
    if not path.exists():
        return None
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = ARCHIVE_DIR / f"{path.stem}.{tag}.{stamp}{path.suffix}"
    shutil.copy2(path, target)
    return str(target)


def rel(path: Path, base: Path = OUT_ROOT) -> str:
    return path.resolve().relative_to(base.resolve()).as_posix()


def parse_vec(text: str | None, default: str) -> List[float]:
    raw = text or default
    return [float(v) for v in raw.split()]


def rewrite_mesh_files(root: ET.Element, prefix: str) -> None:
    for mesh in root.findall(".//mesh"):
        file_name = mesh.get("file")
        if not file_name:
            continue
        mesh.set("file", f"{prefix}/{file_name}")


def first_child(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(tag)
    if child is None:
        child = ET.SubElement(parent, tag)
    return child


def find_body(root: ET.Element, name: str) -> ET.Element | None:
    for body in root.findall(".//body"):
        if body.get("name") == name:
            return body
    return None


def remove_top_level(root: ET.Element, names: tuple[str, ...]) -> None:
    for name in names:
        for elem in list(root.findall(name)):
            root.remove(elem)


def build_combined(hand_pos: str, hand_quat: str) -> Dict[str, Any]:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    arm_tree = ET.parse(ARM_XML)
    hand_tree = ET.parse(HAND_XML)
    arm_root = arm_tree.getroot()
    hand_root = hand_tree.getroot()

    rewrite_mesh_files(arm_root, "../arm_stage1_export/meshes")
    rewrite_mesh_files(hand_root, "../hand_stage1_export/meshes_export4")

    combined = ET.Element("mujoco", {"model": "arm_hand_export4_palmar_ypos_candidate"})
    ET.SubElement(combined, "compiler", {"angle": "radian", "autolimits": "true"})
    ET.SubElement(combined, "option", {"timestep": "0.002", "gravity": "0 0 -9.81"})
    visual = ET.SubElement(combined, "visual")
    ET.SubElement(visual, "global", {"azimuth": "205", "elevation": "-22", "offwidth": "1280", "offheight": "900"})

    # Keep hand default contact settings.
    hand_default = hand_root.find("default")
    if hand_default is not None:
        combined.append(hand_default)

    asset = ET.SubElement(combined, "asset")
    for src_root in (arm_root, hand_root):
        src_asset = src_root.find("asset")
        if src_asset is None:
            continue
        for child in list(src_asset):
            asset.append(child)

    world = ET.SubElement(combined, "worldbody")
    arm_world = arm_root.find("worldbody")
    if arm_world is None:
        raise RuntimeError(f"Arm XML has no worldbody: {ARM_XML}")
    for body in arm_world.findall("body"):
        world.append(body)

    ee_tool = find_body(combined, "ee_tool_frame")
    if ee_tool is None:
        raise RuntimeError("Could not find ee_tool_frame in arm model")

    hand_world = hand_root.find("worldbody")
    if hand_world is None:
        raise RuntimeError(f"Hand XML has no worldbody: {HAND_XML}")
    hand_bodies = list(hand_world.findall("body"))
    if len(hand_bodies) != 1:
        raise RuntimeError(f"Expected one hand root body, got {len(hand_bodies)}")
    hand_root_body = hand_bodies[0]
    hand_root_body.set("pos", hand_pos)
    hand_root_body.set("quat", hand_quat)
    ee_tool.append(hand_root_body)

    actuator = ET.SubElement(combined, "actuator")
    for src_root in (arm_root, hand_root):
        src_act = src_root.find("actuator")
        if src_act is None:
            continue
        for child in list(src_act):
            actuator.append(child)

    ET.indent(ET.ElementTree(combined), space="  ")
    backup(OUT_XML, "before_arm_hand_assembly")
    ET.ElementTree(combined).write(OUT_XML, encoding="utf-8", xml_declaration=True)

    scene = f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<mujoco model=\"arm_hand_export4_scene\">
  <include file=\"{OUT_XML.name}\"/>
  <statistic extent=\"0.9\" center=\"0 0 0.12\"/>
  <visual>
    <rgba haze=\"0.15 0.25 0.35 1\"/>
    <quality shadowsize=\"8192\"/>
    <global azimuth=\"205\" elevation=\"-22\" offwidth=\"1280\" offheight=\"900\"/>
  </visual>
  <asset>
    <texture type=\"skybox\" builtin=\"gradient\" rgb1=\"0.30 0.50 0.70\" rgb2=\"0.00 0.00 0.00\" width=\"512\" height=\"3072\"/>
    <texture type=\"2d\" name=\"arm_hand_ground_checker\" builtin=\"checker\" mark=\"edge\" rgb1=\"0.20 0.30 0.40\" rgb2=\"0.10 0.20 0.30\" markrgb=\"0.80 0.80 0.80\" width=\"300\" height=\"300\"/>
    <material name=\"arm_hand_ground\" texture=\"arm_hand_ground_checker\" texrepeat=\"5 5\" texuniform=\"true\" reflectance=\"0.20\"/>
  </asset>
  <worldbody>
    <light name=\"arm_hand_fill_light\" pos=\"0 0 1\"/>
    <light name=\"arm_hand_key_light\" pos=\"0.3 0 1.5\" dir=\"0 0 -1\" directional=\"true\"/>
    <geom name=\"arm_hand_floor\" type=\"plane\" pos=\"0 0 -0.12\" size=\"0 0 0.05\" material=\"arm_hand_ground\" contype=\"0\" conaffinity=\"4\"/>
    <camera name=\"arm_hand_overview\" pos=\"-0.62 -0.72 0.42\" xyaxes=\"0.757769 -0.652523 0 0.147191 0.170932 0.974226\" fovy=\"45\"/>
    <camera name=\"arm_hand_side\" pos=\"0.65 -0.25 0.35\" xyaxes=\"0.358979 0.933346 0 -0.171268 0.0658725 0.98302\" fovy=\"45\"/>
    <camera name=\"arm_hand_wrist_closeup\" pos=\"0.25 -0.32 0.24\" xyaxes=\"0.788 0.616 0 -0.185 0.237 0.954\" fovy=\"36\"/>
  </worldbody>
</mujoco>
"""
    backup(SCENE_XML, "before_arm_hand_assembly_scene")
    SCENE_XML.write_text(scene, encoding="utf-8")

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "arm_source": str(ARM_XML),
        "hand_source": str(HAND_XML),
        "combined_xml": str(OUT_XML),
        "scene_xml": str(SCENE_XML),
        "attachment_parent": "ee_tool_frame",
        "attached_body": "hand_base_link",
        "hand_root_pos_in_ee_tool_frame": parse_vec(hand_pos, "0 0 0"),
        "hand_root_quat_in_ee_tool_frame": parse_vec(hand_quat, "1 0 0 0"),
        "notes": [
            "Experimental combined model only.",
            "The hand root is a child of ee_tool_frame, not a separate model placed at a coincident point.",
            "TODO: visually confirm flange-to-wrist orientation and decide any final fixed transform.",
        ],
    }
    write_json(META, payload)
    write_report(payload)
    return payload


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    backup(path, "before_arm_hand_assembly_meta")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_report(payload: Dict[str, Any]) -> None:
    lines = [
        "# Arm + Export4 Hand Assembly Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "Experimental MuJoCo assembly only. CAD, STL, URDF joint tree, hand current-baseline, and arm current model were not overwritten.\n\n",
        "## Sources\n\n",
        f"- Arm source: `{payload['arm_source']}`\n",
        f"- Hand source: `{payload['hand_source']}`\n\n",
        "## Outputs\n\n",
        f"- Combined hand-arm MJCF: `{payload['combined_xml']}`\n",
        f"- Scene: `{payload['scene_xml']}`\n\n",
        "## Attachment\n\n",
        f"- Parent frame/body: `{payload['attachment_parent']}`\n",
        f"- Attached hand root: `{payload['attached_body']}`\n",
        f"- Hand root local pos: `{payload['hand_root_pos_in_ee_tool_frame']}`\n",
        f"- Hand root local quat: `{payload['hand_root_quat_in_ee_tool_frame']}`\n\n",
        "## Notes\n\n",
        "- This attaches the hand as a real child body under the arm end-effector frame, avoiding the prior one-point separate-model look.\n",
        "- First pass uses identity hand orientation relative to `ee_tool_frame` and zero translation.\n",
        "- TODO: inspect close-up renders and tune the fixed hand mount transform if flange and wrist are rotated or offset.\n",
    ]
    backup(REPORT, "before_arm_hand_assembly_report")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build arm + export4 hand assembly candidate.")
    parser.add_argument("--hand-pos", default="0 0 0")
    parser.add_argument("--hand-quat", default="1 0 0 0")
    args = parser.parse_args()
    payload = build_combined(args.hand_pos, args.hand_quat)
    print(f"Saved combined XML: {payload['combined_xml']}")
    print(f"Saved scene XML: {payload['scene_xml']}")
    print(f"Saved report: {REPORT}")


if __name__ == "__main__":
    main()
